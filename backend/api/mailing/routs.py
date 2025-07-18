from typing import List

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.db.models import Mailing, User

from .schemas import MailingRead, MailingCreate, MailingUpdate


mailing_router = APIRouter(prefix="/mailings", tags=["Рассылки"])


@mailing_router.get("/", response_model=List[MailingRead])
async def get_mailings(session: AsyncSession = Depends(get_session)):
    query = select(Mailing)
    result = await session.execute(query)
    mailings = result.scalars().all()
    return [MailingRead.model_validate(m) for m in mailings]


@mailing_router.post("/", response_model=MailingRead, status_code=201)
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
    # except IntegrityError:
    #     await session.rollback()
    #     raise HTTPException(status_code=409, detail="Такая рассылка уже есть")
    return MailingRead.model_validate(db_obj)


@mailing_router.patch("/{mailing_id}", response_model=MailingRead)
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
