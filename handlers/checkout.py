import logging
import random
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import SHOP_NAME
from handlers.keyboards import category_keyboard, confirm_keyboard, post_order_keyboard
from handlers.states import (
    BROWSE_CATEGORY,
    CART_VIEW,
    COLLECT_ADDRESS,
    COLLECT_NAME,
    COLLECT_PHONE,
    CONFIRM_ORDER,
    POST_ORDER,
    USE_SAVED_PROFILE,
)
from models import DeliveryInfo, Order

logger = logging.getLogger(__name__)

# Regex kiểm tra số điện thoại Việt Nam
_PHONE_RE = re.compile(r"^(0|84)[0-9]{9}$")


def _new_order_id() -> str:
    """Sinh mã đơn hàng: DDMMHHMMSS + 2 số ngẫu nhiên."""
    return datetime.now().strftime("%d%m%H%M%S") + f"{random.randint(0, 99):02d}"


# ──────────────────────────────────────────────
# Dùng profile đã lưu / nhập địa chỉ mới
# ──────────────────────────────────────────────

async def use_saved_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách chọn '✅ Dùng địa chỉ này' → build order ngay từ profile đã lưu."""
    query = update.callback_query
    await query.answer()

    saved: DeliveryInfo = context.user_data.get("saved_profile")
    cart: list = context.user_data.get("cart", [])
    order_id = _new_order_id()
    order = Order(items=cart, delivery=saved, order_id=order_id,
                  user_id=update.effective_user.id)
    context.user_data["pending_order"] = order

    await query.edit_message_text(
        f"📋 <b>XÁC NHẬN ĐƠN HÀNG</b>\n\n{order.full_summary()}\n\n"
        "Thông tin trên có chính xác không?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(),
    )
    return CONFIRM_ORDER


async def enter_new_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách chọn '📝 Nhập địa chỉ mới' → bắt đầu form nhập thay thường."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 <b>THÔNG TIN GIAO HÀNG</b>\n\n"
        "Vui lòng nhập <b>Họ và tên</b> của bạn:",
        parse_mode="HTML",
    )
    return COLLECT_NAME


# ──────────────────────────────────────────────
# Bước 1: Thu thập tên
# ──────────────────────────────────────────────

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận tên khách → hỏi số điện thoại."""
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text(
            "⚠️ Tên quá ngắn. Vui lòng nhập <b>Họ và tên</b> đầy đủ:",
            parse_mode="HTML",
        )
        return COLLECT_NAME

    context.user_data["delivery_name"] = name

    await update.message.reply_text(
        f"👤 Tên: <b>{name}</b> ✅\n\n"
        "📞 Vui lòng nhập <b>Số điện thoại</b> nhận hàng:",
        parse_mode="HTML",
    )
    return COLLECT_PHONE


# ──────────────────────────────────────────────
# Bước 2: Thu thập số điện thoại
# ──────────────────────────────────────────────

async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận số điện thoại → validate → hỏi địa chỉ."""
    phone = update.message.text.strip().replace(" ", "").replace("-", "")

    if not _PHONE_RE.match(phone):
        await update.message.reply_text(
            "⚠️ Số điện thoại không hợp lệ.\n"
            "Vui lòng nhập lại (VD: <code>0901234567</code>):",
            parse_mode="HTML",
        )
        return COLLECT_PHONE

    context.user_data["delivery_phone"] = phone

    await update.message.reply_text(
        f"📞 SĐT: <b>{phone}</b> ✅\n\n"
        "📍 Vui lòng nhập <b>Địa chỉ giao hàng</b> (số nhà, đường, phường/xã, quận/huyện):",
        parse_mode="HTML",
    )
    return COLLECT_ADDRESS


# ──────────────────────────────────────────────
# Bước 3: Thu thập địa chỉ → hiển thị xác nhận
# ──────────────────────────────────────────────

async def collect_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận địa chỉ → tổng hợp đơn hàng → hiển thị để xác nhận."""
    address = update.message.text.strip()

    if len(address) < 5:
        await update.message.reply_text(
            "⚠️ Địa chỉ quá ngắn. Vui lòng nhập đầy đủ địa chỉ giao hàng:",
        )
        return COLLECT_ADDRESS

    context.user_data["delivery_address"] = address

    # Tổng hợp đơn
    cart: list = context.user_data.get("cart", [])
    delivery = DeliveryInfo(
        name=context.user_data["delivery_name"],
        phone=context.user_data["delivery_phone"],
        address=address,
    )
    order_id = _new_order_id()
    order = Order(items=cart, delivery=delivery, order_id=order_id,
                  user_id=update.effective_user.id)

    # Lưu order vào user_data để dùng lúc confirm
    context.user_data["pending_order"] = order

    await update.message.reply_text(
        f"📋 <b>XÁC NHẬN ĐƠN HÀNG</b>\n\n{order.full_summary()}\n\n"
        "Thông tin trên có chính xác không?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(),
    )
    return CONFIRM_ORDER


