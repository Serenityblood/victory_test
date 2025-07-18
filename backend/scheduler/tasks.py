import asyncio
import logging

from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import select

from db import db_manager
from db.models import User, Mailing
from scheduler.report import MailingReport
from scheduler.mailing_converter import MailingSendConverter
from config import CAN_SEE_MAILING_REPORTS


logger = logging.getLogger("TasksLogger")


async def send_tg_message(url, data, chat_id):
    data.update({"chat_id": chat_id})
    async with AsyncClient() as client:
        response = await client.post(url=url, json=data)
    return response


async def check_and_send_mailings():
    """Проверяет необходимость начинать рассылки"""
    logger.debug("Начинаю проверку рассылок")
    async with db_manager.session() as session:
        # Получаем данные из бд
        moderators_result = await session.execute(
            select(User.tg_id).where(User.role.in_(CAN_SEE_MAILING_REPORTS))
        )
        moderators = list(moderators_result.scalars().all())
        user_result = await session.execute(select(User.tg_id))
        users_tg_id = list(user_result.scalars().all())
        if not users_tg_id:
            logger.debug("В базе нет пользователей для рассылок")
            return
        mailing_result = await session.execute(
            select(Mailing).where(
                (Mailing.send_at <= datetime.now(timezone.utc))
                & (Mailing.status == "pending")
            )
        )
        mailings = mailing_result.scalars().all()

        # Инициализация конвертора для преобразования данных под API TG
        converter = MailingSendConverter()
        for mailing in mailings:
            # Инициализируем объект отчета для сбора статистики
            mailing_report = MailingReport(mailing.name)

            # Запуск таймера рассылки
            mailing_report.start_timer()
            url, prepared_data = converter.prepare_to_send(mailing)

            # Создаем фоновые задачи для отправки. Слабое место для памяти в будущем,
            # если будет много пользователей - нужен контроль за количеством одновременных фоновых задач.
            # Подойдет семафор или конструкции с asyncio.wait()
            tasks = []
            for tg_id in users_tg_id:
                tasks.append(
                    asyncio.create_task(send_tg_message(url, prepared_data, tg_id))
                )
            logger.info(f"Началась рассылка {mailing.id}")

            # Ждем выполнения всех фоновых задач, чтобы собрать статистику и остановить таймер
            results = await asyncio.gather(*tasks)
            mailing_report.stop_timer()
            for response in results:
                if response.status_code in (200, 201):
                    mailing_report.add_sent()
                else:
                    logger.error(response.json())
                    mailing_report.add_error()

            # Рассылка статистики модерам
            for moderator_tg_id in moderators:
                url, prepared_data = mailing_report.prepare_data_to_send()
                asyncio.create_task(
                    send_tg_message(url, prepared_data, moderator_tg_id)
                )
            logger.info(f"Началась рассылка для модераторов с отчетом по {mailing.id}")
            mailing.status = "done"
        await session.commit()
