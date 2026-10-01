# Privacy Eye — Authentication & Database Audit

**Document Status**: Production Security Audit  
**Date**: October 2026  
**Auditor**: Senior Backend Engineer, Authentication Architect & Security Specialist  

---

## 1. Executive Summary

This audit assesses the current state of authentication, session management, authorization, and data isolation in the Privacy Eye monorepo across both the FastAPI backend and Next.js frontend. It identifies existing capabilities, architectural gaps, and specifies the exact roadmap required to establish a production-grade, database-backed, persistent authentication system.

---

## 2. What Already Exists

### 2.1 Backend (FastAPI + SQLAlchemy)
1. **User Model (`backend/app/database/models.py`)**:
   - The `User` SQLAlchemy model is defined with UUID primary key `id`, unique indexed `email`, `hashed_password`, `full_name`, `role` (`UserRole.USER`, `ADMIN`, `ENTERPRISE`), `is_active`, `is_verified`, `created_at`, `updated_at`, and `last_login_at`.
   - Existing foreign-key relationships link `users.id` to `media_analysis.user_id`, `reports.user_id`, `api_keys.user_id`, and `audit_logs.user_id`.
2. **Current Authentication Routes (`backend/app/api/v1/routes/auth.py`)**:
   - `POST /api/v1/auth/register`: Accepts email, password, full_name, checks for existing email, creates user.
   - `POST /api/v1/auth/login`: Validates credentials, updates `last_login_at`, logs `AuditLog`, returns access and refresh JWT tokens.
   - `POST /api/v1/auth/refresh`: Accepts refresh token string, issues new access token.
   - `GET /api/v1/auth/me`: Returns sanitized `UserResponse`.
3. **Authentication Dependency (`backend/app/core/security.py`)**:
   - `get_current_user` extracts Bearer JWT token from `Authorization` header, decodes payload, fetches active user from database.
   - Protected routes (`analysis.py`, `reports.py`, `live_scan.py`, `users.py`) require `current_user: User = Depends(get_current_user)`.
   - Ownership validation: `analysis.py` filters queries with `MediaAnalysis.user_id == current_user.id`.

### 2.2 Frontend (Next.js 14)
1. **Login & Registration Pages (`frontend/app/auth/login/page.tsx`, `register/page.tsx`)**:
   - Implemented with React Hook Form, Lucide icons, and the Privacy Eye dark frosted glass design system.
2. **API Client (`frontend/lib/api.ts`)**:
   - Axios instance with request interceptor attaching `Authorization: Bearer <token>` from cookies (`js-cookie`).
   - Response interceptor catching `401 Unauthorized` and attempting refresh.
3. **Protected Layout (`frontend/app/dashboard/layout.tsx`)**:
   - Checks for `access_token` cookie; redirects unauthenticated visitors to `/auth/login`.

---

## 3. What Is Missing

1. **Argon2id Password Hashing**:
   - Existing code uses legacy `bcrypt` hashing with a 72-byte truncation limitation. The system lacks **Argon2id** (the state-of-the-art password hashing standard recommended by OWASP).
2. **Server-Side Session Tracking (`UserSession` Table)**:
   - Tokens are currently purely stateless JWTs with no database record of issued sessions.
   - Consequently, true session revocation, concurrent session management ("Security & Sessions" page), "Log out all devices", and compromised token blacklisting are not currently possible.
3. **Missing Authentication Endpoints**:
   - `POST /api/v1/auth/logout`: Missing endpoint to invalidate current session and clear server/client cookies.
   - `POST /api/v1/auth/logout-all`: Missing endpoint to revoke all active sessions across all devices.
   - `POST /api/v1/auth/change-password`: Missing endpoint to verify old password and set new password securely.
   - `POST /api/v1/auth/forgot-password` & `POST /api/v1/auth/reset-password`: Missing password reset pipeline with enumeration-safe responses.
   - `GET /api/v1/auth/sessions`: Missing endpoint to inspect active sessions (IP, user-agent, last seen).
   - `DELETE /api/v1/users/me`: Missing account deletion workflow with cascading data cleanup.
4. **HttpOnly & SameSite Cookie Persistence**:
   - Cookies are currently managed on the client side via `js-cookie`, exposing access/refresh tokens to client-side scripts.
   - Missing server-set `HttpOnly`, `Secure`, `SameSite=Lax/Strict` cookies with configurable "Remember Me" TTL.
5. **Centralized Frontend Authentication Context (`AuthProvider` / `useAuth`)**:
   - Auth state is currently decentralized; components independently check `Cookies.get('access_token')` or call `authApi.me()`.
   - Lacks centralized reactive user state, leading to potential hydration flicker ("flash of unauthenticated state").
6. **Password Policy & Normalization**:
   - Email normalization needs strict lowercase trimming on both frontend and backend to prevent duplicate logical accounts.
   - Password confirmation (`confirm_password`) needs validation in registration and password change forms.

---

## 4. Current Database Structure

```
+--------------------------------------------------------------+
|                            users                             |
+--------------------------------------------------------------+
| id                     UUID / String(36) [PK]                |
| email                  String(320) [UNIQUE, INDEX]           |
| hashed_password        String(255)                           |
| full_name              String(200)                           |
| role                   Enum: USER, ADMIN, ENTERPRISE         |
| is_active              Boolean (default: True)               |
| is_verified            Boolean (default: False)              |
| scans_used_this_month  Integer (default: 0)                  |
| scans_limit            Integer (default: 20)                 |
| created_at             DateTime with timezone                |
| updated_at             DateTime with timezone                |
| last_login_at          DateTime with timezone                |
+------------------------------+-------------------------------+
                               |
            +------------------+-------------------+
            |                  |                   |
            v                  v                   v
     +--------------+   +--------------+    +--------------+
     |media_analysis|   |   reports    |    |   api_keys   |
     +--------------+   +--------------+    +--------------+
     | user_id [FK] |   | user_id [FK] |    | user_id [FK] |
     +--------------+   +--------------+    +--------------+
```

---

## 5. Required Architectural Modifications

1. **Add `UserSession` Table**:
   - Fields: `id`, `user_id` (FK), `session_token_hash`, `refresh_token_hash`, `ip_address`, `user_agent`, `is_remember_me`, `expires_at`, `created_at`, `last_used_at`, `revoked_at`.
2. **Upgrade Cryptographic Module**:
   - Implement `Argon2id` hasher with fallback for legacy bcrypt verification to allow seamless password migration without breaking existing accounts.
3. **Hybrid Authentication Scheme**:
   - Support both **HttpOnly Cookie** transport (for browsers with CSRF protection) and **Bearer Header** transport (for API developers, Swagger UI, and automated clients).
4. **Centralized Frontend Auth State**:
   - Create `AuthContext.tsx` providing `user`, `isAuthenticated`, `isLoading`, `login`, `register`, `logout`, `refreshSession`.
   - Update `GlassNavbar`, `DashboardLayout`, and dashboard pages to consume this single source of truth.
5. **Strict IDOR Prevention & Testing**:
   - Comprehensive test suite asserting that User A cannot read, modify, or delete User B's scans or reports, even when knowing the UUID.
