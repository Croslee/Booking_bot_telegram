import csv
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from config import MENU_FILE
from models import MenuItem

logger = logging.getLogger(__name__)


def load_menu() -> Dict[str, List[MenuItem]]:
    """
    Đọc Menu.csv và trả về dict nhóm theo danh mục.
    Chỉ load những món có available=true.

    Returns:
        {"Trà Sữa": [MenuItem, ...], "Cà Phê": [...], ...}
    """
    menu: Dict[str, List[MenuItem]] = defaultdict(list)

    try:
        with open(MENU_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Bỏ qua dòng trống hoặc món không có sẵn
                if not row.get("item_id") or row.get("available", "").strip().lower() != "true":
                    continue
                item = MenuItem(
                    item_id=row["item_id"].strip(),
                    category=row["category"].strip(),
                    name=row["name"].strip(),
                    description=row["description"].strip(),
                    price_m=int(row["price_m"].strip()),
                    price_l=int(row["price_l"].strip()),
                    available=True,
                )
                menu[item.category].append(item)

        logger.info("Đã load menu: %d danh mục, %d món.",
                    len(menu), sum(len(v) for v in menu.values()))
    except FileNotFoundError:
        logger.error("Không tìm thấy file menu: %s", MENU_FILE)
        raise
    except (KeyError, ValueError) as e:
        logger.error("Lỗi parse menu: %s", e)
        raise

    return dict(menu)


def get_item_by_id(menu: Dict[str, List[MenuItem]], item_id: str) -> Optional[MenuItem]:
    """Tìm MenuItem theo item_id trên toàn bộ menu."""
    for items in menu.values():
        for item in items:
            if item.item_id == item_id:
                return item
    return None
