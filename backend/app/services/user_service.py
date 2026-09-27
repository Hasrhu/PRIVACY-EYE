"""
User service — database operations for users.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User
from app.schemas.schemas import UserRegisterRequest
from app.core.security import hash_password


class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, body: UserRegisterRequest) -> User:
        user = User(
            id=str(uuid.uuid4()),
            email=body.email.lower(),
            hashed_password=hash_password(body.password),
            full_name=body.full_name,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user


user_service = UserService()
