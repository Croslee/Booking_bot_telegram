"""
handlers/seller.py — Lệnh và callback dành riêng cho người bán.

Lệnh:
    /history      — 10 đơn hàng gần nhất kèm trạng thái
    /stats        — thống kê doanh thu hôm nay + tổng
    /export       — xuất toàn bộ lịch sử dưới dạng .txt và .csv (mở được bằng Excel)
    /reloadmenu   — tải lại menu từ Menu.csv mà không cần restart bot

Callback:
    done_<order_id>    — đánh dấu đơn "Đã làm xong"
    cancel_<order_id>  — đánh dấu đơn "Đã huỷ"
"""

import csv
import io
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import SELLER_CHAT_ID, SHOP_NAME
from menu_loader import load_menu
from order_history import get_order_by_id, get_stats, get_today_orders, load_orders, update_order_status

logger = logging.getLogger(__name__)

# ── Trạng thái hiển thị ──────────────────────────────────────────────
STATUS_LABEL = {
    "confirmed": "🟡 Mới",
    "done":      "✅ Xong",
    "cancelled": "❌ Huỷ",
}


def _is_seller(update: Update) -> bool:
    """Kiểm tra xem người gửi lệnh có phải seller không."""
    user_id = str(update.effective_user.id)
    return user_id == str(SELLER_CHAT_ID)


