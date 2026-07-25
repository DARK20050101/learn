from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import hash_password, verify_password


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_by_login(db: AsyncSession, login: str) -> User | None:
    result = await db.execute(select(User).where(or_(User.email == login, User.username == login)))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    conflict = await db.scalar(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱或用户名已存在")
    user = User(
        email=str(data.email).lower(),
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, login: str, password: str) -> User | None:
    user = await get_by_login(db, login)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)
    if "email" in changes:
        changes["email"] = str(changes["email"]).lower()
    password = changes.pop("password", None)
    if password:
        changes["hashed_password"] = hash_password(password)
    if "email" in changes or "username" in changes:
        filters = []
        if "email" in changes:
            filters.append(User.email == changes["email"])
        if "username" in changes:
            filters.append(User.username == changes["username"])
        conflict = await db.scalar(select(User).where(or_(*filters), User.id != user.id))
        if conflict:
            raise HTTPException(status_code=409, detail="邮箱或用户名已存在")
    for field, value in changes.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
