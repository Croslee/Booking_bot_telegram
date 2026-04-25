# 🧋 Bot Đặt Đồ Uống — Telegram

Bot Telegram giúp khách đặt hàng trực tiếp qua chat, người bán nhận đơn và xác nhận bằng nút bấm — không cần app riêng, không cần gọi điện.

Video Demo: https://drive.google.com/file/d/1_CWlWL1wFy70lv4vuFjafJz6EjBGSrq2/view?usp=sharing

---

## Tính năng

**Phía khách hàng**
- Duyệt menu theo danh mục, chọn size M/L, số lượng
- Giỏ hàng: thêm, xoá, xoá hết
- Nhập thông tin giao hàng (tên, SĐT, địa chỉ) — tự động lưu để lần sau dùng lại
- Xem lại đơn trước khi xác nhận
- Nhận thông báo khi đơn được xác nhận hoàn thành hoặc huỷ
- Nhận mã QR bot để chia sẻ

**Phía người bán**
- Nhận thông báo đơn hàng mới kèm đầy đủ thông tin
- Bấm ✅ Đã làm xong hoặc ❌ Huỷ đơn ngay trên Telegram
- `/history` — xem 10 đơn gần nhất + doanh thu hôm nay
- `/stats` — thống kê tổng quan: doanh thu, số đơn, món bán chạy
- `/export` — xuất lịch sử đơn hàng dạng `.txt` và `.csv` (mở được bằng Excel)
- `/qr` — lấy ảnh QR code có thương hiệu để chia sẻ hoặc in dán

---

## Yêu cầu

- Python 3.12+
- Tài khoản Telegram + Bot Token từ [@BotFather](https://t.me/BotFather)

---

## Cài đặt và chạy local

### 1. Clone repo

```bash
git clone https://github.com/Croslee/Booking_bot_telegram.git
cd Booking_bot_telegram
```

### 2. Tạo môi trường ảo và cài thư viện

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Tạo file `.env`

Copy từ file mẫu rồi điền thông tin thật:

```bash
cp .env.example .env
```

Mở `.env` và điền:

```env
BOT_TOKEN=token_từ_botfather
SELLER_CHAT_ID=chat_id_người_bán
BOT_USERNAME=username_bot_không_có_@
SHOP_NAME=Tên quán của bạn
```

> **Lấy SELLER_CHAT_ID:** Nhắn tin cho [@userinfobot](https://t.me/userinfobot) → copy số `Id`

### 4. Chạy bot

```bash
python bot.py
```

Bot chạy ở **polling mode** — nhấn `Ctrl+C` để dừng.

---

## Deploy lên Railway

### 1. Tạo project

- Vào [railway.app](https://railway.app) → đăng nhập bằng GitHub
- **New Project → Deploy from GitHub repo** → chọn repo này

### 2. Thêm biến môi trường

Trong Railway dashboard → tab **Variables**:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Token từ @BotFather |
| `SELLER_CHAT_ID` | Chat ID người bán |
| `BOT_USERNAME` | Username bot (không có @) |
| `SHOP_NAME` | Tên quán |
| `DATA_DIR` | `/data` |

> `PORT` và `RAILWAY_PUBLIC_DOMAIN` Railway tự gán — không cần điền.

### 3. Gắn Volume (persistent disk) — bắt buộc để không mất dữ liệu

1. Trong project → tab **Volumes** → **New Volume**
2. **Mount Path:** `/data`
3. Nhấn **Create** — dữ liệu trong `/data` sẽ tồn tại qua mọi lần redeploy

### 4. Tạo domain

Tab **Settings → Networking → Generate Domain** → Railway cấp domain và bot tự chuyển sang webhook mode.

### 5. Kích hoạt kết nối người bán

Sau khi deploy, người bán mở bot và gõ `/start` một lần để Telegram cho phép bot gửi tin nhắn tới.

---

## Cấu trúc dự án

```
├── bot.py                  # Entry point
├── config.py               # Biến môi trường
├── models.py               # Data classes: MenuItem, CartItem, Order...
├── menu_loader.py          # Đọc Menu.csv
├── order_history.py        # Lưu/đọc orders.json
├── user_profiles.py        # Lưu thông tin giao hàng của khách
├── generate_qr.py          # Tạo ảnh QR code
├── test_order_flow.py      # Script test luồng đặt hàng (local)
├── Menu.csv                # Database menu
├── handlers/
│   ├── start.py            # Lệnh /start
│   ├── menu.py             # Duyệt menu
│   ├── cart.py             # Giỏ hàng
│   ├── checkout.py         # Luồng đặt hàng
│   ├── notify.py           # Gửi thông báo cho người bán
│   ├── seller.py           # Lệnh và callback người bán
│   ├── qr_handler.py       # Lệnh /qr
│   ├── keyboards.py        # Tất cả InlineKeyboard
│   └── states.py           # Hằng số trạng thái ConversationHandler
├── .env.example            # Template biến môi trường
├── requirements.txt        # Thư viện Python
├── Procfile                # Lệnh khởi động cho Railway
└── runtime.txt             # Phiên bản Python
```

---

## Chỉnh sửa menu

Mở file `Menu.csv` và thêm/sửa/xoá dòng theo định dạng:

```
category,item_id,name,description,price_m,price_l,available
Trà sữa,ts001,Trà sữa truyền thống,Hương vị cổ điển đậm đà,25000,30000,true
```

| Cột | Mô tả |
|-----|-------|
| `category` | Nhóm món hiển thị trên menu |
| `item_id` | Mã món — phải là duy nhất |
| `name` | Tên món |
| `description` | Mô tả ngắn |
| `price_m` | Giá size M (VNĐ) |
| `price_l` | Giá size L (VNĐ) |
| `available` | `true` / `false` — ẩn/hiện món |

Khởi động lại bot sau khi sửa menu.

---

## Lệnh bot

| Lệnh | Đối tượng dùng | Tác dụng |
|------|---------|----------|
| `/start` | Khách | Bắt đầu đặt hàng |
| `/cancel` | Khách | Huỷ đơn đang đặt |
| `/help` | Khách | Hướng dẫn sử dụng |
| `/qr` | Tất cả | Lấy mã QR bot |
| `/history` | Người bán | 10 đơn gần nhất + doanh thu hôm nay |
| `/stats` | Người bán | Thống kê tổng quan |
| `/export` | Người bán | Xuất lịch sử đơn hàng |
| `/reloadmenu` | Người bán | Tải lại menu từ Menu.csv (không cần restart) |
