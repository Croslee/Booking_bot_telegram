# Changelog

## [1.1.0] — 2026-03-02

### Sửa lỗi vận hành

#### Persistent storage — Railway Volume
- Thêm biến `DATA_DIR` vào `config.py`: mặc định là thư mục project khi chạy local, trỏ tới `/data` (Railway Volume) khi deploy
- `order_history.py` và `user_profiles.py` dùng `DATA_DIR` thay vì đường dẫn cứng `os.path.dirname(__file__)`
- `orders.json` và `user_profiles.json` không còn bị xoá khi Railway redeploy
- Cập nhật `.env.example` và `README.md` hướng dẫn gắn Volume trên Railway

#### Race condition
- Thêm `threading.Lock` vào `order_history.py`: bảo vệ `save_order()` và `update_order_status()` khỏi ghi đè đồng thời
- Thêm `threading.Lock` vào `user_profiles.py`: bảo vệ `save_profile()` tương tự

#### Reload menu không cần restart
- Thêm lệnh `/reloadmenu` (chỉ seller) — đọc lại `Menu.csv` và cập nhật `bot_data["menu"]` ngay lập tức
- Phản hồi số danh mục và số món sau khi reload thành công

---

## [1.0.0] — 2026-03-02

Phiên bản đầu tiên hoàn chỉnh, sẵn sàng deploy.

---

### Tính năng mới

#### Luồng đặt hàng (khách)
- Duyệt menu theo danh mục từ `Menu.csv`
- Chọn size M/L, số lượng (nút 1–5 hoặc nhập tay)
- Giỏ hàng: thêm/xoá món, xoá hết, xem tổng
- Nhập thông tin giao hàng: tên, số điện thoại (validate định dạng VN), địa chỉ
- Lưu thông tin giao hàng — lần sau đặt không cần nhập lại
- Xem lại đơn đầy đủ trước khi xác nhận hoặc chỉnh sửa
- Sau đặt thành công: chọn tiếp tục đặt thêm hoặc kết thúc

#### Thông báo và trạng thái đơn hàng
- Bot gửi thông báo đơn hàng đầy đủ tới người bán kèm nút ✅/❌
- Người bán bấm nút → bot tự động thông báo lại cho khách
- Khách nhận tin "Đơn đã hoàn thành" hoặc "Đơn đã bị huỷ" kèm mã đơn

#### Lệnh người bán
- `/history` — 10 đơn gần nhất kèm trạng thái + tổng doanh thu hôm nay
- `/stats` — thống kê: tổng đơn, doanh thu, trung bình/đơn, món bán chạy nhất
- `/export` — xuất toàn bộ lịch sử dạng `.txt` và `.csv` (UTF-8 BOM, mở được bằng Excel)

#### Tiện ích
- `/qr` — tạo và gửi ảnh QR code có thương hiệu (tên quán + màu sắc tùy chỉnh)
- `/help` — hướng dẫn sử dụng cho khách
- `/cancel` — huỷ đơn đang trong quá trình đặt

---

### Kiến trúc & kỹ thuật
- `python-telegram-bot` v22.6, `ConversationHandler` 12 trạng thái (0–11)
- Tự động chuyển polling ↔ webhook dựa trên `WEBHOOK_URL` / `RAILWAY_PUBLIC_DOMAIN`
- Lưu trữ đơn hàng dạng JSON (`orders.json`), profile khách dạng JSON (`user_profiles.json`)
- QR code tạo in-memory bằng `qrcode` + `Pillow` — không lưu file

---

### Cải tiến trong quá trình phát triển

#### Mã đơn hàng
- Thêm 2 chữ số ngẫu nhiên vào cuối mã đơn (`DDMMHHMMSS` + `XX`) để tránh trùng khi đặt cùng thời điểm
- Tách thành helper `_new_order_id()` để tránh code lặp

#### Lưu trữ `user_id`
- Lưu `user_id` (Telegram chat ID) của khách vào `Order` và `orders.json`
- Dùng để gửi thông báo ngược lại cho khách khi người bán cập nhật trạng thái

#### Giao diện sau đặt hàng
- Thay vì kết thúc ngay, hiển thị 2 nút: "Đặt thêm món" và "Xong rồi, hẹn lần sau"
- Bấm nút không ghi đè tin nhắn xác nhận đơn — giữ nguyên, tạo tin nhắn mới

---

### Dọn dẹp & tối ưu
- Xoá chức năng in QR ra file (`generate()`, `OUTPUT_FILE`) — chỉ giữ lại tạo QR qua Telegram
- Chuyển `import config` cục bộ trong hàm lên module level
- Tách `get_today_orders()` ra `order_history.py` để tái sử dụng
- Xoá `__pycache__`, thư mục temp, file test data, file generated
- Bổ sung `.gitignore` cho `orders.json`, `user_profiles.json`, `order_report.txt`

---

### Deploy
- Cấu hình Railway: `Procfile` (`web: python bot.py`), `runtime.txt` (`python-3.12.0`)
- `config.py` tự đọc `RAILWAY_PUBLIC_DOMAIN` → không cần set `WEBHOOK_URL` thủ công trên Railway
- Xoá `render.yaml` (không dùng Render)
