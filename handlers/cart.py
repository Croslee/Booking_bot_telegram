import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.keyboards import (
    cart_keyboard,
    category_keyboard,
    empty_cart_keyboard,
    saved_profile_keyboard,
)
from handlers.states import BROWSE_CATEGORY, CART_VIEW, COLLECT_NAME, USE_SAVED_PROFILE
from models import Order

logger = logging.getLogger(__name__)


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị giỏ hàng hiện tại. Được gọi từ nhiều nơi."""
    query = update.callback_query

    cart: list = context.user_data.get("cart", [])
    order = Order(items=cart)

    text = f"🛒 <b>GIỎ HÀNG CỦA BẠN</b>\n\n{order.cart_summary()}"

    if not cart:
        text = "🛒 Giỏ hàng đang trống.\n\nChọn món để bắt đầu nhé!"
        markup = empty_cart_keyboard()
    else:
        markup = cart_keyboard(cart)

    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        # Gọi trực tiếp từ non-callback (ít xảy ra, nhưng để an toàn)
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    return CART_VIEW


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback 'view_cart' — xem giỏ từ màn hình danh mục."""
    query = update.callback_query
    await query.answer()
    return await show_cart(update, context)


async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xóa một món khỏi giỏ theo index (callback 'remove_{idx}')."""
    query = update.callback_query
    await query.answer()

    idx = int(query.data[len("remove_"):])
    cart: list = context.user_data.get("cart", [])

    if 0 <= idx < len(cart):
        removed = cart.pop(idx)
        await query.answer(f"🗑 Đã xóa {removed.item.name}", show_alert=False)

    return await show_cart(update, context)


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xóa toàn bộ giỏ hàng."""
    query = update.callback_query
    await query.answer("🗑 Đã xóa toàn bộ giỏ hàng.", show_alert=True)

    context.user_data["cart"] = []
    return await show_cart(update, context)


async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nút 'Thêm món' → quay lại màn hình chọn danh mục."""
    query = update.callback_query
    await query.answer()

    menu: dict = context.bot_data.get("menu", {})
    categories = list(menu.keys())

    await query.edit_message_text(
        "📋 <b>MENU TRÀ SỮA NHÀ MÌNH</b>\n\nChọn danh mục bạn muốn xem:",
        parse_mode="HTML",
        reply_markup=category_keyboard(categories),
    )
    return BROWSE_CATEGORY


async def proceed_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nút '✅ Đặt hàng' → kiểm tra profile đã lưu hoặc hỏi thông tin mới."""
    from user_profiles import load_profile  # tránh circular import

    query = update.callback_query
    await query.answer()

    cart: list = context.user_data.get("cart", [])
    if not cart:
        await query.answer("Giỏ hàng trống, hãy chọn món trước nhé!", show_alert=True)
        return CART_VIEW

    user_id = update.effective_user.id
    saved = load_profile(user_id)

    if saved:
        await query.edit_message_text(
            "📦 <b>THÔNG TIN GIAO HÀNG</b>\n\n"
            "Bạn muốn giao đến địa chỉ đã lưu không?\n\n"
            f"👤 {saved.name}\n"
            f"📞 {saved.phone}\n"
            f"📍 {saved.address}",
            parse_mode="HTML",
            reply_markup=saved_profile_keyboard(),
        )
        context.user_data["saved_profile"] = saved
        return USE_SAVED_PROFILE

    await query.edit_message_text(
        "📝 <b>THÔNG TIN GIAO HÀNG</b>\n\n"
        "Vui lòng nhập <b>Họ và tên</b> của bạn:",
        parse_mode="HTML",
    )
    return COLLECT_NAME