# ── /history ─────────────────────────────────────────────────────────

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi bảng 10 đơn hàng gần nhất với trạng thái."""
    if not _is_seller(update):
        await update.message.reply_text("⛔ Lệnh này chỉ dành cho người bán.")
        return

    orders = load_orders()
    if not orders:
        await update.message.reply_text("📭 Chưa có đơn hàng nào.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_orders = get_today_orders(orders)
    today_revenue = sum(o["total"] for o in today_orders)
    today_done = sum(1 for o in today_orders if o.get("status") == "done")

    recent = orders[-10:][::-1]  # 10 đơn mới nhất, mới nhất trên đầu
    lines = ["<b>📋 LỊCH SỬ ĐƠN HÀNG (10 đơn gần nhất)</b>\n"]

    for o in recent:
        status = STATUS_LABEL.get(o.get("status", "confirmed"), "🟡 Mới")
        lines.append(
            f"{status}  <b>#{o['order_id']}</b> — {o['customer']['name']}\n"
            f"   💰 {o['total']:,}đ  |  🕐 {o['created_at']}"
        )

    lines.append(
        f"─────────────────────────\n"
        f"📅 <b>Hôm nay ({today_str})</b>\n"
        f"   Tổng đơn: {len(today_orders)}  |  Hoàn thành: {today_done}\n"
        f"   💵 Doanh thu: <b>{today_revenue:,}đ</b>"
    )

    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")


# ── /stats ────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi thống kê tổng quan và hôm nay."""
    if not _is_seller(update):
        await update.message.reply_text("⛔ Lệnh này chỉ dành cho người bán.")
        return

    stats = get_stats()
    orders = load_orders()

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_orders = get_today_orders(orders)
    today_revenue = sum(o["total"] for o in today_orders)
    today_done = sum(1 for o in today_orders if o.get("status") == "done")
    today_cancelled = sum(1 for o in today_orders if o.get("status") == "cancelled")

    msg = (
        f"<b>📊 THỐNG KÊ CỬA HÀNG</b>\n\n"
        f"<b>Hôm nay ({today_str})</b>\n"
        f"  Tổng đơn    : {len(today_orders)} đơn\n"
        f"  Đã hoàn thành: {today_done} đơn\n"
        f"  Đã huỷ      : {today_cancelled} đơn\n"
        f"  Doanh thu   : {today_revenue:,}đ\n\n"
        f"<b>Tổng cộng</b>\n"
        f"  Tổng đơn    : {stats['total_orders']} đơn\n"
        f"  Doanh thu   : {stats['total_revenue']:,}đ\n"
        f"  TB/đơn      : {stats['avg_order_value']:,}đ\n"
        f"  Món bán chạy: {stats.get('most_ordered', 'N/A')}"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


# ── /export ───────────────────────────────────────────────────────────

def _build_txt(orders: list, stats: dict) -> str:
    """Tạo nội dung báo cáo .txt."""
    sep = "=" * 68
    lines = [
        sep,
        f"  BAO CAO DON HANG",
        f"  Xuat luc: {datetime.now().strftime('%H:%M %d/%m/%Y')}",
        sep, "",
    ]
    for i, o in enumerate(orders, 1):
        status = STATUS_LABEL.get(o.get("status", "confirmed"), "🟡 Mới")
        lines.append(f"  [{i}] Don #{o['order_id']}  |  {o['created_at']}  |  {status}")
        lines.append(f"      Khach : {o['customer']['name']}  |  {o['customer']['phone']}")
        lines.append(f"      DC    : {o['customer']['address']}")
        for item in o["items"]:
            size_str = f"({item['size']})" if item["size"] != "N/A" else "      "
            lines.append(
                f"        - {item['name']:<28} {size_str} "
                f"x{item['quantity']}  =  {item['subtotal']:>8,}d"
            )
        lines.append(f"      {'':>50} TONG: {o['total']:>8,}d")
        lines.append("")
    lines += [
        sep,
        f"  THONG KE",
        f"  Tong don     : {stats['total_orders']}",
        f"  Doanh thu    : {stats['total_revenue']:,}d",
        f"  TB / don     : {stats['avg_order_value']:,}d",
        f"  Mon ban chay : {stats.get('most_ordered', 'N/A')}",
        sep,
    ]
    return "\n".join(lines)


def _build_csv(orders: list) -> bytes:
    """Tạo nội dung báo cáo .csv (UTF-8 BOM để Excel nhận đúng)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "STT", "Ma Don", "Ngay Gio", "Trang Thai",
        "Ten Khach", "SDT", "Dia Chi",
        "Ten Mon", "Size", "So Luong", "Don Gia (d)", "Thanh Tien (d)", "Tong Don (d)",
    ])
    for i, o in enumerate(orders, 1):
        status_vi = {"confirmed": "Moi", "done": "Hoan thanh", "cancelled": "Da huy"}.get(
            o.get("status", "confirmed"), "Moi"
        )
        for item in o["items"]:
            writer.writerow([
                i,
                o["order_id"],
                o["created_at"],
                status_vi,
                o["customer"]["name"],
                o["customer"]["phone"],
                o["customer"]["address"],
                item["name"],
                item["size"],
                item["quantity"],
                item["price"],
                item["subtotal"],
                o["total"],
            ])
    # UTF-8 BOM: Excel mở đúng tiếng Việt
    return "\ufeff".encode("utf-8") + buf.getvalue().encode("utf-8")


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xuất toàn bộ lịch sử đơn dưới dạng .txt và .csv."""
    if not _is_seller(update):
        await update.message.reply_text("⛔ Lệnh này chỉ dành cho người bán.")
        return

    orders = load_orders()
    if not orders:
        await update.message.reply_text("📭 Chưa có đơn hàng nào để xuất.")
        return

    stats = get_stats()
    date_tag = datetime.now().strftime("%d%m%Y")

    # ── Gửi file .txt ──
    txt_buf = io.BytesIO(_build_txt(orders, stats).encode("utf-8"))
    txt_buf.name = f"donhang_{date_tag}.txt"
    await update.message.reply_document(
        document=txt_buf,
        filename=txt_buf.name,
        caption=f"📄 Báo cáo văn bản — {len(orders)} đơn",
    )

    # ── Gửi file .csv ──
    csv_buf = io.BytesIO(_build_csv(orders))
    csv_buf.name = f"donhang_{date_tag}.csv"
    await update.message.reply_document(
        document=csv_buf,
        filename=csv_buf.name,
        caption="📊 File CSV — mở bằng Excel hoặc Google Sheets",
    )


# ── Callback: done / cancel ───────────────────────────────────────────

async def handle_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xử lý nút ✅ Đã làm xong  /  ❌ Huỷ đơn mà seller bấm.
    callback_data format:  done_<order_id>  |  cancel_<order_id>
    """
    query = update.callback_query
    await query.answer()

    # Chỉ seller mới được tương tác
    if str(query.from_user.id) != str(SELLER_CHAT_ID):
        await query.answer("⛔ Bạn không có quyền thao tác.", show_alert=True)
        return

    data = query.data  # e.g.  "done_0103173643"
    if "_" not in data:
        return

    action, order_id = data.split("_", 1)

    if action == "done":
        ok = update_order_status(order_id, "done")
        if ok:
            new_text = query.message.text + "\n\n✅ <b>Đã hoàn thành</b>"
            await query.edit_message_text(new_text, parse_mode="HTML")
            await _notify_customer_done(context, order_id)
        else:
            await query.answer(f"Không tìm thấy đơn #{order_id}.", show_alert=True)

    elif action == "cancel":
        ok = update_order_status(order_id, "cancelled")
        if ok:
            new_text = query.message.text + "\n\n❌ <b>Đã huỷ đơn</b>"
            await query.edit_message_text(new_text, parse_mode="HTML")
            await _notify_customer_cancelled(context, order_id)
        else:
            await query.answer(f"Không tìm thấy đơn #{order_id}.", show_alert=True)


async def _notify_customer_done(context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Gửi thông báo đơn hoàn thành đến khách hàng."""
    order = get_order_by_id(order_id)
    if not order:
        return
    user_id = order.get("user_id", 0)
    if not user_id:
        return
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>Đơn hàng #{order_id} đã được xác nhận!</b>\n\n"
                f"Cửa hàng đang chuẩn bị đơn của bạn.\n"
                f"Chúng mình sẽ liên hệ sớm nhất có thể 🙏\n\n"
                f"Cảm ơn bạn đã ủng hộ <b>{SHOP_NAME}</b> 🧋"
            ),
            parse_mode="HTML",
        )
    except Exception:
        logger.warning("Không gửi được thông báo hoàn thành cho user_id=%s", user_id)


