import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from config import SELLER_CHAT_ID
from models import Order

logger = logging.getLogger(__name__)


def _seller_action_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Bàn phím inline đính kèm thông báo đơn — cho phép seller xác nhận/huỷ."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Đã làm xong",  callback_data=f"done_{order_id}"),
            InlineKeyboardButton("❌ Huỷ đơn",      callback_data=f"cancel_{order_id}"),
        ]
    ])


async def send_order_to_seller(bot: Bot, order: Order) -> bool:
    """
    Gửi chi tiết đơn hàng đến SELLER_CHAT_ID kèm nút xác nhận/huỷ.

    Returns:
        True nếu gửi thành công, False nếu thất bại.
    """
    message = (
        f"🔔 <b>ĐƠN HÀNG MỚI!</b>\n\n"
        f"{order.full_summary()}"
    )

    try:
        await bot.send_message(
            chat_id=SELLER_CHAT_ID,
            text=message,
            parse_mode="HTML",
            reply_markup=_seller_action_keyboard(order.order_id),
        )
        logger.info("Đã gửi đơn #%s đến seller.", order.order_id)
        return True
    except TelegramError as e:
        logger.error("Gửi thông báo seller thất bại (đơn #%s): %s", order.order_id, e)
        return False
