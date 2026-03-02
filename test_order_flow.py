"""
test_order_flow.py — Giả lập khách đặt hàng, gửi thông báo Telegram cho seller,
                     và lưu lịch sử đơn hàng.

Chạy:
    python test_order_flow.py
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Force UTF-8 output trên Windows terminal ──────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── Đảm bảo import được các module trong project ──────────────────
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Bot

from config import BOT_TOKEN, SELLER_CHAT_ID, SHOP_NAME
from menu_loader import load_menu, get_item_by_id
from models import CartItem, DeliveryInfo, Order
from order_history import save_order, load_orders, get_stats
from handlers.notify import send_order_to_seller

# ──────────────────────────────────────────────────────────────────
# Dữ liệu giả lập khách hàng
# ──────────────────────────────────────────────────────────────────

FAKE_CUSTOMERS = [
    DeliveryInfo(name="Nguyen Thi Lan",    phone="0901234567", address="12 Nguyen Hue, Q.1, TP.HCM"),
    DeliveryInfo(name="Tran Van Minh",     phone="0912345678", address="45 Le Loi, Q.3, TP.HCM"),
    DeliveryInfo(name="Pham Thi Hoa",      phone="0923456789", address="78 CMT8, Q.10, TP.HCM"),
    DeliveryInfo(name="Le Quoc Bao",       phone="0934567890", address="99 Hai Ba Trung, Q.1, TP.HCM"),
    DeliveryInfo(name="Nguyen Van Thanh",  phone="0945678901", address="21 Dien Bien Phu, Q.BT, TP.HCM"),
]

# item_id, size, quantity
FAKE_ORDERS_ITEMS = [
    # Don 1: Tra sua + Topping
    [("TS01", "L", 2), ("TS04", "M", 1), ("TOP01", "N/A", 2)],
    # Don 2: Tra trai cay
    [("TTG01", "L", 1), ("TTG03", "M", 2), ("TOP03", "N/A", 1)],
    # Don 3: Ca phe va da xay
    [("CF02", "L", 2), ("DX03", "M", 1), ("TOP06", "N/A", 2)],
    # Don 4: Nhieu mon
    [("TS02", "L", 3), ("TTG05", "M", 1), ("DX01", "L", 1), ("TOP02", "N/A", 3)],
    # Don 5: Chi topping + ca phe
    [("CF04", "L", 1), ("TOP05", "N/A", 1), ("TOP08", "N/A", 2)],
]


# ──────────────────────────────────────────────────────────────────
# Tạo Order object từ dữ liệu giả lập
# ──────────────────────────────────────────────────────────────────

def build_fake_order(menu: dict, items_spec: list, delivery: DeliveryInfo,
                     offset_minutes: int = 0) -> Order:
    """Tạo Order từ danh sách (item_id, size, qty)."""
    cart = []
    for item_id, size, qty in items_spec:
        item = get_item_by_id(menu, item_id)
        if item:
            cart.append(CartItem(item=item, size=size, quantity=qty))
        else:
            print(f"  [WARN] Khong tim thay item_id: {item_id}")

    created_at = datetime.now() - timedelta(minutes=offset_minutes)
    order_id   = created_at.strftime("%d%m%H%M%S") + f"{random.randint(0, 99):02d}"

    return Order(
        items=cart,
        delivery=delivery,
        created_at=created_at,
        order_id=order_id,
    )


# ──────────────────────────────────────────────────────────────────
# In báo cáo ra màn hình
# ──────────────────────────────────────────────────────────────────

LINE = "-" * 70

def print_order_table(orders: list) -> None:
    """In bảng tóm tắt tất cả đơn hàng."""
    print(f"\n{LINE}")
    print(f"  LICH SU DON HANG | {SHOP_NAME}")
    print(LINE)
    print(f"  {'STT':<4} {'Ma don':<12} {'Khach hang':<22} {'SDT':<13} {'Tong':<12} {'Thoi gian'}")
    print(LINE)

    for i, o in enumerate(orders, 1):
        print(
            f"  {i:<4} "
            f"#{o['order_id']:<11} "
            f"{o['customer']['name']:<22} "
            f"{o['customer']['phone']:<13} "
            f"{o['total']:>9,}d  "
            f"{o['created_at']}"
        )

    print(LINE)


def print_stats(stats: dict) -> None:
    """In thống kê tổng quan."""
    print(f"\n  THONG KE TONG QUAN")
    print(f"  {'Tong so don:':<30} {stats['total_orders']} don")
    print(f"  {'Tong doanh thu:':<30} {stats['total_revenue']:,}d")
    print(f"  {'Gia tri don trung binh:':<30} {stats['avg_order_value']:,}d")
    if stats.get("most_ordered"):
        print(f"  {'Mon ban chay nhat:':<30} {stats['most_ordered']}")
    print(LINE)


def print_order_detail(order: Order, idx: int, sent: bool) -> None:
    """In chi tiết một đơn vừa xử lý."""
    status = "[SENT]  " if sent else "[FAILED]"
    print(f"\n  {status} Don #{order.order_id} | {order.delivery.name}")
    for ci in order.items:
        size_str = f"({ci.size})" if not ci.item.is_topping() else "     "
        print(f"         + {ci.item.name:<28} {size_str} x{ci.quantity}  =  {ci.subtotal:>8,}d")
    print(f"         {'':>45} TONG: {order.total:>8,}d")


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

async def run_tests() -> None:
    print(f"\n{LINE}")
    print(f"  TEST ORDER FLOW | {SHOP_NAME}")
    print(f"  Chay luc : {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print(LINE)

    # 1. Load menu
    menu = load_menu()
    print(f"\n  [OK] Da load menu: {sum(len(v) for v in menu.values())} mon trong {len(menu)} danh muc")

    # 2. Khoi tao bot
    bot = Bot(token=BOT_TOKEN)
    bot_info = await bot.get_me()
    print(f"  [OK] Bot: @{bot_info.username}  |  Seller ID: {SELLER_CHAT_ID}")

    # 3. Tao va xu ly tung don gia lap
    print(f"\n  Bat dau gia lap {len(FAKE_ORDERS_ITEMS)} don hang...\n")

    results = []
    for idx, (items_spec, delivery) in enumerate(
        zip(FAKE_ORDERS_ITEMS, FAKE_CUSTOMERS), start=1
    ):
        # Offset thoi gian de don khong cung luc (don truoc = lau hon)
        offset = (len(FAKE_ORDERS_ITEMS) - idx) * 17

        order = build_fake_order(menu, items_spec, delivery, offset_minutes=offset)
        sent  = await send_order_to_seller(bot, order)
        save_order(order)

        print_order_detail(order, idx, sent)
        results.append((order, sent))

        await asyncio.sleep(0.3)   # tranh rate limit Telegram

    # 4. In bang tom tat
    orders = load_orders()
    print_order_table(orders)

    # 5. In thong ke
    stats = get_stats()
    print_stats(stats)

    # 6. Ket qua goi y
    sent_count   = sum(1 for _, s in results if s)
    failed_count = len(results) - sent_count
    print(f"\n  KET QUA: {sent_count}/{len(results)} don gui Telegram thanh cong", end="")
    if failed_count:
        print(f"  |  {failed_count} don that bai (kiem tra log)")
    else:
        print("  — Tat ca thanh cong!")
    print(f"{LINE}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
