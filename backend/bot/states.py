from aiogram.fsm.state import StatesGroup, State


class AdminMenu(StatesGroup):
    look_mailings = State()
    index_query = State()
    change_role = State()
    choose_tg_id = State()
    choose_role = State()


class MailingCreate(StatesGroup):
    choose_name = State()
    choose_message = State()
    choose_send_at = State()
    constructor_menu = State()
    new_button_text = State()
    new_button_url = State()
    new_media_type = State()
    new_media_url = State()
    change_button_text = State()
    change_button_url = State()
    change_name = State()
    change_message = State()
    change_send_at = State()
