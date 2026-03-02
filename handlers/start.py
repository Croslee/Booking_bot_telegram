import logging

from telegram import Update
from telegram.ext import ContextTypes

import config
from handlers.keyboards import category_keyboard, welcome_keyboard
from handlers.states import BROWSE_CATEGORY

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /start — Chào khách, giải thích bot và hiển thị nút đặt hàng."""
    # Khởi tạo giỏ hàng mới cho phiên này
    context.user_data["cart"] = []
    context.user_data["current_item"] = None
    context.user_data["current_category"] = None

    user_first_name = update.effective_user.first_name or "bạn"
    shop_name = config.SHOP_NAME

    # Phát hiện khách mới (lần đầu dùng) hay khách quay lại
    is_new = not context.user_data.get("has_ordered_before", False)

    if is_new:
        intro = (
            "👇 Nhấn để xem menu và đặt hàng ngay:"
        )
    else:
        intro = (
            f"<b>Chào mừng trở lại, {user_first_name}!</b>\n\n"
            f"Bạn muốn order gì hôm nay tại <b>{shop_name}</b>?\n\n"
            "👇 Nhấn để bắt đầu:"
        )

    await update.message.reply_text(
        intro,
        parse_mode="HTML",
        reply_markup=welcome_keyboard(),
    )
    return BROWSE_CATEGORY


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị danh sách danh mục — được gọi từ callback 'start_order'."""
    query = update.callback_query
    await query.answer()

    menu: dict = context.bot_data.get("menu", {})
    categories = list(menu.keys())

    await query.edit_message_text(
        "<b>MENU TRÀ SỮA NHÀ MÌNH</b>\n\n"
        "Chọn danh mục bạn muốn xem:",
        parse_mode="HTML",
        reply_markup=category_keyboard(categories),
    )
    return BROWSE_CATEGORY
