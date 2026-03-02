"""
bot.py — Entry point của Telegram Bot Trà Sữa Nhà Mình.

Khởi chạy:
    python bot.py
"""
import logging
import warnings

from telegram.warnings import PTBUserWarning

# Suppress warning về per_message=False trong ConversationHandler
# Đây là hành vi đúng cho bot chat tuần tự (không phải inline message bot)
warnings.filterwarnings("ignore", category=PTBUserWarning)

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
from handlers import (
    add_more,
    ask_custom_quantity,
    back_to_categories,
    back_to_items,
    back_to_size,
    clear_cart,
    cmd_export,
    cmd_history,
    cmd_reload_menu,
    cmd_stats,
    collect_address,
    collect_name,
    collect_phone,
    enter_new_address,
    handle_cancel_order,
    handle_category,
    handle_confirm,
    handle_custom_quantity,
    handle_edit_delivery,
    handle_item,
    handle_order_action,
    handle_order_again,
    handle_order_done,
    handle_quantity,
    handle_size,
    proceed_checkout,
    remove_item,
    send_qr,
    show_categories,
    start,
    use_saved_profile,
    view_cart,
)
from handlers.states import (
    BROWSE_CATEGORY,
    BROWSE_ITEMS,
    CART_VIEW,
    COLLECT_ADDRESS,
    COLLECT_NAME,
    COLLECT_PHONE,
    CONFIRM_ORDER,
    ENTER_QUANTITY,
    POST_ORDER,
    SELECT_QUANTITY,
    SELECT_SIZE,
    USE_SAVED_PROFILE,
)
from menu_loader import load_menu

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)   # giảm noise
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Fallback handlers
# ──────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /help — hướng dẫn sử dụng bot."""
    await update.message.reply_text(
        "📖 <b>HƯỚNG DẪN SỬ DỤNG BOT</b>\n\n"
        "🛒 <b>Đặt hàng:</b> Gõ /start → chọn món → thanh toán\n"
        "❌ <b>Huỷ đơn:</b> Gõ /cancel bất kỳ lúc nào\n"
        "📲 <b>Chia sẻ:</b> Gõ /qr để lấy mã QR chia sẻ cho bạn bè\n\n"
        "💬 Cần hỗ trợ thêm? Nhắn Zalo cho cửa hàng nhé!",
        parse_mode="HTML",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /cancel — huỷ mọi thứ và quay về đầu."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Đã huỷ. Gõ /start để bắt đầu lại nhé!"
    )
    return ConversationHandler.END


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tin nhắn không hợp lệ trong luồng hội thoại."""
    await update.message.reply_text(
        "⚠️ Vui lòng sử dụng các nút bấm để điều hướng.\n"
        "Gõ /cancel để huỷ và bắt đầu lại."
    )


# ──────────────────────────────────────────────
# Startup: load menu vào bot_data
# ──────────────────────────────────────────────

async def on_startup(application: Application) -> None:
    """Chạy lúc bot khởi động — load menu một lần duy nhất."""
    menu = load_menu()
    application.bot_data["menu"] = menu
    logger.info("Menu đã được load: %s", list(menu.keys()))


# ──────────────────────────────────────────────
# Xây dựng ConversationHandler
# ──────────────────────────────────────────────

def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            # ── Duyệt danh mục ──
            BROWSE_CATEGORY: [
                CallbackQueryHandler(show_categories,    pattern="^start_order$"),
                CallbackQueryHandler(handle_category,    pattern="^cat_"),
                CallbackQueryHandler(view_cart,          pattern="^view_cart$"),
            ],

            # ── Duyệt món ──
            BROWSE_ITEMS: [
                CallbackQueryHandler(handle_item,          pattern="^item_"),
                CallbackQueryHandler(back_to_categories,   pattern="^back_to_categories$"),
            ],

            # ── Chọn size ──
            SELECT_SIZE: [
                CallbackQueryHandler(handle_size,      pattern="^size_"),
                CallbackQueryHandler(back_to_items,    pattern="^back_to_items$"),
            ],

            # ── Chọn số lượng (nút 1-5 hoặc nhập tay) ──
            SELECT_QUANTITY: [
                CallbackQueryHandler(handle_quantity,       pattern=r"^qty_\d+$"),
                CallbackQueryHandler(ask_custom_quantity,   pattern="^qty_custom$"),
                CallbackQueryHandler(back_to_size,          pattern="^back_to_size$"),
            ],

            # ── Nhập số lượng thủ công ──
            ENTER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_quantity),
            ],

            # ── Giỏ hàng ──
            CART_VIEW: [
                CallbackQueryHandler(add_more,          pattern="^add_more$"),
                CallbackQueryHandler(clear_cart,        pattern="^cart_clear$"),
                CallbackQueryHandler(proceed_checkout,  pattern="^cart_checkout$"),
                CallbackQueryHandler(remove_item,       pattern="^remove_"),
            ],

            # ── Hỏi có dùng địa chỉ đã lưu không ──
            USE_SAVED_PROFILE: [
                CallbackQueryHandler(use_saved_profile,  pattern="^profile_use$"),
                CallbackQueryHandler(enter_new_address,  pattern="^profile_new$"),
            ],

            # ── Thu thập thông tin giao hàng ──
            COLLECT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name),
            ],
            COLLECT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_phone),
            ],
            COLLECT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_address),
            ],

            # ── Xác nhận đơn ──
            CONFIRM_ORDER: [
                CallbackQueryHandler(handle_confirm,        pattern="^order_confirm$"),
                CallbackQueryHandler(handle_edit_delivery,  pattern="^order_edit$"),
                CallbackQueryHandler(handle_cancel_order,   pattern="^order_cancel$"),
            ],

            # ── Sau đặt hàng thành công ──
            POST_ORDER: [
                CallbackQueryHandler(handle_order_again, pattern="^order_again$"),
                CallbackQueryHandler(handle_order_done,  pattern="^order_done$"),
            ],
        },
        fallbacks=[
            CommandHandler("start",  start),
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message),
        ],
        allow_reentry=True,
        per_message=False,   # track theo chat, không theo từng message (suppress PTBUserWarning)
    )


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )

    # ── Lệnh toàn cục (hoạt động mọi lúc, kể cả trong conversation) ──
    # group=-1 đảm bảo chạy trước ConversationHandler
    app.add_handler(CommandHandler("qr",       send_qr),           group=-1)
    app.add_handler(CommandHandler("help",     help_command),      group=-1)
    app.add_handler(CommandHandler("history",     cmd_history),       group=-1)
    app.add_handler(CommandHandler("stats",       cmd_stats),         group=-1)
    app.add_handler(CommandHandler("export",      cmd_export),        group=-1)
    app.add_handler(CommandHandler("reloadmenu",  cmd_reload_menu),   group=-1)

    # ── Callback từ seller: xác nhận / huỷ đơn ──
    # Phải đăng ký group=-1 để không bị ConversationHandler chặn
    app.add_handler(CallbackQueryHandler(handle_order_action, pattern="^(done|cancel)_"), group=-1)

    # ── Luồng hội thoại chính ──
    app.add_handler(build_conversation_handler())

    if config.WEBHOOK_URL:
        # ── Production: Webhook mode ──────────────────────────────────
        # Telegram gọi vào server thay vì server liên tục hỏi Telegram
        # Phù hợp với Render / Railway khi có URL public cố định
        webhook_path = "/telegram"
        logger.info(
            "Chạy WEBHOOK mode tại %s%s (port %d)",
            config.WEBHOOK_URL, webhook_path, config.PORT,
        )
        app.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=webhook_path,                          # path bot lắng nghe
            webhook_url=f"{config.WEBHOOK_URL}{webhook_path}",  # URL đăng ký với Telegram
            drop_pending_updates=True,
        )
    else:
        # ── Development: Polling mode ─────────────────────────────────
        # Dùng khi chạy local — không cần URL public
        logger.info("Chạy POLLING mode (local). Nhấn Ctrl+C để dừng.")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    main()
