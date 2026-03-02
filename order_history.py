"""
order_history.py — Module lưu trữ và đọc lịch sử đơn hàng.

Định dạng: JSON  →  orders.json  (append mỗi khi có đơn mới)
"""

import json
import logging
import os
import threading
from datetime import datetime
from typing import Optional

from config import DATA_DIR
from models import Order

logger = logging.getLogger(__name__)

HISTORY_FILE = os.path.join(DATA_DIR, "orders.json")
_lock = threading.Lock()  # bảo vệ đọc-ghi file khỏi race condition


# ──────────────────────────────────────────────
# Serialize / Deserialize
# ──────────────────────────────────────────────

def _order_to_dict(order: Order) -> dict:
    """Chuyển Order object → dict có thể JSON-serialize."""
    return {
        "order_id":   order.order_id,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status":     "confirmed",
        "user_id":    order.user_id,
        "customer": {
            "name":    order.delivery.name,
            "phone":   order.delivery.phone,
            "address": order.delivery.address,
        },
        "items": [
            {
                "item_id":  ci.item.item_id,
                "name":     ci.item.name,
                "category": ci.item.category,
                "size":     ci.size,
                "quantity": ci.quantity,
                "price":    ci.item.price(ci.size),
                "subtotal": ci.subtotal,
            }
            for ci in order.items
        ],
        "total": order.total,
    }


# ──────────────────────────────────────────────
# Ghi / Đọc
# ──────────────────────────────────────────────

def save_order(order: Order) -> None:
    """
    Ghi đơn hàng vào orders.json.
    Nếu file chưa tồn tại thì tạo mới.
    """
    with _lock:
        orders = load_orders()
        orders.append(_order_to_dict(order))
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    logger.info("Đã lưu đơn #%s vào lịch sử (%d đơn tổng cộng).",
                order.order_id, len(orders))


def load_orders() -> list:
    """Đọc toàn bộ lịch sử đơn hàng. Trả về list rỗng nếu chưa có file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Không đọc được file lịch sử: %s", e)
        return []


def get_order_by_id(order_id: str) -> Optional[dict]:
    """Tìm đơn theo order_id. Trả về None nếu không tìm thấy."""
    for order in load_orders():
        if order.get("order_id") == order_id:
            return order
    return None


def get_today_orders(orders: list) -> list:
    """Lọc các đơn hàng trong ngày hôm nay từ danh sách đã load."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    return [o for o in orders if o.get("created_at", "").startswith(today_str)]


def get_stats() -> dict:
    """Thống kê nhanh từ lịch sử đơn hàng."""
    orders = load_orders()
    if not orders:
        return {"total_orders": 0, "total_revenue": 0, "avg_order_value": 0}

    total_revenue = sum(o["total"] for o in orders)
    return {
        "total_orders":    len(orders),
        "total_revenue":   total_revenue,
        "avg_order_value": total_revenue // len(orders),
        "most_ordered":    _most_ordered_item(orders),
    }


def update_order_status(order_id: str, status: str) -> bool:
    with _lock:
        orders = load_orders()
        for order in orders:
            if order.get("order_id") == order_id:
                order["status"] = status
                order["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(orders, f, ensure_ascii=False, indent=2)
                logger.info("Don #%s -> trang thai: %s", order_id, status)
                return True
    logger.warning("Khong tim thay don #%s de cap nhat.", order_id)
    return False


def _most_ordered_item(orders: list) -> str:
    """Tìm món được đặt nhiều nhất."""
    counter: dict = {}
    for order in orders:
        for item in order.get("items", []):
            name = item["name"]
            counter[name] = counter.get(name, 0) + item["quantity"]
    if not counter:
        return "N/A"
    return max(counter, key=counter.get)
