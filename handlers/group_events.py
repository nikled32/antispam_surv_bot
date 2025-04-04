import logging
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.captcha_service import CaptchaGenerator
from services.storage import PendingUsersStorage

logger = logging.getLogger(__name__)
storage = PendingUsersStorage()


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает новых участников группы"""
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        try:
            # Правильные параметры для ChatPermissions в PTB 20.x
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=member.id,
                permissions=ChatPermissions(
                    can_send_messages=False,  # Базовые сообщения
                    can_send_audios=False,  # Аудио
                    can_send_documents=False,  # Документы
                    can_send_photos=False,  # Фото
                    can_send_videos=False,  # Видео
                    can_send_video_notes=False,  # Видео-заметки
                    can_send_voice_notes=False,  # Голосовые заметки
                    can_send_polls=False,  # Опросы
                    can_send_other_messages=False,  # Стикеры, GIF и др.
                    can_add_web_page_previews=False  # Превью ссылок
                )
            )

            # Генерируем капчу
            question, answer = CaptchaGenerator.generate_math_captcha()

            # Сохраняем данные
            storage.add_user(
                user_id=str(member.id),
                chat_id=str(update.effective_chat.id),
                question=question,
                answer=answer
            )

            # Отправляем капчу в ЛС
            try:
                await context.bot.send_message(
                    chat_id=member.id,
                    text=f"🔐 Для доступа к чату решите:\n\n{question}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Я не бот", callback_data=f"captcha_{member.id}")]
                    ])
                )
            except Exception as e:
                logger.error(f"Не удалось отправить ЛС: {e}")
                await update.message.reply_text(
                    f"{member.mention_html()}, напишите мне в ЛС для проверки!",
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"Ошибка обработки участника {member.id}: {e}", exc_info=True)