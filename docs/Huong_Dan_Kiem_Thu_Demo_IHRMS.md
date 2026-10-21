# Hướng dẫn kiểm thử demo IHRMS

Tài liệu này dùng cho môi trường demo hoặc SIT có **dữ liệu giả**. Không dùng tài khoản demo hay tạo bản ghi thử trực tiếp trên môi trường đang vận hành.

## Chuẩn bị

1. Dùng một tổ chức, phòng ban, nhân viên, ứng viên, tài sản và kỳ lương thử riêng.
2. Tạo tối thiểu các vai trò: Nhân viên, Quản lý phòng ban, HCNS, Tài chính và Giám đốc.
3. Chuẩn bị một tài khoản Microsoft 365 thử nếu cần mở bản nháp Outlook; thao tác này không gửi thư tự động.
4. Sau khi kết thúc, xóa hoặc lưu trữ riêng toàn bộ bản ghi demo theo quy trình của đơn vị.

## Kịch bản theo vai trò

### Nhân viên

- Vào **Cá nhân** để xem hồ sơ, gửi yêu cầu cập nhật, lập đơn nghỉ, nhập bảng công và xem phiếu lương đã phát hành.
- Vào **Công việc/KPI** để cập nhật tiến độ, đính kèm minh chứng khi hoạt động đã kết thúc và xem kết quả KPI của mình.
- Mở chuông thông báo, đọc trạng thái mới, rồi đánh dấu đã đọc. Bản nháp Outlook chỉ mở để người dùng tự kiểm tra và tự gửi.

### Quản lý phòng ban

- Duyệt đơn nghỉ và bảng công của phòng ban; thử mở hồ sơ hoặc đơn của phòng ban khác để xác nhận bị từ chối.
- Tạo/giao việc, cập nhật KPI trong phạm vi phòng ban và xem lịch sử của nhân viên phụ trách.
- Thử tạo hai yêu cầu đặt cùng một phòng/xe trong cùng thời gian, sau đó duyệt một yêu cầu: yêu cầu còn lại phải không thể cùng được duyệt.

### HCNS

- Tạo và cập nhật hồ sơ nhân viên, hợp đồng, lương và thủ tục vòng đời nhân sự.
- Từ **Nhân sự → NV & Hồ sơ → Thao tác**, ghi nhận nâng lương, bổ nhiệm hoặc điều chuyển rồi chọn soạn quyết định. Kiểm tra bản soạn dùng đúng bản ghi nguồn và ngày hiệu lực.
- Vào **Nhân sự → Biểu mẫu HCNS**, chọn một hồ sơ. Các trường có danh mục phải dùng danh sách chọn; các trường phù hợp phải tự điền từ hồ sơ. Mẫu tuyển dụng vẫn yêu cầu chọn ứng viên riêng.
- Với quyết định, lưu bản nháp, gửi duyệt, duyệt bởi người có quyền khác người gửi, rồi ban hành PDF. Bản nháp chưa làm thay đổi hồ sơ nhân viên.

### Tài chính và Giám đốc

- Tạo kỳ lương thử, tính lương từ cấu hình thử đã được kiểm tra, khóa kỳ và phát hành phiếu lương. Không thay thông số BHXH/PIT thật để phục vụ demo.
- Duyệt đề nghị mua sắm, kiểm tra không thể phát hành kho vượt tồn; đánh dấu đã mua sau khi được duyệt.
- Giám đốc duyệt quyết định nhân sự hoặc đề xuất hoạt động dự án; người ban hành kiểm tra tệp PDF và lịch sử quyết định.

## Kiểm tra biểu mẫu và xuất tệp

1. Chọn cán bộ ở danh mục nguồn, mở mẫu cần dùng và kiểm tra họ tên, phòng ban, vị trí cùng các dữ liệu phù hợp đã được điền.
2. Với QĐ bổ nhiệm/điều chỉnh lương, chọn người ký riêng; nhập lương số và kiểm tra phần bằng chữ tự đổi.
3. Bấm **Cập nhật bản xem trước**, kiểm tra nội dung trước khi tải Word hoặc in/lưu PDF.
4. Xác nhận tên tệp theo cú pháp `LoaiTaiLieu_MaHoSo_YYYYMMDD.ext`, ví dụ `QD_NangLuong_VH-999_20261006.docx`.
5. Đóng/mở lại trình duyệt hoặc tải cứng trang nếu máy từng mở phiên bản cũ của biểu mẫu.

## Kết quả cần ghi nhận

Ghi mã bản ghi demo, vai trò đã dùng, thao tác, kết quả mong đợi/thực tế, thời điểm, ảnh chụp nếu có lỗi và tên tệp đã xuất. Không ghi mật khẩu, token, số CCCD, số tài khoản, tệp hồ sơ thật hoặc ảnh có dữ liệu cá nhân vào biên bản lỗi.

Các giới hạn tích hợp như Word/Excel desktop, Outlook/Microsoft 365, máy in PDF, SQL Server/IIS và quyền lưu trữ doanh nghiệp cần được người phụ trách xác nhận trên môi trường tương ứng. Kết quả chạy cô lập của dự án được ghi tại [Báo cáo kiểm thử demo](archive/reviews/Bao_Cao_Kiem_Thu_Demo_2026-10-06.md).
