# Bài thu hoạch cá nhân (Reflection)

- **Họ và tên:** Nguyễn Phương Thùy
- **Mã Học Viên:** 2A202601953
- **Vai trò trong dự án:** Code Frontend (React)

## 1. Những đóng góp của tôi trong dự án
- Xây dựng toàn bộ giao diện người dùng bằng React/Vite với bố cục Split-pane (trái là bài giảng PDF, phải là bảng điều khiển AI).
- Xử lý các tương tác phức tạp: Fix lỗi không cuộn/kéo được chuột trên giao diện Mindmap (thêm `e.preventDefault()` và xử lý Touchpad).
- Fix lỗi đồng bộ hiển thị PDF: Ép Iframe của trình duyệt luôn bắt đầu từ `#page=1` để tránh tình trạng nhảy trang lộn xộn khi đổi bài giảng.
- Cải thiện UX/UI cho Flashcard: Thêm nhãn "Nhánh: [Tên chủ đề]" màu xanh dương nổi bật ngay trên đỉnh thẻ để sinh viên biết câu hỏi thuộc phần nào.
- Xử lý triệt để lỗi "state bleeding": Tự động xóa sạch lịch sử thẻ yếu (`history`) khi người dùng chuyển sang file PDF mới để AI không bị nhầm lẫn dữ liệu.

## 2. Bài học lớn nhất tôi rút ra được từ góc độ Xây dựng sản phẩm AI (AI Product)
- **UI/UX quyết định việc AI có được dùng hay không:** Một AI thông minh đến mấy nhưng nếu đặt trong một giao diện giật lag, không kéo thả được thì người dùng cũng sẽ bỏ cuộc.
- Việc hiển thị trạng thái (Loading state) khi AI đang suy nghĩ là cực kỳ quan trọng để giữ chân người dùng trong lúc chờ đợi API phản hồi (mất 10-20 giây).

## 3. Khó khăn lớn nhất gặp phải và cách giải quyết
- Việc tích hợp thư viện Mindmap và đồng bộ nó với các thao tác vuốt Touchpad (chuột cảm ứng) rất khó, thường bị xung đột với tính năng Zoom của trình duyệt.
- **Cách giải quyết:** Tôi đã phải can thiệp sâu vào hàm `handleWheel`, bắt sự kiện `ctrlKey` để phân biệt giữa hành động Panning (di chuyển) và Zooming.

## 4. Nếu có thêm thời gian, tôi sẽ làm gì khác đi?
- Tôi muốn làm thêm tính năng click vào nhánh Mindmap thì màn hình PDF bên trái sẽ tự động cuộn (scroll) đến đúng trang slide tương ứng của nhánh đó.
