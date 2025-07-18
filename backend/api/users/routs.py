from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.db.models import User
from backend.api.users.schemas import UserCreate, UserRead, RoleListResponse, UserUpdate

user_router = APIRouter(prefix="/users", tags=["Пользователи"])


@user_router.post("/", response_model=UserRead)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    db_user = User(**user.model_dump())
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Вы уже зарегистрированы",
        )
    return UserRead.model_validate(db_user)
    # return JSONResponse(status_code=201, content={"hello": "hello"})


@user_router.get("/{tg_id}", response_model=UserRead)
async def get_user_by_tg_id(tg_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    db_user: Optional[User] = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Такого пользователя нет в базе")
    return UserRead.model_validate(db_user)


@user_router.get("/constraints/roles", response_model=RoleListResponse)
async def get_roles(session: AsyncSession = Depends(get_session)):
    result = await session.execute(text("SELECT unnest(enum_range(NULL::userrole));"))
    roles = [row[0] for row in result.fetchall()]
    return RoleListResponse(roles=roles)


@user_router.patch("/{tg_id}", response_model=UserRead)
async def update_user_by_tg_id(
    tg_id: int,
    update: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    data = update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_user, key, value)

    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="User with this tg_id already exists",
        )
    return UserRead.model_validate(db_user)
