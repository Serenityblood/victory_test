import logging
import jwt

from typing import Callable, Optional, List, Dict, Tuple, Union

from httpx import Response
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import SECRET_KEY
from states import MailingCreate
from mailingconstructor import MailingConstructor


logger = logging.getLogger("UtilsLogger")


def get_api_token():
    return jwt.encode({}, SECRET_KEY, algorithm="HS256")


async def make_safe_request(method: Callable, *args, **kwargs) -> Optional[Response]:
    """
    Функция для безопасной работы с апи
    :param method: метод класса для запроса на какую-либо точку апи
    :param args: необходимые для работы метода аргументы
    :param kwargs:
    :return:
    """
    try:
        response: Response = await method(*args, **kwargs)
        if response.status_code not in [200, 201, 204, 400, 404, 409, 422]:
            logger.debug(
                f"Что-то случилось с запросом на {response.url}, code={response.status_code}, data={response.json()}"
            )
            return None
        return response
    except Exception as e:
        logger.error(e)


def keyboard_builder(rows: List[List[Tuple]]) -> types.InlineKeyboardMarkup:
    """Дефолтный билдер клавиатуры"""
    kb = []
    for buttons in rows:
        row = []
        for text, data in buttons:
            row.append(types.InlineKeyboardButton(text=text, callback_data=data))
        kb.append(row)
    return types.InlineKeyboardMarkup(inline_keyboard=kb)


def build_keyboard_for_mailing_look(
    current_index: int, mailings_count: int
) -> types.InlineKeyboardMarkup:
    """
    Билдер для клавиатуры просмотра рассылок в админ-меню
    :param current_index:
    :param mailings_count:
    :return:
    """
    buttons = []
    kb = []
    exit_button = [("Выход", "mailings_exit")]
    change_delete_buttons = [
        ("Изменить", "change_mailing"),
        ("Удалить", "delete_mailing"),
    ]
    if mailings_count > 1:
        buttons.append([("Ввести порядковый номер", "mailing_search")])
        if current_index - 1 >= 0:
            kb.append(("<---", f"look_mailings_{current_index - 1}"))
        if current_index + 1 < mailings_count:
            kb.append(("--->", f"look_mailings_{current_index + 1}"))
    buttons.append(kb)
    buttons.append(change_delete_buttons)
    buttons.append(exit_button)
    return keyboard_builder(buttons)


def build_constructor_keyboard(
    constructor: MailingConstructor, mode: str
) -> types.InlineKeyboardMarkup:
    """
    Билдер для клавиатуры в конструкторе рассылок
    :param constructor: Конструктор с данными о рассылке
    :param mode: "create" или что-то другое, в зависимости от мода разные эндпоинты для сохранения дергаются
    :return:
    """
    buttons = []
    add_buttons = [("Добавить кнопку", "add_button")]
    change_buttons = [
        ("Изменить имя", "change_name"),
        ("Изменить время отправки", "change_send_at"),
    ]
    change_buttons_2 = [("Изменить сообщение", "change_message")]
    if mode == "create":
        exit_save_buttons = [
            ("Отправить", "save_mailing"),
            ("Выйти", "exit_constructor"),
        ]
    else:
        exit_save_buttons = [
            ("Сохранить", "save_change_mailing"),
            ("Выйти", "exit_constructor"),
        ]
    delete_buttons = []
    if constructor.has_keyboard:
        change_buttons_2.append(("Изменить кнопку", "change_button"))
        delete_buttons.append(("Удалить кнопку", "delete_button"))
    if constructor.has_media:
        add_buttons.append(("Заменить медиа", "add_media"))
        delete_buttons.append(("Удалить медиа", "delete_media"))
    else:
        add_buttons.append(("Добавить медиа", "add_media"))
    buttons.append(add_buttons)
    buttons.append(change_buttons)
    buttons.append(change_buttons_2)
    if delete_buttons:
        buttons.append(delete_buttons)
    buttons.append(exit_save_buttons)
    return keyboard_builder(buttons)


def generate_choose_index_entities(
    keyboard: List[Dict], callback_prefix: str
) -> Tuple[str, types.InlineKeyboardMarkup]:
    """
    Генерирует кнопки для выбора на основе индексов в листе keyboard
    :param keyboard:
    :param callback_prefix: перфикс перед индексом в callback_data
    :return: Возвращает кортеж из текста для ответа и клавиатуры
    """
    text = "Кнопки:\n\n"
    exit_button = [("В меню", "to_constructor_menu")]
    kb = []
    for index, button in enumerate(keyboard):
        text += f"{index}: {button}\n"
        kb.append((f"{index}", f"{callback_prefix}{index}"))
    return text, keyboard_builder([kb, exit_button])


async def to_menu(
    constructor: MailingConstructor,
    state: FSMContext,
    body_entity: Union[types.CallbackQuery, types.Message],
) -> None:
    """
    Устанавливает состояние MailingCreate.constructor_menu и возвращает в меню конструктора
    :param constructor: Конструктор с данными о рассылке
    :param state: Машина состояния
    :param body_entity: либо types.Message, либо types.CallbackData, в зависимоти от типа разные подходы
    :return:
    """
    mode = (await state.get_data()).get("constructor_mode", "create")
    if type(body_entity) is types.CallbackQuery:
        await state.set_state(MailingCreate.constructor_menu)
        await body_entity.answer()
        await body_entity.message.answer(
            text=constructor.represent(),
            reply_markup=build_constructor_keyboard(constructor, mode),
            parse_mode="HTML",
        )
    else:
        await state.set_state(MailingCreate.constructor_menu)
        await body_entity.answer(
            text=constructor.represent(),
            reply_markup=build_constructor_keyboard(constructor, mode),
            parse_mode="HTML",
        )


async def get_constructor(state: FSMContext) -> MailingConstructor:
    """Получение конструктора из кэша"""
    redis_data = await state.get_data()
    return MailingConstructor.from_dict(redis_data.get("constructor"))
