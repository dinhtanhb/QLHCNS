# Phê bình Trang chủ và Báo cáo định biên — 15/10/2026

Phương pháp: hai đánh giá độc lập của Impeccable (A: design_assessment_a; B: design_assessment_b). Phạm vi là cách trình bày; giữ nghiệp vụ, quyền, nguồn số liệu, liên kết và giấy in. Chế độ: Operate. Căn cứ: DESIGN.md, MASTER, token navy–teal và hai ảnh chủ dự án gửi. Thư mục ảnh Atoms không hiện hữu trong checkout này.

## Trước sửa

Giao diện có bản sắc IHRMS và thứ tự nghiệp vụ hợp lý, nhưng giống nhiều khối bị ép vào một màn hình. Chữ gần cùng cỡ, hàng sít, viền và nút cạnh tranh nhau khiến mắt khó chọn điểm bắt đầu.

- **Phân cấp — chưa đạt:** tiêu đề nhóm gần giống nhãn. Dùng h1 24/32, h2 18/28, nhãn 14/20, KPI 32/40, số vừa 24/32; phân biệt thêm bằng trọng lượng và màu.
- **Nhịp — chưa đạt:** đệm thẻ 4px và các trần chiều cao làm nội dung dính nhau. Dùng đệm 16–20px, gap thẻ16px/nhóm32px; trả lại 5/3 dòng theo vai trò, cuộn tự nhiên.
- **Căn lề — chưa đạt:** tên phòng và thanh xa nhau; số Tuyển dụng không cùng trục. Dùng cột tên200px/thanh co giãn/số72px/cờ; dải chỉ số số trên, nhãn dưới và divider nhẹ.
- **Kiềm chế — chưa đạt:** viền/bóng/icon trang trí và phần vượt nâu đặc gây ồn. Bỏ bóng, dùng viền trang trí nhạt, icon chỉ ở KPI/trạng thái; cảnh báo bằng phần vượt mảnh và huy hiệu nhẹ. Đưa trạng thái rỗng vào thẻ.
- **Nhất quán — chưa đạt:** báo cáo có tiêu đề nhỏ, bộ lọc rời và số lệch cột. Dùng cùng thang chữ/thẻ; căn phải số, nhãn “Vượt/Thiếu/Đủ”, giữ số gốc và công thức.

Ưu tiên P1: phân cấp chữ, khoảng thở và ý nghĩa chênh lệch. P2: trục định biên, dải Dự án/Tuyển dụng, tên bị cắt và vùng cuộn báo cáo có nhãn/focus. KPI không có đích hợp lệ vẫn chỉ hiển thị; không tự thêm drilldown hoặc tham số mới.

Điểm heuristic trước sửa: trạng thái3, ngôn ngữ3, chủ động3, nhất quán2, ngăn hiểu nhầm2, nhận biết3, hiệu suất2, tối giản1, phục hồi lỗi2 (chưa quan sát lỗi thật), trợ giúp3: **24/40**. Điểm này đánh giá hai trang quan sát được, không chứng nhận toàn hệ thống.

Người dùng thường xuyên cần thấy chênh lệch/việc chờ nhanh; người mới cần hiểu dấu âm/dương; người dùng bàn phím cần focus rõ và tên đầy đủ. Nhân viên ít nội dung nên giữ thoáng, không thêm số để lấp chỗ. HR có nhiều lựa chọn nên giảm tải bằng nhịp và thứ bậc, không bỏ nghiệp vụ.

Điểm mạnh cần giữ: palette sáng/tối, phạm vi/ngày cập nhật, thứ tự nhóm, donut có ký hiệu và bảng thay thế, liên kết nghiệp vụ và Cách tính.

## Bằng chứng và giới hạn

A xem trực tiếp32 ảnh (4 vai trò ×1440/1756 ×sáng/tối ×màn hình đầu/toàn trang), hai ảnh chủ dự án và live HR/báo cáo. B xem live desktop/mobile và DOM của hai trang. Server8796 còn template cache có URL compact-final; không gán các ảnh cũ đó cho toàn bộ HEAD. Baseline mới được dựng từ archive `f9c1395` tại port8811 trên DB giả tách biệt; nguồn mới port8810, restart sau đổi template.

Detector trước sửa chạy đúng markup:26 advisory `design-system-color`, đều line0/rgb(0,0,0), vì không resolve được URL Django `{% static %}`. Đây là false positive của quét template chưa render; không phải26 lỗi màu đã xác minh. Không thêm ignore/waiver để làm xanh. CUA evaluate chỉ đọc nên không inject script/overlay; dùng ảnh thật/DOM và scan nguồn. Không khởi động server overlay.

Chưa kiểm screen reader, zoom native200%, tài khoản thật hay máy in thật. Tab của B đã đóng; server/ảnh giả và kết quả quét giữ ngoài Git. Không lấy ảnh UI làm bằng chứng nghiệp vụ/khả năng tiếp cận toàn bộ.

Questions skipped: yêu cầu đã chốt hệ chữ, nhịp, palette, bố cục và phạm vi. Phiên bản Impeccable này dùng `layout` thay `arrange`, không có lệnh `normalize`; chuẩn hóa thực hiện theo token/MASTER bằng layout/typeset/polish. Các vòng và kết luận sau sửa được cập nhật cùng đợt trong nhật ký và mục dưới.

## Sau sửa

Chưa nghiệm thu. Chỉ cập nhật sau khi xem bộ ảnh cuối, kiểm tra tự động và phê bình độc lập lại; không suy từ detector sạch rằng giao diện đã tốt.