async def _notify_customer_cancelled(context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Gửi thông báo đơn bị huỷ đến khách hàng."""
    order = get_order_by_id(order_id)
    if not order:
        return
    user_id = order.get("user_id", 0)
    if not user_id:
        return
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>Đơn hàng #{order_id} đã bị huỷ.</b>\n\n"
                f"Vui lòng liên hệ <b>{SHOP_NAME}</b> để biết thêm chi tiết."
            ),
            parse_mode="HTML",
        )
    except Exception:
        logger.warning("Không gửi được thông báo huỷ cho user_id=%s", user_id)


# ── /reloadmenu ───────────────────────────────────────────────────────

async def cmd_reload_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tải lại menu từ Menu.csv mà không cần restart bot."""
    if not _is_seller(update):
        await update.message.reply_text("⛔ Lệnh này chỉ dành cho người bán.")
        return

    try:
        menu = load_menu()
        context.bot_data["menu"] = menu
        total_items = sum(len(items) for items in menu.values())
        await update.message.reply_text(
            f"✅ <b>Menu đã được tải lại!</b>\n\n"
            f"📂 Danh mục: <b>{len(menu)}</b>\n"
            f"🧋 Tổng số món: <b>{total_items}</b>",
            parse_mode="HTML",
        )
        logger.info("Menu đã được reload bởi seller. %d danh mục, %d món.", len(menu), total_items)
    except Exception as e:
        logger.error("Lỗi khi reload menu: %s", e)
        await update.message.reply_text(f"❌ Lỗi khi tải menu: {e}")
