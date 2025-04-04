import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN") or "ВАШ_ТОКЕН"
CAPTCHA_TIME = 120                             # Время на капчу (сек)
ADMIN_IDS = [123456789]                        # ID админов
WHITELIST = ["GoodBot", "HelperBot"]           # Разрешённые боты

# Настройки мьюта
DEFAULT_PERMISSIONS = {
    "can_send_messages": False,
    "can_send_media_messages": False,
    "can_send_other_messages": False,
    "can_add_web_page_previews": False
}