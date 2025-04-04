import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает все необработанные исключения в боте.

    Args:
        update: Объект update, может быть None
        context: Контекст бота
    """
    try:
        # Логируем ошибку с трейсбэком
        logger.error(
            "Исключение во время обработки сообщения:",
            exc_info=context.error
        )

        # Отправляем сообщение пользователю, если возможно
        if isinstance(update, Update) and update.effective_message:
            error_text = (
                "⚠️ Произошла непредвиденная ошибка. "
                "Администратор уже уведомлен и работает над исправлением.\n"
                f"Код ошибки: {hash(context.error)}"
            )
            await update.effective_message.reply_text(error_text)

        # Дополнительная обработка специфических ошибок
        if isinstance(context.error, TelegramError):
            logger.warning(f"Telegram API ошибка: {context.error}")

    except Exception as secondary_error:
        # Если что-то пошло не так в самом обработчике ошибок
        logger.critical(
            "ОШИБКА В ОБРАБОТЧИКЕ ОШИБОК!",
            exc_info=secondary_error
        )