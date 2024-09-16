from aiogram.types import BotCommand

HELP = """
<b>/start</b> - начать работу
<b>/help</b> - помощь
<b>/admin_reg</b> - войти как админ
<b>/exit_admin</b> - выйти из админки
<b>/get_premium</b> - получить премиум подписку
<b>/my_premium</b> - моя премиум подписка
"""

my_commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="admin_reg", description="Войти как админ"),
        BotCommand(command="exit_admin", description="Выйти из админки"),
        BotCommand(command="get_premium", description="Получить премиум подписку"),
        BotCommand(command="my_premium", description="Моя премиум подписка"),
]