# ──────────────────────────────────────────────
# Xử lý xác nhận / sửa / huỷ đơn
# ──────────────────────────────────────────────

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách bấm '✅ Xác nhận' → gửi đơn cho seller → lưu lịch sử → kết thúc."""
    from handlers.notify import send_order_to_seller  # tránh circular import
    from order_history import save_order
    from user_profiles import save_profile

    query = update.callback_query
    await query.answer()

    order: Order = context.user_data.get("pending_order")

    if not order:
        await query.edit_message_text("⚠️ Không tìm thấy đơn hàng. Vui lòng đặt lại.")
        return BROWSE_CATEGORY

    # Gửi thông báo cho seller
    seller_notified = await send_order_to_seller(context.bot, order)

    # Lưu vào lịch sử đơn hàng (luôn lưu dù seller có nhận được hay không)
    save_order(order)

    # Lưu thông tin giao hàng để lần sau dùng lại
    save_profile(update.effective_user.id, order.delivery)

    if seller_notified:
        await query.edit_message_text(
            f"🎉 <b>Đặt hàng thành công!</b>\n\n"
            f"Mã đơn: <b>#{order.order_id}</b>\n"
            f"Tổng tiền: <b>{order.total:,}đ</b>\n\n"
            "Chúng mình sẽ liên hệ xác nhận trong vài phút nhé! 🙏\n"
            f"Cảm ơn bạn đã đặt hàng tại <b>{SHOP_NAME}</b> 🧋",
            parse_mode="HTML",
            reply_markup=post_order_keyboard(),
        )
    else:
        await query.edit_message_text(
            "⚠️ Đặt hàng thành công nhưng thông báo cho cửa hàng gặp sự cố.\n"
            f"Vui lòng liên hệ trực tiếp và cung cấp mã đơn: <b>#{order.order_id}</b>",
            parse_mode="HTML",
            reply_markup=post_order_keyboard(),
        )

    context.user_data.clear()
    context.user_data["has_ordered_before"] = True
    return POST_ORDER


async def handle_edit_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách bấm '✏️ Sửa thông tin' → quay lại nhập tên."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 <b>NHẬP LẠI THÔNG TIN GIAO HÀNG</b>\n\n"
        "Vui lòng nhập <b>Họ và tên</b> của bạn:",
        parse_mode="HTML",
    )
    return COLLECT_NAME


async def handle_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách bấm '❌ Huỷ đơn' → xoá giỏ → quay về menu."""
    query = update.callback_query
    await query.answer("Đơn hàng đã bị huỷ.", show_alert=True)

    context.user_data.clear()
    menu: dict = context.bot_data.get("menu", {})
    categories = list(menu.keys())

    await query.edit_message_text(
        "❌ Đã huỷ đơn hàng.\n\nBạn có muốn đặt lại không?",
        parse_mode="HTML",
        reply_markup=category_keyboard(categories),
    )
    return BROWSE_CATEGORY


# ──────────────────────────────────────────────
# Sau đặt hàng thành công: tiếp tục hay kết thúc
# ──────────────────────────────────────────────

async def handle_order_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách bấm '🛒 Đặt thêm món' → xoá giỏ → gửi tin mới về danh mục."""
    query = update.callback_query
    await query.answer()

    context.user_data.pop("cart", None)
    menu: dict = context.bot_data.get("menu", {})
    categories = list(menu.keys())

    # Xoá nút khỏi tin đặt hàng thành công (giữ nguyên nội dung)
    await query.edit_message_reply_markup(reply_markup=None)

    # Gửi tin mới bên dưới
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="📋 <b>MENU TRÀ SỮA NHÀ MÌNH</b>\n\nChọn danh mục bạn muốn xem:",
        parse_mode="HTML",
        reply_markup=category_keyboard(categories),
    )
    return BROWSE_CATEGORY


async def handle_order_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Khách bấm '👋 Xong rồi, hẹn lần sau' → gửi tin tạm biệt mới, kết thúc hội thoại."""
    query = update.callback_query
    await query.answer()

    # Xoá nút khỏi tin đặt hàng thành công (giữ nguyên nội dung)
    await query.edit_message_reply_markup(reply_markup=None)

    # Gửi tin tạm biệt mới bên dưới
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="👋 <b>Hẹn gặp lại bạn lần sau nhé!</b>\n\n"
             "Gõ /start bất kỳ lúc nào để đặt hàng tiếp 🧋",
        parse_mode="HTML",
    )
    return -1  # ConversationHandler.END
