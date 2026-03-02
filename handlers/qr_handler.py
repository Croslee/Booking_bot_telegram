"""
qr_handler.py — Lệnh /qr: gửi ảnh QR code ngay trong Telegram.

Dùng cho:
- Seller gõ /qr → nhận ảnh QR → forward sang Zalo, Facebook...
- Bất kỳ admin nào muốn lấy link chia sẻ nhanh
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import config
from generate_qr import qr_to_bytes

logger = logging.getLogger(__name__)


async def send_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lệnh /qr — tạo và gửi ảnh QR code về bot link.
    Hoạt động ngoài ConversationHandler nên luôn khả dụng.
    """
    if not config.BOT_USERNAME:
        await update.message.reply_text(
            "⚠️ Chưa cấu hình <code>BOT_USERNAME</code> trong file .env\n"
            "Thêm dòng: <code>BOT_USERNAME=ten_bot_cua_ban</code>",
            parse_mode="HTML",
        )
        return

    bot_url   = f"https://t.me/{config.BOT_USERNAME}"
    shop_name = config.SHOP_NAME

    await update.message.reply_text("⏳ Đang tạo QR code...")

    try:
        buffer = qr_to_bytes(bot_url, shop_name)
        await update.message.reply_photo(
            photo=buffer,
            caption=(
                f"<b>QR code đặt hàng — {shop_name}</b>\n\n"
                f"🔗 Link trực tiếp: {bot_url}\n\n"
                "👉 <b>Cách dùng cho seller:</b>\n"
                "• <b>In ảnh này</b> dán tại quầy thu ngân\n"
                "• <b>Đăng lên Zalo</b> (story / tin nhắn nhóm)\n"
                "• Gửi link trực tiếp cho khách quen qua Zalo"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Tạo QR thất bại: %s", e)
        await update.message.reply_text(
            "❌ Tạo QR thất bại. Kiểm tra log để biết chi tiết."
        )
