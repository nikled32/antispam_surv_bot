import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
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
        self.application = None
        self.shutdown_event = asyncio.Event()

    async def run(self):
        """Основной цикл работы бота"""
        try:
            # Инициализация приложения (актуальный способ для версии 20.x+)
            self.application = (
                ApplicationBuilder()
                .token(settings.TOKEN)
                .connect_timeout(30)
                .read_timeout(30)
                .concurrent_updates(True)  # Важно для обработки параллельных запросов
                .post_shutdown(self._on_shutdown)
                .build()
            )

            # Регистрация обработчиков
            self._setup_handlers()

            # Очистка предыдущих обновлений
            await self.application.bot.delete_webhook(drop_pending_updates=True)

            logger.info("Запускаем бота...")
            await self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False,
                stop_signals=[]
            )

            # Используем create_task для избежания конфликтов
            asyncio.create_task(self.application.updater.start_polling(drop_pending_updates=True))

            logger.info("Бот успешно запущен")
            await self.shutdown_event.wait()

        except asyncio.CancelledError:
            logger.info("Бот получил запрос на остановку")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            logger.critical(f"Фатальная ошибка: {e}", exc_info=True)
            raise  # После этого Fly.io перезапустит контейнер
        finally:
            await self._safe_shutdown()

    async def _on_shutdown(self, app):
        logger.info("Завершаем работу...")
        self._should_stop.set()

    def _setup_handlers(self):
        """Регистрация всех обработчиков"""
        # Обработчики из private_chat.py
        self.application.add_handler(CommandHandler("start", private_chat.handle_start))
        self.application.add_handler(CallbackQueryHandler(
            private_chat.handle_captcha_button,
            pattern="^captcha_"
        ))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
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
            logger.info("Завершение работы бота...")
            try:
                if hasattr(self.application, 'updater') and self.application.updater:
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
    # Создаем и устанавливаем глобальный event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = BotRunner()

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
        # Корректное завершение всех задач
        pending = asyncio.all_tasks(loop=loop)
        for task in pending:
            task.cancel()

        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
        logger.info("Event loop закрыт")


if __name__ == "__main__":
    main()