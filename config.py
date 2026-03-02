import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str       = os.getenv("BOT_TOKEN", "")
SELLER_CHAT_ID: str  = os.getenv("SELLER_CHAT_ID", "")
BOT_USERNAME: str    = os.getenv("BOT_USERNAME", "")   # VD: trasua_nhaminhbot (không có @)
SHOP_NAME: str       = os.getenv("SHOP_NAME", "Trà Sữa Nhà Mình")
MENU_FILE: str       = os.path.join(os.path.dirname(__file__), "Menu.csv")

# ── Lưu trữ dữ liệu ──────────────────────────────────────────────
# Local: mặc định cùng thư mục với bot.py
# Railway: đặt DATA_DIR=/data và gắn Volume tại /data để dữ liệu không mất khi redeploy
DATA_DIR: str = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))

# ── Cấu hình deploy ──────────────────────────────────────────────
# Để trống khi chạy local (polling mode).
# Railway tự gán RAILWAY_PUBLIC_DOMAIN → webhook tự động hoạt động.
# Hoặc tự điền WEBHOOK_URL nếu dùng nền tảng khác.
_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", f"https://{_railway_domain}" if _railway_domain else "")
PORT: int        = int(os.getenv("PORT", "8443"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN chưa được cấu hình trong file .env")

if not SELLER_CHAT_ID:
    raise ValueError("SELLER_CHAT_ID chưa được cấu hình trong file .env")
