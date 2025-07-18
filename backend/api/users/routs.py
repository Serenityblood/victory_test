from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from db.models import User
from api.users.schemas import UserCreate, UserRead, RoleListResponse, UserUpdate

user_router = APIRouter(prefix="/users", tags=["Пользователи"])


@user_router.post(
    "/",
    response_model=UserRead,
    summary="Создать пользователя",
    description="""
Создаёт нового пользователя.  
Если пользователь с таким tg_id уже существует — вернёт ошибку 409.

**Поля запроса:**
- name (str, опционально): Имя пользователя
- tg_id (int, обязательно): Telegram ID пользователя
- role (str, опционально): Роль (user/admin/moderator). По умолчанию "user".

**Ответ:**
- 201: Информация о созданном пользователе
- 409: Такой пользователь уже существует
""",
)
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


@user_router.get(
    "/{tg_id}",
    response_model=UserRead,
    summary="Получить пользователя по tg_id",
    description="""
Возвращает информацию о пользователе по его Telegram ID (`tg_id`).

**Параметры:**
- tg_id (int): Telegram ID пользователя

**Ответ:**
- 200: Информация о пользователе
- 404: Пользователь не найден
""",
)
async def get_user_by_tg_id(tg_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    db_user: Optional[User] = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Такого пользователя нет в базе")
    return UserRead.model_validate(db_user)


@user_router.get(
    "/constraints/roles",
    response_model=RoleListResponse,
    summary="Получить список ролей пользователей",
    description="""
Возвращает список всех возможных ролей для пользователей (enum из базы).

**Ответ:**
- 200: Список ролей (например, ["user", "admin", "moderator"])
""",
)
async def get_roles(session: AsyncSession = Depends(get_session)):
    result = await session.execute(text("SELECT unnest(enum_range(NULL::userrole));"))
    roles = [row[0] for row in result.fetchall()]
    return RoleListResponse(roles=roles)


@user_router.patch(
    "/{tg_id}",
    response_model=UserRead,
    summary="Изменить пользователя по tg_id",
    description="""
Частично обновляет данные пользователя по Telegram ID (`tg_id`).

**Параметры пути:**
- tg_id (int): Telegram ID пользователя

**Тело запроса (одно или несколько полей):**
- name (str, опционально): Имя пользователя
- role (str, опционально): Роль (user/admin/moderator)

**Ответ:**
- 200: Обновлённые данные пользователя
- 404: Пользователь не найден
- 409: Такой tg_id уже существует
""",
)
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
