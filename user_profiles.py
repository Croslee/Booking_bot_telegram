"""
user_profiles.py — Lưu thông tin giao hàng theo user_id để dùng lại lần sau.

File: user_profiles.json  (dict: user_id_str → {name, phone, address})
"""

import json
import logging
import os
import threading
from typing import Optional

from config import DATA_DIR
from models import DeliveryInfo

logger = logging.getLogger(__name__)

PROFILES_FILE = os.path.join(DATA_DIR, "user_profiles.json")
_lock = threading.Lock()


def _load_all() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Không đọc được user_profiles.json: %s", e)
        return {}


def save_profile(user_id: int, delivery: DeliveryInfo) -> None:
    """Ghi đè thông tin giao hàng cho user_id."""
    with _lock:
        profiles = _load_all()
        profiles[str(user_id)] = {
            "name":    delivery.name,
            "phone":   delivery.phone,
            "address": delivery.address,
        }
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    logger.info("Đã lưu profile cho user %s.", user_id)


def load_profile(user_id: int) -> Optional[DeliveryInfo]:
    """Trả về DeliveryInfo đã lưu, hoặc None nếu chưa có."""
    data = _load_all().get(str(user_id))
    if not data:
        return None
    return DeliveryInfo(
        name=data["name"],
        phone=data["phone"],
        address=data["address"],
    )
