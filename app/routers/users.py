from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.user import Token, UserCreate, UserRead, UserUpdate
from app.services import users as user_service
from app.services.auth import create_access_token

router = APIRouter(prefix="/users", tags=["用户"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DbSession) -> UserRead:
    return await user_service.create_user(db, data)


@router.post("/login", response_model=Token)
async def login(
    db: DbSession, username: Annotated[str, Form()], password: Annotated[str, Form()]
) -> Token:
    user = await user_service.authenticate(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail="用户名/邮箱或密码错误", headers={"WWW-Authenticate": "Bearer"}
        )
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> UserRead:
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserRead:
    return await user_service.update_user(db, current_user, data)
