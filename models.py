from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MenuItem:
    """Đại diện cho một món trong menu."""

    item_id: str
    category: str
    name: str
    description: str
    price_m: int
    price_l: int
    available: bool

    def price(self, size: str) -> int:
        """Trả về giá theo size. Topping không phân biệt size."""
        return self.price_m if size in ("M", "N/A") else self.price_l

    def is_topping(self) -> bool:
        return self.category == "Topping"

    def price_display(self) -> str:
        if self.is_topping():
            return f"{self.price_m:,}đ"
        return f"M: {self.price_m:,}đ  |  L: {self.price_l:,}đ"


@dataclass
class CartItem:
    """Một dòng trong giỏ hàng."""

    item: MenuItem
    size: str       # "M", "L", hoặc "N/A" với topping
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.item.price(self.size) * self.quantity

    def display(self) -> str:
        size_str = f" ({self.size})" if not self.item.is_topping() else ""
        return f"• {self.item.name}{size_str} x{self.quantity} — {self.subtotal:,}đ"


@dataclass
class DeliveryInfo:
    """Thông tin giao hàng của khách."""

    name: str = ""
    phone: str = ""
    address: str = ""


@dataclass
class Order:
    """Toàn bộ đơn hàng."""

    items: list = field(default_factory=list)          # list[CartItem]
    delivery: DeliveryInfo = field(default_factory=DeliveryInfo)
    created_at: datetime = field(default_factory=datetime.now)
    order_id: str = ""
    user_id: int = 0   # Telegram chat_id của khách, dùng để gửi thông báo lại

    @property
    def total(self) -> int:
        return sum(ci.subtotal for ci in self.items)

    def cart_summary(self) -> str:
        """Hiển thị giỏ hàng ngắn gọn (cho khách xem)."""
        if not self.items:
            return "🛒 Giỏ hàng trống."
        lines = [ci.display() for ci in self.items]
        return "\n".join(lines) + f"\n{'─' * 28}\n💰 <b>Tổng: {self.total:,}đ</b>"

    def full_summary(self) -> str:
        """Tóm tắt đầy đủ đơn hàng (dùng để xác nhận & gửi seller)."""
        lines = [ci.display() for ci in self.items]
        items_text = "\n".join(lines)
        return (
            f"🛎 <b>ĐƠN HÀNG #{self.order_id}</b>\n"
            f"{'─' * 28}\n"
            f"👤 {self.delivery.name}\n"
            f"📞 {self.delivery.phone}\n"
            f"📍 {self.delivery.address}\n"
            f"{'─' * 28}\n"
            f"{items_text}\n"
            f"{'─' * 28}\n"
            f"💰 <b>TỔNG: {self.total:,}đ</b>\n"
            f"🕐 {self.created_at.strftime('%H:%M %d/%m/%Y')}"
        )
