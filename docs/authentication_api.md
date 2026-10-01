# Privacy Eye — Authentication API Contract

This document provides the formal API specification for all authentication, session management, user security, and profile endpoints in Privacy Eye.

Base URL: `/api/v1`

---

## 1. Authentication Endpoints

### 1.1 POST `/auth/register`
Creates a new persistent database-backed user account and immediately returns authenticated tokens/cookies.

**Request Body**:
```json
{
  "email": "analyst@agency.gov",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "full_name": "Specialist Jane Doe"
}
```

**Success Response (`201 Created`)**:
```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "analyst@agency.gov",
    "full_name": "Specialist Jane Doe",
    "role": "USER",
    "is_verified": false,
    "scans_used_this_month": 0,
    "scans_limit": 20,
    "created_at": "2026-10-01T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "f7a3...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

### 1.2 POST `/auth/login`
Authenticates user credentials against Argon2id hash in PostgreSQL, creates a server-side session, and issues tokens.

**Request Body**:
```json
{
  "email": "analyst@agency.gov",
  "password": "SecurePassword123!",
  "remember_me": true
}
```

**Success Response (`200 OK`)**:
```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "analyst@agency.gov",
    "full_name": "Specialist Jane Doe",
    "role": "USER"
  },
  "tokens": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "f7a3...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```
*Sets `Set-Cookie: access_token=...; HttpOnly; SameSite=Lax; Path=/` and `refresh_token=...`.*

---

### 1.3 POST `/auth/refresh`
Rotates the session refresh token and issues a fresh access token. Reads refresh token from Cookie or request body.

**Request Body** (optional if cookie present):
```json
{
  "refresh_token": "f7a3..."
}
```

**Success Response (`200 OK`)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "d9b2...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 1.4 POST `/auth/logout`
Invalidates the current session in PostgreSQL and clears authentication cookies.

**Headers**: `Authorization: Bearer <access_token>` (or cookie)

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Session successfully terminated."
}
```

---

### 1.5 POST `/auth/logout-all`
Revokes all active sessions across all devices for the authenticated user.

**Headers**: `Authorization: Bearer <access_token>`

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "revoked_sessions": 3,
  "message": "All active sessions have been invalidated."
}
```

---

### 1.6 GET `/auth/me`
Retrieves the currently authenticated user's profile.

**Headers**: `Authorization: Bearer <access_token>` (or cookie)

**Success Response (`200 OK`)**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "analyst@agency.gov",
  "full_name": "Specialist Jane Doe",
  "role": "USER",
  "is_verified": false,
  "scans_used_this_month": 0,
  "scans_limit": 20,
  "created_at": "2026-10-01T12:00:00Z"
}
```

---

### 1.7 POST `/auth/change-password`
Changes the user's password, verifying their old password and re-hashing with Argon2id.

**Request Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!",
  "confirm_password": "NewSecurePassword456!"
}
```

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Password changed successfully. All other sessions have been logged out."
}
```

---

### 1.8 POST `/auth/forgot-password`
Initiates password reset workflow. Always returns a generic success message to prevent account enumeration.

**Request Body**:
```json
{
  "email": "analyst@agency.gov"
}
```

**Success Response (`200 OK`)**:
```json
{
  "message": "If an account exists with this email address, password reset instructions have been issued."
}
```

---

### 1.9 POST `/auth/reset-password`
Completes password reset using a cryptographic reset token.

**Request Body**:
```json
{
  "token": "reset-token-uuid-string",
  "new_password": "BrandNewPassword789!",
  "confirm_password": "BrandNewPassword789!"
}
```

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Password has been successfully updated. You may now sign in."
}
```

---

## 2. Session Management Endpoints

### 2.1 GET `/auth/sessions`
Lists all active sessions for the authenticated user (for the "Security & Sessions" UI).

**Success Response (`200 OK`)**:
```json
[
  {
    "id": "session-1",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "is_current": true,
    "created_at": "2026-10-01T10:00:00Z",
    "last_used_at": "2026-10-01T12:15:00Z",
    "expires_at": "2026-10-31T10:00:00Z"
  }
]
```

### 2.2 DELETE `/auth/sessions/{session_id}`
Terminates a specific session by ID.

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Session terminated."
}
```

---

## 3. Account Deletion

### 3.1 DELETE `/users/me`
Permanently deletes the authenticated user's account and cascades deletion to their sessions, analyses, and reports.

**Request Body**:
```json
{
  "password_confirmation": "SecurePassword123!"
}
```

**Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Account and all associated private data permanently deleted."
}
```
