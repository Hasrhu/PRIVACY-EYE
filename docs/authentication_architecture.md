# Privacy Eye — Authentication & Session Architecture

**Version**: 2.0.0-production  
**Security Standard**: OWASP ASVS v4.0.3 L2 / NIST SP 800-63B  
**Author**: Authentication Architect & Lead Security Engineer  

---

## 1. Architecture Overview

Privacy Eye utilizes a **Hybrid State-Tracking Session Architecture**:
1. **Cryptographic Algorithm**: Passwords are saved exclusively as **Argon2id** hashes (with backward-compatible verification for legacy bcrypt records).
2. **Access Tokens**: Short-lived, digitally signed JSON Web Tokens (JWT) using `HS256` (60-minute default lifetime), carrying the user subject `sub`, user `role`, and `session_id`.
3. **Persistent Server-Side Sessions (`UserSession`)**: Every authenticated login creates a distinct session record in PostgreSQL/SQLite. Refresh tokens are cryptographic SHA-256 digests referencing this session record.
4. **Transport Layer**:
   - **Browser Clients (Next.js)**: Authenticated state is transported via secure `access_token` and `refresh_token` cookies (`HttpOnly`, `SameSite=Lax`, `Secure` in production) alongside standard Bearer Authorization headers for API resilience.
   - **API / Mobile Clients**: Standard `Authorization: Bearer <access_token>` headers.
5. **Remember Me**: Configures session expiry (30 days if enabled, 24 hours if disabled).

```
+-----------------------------------------------------------------------------------+
|                                  BROWSER CLIENT                                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                        Credentials / Cookies / Tokens
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                 FASTAPI GATEWAY                                   |
|   Rate Limiting (60/min)  ->  CORS Validation  ->  CSRF & SameSite Verification  |
+-----------------------------------------+-----------------------------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
       +----------------------------+            +----------------------------+
       |     AuthService (Logic)    |            |   Security Dependency      |
       |  - Argon2id Password Check |            |  - get_current_user        |
       |  - Session Creation        |            |  - require_authenticated   |
       |  - Token Issuance/Rotation |            |  - require_admin           |
       +--------------+-------------+            +-------------+--------------+
                      |                                        |
                      +-------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               DATABASE (PostgreSQL)                               |
|                                                                                   |
|   +-----------------------+     1:N      +------------------------------------+   |
|   |         users         | ------------>|              sessions              |   |
|   | (id, email, pwd_hash) |              | (id, user_id, token_hash, expires) |   |
|   +-----------+-----------+              +------------------------------------+   |
|               | 1:N                                                               |
|               +------------> media_analysis  (user_id FK)                         |
|               +------------> reports         (user_id FK)                         |
|               +------------> live_sessions   (user_id FK)                         |
|               +------------> audit_logs      (user_id FK)                         |
+-----------------------------------------------------------------------------------+
```

---

## 2. Authentication Flows

### 2.1 User Registration Flow
```
User -> Register Form -> Input Validation -> POST /api/v1/auth/register
  -> FastAPI checks email uniqueness (normalized lowercase)
  -> Password policy check (min 8 chars, 1 uppercase, 1 digit)
  -> Argon2id password hashing ($argon2id$v=19$m=65536,t=3,p=4...)
  -> Create User in PostgreSQL
  -> Create initial Session in `sessions` table
  -> Issue JWT Access Token & Refresh Token
  -> Log AuditLog("USER_REGISTERED")
  -> Return authenticated state & user profile -> Redirect to /dashboard
```

### 2.2 User Login Flow ("Remember Me" Aware)
```
User -> Login Form (email, password, remember_me) -> POST /api/v1/auth/login
  -> FastAPI fetches user by normalized email
  -> Verify password hash via Argon2id (or fallback bcrypt with auto-rehash upgrade)
  -> Verify `is_active == True`
  -> Compute TTL: 30 days if `remember_me=True`, 24 hours if `False`
  -> Create `UserSession` record (storing SHA-256 hash of refresh token, IP, User-Agent)
  -> Update `users.last_login_at`
  -> Log AuditLog("LOGIN_SUCCESS")
  -> Set HttpOnly cookies + Return TokenResponse
  -> Next.js AuthProvider updates state -> Redirect to /dashboard or `next` URL
```

### 2.3 Session Refresh & Token Rotation
```
Client Request -> 401 Unauthorized / Token Expired
  -> Client sends POST /api/v1/auth/refresh (via Cookie or JSON body)
  -> Backend hashes refresh token, validates against `sessions` table
  -> Verify session: `expires_at > now` and `revoked_at IS NULL`
  -> Session Rotation:
       - Generate new refresh token
       - Update existing session's `refresh_token_hash` and `last_used_at`
       - Generate new access token
  -> Return new tokens & set updated cookies
```

### 2.4 Single Session Logout
```
User clicks "Sign Out" -> POST /api/v1/auth/logout
  -> Backend marks active `UserSession.revoked_at = now()`
  -> Clears auth cookies (`Max-Age=0`)
  -> Log AuditLog("LOGOUT")
  -> Client clears local auth state -> Redirect to /auth/login
```

### 2.5 Multi-Device Logout ("Sign Out All Devices")
```
User clicks "Sign Out All Other Sessions" / "Logout Everywhere"
  -> POST /api/v1/auth/logout-all
  -> Backend executes: UPDATE sessions SET revoked_at = now() WHERE user_id = current_user.id
  -> Clears current cookies
  -> Log AuditLog("LOGOUT_ALL_SESSIONS")
  -> All existing refresh tokens for that user immediately fail validation
```

### 2.6 Password Change
```
User -> POST /api/v1/auth/change-password (current_password, new_password)
  -> Verify current password with Argon2id
  -> Validate new password strength
  -> Hash new password with Argon2id
  -> Update `users.hashed_password`
  -> Invalidate all existing sessions (except optional current session)
  -> Log AuditLog("PASSWORD_CHANGED")
```

---

## 3. Multi-Tenant Authorization & IDOR Protection

Privacy Eye strictly enforces **Broken Object Level Authorization (BOLA / IDOR)** prevention on the backend:
1. **No Client-Supplied User IDs**: No endpoint accepts a `user_id` parameter from the client body or query to determine ownership.
2. **Context-Derived Ownership**: The user identity is extracted purely from the cryptographically verified JWT/Session:
   ```python
   current_user: User = Depends(get_current_user)
   ```
3. **Database Query Scoping**: All database queries for user resources include explicit ownership filtering:
   ```python
   # Scoped retrieval:
   result = await db.execute(
       select(MediaAnalysis).where(
           MediaAnalysis.id == analysis_id,
           MediaAnalysis.user_id == current_user.id,
           MediaAnalysis.deleted_at.is_(None),
       )
   )
   ```
   If a user requests an ID belonging to another user, the backend returns a clean `404 Not Found` (preventing both data leakage and resource existence enumeration).
