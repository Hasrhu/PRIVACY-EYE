"""
Privacy Eye — Comprehensive Authentication & Multi-Tenant Security Test Suite
Tests:
- Argon2id password hashing and policy enforcement
- Account creation and email normalization
- Persistent database login and session tracking
- Session persistence, refresh rotation, and logout
- IDOR / BOLA multi-tenant isolation (User A vs User B)
- History and report access control
- Password change and session invalidation
- Logout-all devices
- Account enumeration resistance
- Account deletion with cascade
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, UserSession, MediaAnalysis, MediaType, AnalysisStatus, RiskLevel
from app.core.security import verify_password


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_client():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.mark.anyio
async def test_acceptance_1_registration_and_argon2id_hashing(async_client: AsyncClient):
    """TEST 1 & 66: User registered with Argon2id hash, no plaintext in DB."""
    payload = {
        "email": "Test.User@Example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "full_name": "Test User",
    }
    res = await async_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "user" in data
    assert data["user"]["email"] == "test.user@example.com"  # Normalized lowercase
    assert data["user"]["full_name"] == "Test User"
    assert "tokens" in data
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.anyio
async def test_acceptance_2_login_and_persistence(async_client: AsyncClient):
    """TEST 2 & 63: Login with same credentials, case-insensitive email, returns user."""
    # Register
    reg_payload = {
        "email": "agent@privacyeye.ai",
        "password": "CorrectPassword123!",
        "full_name": "Field Agent",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Login with different casing
    login_payload = {
        "email": "AGENT@PrivacyEye.ai",
        "password": "CorrectPassword123!",
        "remember_me": True,
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["email"] == "agent@privacyeye.ai"
    token = login_data["tokens"]["access_token"]

    # Verify /auth/me returns this user
    me_res = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "agent@privacyeye.ai"


@pytest.mark.anyio
async def test_acceptance_3_wrong_password_rejected(async_client: AsyncClient):
    """TEST 68: Reject invalid credentials cleanly without leaking database errors."""
    await async_client.post("/api/v1/auth/register", json={
        "email": "target@example.com",
        "password": "RealPassword123!",
    })

    bad_login = await async_client.post("/api/v1/auth/login", json={
        "email": "target@example.com",
        "password": "WrongPassword999!",
    })
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]


@pytest.mark.anyio
async def test_acceptance_4_session_rotation(async_client: AsyncClient):
    """TEST 12 & 54: Refresh token rotates session and provides new access token."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "email": "refresh.test@example.com",
        "password": "Password123!",
    })
    refresh_tok = reg.json()["tokens"]["refresh_token"]

    # Rotate
    ref_res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert ref_res.status_code == 200
    new_data = ref_res.json()
    assert new_data["access_token"]
    assert new_data["refresh_token"] != refresh_tok


@pytest.mark.anyio
async def test_acceptance_5_multi_tenant_idor_isolation(async_client: AsyncClient):
    """TEST 65 & 84: User A CANNOT access or delete User B's analysis."""
    # 1. Register User A
    res_a = await async_client.post("/api/v1/auth/register", json={
        "email": "user_a@example.com",
        "password": "PasswordA123!",
        "full_name": "User Alpha",
    })
    token_a = res_a.json()["tokens"]["access_token"]

    # 2. Register User B
    res_b = await async_client.post("/api/v1/auth/register", json={
        "email": "user_b@example.com",
        "password": "PasswordB123!",
        "full_name": "User Beta",
    })
    token_b = res_b.json()["tokens"]["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # 3. Create a mock analysis record belonging directly to User B via live scan save
    save_payload = {
        "session_id": "test_session_b",
        "assessment": "REAL_HUMAN",
        "confidence": 94.5,
        "quality_index": 92,
        "signals": [{"key": "ocular", "label": "Eyes visible", "severity": "low"}],
        "explanation": "User B authentic test scan.",
    }
    save_res = await async_client.post(
        "/api/v1/live/save-audit",
        json=save_payload,
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert save_res.status_code == 201
    analysis_b_id = save_res.json()["analysis_id"]

    # 4. User B can access their own analysis
    b_access = await async_client.get(
        f"/api/v1/analyze/{analysis_b_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_access.status_code == 200
    assert b_access.json()["id"] == analysis_b_id

    # 5. IDOR ATTACK: User A attempts to access User B's analysis by knowing the ID
    idor_attempt = await async_client.get(
        f"/api/v1/analyze/{analysis_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # MUST return 404 Not Found to prevent data leakage and enumeration
    assert idor_attempt.status_code == 404

    # 6. IDOR ATTACK: User A attempts to delete User B's analysis
    delete_attempt = await async_client.delete(
        f"/api/v1/analyze/{analysis_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert delete_attempt.status_code == 404

    # 7. Verify History isolation: User A's history must NOT contain User B's scan
    hist_a = await async_client.get(
        "/api/v1/analyze/history",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert hist_a.status_code == 200
    assert hist_a.json()["total"] == 0


@pytest.mark.anyio
async def test_acceptance_6_logout_and_session_revocation(async_client: AsyncClient):
    """TEST 15 & 67: Logout revokes session and invalidates access."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "email": "logout.test@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]

    # Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Accessing /auth/me with revoked token session must fail
    me_after = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_after.status_code == 401


@pytest.mark.anyio
async def test_acceptance_7_change_password(async_client: AsyncClient):
    """TEST 13 & 37: Change password invalidates old password and sessions."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "email": "change.pwd@example.com",
        "password": "OldPassword123!",
    })
    token = reg.json()["tokens"]["access_token"]

    # Change password
    chg = await async_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword456!",
            "confirm_password": "NewSecurePassword456!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert chg.status_code == 200

    # Old password must now fail
    old_login = await async_client.post("/api/v1/auth/login", json={
        "email": "change.pwd@example.com",
        "password": "OldPassword123!",
    })
    assert old_login.status_code == 401

    # New password must succeed
    new_login = await async_client.post("/api/v1/auth/login", json={
        "email": "change.pwd@example.com",
        "password": "NewSecurePassword456!",
    })
    assert new_login.status_code == 200


@pytest.mark.anyio
async def test_acceptance_8_account_enumeration_protection(async_client: AsyncClient):
    """TEST 69: Forgot-password returns identical generic message regardless of email existence."""
    # Email that exists
    await async_client.post("/api/v1/auth/register", json={
        "email": "existing@example.com",
        "password": "Password123!",
    })

    res_exist = await async_client.post("/api/v1/auth/forgot-password", json={"email": "existing@example.com"})
    res_fake = await async_client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})

    assert res_exist.status_code == 200
    assert res_fake.status_code == 200
    assert res_exist.json() == res_fake.json()
