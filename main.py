import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from handlers import group_events, private_chat, errors
from config import settings

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotRunner:
    def __init__(self):
        self.application = None  # Переименовано в application для ясности
        self.shutdown_event = asyncio.Event()

    async def run(self):
        """Основной цикл работы бота"""
        try:
            # Инициализация приложения
            self.application = Application.builder() \
                .token(settings.TOKEN) \
                .connect_timeout(30) \
                .read_timeout(30) \
                .build()

            # Регистрация обработчиков
            self._setup_handlers()

            logger.info("Запуск бота...")
            await self.application.initialize()
            await self.application.start()

            # Запускаем polling
            await self.application.updater.start_polling()
            logger.info("Бот успешно запущен")

            # Ожидаем сигнала завершения
            await self.shutdown_event.wait()

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            await self._safe_shutdown()

    def _setup_handlers(self):
        """Регистрация всех обработчиков"""
        # Обработчики из private_chat.py
        self.application.add_handler(CommandHandler("start", private_chat.handle_start))
        self.application.add_handler(CallbackQueryHandler(
            private_chat.handle_captcha_button,
            pattern="^captcha_"
        ))
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            private_chat.handle_captcha_answer
        ))

        # Обработчик новых участников
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            group_events.handle_new_member
        ))

        # Обработчик ошибок
        self.application.add_error_handler(errors.error_handler)

    async def _safe_shutdown(self):
        """Безопасное завершение работы"""
        if self.application:
            try:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Ошибка при завершении: {e}")


async def shutdown(signal, runner):
    """Обработка сигналов завершения"""
    logger.info(f"Получен сигнал {signal.name}, завершение работы...")
    runner.shutdown_event.set()


def main():
    runner = BotRunner()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Настройка обработки сигналов
        if sys.platform != 'win32':
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(shutdown(s, runner))
                )

        loop.run_until_complete(runner.run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}", exc_info=True)
    finally:
        # Корректное завершение
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        logger.info("Бот завершил работу")


if __name__ == "__main__":
    main()