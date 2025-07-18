from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from db.models import Mailing, User
from api.mailing.schemas import MailingRead, MailingCreate, MailingUpdate


mailing_router = APIRouter(prefix="/mailings", tags=["Рассылки"])


@mailing_router.get(
    "/",
    response_model=List[MailingRead],
    summary="Получить список всех ожидающих рассылок",
    description="""
Возвращает все рассылки со статусом "pending" (ожидающие отправки), отсортированные по времени отправки (`send_at`).

**Ответ:**
- 200: Список рассылок в формате MailingRead
""",
)
async def get_mailings(session: AsyncSession = Depends(get_session)):
    query = select(Mailing).where(Mailing.status == "pending").order_by(Mailing.send_at)
    result = await session.execute(query)
    mailings = result.scalars().all()
    return [MailingRead.model_validate(m) for m in mailings]


@mailing_router.post(
    "/",
    response_model=MailingRead,
    status_code=201,
    summary="Создать новую рассылку",
    description="""
Создаёт новую рассылку.

**Поля запроса:**
- name (str): Название рассылки
- send_at (datetime): Время отправки рассылки
- message (str): Текст сообщения
- extra (dict, опционально): Дополнительные параметры (медиа, кнопки и т.д.)
- creator_id (int): Telegram ID пользователя-автора

**Ответ:**
- 201: Данные созданной рассылки
- 404: Пользователь-автор не найден (если creator_id невалидный)
""",
)
async def create_mailing(
    data: MailingCreate,
    session: AsyncSession = Depends(get_session),
):
    user_tg_id = data.creator_id
    result = await session.execute(select(User).where(User.tg_id == user_tg_id))
    user = result.scalar_one_or_none()
    data.creator_id = user.id
    db_obj = Mailing(**data.model_dump(exclude_unset=True))
    session.add(db_obj)
    # try:
    await session.commit()
    await session.refresh(db_obj)
    return MailingRead.model_validate(db_obj)


@mailing_router.patch(
    "/{mailing_id}",
    response_model=MailingRead,
    summary="Обновить данные рассылки",
    description="""
Частично обновляет рассылку по её id.

**Параметры пути:**
- mailing_id (int): ID рассылки

**Тело запроса:**
- Любые изменяемые поля рассылки (см. MailingUpdate)

**Ответ:**
- 200: Обновлённая рассылка
- 404: Такая рассылка не найдена
- 400: Ошибка обновления (например, конфликт данных)
""",
)
async def update_mailing(
    mailing_id: int,
    data: MailingUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Mailing).where(Mailing.id == mailing_id))
    db_obj = result.scalar_one_or_none()
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Такой рассылки нет")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(db_obj, k, v)
    try:
        await session.commit()
        await session.refresh(db_obj)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Ошибка обновления")
    return MailingRead.model_validate(db_obj)


@mailing_router.delete(
    "/{mailing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить рассылку",
    description="""
Удаляет рассылку по её id.

**Параметры пути:**
- mailing_id (int): ID рассылки

**Ответ:**
- 204: Успешно удалено (без тела)
- 404: Такой рассылки нет
""",
)
async def delete_mailing(
    mailing_id: int,
    session: AsyncSession = Depends(get_session),
):
    # Проверяем, есть ли такая рассылка
    result = await session.execute(select(Mailing).where(Mailing.id == mailing_id))
    mailing = result.scalar_one_or_none()
    if mailing is None:
        raise HTTPException(status_code=404, detail="Такой рассылки нет")
    await session.delete(mailing)
    await session.commit()
