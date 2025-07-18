from .utils import keyboard_builder


start_command_text = "Вы подписались на рассылки от меня =)"
error_text = "Что-то пошло не так, попробуйте позже"
admin_keyboard = keyboard_builder(
    [[("Изменить роль", "change_role"), ("Посмотреть рассылки", "look_mailings")]]
)
