# Các trạng thái của ConversationHandler
(
    BROWSE_CATEGORY,
    BROWSE_ITEMS,
    SELECT_SIZE,
    SELECT_QUANTITY,
    CART_VIEW,
    COLLECT_NAME,
    COLLECT_PHONE,
    COLLECT_ADDRESS,
    CONFIRM_ORDER,
) = range(9)

# Trạng thái mở rộng
ENTER_QUANTITY    = 9   # khách nhập số lượng thủ công (>5)
USE_SAVED_PROFILE = 10  # hỏi khách có dùng thông tin giao hàng đã lưu không
POST_ORDER        = 11  # sau đặt hàng thành công: tiếp tục hay kết thúc
