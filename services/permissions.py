from telegram import ChatPermissions
from telegram.ext import CallbackContext


async def grant_permissions(chat_id: int, user_id: int, context: CallbackContext) -> None:
    """Снимает мьют с пользователя в группе."""
    await context.bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )