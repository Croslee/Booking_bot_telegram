"""
Tập trung toàn bộ logic tạo InlineKeyboardMarkup.
Tách ra file riêng để handlers không bị rối bởi UI code.
"""
from typing import Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models import CartItem, MenuItem

# ──────────────────────────────────────────────
# Màn hình chào / welcome
# ──────────────────────────────────────────────

def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Đặt hàng ngay", callback_data="start_order")],
    ])


# ──────────────────────────────────────────────
# Danh mục
# ──────────────────────────────────────────────

CATEGORY_EMOJI: Dict[str, str] = {
    "Trà Sữa": "🧋",
    "Trà Trái Cây": "🍓",
    "Cà Phê": "☕",
    "Đá Xay": "🧊",
    "Topping": "✨",
}

def category_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"{CATEGORY_EMOJI.get(cat, '🍹')} {cat}",
            callback_data=f"cat_{cat}"
        )]
        for cat in categories
    ]
    buttons.append([InlineKeyboardButton("🛒 Xem giỏ hàng", callback_data="view_cart")])
    return InlineKeyboardMarkup(buttons)


# ──────────────────────────────────────────────
# Danh sách món trong một danh mục
# ──────────────────────────────────────────────

def items_keyboard(items: List[MenuItem]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"{item.name}  —  {item.price_display()}",
            callback_data=f"item_{item.item_id}"
        )]
        for item in items
    ]
    buttons.append([InlineKeyboardButton("⬅ Quay lại danh mục", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(buttons)


# ──────────────────────────────────────────────
# Chọn size
# ──────────────────────────────────────────────

def size_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥤 Size M", callback_data="size_M"),
            InlineKeyboardButton("🥤 Size L", callback_data="size_L"),
        ],
        [InlineKeyboardButton("⬅ Quay lại", callback_data="back_to_items")],
    ])


# ──────────────────────────────────────────────
# Chọn số lượng
# ──────────────────────────────────────────────

def quantity_keyboard() -> InlineKeyboardMarkup:
    qty_buttons = [
        InlineKeyboardButton(str(i), callback_data=f"qty_{i}")
        for i in range(1, 6)
    ]
    return InlineKeyboardMarkup([
        qty_buttons,
        [InlineKeyboardButton("Nhập số lượng khác", callback_data="qty_custom")],
        [InlineKeyboardButton("⬅ Quay lại", callback_data="back_to_size")],
    ])


# ──────────────────────────────────────────────
# Giỏ hàng
# ──────────────────────────────────────────────

def cart_keyboard(cart: List[CartItem]) -> InlineKeyboardMarkup:
    buttons = []

    # Nút xóa từng món
    for idx, ci in enumerate(cart):
        buttons.append([
            InlineKeyboardButton(
                f"🗑 Xóa: {ci.item.name}",
                callback_data=f"remove_{idx}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("➕ Thêm món", callback_data="add_more"),
        InlineKeyboardButton("🗑 Xóa tất cả", callback_data="cart_clear"),
    ])
    buttons.append([
        InlineKeyboardButton("✅ Đặt hàng", callback_data="cart_checkout"),
        InlineKeyboardButton("❌ Huỷ đơn", callback_data="cart_cancel"),
    ])
    return InlineKeyboardMarkup(buttons)


def empty_cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Mua hàng ngay", callback_data="add_more")],
    ])


# ──────────────────────────────────────────────
# Xác nhận đơn
# ──────────────────────────────────────────────

def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Xác nhận đặt hàng", callback_data="order_confirm")],
        [InlineKeyboardButton("✏️ Sửa thông tin giao hàng", callback_data="order_edit")],
        [InlineKeyboardButton("❌ Huỷ đơn", callback_data="order_cancel")],
    ])


# ──────────────────────────────────────────────
# Dùng lại thông tin giao hàng đã lưu
# ──────────────────────────────────────────────

def saved_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Dùng địa chỉ này", callback_data="profile_use")],
        [InlineKeyboardButton("📝 Nhập địa chỉ mới",  callback_data="profile_new")],
    ])


# ──────────────────────────────────────────────
# Sau khi đặt hàng thành công
# ──────────────────────────────────────────────

def post_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Đặt thêm món", callback_data="order_again")],
        [InlineKeyboardButton("👋 Xong rồi, hẹn lần sau", callback_data="order_done")],
    ])
