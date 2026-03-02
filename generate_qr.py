"""
generate_qr.py — Tạo QR code có thương hiệu (dùng trong lệnh /qr của bot).
"""

import io

import qrcode
from PIL import Image, ImageDraw, ImageFont

# ── Màu sắc thương hiệu ──────────────────────────────────────────
COLOR_BG       = "#FFFFFF"   # nền trắng
COLOR_QR_FILL  = "#1E3A5F"   # xanh đậm cho QR
COLOR_BANNER   = "#1E3A5F"   # nền banner trên/dưới
COLOR_TEXT     = "#FFFFFF"   # chữ trắng trên banner
COLOR_SUB      = "#555555"   # chữ phụ màu xám


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Tải font hệ thống; fallback về default nếu không có."""
    candidates = (
        ["arialbd.ttf", "Arial Bold.ttf"]
        if bold
        else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def build_qr_image(bot_url: str) -> Image.Image:
    """Tạo QR code thuần (không viền phụ)."""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=3,
    )
    qr.add_data(bot_url)
    qr.make(fit=True)
    return qr.make_image(fill_color=COLOR_QR_FILL, back_color=COLOR_BG).convert("RGB")


def build_branded_image(shop_name: str, bot_url: str) -> Image.Image:

    qr_img = build_qr_image(bot_url)
    qr_w, qr_h = qr_img.size

    # Kích thước tổng
    padding   = 40
    banner_h  = 90
    footer_h  = 110
    total_w   = qr_w + padding * 2
    total_h   = banner_h + qr_h + padding * 2 + footer_h

    canvas = Image.new("RGB", (total_w, total_h), COLOR_BG)
    draw   = ImageDraw.Draw(canvas)

    # ── Banner trên ────────────────────────────
    draw.rectangle([(0, 0), (total_w, banner_h)], fill=COLOR_BANNER)
    f_title = _get_font(30, bold=True)
    title   = f"🧋  {shop_name}"
    bbox    = draw.textbbox((0, 0), title, font=f_title)
    tx      = (total_w - (bbox[2] - bbox[0])) // 2
    ty      = (banner_h - (bbox[3] - bbox[1])) // 2
    draw.text((tx, ty), title, fill=COLOR_TEXT, font=f_title)

    # ── QR code ────────────────────────────────
    qr_x = padding
    qr_y = banner_h + padding
    canvas.paste(qr_img, (qr_x, qr_y))

    # ── Footer ─────────────────────────────────
    footer_y = banner_h + qr_h + padding * 2
    draw.rectangle([(0, footer_y), (total_w, total_h)], fill=COLOR_BANNER)

    f_main = _get_font(24, bold=True)
    f_sub  = _get_font(19)

    lines = [
        (f_main, "Quét mã để đặt hàng online"),
        (f_sub,  "Nhanh – Không nhầm đơn – Không cần chờ"),
    ]
    y_cursor = footer_y + 14
    for font, line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x    = (total_w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y_cursor), line, fill=COLOR_TEXT, font=font)
        y_cursor += (bbox[3] - bbox[1]) + 10

    # Link nhỏ bên dưới
    f_link = _get_font(16)
    bbox   = draw.textbbox((0, 0), bot_url, font=f_link)
    x      = (total_w - (bbox[2] - bbox[0])) // 2
    draw.text((x, y_cursor + 4), bot_url, fill="#AAAAAA", font=f_link)

    return canvas


def qr_to_bytes(bot_url: str, shop_name: str) -> io.BytesIO:
    """Tạo QR trong bộ nhớ (dùng cho lệnh /qr trong bot)."""
    img    = build_qr_image(bot_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
