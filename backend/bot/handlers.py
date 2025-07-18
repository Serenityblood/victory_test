import logging
from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from backend.bot.config import (
    ADMIN_KEY,
    ALLOWED_TO_ADMIN_MENU_ROLES,
    ALLOWED_TO_MAILING_CONSTRUCTOR_ROLES,
    DATETIME_FORMAT,
    ALLOWED_MEDIA_TYPES,
)
from backend.bot.states import MailingCreate, AdminMenu
from backend.bot.templates import start_command_text, error_text, admin_keyboard
from backend.bot.utils import (
    make_safe_request,
    keyboard_builder,
    build_keyboard_for_mailing_look,
    build_constructor_keyboard,
    generate_choose_index_entities,
    to_menu,
    get_constructor,
)
from backend.bot.mailingreader import MailingReader
from backend.bot.mailingconstructor import (
    MailingConstructor,
    NameValidationError,
    SendAtValidationError,
)


router_v1 = Router()
logger = logging.getLogger("HandlerLogger")


@router_v1.message(CommandStart())
async def start(msg: types.Message):
    output_data = dict()
    splitted = msg.text.split()
    if len(splitted) > 1:
        if splitted[1] == ADMIN_KEY:
            role = "admin"
        else:
            await msg.answer(
                text="Предоставлен неправильный ключ регистрации для админа"
            )
            return
        output_data["role"] = role
    output_data["name"] = msg.from_user.full_name if msg.from_user.full_name else None
    output_data["user_id"] = msg.from_user.id
    response = await make_safe_request(
        msg.bot.api_accessor.register_new_user, **output_data
    )
    if not response:
        await msg.answer(text=error_text)
        return
    if response.status_code == 409:
        await msg.answer(text=response.json().get("detail", error_text))
        return
    api_data = response.json()
    logger.info(
        f"Зарегистрирован новый пользователь. "
        f"id: {api_data['tg_id']}, "
        f"role: {api_data['role']}, "
        f"name: {api_data['name']}"
    )
    await msg.answer(text=start_command_text)


@router_v1.message(Command("adminmenu"))
async def adminmenu(msg: types.Message, state: FSMContext):
    await state.clear()
    user_id = msg.from_user.id
    response = await make_safe_request(msg.bot.api_accessor.get_user_by_tg_id, user_id)
    if not response:
        await msg.answer(text=error_text)
        return
    if response.status_code == 404:
        await msg.answer(text=response.json()["detail"])
        return
    data = response.json()
    if data["role"] not in ALLOWED_TO_ADMIN_MENU_ROLES:
        await msg.answer("Вы не имеете доступа к админ-меню")
        return
    await msg.answer(text="Админ меню", reply_markup=admin_keyboard)


@router_v1.callback_query(F.data == "look_mailings")
async def get_mailings(clbk: types.CallbackQuery, state: FSMContext):
    response = await make_safe_request(clbk.bot.api_accessor.get_mailings)
    if not response:
        await clbk.message.answer(text=error_text)
        return
    data = response.json()
    if not data:
        await clbk.message.answer(text="Рассылок нет", reply_markup=admin_keyboard)
    mailings_count = len(data)
    index = 0
    text = MailingReader(data[index]).render()
    text += f"\n\n Порядковый номер рассылки: {index + 1}/{mailings_count}"
    await state.set_data(data={"mailing_data": data})
    await state.set_state(AdminMenu.look_mailings)
    await clbk.answer()
    await clbk.message.answer(
        text=text,
        reply_markup=build_keyboard_for_mailing_look(index, mailings_count),
        parse_mode="HTML",
    )


@router_v1.callback_query(AdminMenu.look_mailings, F.data == "mailing_search")
async def set_index_query(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminMenu.index_query)
    await clbk.answer()
    await clbk.message.answer(
        text="Напишите порядковый номер рассылки, на которую хотите перейти. Для выхода напишите 'отмена'"
    )


