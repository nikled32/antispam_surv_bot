import logging
from config import settings
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram import ChatPermissions, Bot
from services.storage import PendingUsersStorage

logger = logging.getLogger(__name__)
storage = PendingUsersStorage()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start"""
    user_id = str(update.effective_user.id)
    user_data = storage.get_user_data(user_id)

    if not user_data:
        await update.message.reply_text("Привет! Для доступа к чату нужно пройти проверку.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Я не бот", callback_data=f"captcha_{user_id}")]
    ])

    await update.message.reply_text(
        text=f"Решите капчу для доступа:\n\n{user_data['question']}",
        reply_markup=keyboard
    )


async def handle_captcha_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие кнопки капчи"""
    query = update.callback_query
    await query.answer()

    try:
        user_id = query.data.split('_')[1]
        user_data = storage.get_user_data(user_id)

        if not user_data:
            await query.edit_message_text("❌ Время проверки истекло")
            return

        context.user_data["expected_answer"] = user_data["answer"]
        await query.edit_message_text(f"Введите ответ цифрами ({user_data['question']}):")

    except Exception as e:
        logger.error(f"Ошибка обработки кнопки: {e}", exc_info=True)
        await query.edit_message_text("⚠️ Ошибка. Попробуйте позже.")


async def handle_captcha_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_answer = update.message.text

    try:
        user_data = storage.get_user_data(user_id)
        if not user_data or "expected_answer" not in context.user_data:
            admin_bot = Bot(token=settings.TOKEN)
            await admin_bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"❌ Пользователь @{update.effective_user.username} заигнорил капчу\n"
                     f"ID: {user_id}\n"
            )
            return

        if user_answer == context.user_data["expected_answer"]:
            await context.bot.restrict_chat_member(
                chat_id=user_data["chat_id"],
                user_id=update.effective_user.id,
                permissions=ChatPermissions.all_permissions()
            )
            await update.message.reply_text("✅ Проверка пройдена! Теперь вы можете писать в чате.")
            storage.remove_user(user_id)
        else:
            # Уведомление админу о неудачной попытке
            admin_bot = Bot(token=settings.TOKEN)
            await admin_bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"❌ Пользователь @{update.effective_user.username} не прошел капчу\n"
                     f"ID: {user_id}\n"
                     f"Введенный ответ: {user_answer}\n"
                     f"Правильный ответ: {context.user_data['expected_answer']}"
            )

            await update.message.reply_text("❌ Неверный ответ. Попробуйте ещё раз.")

    except Exception as e:
        logger.error(f"Ошибка проверки капчи: {e}", exc_info=True)