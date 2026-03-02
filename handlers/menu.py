import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.keyboards import (
    category_keyboard,
    items_keyboard,
    quantity_keyboard,
    size_keyboard,
)
from handlers.states import BROWSE_CATEGORY, BROWSE_ITEMS, ENTER_QUANTITY, SELECT_QUANTITY, SELECT_SIZE
from menu_loader import get_item_by_id
from models import CartItem

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Chọn danh mục
# ──────────────────────────────────────────────

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn một danh mục → hiển thị các món trong danh mục đó."""
    query = update.callback_query
    await query.answer()

    # callback_data dạng "cat_Trà Sữa"
    category = query.data[len("cat_"):]
    context.user_data["current_category"] = category

    menu: dict = context.bot_data.get("menu", {})
    items = menu.get(category, [])

    if not items:
        await query.edit_message_text("⚠️ Danh mục này hiện không có món nào.")
        return BROWSE_CATEGORY

    await query.edit_message_text(
        f"📂 <b>{category}</b>\n\nChọn món bạn muốn thêm vào giỏ:",
        parse_mode="HTML",
        reply_markup=items_keyboard(items),
    )
    return BROWSE_ITEMS


async def back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nút ⬅ Quay lại danh mục."""
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


# ──────────────────────────────────────────────
# Chọn món
# ──────────────────────────────────────────────

async def handle_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn một món → hỏi size (nếu không phải topping) hoặc số lượng."""
    query = update.callback_query
    await query.answer()

    item_id = query.data[len("item_"):]
    menu: dict = context.bot_data.get("menu", {})
    item = get_item_by_id(menu, item_id)

    if not item:
        await query.answer("Không tìm thấy món này.", show_alert=True)
        return BROWSE_ITEMS

    context.user_data["current_item"] = item

    if item.is_topping():
        # Topping không cần chọn size
        context.user_data["current_size"] = "N/A"
        await query.edit_message_text(
            f"✨ <b>{item.name}</b>\n"
            f"<i>{item.description}</i>\n\n"
            f"💰 Giá: <b>{item.price_m:,}đ</b>\n\n"
            "Chọn số lượng:",
            parse_mode="HTML",
            reply_markup=quantity_keyboard(),
        )
        return SELECT_QUANTITY

    # Không phải topping → hỏi size
    await query.edit_message_text(
        f"🧋 <b>{item.name}</b>\n"
        f"<i>{item.description}</i>\n\n"
        f"💰 {item.price_display()}\n\n"
        "Chọn size:",
        parse_mode="HTML",
        reply_markup=size_keyboard(),
    )
    return SELECT_SIZE


async def back_to_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nút ⬅ Quay lại danh sách món."""
    query = update.callback_query
    await query.answer()

    category = context.user_data.get("current_category", "")
    menu: dict = context.bot_data.get("menu", {})
    items = menu.get(category, [])

    await query.edit_message_text(
        f"📂 <b>{category}</b>\n\nChọn món bạn muốn thêm vào giỏ:",
        parse_mode="HTML",
        reply_markup=items_keyboard(items),
    )
    return BROWSE_ITEMS


# ──────────────────────────────────────────────
# Chọn size
# ──────────────────────────────────────────────

async def handle_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn size → hiển thị bộ chọn số lượng."""
    query = update.callback_query
    await query.answer()

    size = query.data[len("size_"):]   # "M" hoặc "L"
    context.user_data["current_size"] = size

    item = context.user_data.get("current_item")
    price = item.price(size)

    await query.edit_message_text(
        f"🧋 <b>{item.name}</b>  —  Size <b>{size}</b>\n"
        f"💰 Giá: <b>{price:,}đ / ly</b>\n\n"
        "Chọn số lượng:",
        parse_mode="HTML",
        reply_markup=quantity_keyboard(),
    )
    return SELECT_QUANTITY


async def back_to_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nút ⬅ Quay lại chọn size."""
    query = update.callback_query
    await query.answer()

    item = context.user_data.get("current_item")
    await query.edit_message_text(
        f"🧋 <b>{item.name}</b>\n"
        f"<i>{item.description}</i>\n\n"
        f"💰 {item.price_display()}\n\n"
        "Chọn size:",
        parse_mode="HTML",
        reply_markup=size_keyboard(),
    )
    return SELECT_SIZE


# ──────────────────────────────────────────────
# Chọn số lượng → thêm vào giỏ
# ──────────────────────────────────────────────

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn số lượng → thêm vào giỏ hàng → chuyển sang CART_VIEW."""
    from handlers.cart import show_cart  # import cục bộ tránh circular import

    query = update.callback_query
    await query.answer()

    quantity = int(query.data[len("qty_"):])
    item = context.user_data.get("current_item")
    size = context.user_data.get("current_size", "M")

    cart: list = context.user_data.setdefault("cart", [])
    cart.append(CartItem(item=item, size=size, quantity=quantity))

    await query.answer(f"✅ Đã thêm {item.name} vào giỏ!", show_alert=False)
    return await show_cart(update, context)


# ──────────────────────────────────────────────
# Nhập số lượng thủ công
# ──────────────────────────────────────────────

async def ask_custom_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng bấm '✏️ Nhập số khác' → yêu cầu gõ số."""
    query = update.callback_query
    await query.answer()

    item = context.user_data.get("current_item")
    size = context.user_data.get("current_size", "N/A")
    size_str = f" ({size})" if size != "N/A" else ""

    await query.edit_message_text(
        f"✏️ <b>{item.name}{size_str}</b>\n\n"
        "Nhập số lượng bạn muốn đặt (1 – 99):",
        parse_mode="HTML",
    )
    return ENTER_QUANTITY


async def handle_custom_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận số lượng do khách gõ → validate → thêm vào giỏ."""
    from handlers.cart import show_cart  # tránh circular import

    text = update.message.text.strip()

    if not text.isdigit() or not (1 <= int(text) <= 99):
        await update.message.reply_text(
            "⚠️ Vui lòng nhập một số nguyên từ <b>1</b> đến <b>99</b>:",
            parse_mode="HTML",
        )
        return ENTER_QUANTITY

    quantity = int(text)
    item = context.user_data.get("current_item")
    size = context.user_data.get("current_size", "M")

    cart: list = context.user_data.setdefault("cart", [])
    cart.append(CartItem(item=item, size=size, quantity=quantity))

    await update.message.reply_text(
        f"✅ Đã thêm <b>{quantity} × {item.name}</b> vào giỏ!",
        parse_mode="HTML",
    )
    return await show_cart(update, context)