@router_v1.message(AdminMenu.index_query)
async def index_search_mailng(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.clear()
        await msg.answer(text="Админ меню", reply_markup=admin_keyboard)
        return
    try:
        index = int(msg.text) - 1
    except (ValueError, TypeError):
        await msg.answer(text="Не подходит. Нужно отправить целое число")
        return
    redis_data = await state.get_data()
    mailing_data = redis_data.get("mailing_data")
    mailings_count = len(mailing_data)
    if not 0 <= index < mailings_count:
        await msg.answer(text=f"Нужно отправить число от 1 до {mailings_count}")
        return
    text = MailingReader(mailing_data[index]).render()
    text += f"\n\n Порядковый номер рассылки: {index + 1}/{mailings_count}"
    await state.set_state(AdminMenu.look_mailings)
    await msg.answer(
        text=text,
        reply_markup=build_keyboard_for_mailing_look(index, mailings_count),
        parse_mode="HTML",
    )


@router_v1.callback_query(AdminMenu.look_mailings, F.data.startswith("look_mailings_"))
async def search_mailing(clbk: types.CallbackQuery, state: FSMContext):
    redis_data = await state.get_data()
    mailing_data = redis_data.get("mailing_data")
    index = int(clbk.data.split("look_mailings_")[1])
    mailings_count = len(mailing_data)
    text = MailingReader(mailing_data[index]).render()
    text += f"\n\n Порядковый номер рассылки: {index + 1}/{mailings_count}"
    await clbk.answer()
    await clbk.message.answer(
        text=text,
        reply_markup=build_keyboard_for_mailing_look(index, mailings_count),
        parse_mode="HTML",
    )


@router_v1.callback_query(AdminMenu.look_mailings, F.data == "mailings_exit")
async def exit_mailings(clbk: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await clbk.answer()
    await clbk.message.answer(text="Админ меню", reply_markup=admin_keyboard)


@router_v1.callback_query(F.data == "change_role")
async def set_change_role(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminMenu.choose_tg_id)
    await clbk.answer()
    await clbk.message.answer(
        text="Пришлите айди пользователя, чью роль хотите изменить. Или напишите 'отмена' для выхода"
    )


@router_v1.message(AdminMenu.choose_tg_id)
async def get_user_id_to_change(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.clear()
        await msg.answer(text="Админ меню", reply_markup=admin_keyboard)
        return
    try:
        tg_id = int(msg.text)
    except (ValueError, TypeError):
        await msg.answer(text="Не подходит. Нужно отправить целое число")
        return
    user_response = await make_safe_request(
        msg.bot.api_accessor.get_user_by_tg_id, tg_id
    )
    if not user_response:
        await state.clear()
        await msg.answer(text=error_text)
        return
    if user_response.status_code == 404:
        await msg.answer(
            text=user_response.json().get("detail")
            + "\nПопробуйте ещё раз или напишите 'отмена'"
        )
        return
    await state.set_data(data={"tg_id": tg_id})
    user_data = user_response.json()
    await msg.answer(
        text=(
            f"Информация о пользователе:\n"
            f"Имя: {user_data['name']}\n"
            f"TG ID: {user_data['tg_id']}\n"
            f"Роль: {user_data['role']}"
        )
    )
    roles_response = await make_safe_request(msg.bot.api_accessor.get_user_roles)
    if not roles_response:
        await state.clear()
        await msg.answer(text=error_text)
        return
    roles = roles_response.json()["roles"]
    buttons = []
    row = []
    exit_button = [("Выход", "mailings_exit")]
    for role in roles:
        row.append((role, f"choose_role_{role}"))
    buttons.append(row)
    buttons.append(exit_button)
    await state.set_state(AdminMenu.choose_role)
    await msg.answer(
        text="Выберите роль, которую хотите установить для пользователя",
        reply_markup=keyboard_builder(buttons),
    )


@router_v1.callback_query(AdminMenu.choose_role, F.data.startswith("choose_role_"))
async def change_role(clbk: types.CallbackQuery, state: FSMContext):
    role = clbk.data.split("choose_role_")[1]
    redis_data = await state.get_data()
    tg_id = redis_data.get("tg_id")
    response = await make_safe_request(
        clbk.bot.api_accessor.update_user_role_by_tg_id, tg_id, role
    )
    if not response:
        await state.clear()
        await clbk.message.answer(text=error_text)
        return
    await state.clear()
    await clbk.answer()
    await clbk.message.answer(text="Роль пользователя успешно изменена")
    await clbk.message.answer(text="Админ меню", reply_markup=admin_keyboard)


@router_v1.message(Command("newmailing"))
async def new_maling_init(msg: types.Message, state: FSMContext):
    await state.clear()
    user_id = msg.from_user.id
    response = await make_safe_request(msg.bot.api_accessor.get_user_by_tg_id, user_id)
    if not response:
        await msg.answer(text=error_text)
        return
    if response.status_code == 404:
        await msg.answer(text=response.json()["detail"])
        return
    data = response.json()
    if data["role"] not in ALLOWED_TO_MAILING_CONSTRUCTOR_ROLES:
        await msg.answer("Вы не имеете доступа к созданию рассылок")
        return
    await state.set_state(MailingCreate.choose_name)
    await msg.answer(
        text="Придумайте название для рассылки или напишите 'отмена' для закрытия конструктора"
    )


@router_v1.message(MailingCreate.choose_name)
async def get_mailing_name(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.clear()
        await msg.answer(text="Конструктор закрыт")
        return
    name = msg.text
    if not MailingConstructor.validate_name(name):
        await msg.answer(text="Неподходящее название")
        return
    await state.update_data({"name": name})
    await state.set_state(MailingCreate.choose_message)
    await msg.answer(
        text="Введите основное сообщение, которое будет в рассылке. Доступна HTML разметка. Напишите 'отмена' для закрытия конструктора"
    )


@router_v1.message(MailingCreate.choose_message)
async def get_mailing_message(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.clear()
        await msg.answer(text="Конструктор закрыт")
        return
    message = msg.text
    await state.update_data({"message": message})
    await state.set_state(MailingCreate.choose_send_at)
    await msg.answer(
        text=f"Введите дату и точное время начала рассылки в формате **{DATETIME_FORMAT}**. Или напишите 'сразу', чтобы рассылка началась после сохранения. Напишите 'отмена' для закрытия конструктора"
    )


@router_v1.message(MailingCreate.choose_send_at)
async def get_mailing_send_at(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.clear()
        await msg.answer(text="Конструктор закрыт")
        return
    redis_data = await state.get_data()
    if msg.text == "сразу":
        send_at = None
    else:
        send_at = msg.text
        if not MailingConstructor.validate_send_at(send_at):
            await msg.answer(
                text=f"Неправильная дата. Убедитесь, что она соответствует форме: {DATETIME_FORMAT}"
            )
            return
        send_at = MailingConstructor.convert_datestring_to_correct_format(send_at)
    constructor = MailingConstructor(
        name=redis_data.get("name"),
        message=redis_data.get("message"),
        creator_id=msg.from_user.id,
        send_at=send_at,
    )
    await state.set_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "to_constructor_menu")
async def get_to_constructor_menu(clbk: types.CallbackQuery, state: FSMContext):
    constructor = await get_constructor(state)
    await to_menu(constructor, state, clbk)


@router_v1.callback_query(F.data == "add_button")
async def add_button_to_mailing(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreate.new_button_text)
    await clbk.answer()
    await clbk.message.answer(
        text="Введите текст, который будет у кнопки. Или 'отмена' для отмены добавления"
    )


@router_v1.message(MailingCreate.new_button_text)
async def get_new_button_text(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        redis_data = await state.get_data()
        constructor = MailingConstructor.from_dict(redis_data["constructor"])
        await to_menu(constructor, state, msg)
        return
    text = msg.text
    await state.update_data(data={"new_button_text": text})
    await state.set_state(MailingCreate.new_button_url)
    await msg.answer(
        text="Отправьте URL, на который будет вести кнопка. Или 'отмена' для отмены добавления"
    )


@router_v1.message(MailingCreate.new_button_url)
async def get_new_button_url(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    url = msg.text
    text = redis_data.get("new_button_text")
    constructor.add_button(text, url)
    await state.update_data({"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "add_media")
async def add_media_to_mailing(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreate.new_media_type)
    await clbk.answer()
    await clbk.message.answer(
        text=f"Введите тип вложения из предложенных: {ALLOWED_MEDIA_TYPES}. Или 'отмена' для отмены добавления"
    )


@router_v1.message(MailingCreate.new_media_type)
async def get_media_type(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        redis_data = await state.get_data()
        constructor = MailingConstructor.from_dict(redis_data["constructor"])
        await to_menu(constructor, state, msg)
        return
    media_type = msg.text
    if media_type not in ALLOWED_MEDIA_TYPES:
        await msg.answer(text=f"Нужно выбрать из предложенных: {ALLOWED_MEDIA_TYPES}")
    await state.update_data(data={"new_media_type": media_type})
    await state.set_state(MailingCreate.new_media_url)
    await msg.answer(
        text="Отправьте ссылку на вложение. Ссылка должна быть в открытом доступе. Или 'отмена' для отмены добавления"
    )


@router_v1.message(MailingCreate.new_media_url)
async def get_media_url(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    url = msg.text
    media_type = redis_data.get("new_media_type")
    constructor.add_media(media_type, url)
    await state.update_data(data={"constructor": constructor.to_dict()})
    await state.set_state(MailingCreate.constructor_menu)
    await msg.answer(
        text=constructor.represent(),
        reply_markup=build_constructor_keyboard(constructor),
        parse_mode="HTML",
    )


@router_v1.callback_query(F.data == "change_name")
async def change_name(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreate.change_name)
    await clbk.answer()
    await clbk.message.answer(
        text="Придумайте новое название для рассылки или напишите 'отмена' для возвращения в меню"
    )


@router_v1.message(MailingCreate.change_name)
async def get_new_mailing_name(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    name = msg.text
    try:
        constructor.change_name(name)
    except NameValidationError as ex:
        await msg.answer(text=ex.message)
        return
    await state.update_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "change_message")
async def get_new_mailing_message(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreate.change_message)
    await clbk.answer()
    await clbk.message.answer(
        text="Придумайте новое основное сообщение. Доступна HTML разметка. Напишите 'отмена' для возвращения в меню"
    )


@router_v1.message(MailingCreate.change_message)
async def get_new_mailing_message(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    message = msg.text
    constructor.change_message(message)
    await state.update_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "change_send_at")
async def get_new_mailing_message(clbk: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreate.change_send_at)
    await clbk.answer()
    await clbk.message.answer(
        text=f"Введите новую дату в формате {DATETIME_FORMAT}. Напишите 'сразу' для отправки при сохранении. Напишите 'отмена' для возвращения в меню"
    )


@router_v1.message(MailingCreate.change_send_at)
async def get_new_mailing_name(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    if msg.text == "сразу":
        constructor.send_now()
        await state.update_data(data={"constructor": constructor.to_dict()})
        await to_menu(constructor, state, msg)
        return
    send_at = msg.text
    try:
        constructor.change_send_at(send_at)
    except SendAtValidationError as ex:
        await msg.answer(text=ex.message)
        return
    await state.update_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "change_button")
async def get_button_id(clbk: types.CallbackQuery, state: FSMContext):
    redis_data = await state.get_data()
    keyboard = redis_data["constructor"]["keyboard"]
    text, kb = generate_choose_index_entities(keyboard, "change_button_")
    await clbk.answer()
    await clbk.message.answer(text=text, reply_markup=kb)


@router_v1.callback_query(F.data.startswith("change_button_"))
async def change_button(clbk: types.CallbackQuery, state: FSMContext):
    index = clbk.data.split("change_button_")[1]
    await state.update_data(data={"change_button_index": index})
    await state.set_state(MailingCreate.change_button_text)
    await clbk.answer()
    await clbk.message.answer(
        text="Введите новый текст кнопки или 'отмена' для выхода в меню"
    )


@router_v1.message(MailingCreate.change_button_text)
async def get_changed_button_text(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        redis_data = await state.get_data()
        constructor = MailingConstructor.from_dict(redis_data["constructor"])
        await to_menu(constructor, state, msg)
        return
    text = msg.text
    await state.update_data(data={"new_button_text": text})
    await state.set_state(MailingCreate.new_button_url)
    await msg.answer(
        text="Отправьте URL, на который будет вести кнопка. Или 'отмена' для отмены изменений"
    )


@router_v1.message(MailingCreate.change_button_url)
async def get_changed_button_url(msg: types.Message, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if msg.text == "отмена":
        await to_menu(constructor, state, msg)
        return
    url = msg.text
    text = redis_data.get("new_button_text")
    index = redis_data.get("change_button_index")
    constructor.replace_button(index, text, url)
    await state.update_data({"constructor": constructor.to_dict()})
    await to_menu(constructor, state, msg)


@router_v1.callback_query(F.data == "delete_button")
async def get_delete_button_index(clbk: types.CallbackQuery, state: FSMContext):
    redis_data = await state.get_data()
    keyboard = redis_data["constructor"]["keyboard"]
    text, kb = generate_choose_index_entities(keyboard, "delete_button_")
    await clbk.answer()
    await clbk.message.answer(text=text, reply_markup=kb)


@router_v1.callback_query(F.data.startswith("delete_button_"))
async def delete_button(clbk: types.CallbackQuery, state: FSMContext):
    index = clbk.data.split("delete_button_")[1]
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    constructor.delete_button(index)
    await state.update_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, clbk)


@router_v1.callback_query(F.data == "delete_media")
async def confirm_delete_media(clbk: types.CallbackQuery, state: FSMContext):
    buttons = [[("Да", "delete_media_1"), ("Нет", "delete_media_0")]]
    await clbk.answer()
    await clbk.message.answer(
        text="Точно удаляем медиа?", reply_markup=keyboard_builder(buttons)
    )


@router_v1.callback_query(F.data.startswith("delete_media_"))
async def delete_media(clbk: types.CallbackQuery, state: FSMContext):
    confirm = clbk.data.split("delete_media_")[1]
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if confirm == "0":
        await to_menu(constructor, state, clbk)
        return
    constructor.delete_media()
    await state.update_data(data={"constructor": constructor.to_dict()})
    await to_menu(constructor, state, clbk)


@router_v1.callback_query(F.data == "save_mailing")
async def save_mailing(clbk: types.CallbackQuery, state: FSMContext):
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    response = await make_safe_request(
        clbk.bot.api_accessor.create_new_mailing, **constructor.to_db()
    )
    if not response:
        await clbk.answer()
        await clbk.message.answer(
            text="Возникли неполадки при отправке, попробуйте позже",
            reply_markup=build_constructor_keyboard(constructor),
            parse_mode="HTML",
        )
        return
    if response.status_code == 422:
        await clbk.answer()
        await clbk.message.answer(
            text="Какие-то данные в запросе неправильные. Рассылка не сохранена",
            reply_markup=build_constructor_keyboard(constructor),
            parse_mode="HTML",
        )
        return
    await clbk.answer()
    await state.clear()
    await clbk.message.answer(text="Рассылка сохранена")


@router_v1.callback_query(F.data == "exit_constructor")
async def exit_constructor_confirm(clbk: types.CallbackQuery, state: FSMContext):
    buttons = [[("Да", "exit_constructor_1"), ("Нет", "exit_constructor_0")]]
    await clbk.answer()
    await clbk.message.answer(
        text="Точно выходим? Несохраненные данные будут утеряны",
        reply_markup=keyboard_builder(buttons),
    )


@router_v1.callback_query(F.data.startswith("exit_constructor_"))
async def exit_constructor(clbk: types.CallbackQuery, state: FSMContext):
    confirm = clbk.data.split("exit_constructor_")[1]
    redis_data = await state.get_data()
    constructor = MailingConstructor.from_dict(redis_data["constructor"])
    if confirm == "0":
        await to_menu(constructor, state, clbk)
        return
    await state.clear()
    await clbk.answer()
    await clbk.message.answer(text="Вы вышли из конструктора")
