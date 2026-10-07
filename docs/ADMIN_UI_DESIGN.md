# Thiết kế giao diện trang quản trị IHRMS

## 1. Mục đích

Tài liệu này mô tả giao diện quản trị đang được cấu hình trong IHRMS và ghi lại các nguyên tắc có thể tham khảo khi xây dựng trang quản trị cho QLHD hoặc `nhaplieu_app`.

Đây là tài liệu mô tả cấu hình và định hướng giao diện, không phải thiết kế UI độc lập hay cam kết rằng mọi mục tiêu trong tài liệu đã được triển khai. Thiết kế hiện tại dựa trên Django Admin được tùy biến bằng Jazzmin (giao diện AdminLTE 3).

## 2. Các tệp liên quan trong IHRMS

| Thành phần | Tệp | Vai trò |
|---|---|---|
| Cấu hình giao diện Django Admin | `src/config/settings.py` | Khai báo tiêu đề/nhãn, liên kết, thứ tự nhóm ứng dụng, biểu tượng và các tùy chỉnh bố cục Jazzmin. |
| Giao diện portal nội bộ — không phải Django Admin | `src/templates/base.html` | Khung trang portal, header, menu nghiệp vụ và điều hướng dùng chung. |
| CSS tùy chỉnh | `src/static/css/ihrms.css` | Kiểu dáng portal, điều hướng và một số thành phần biểu mẫu. |
| CSS Tailwind đã build | `src/static/css/tailwind.css` | Các lớp tiện ích được dùng trong template. |
| Màn hình dashboard portal — không phải Django Admin index | `src/apps/portal/templates/portal/dashboard.html` | Nội dung trang chủ của portal; kế thừa `base.html`. |

Trong `settings.py`, cấu hình bắt đầu tại `JAZZMIN_SETTINGS` và `JAZZMIN_UI_TWEAKS`. Ứng dụng chỉ thêm Jazzmin vào `INSTALLED_APPS` khi package có sẵn; nếu không, cấu hình giao diện Jazzmin không được áp dụng và Django Admin dùng giao diện mặc định.

## 3. Đặc điểm giao diện quản trị hiện tại

### Nhận diện và điều hướng

- Tên hiển thị và nội dung chào mừng mang thương hiệu IHRMS.
- Có các liên kết tới portal, trung tâm báo cáo và trang tổng quan quản trị.
- Sidebar được bật và mặc định mở rộng.
- Nhóm ứng dụng được sắp xếp theo luồng nghiệp vụ, gồm nhân sự, tổ chức, chấm công, nghỉ phép, hợp đồng, lương, công việc, KPI, tài liệu, tài sản, tuyển dụng, mua sắm, thông báo, báo cáo và phân quyền.
- Các ứng dụng và mô hình chính có biểu tượng riêng; những mục chưa khai báo dùng biểu tượng mặc định.

### Bố cục và phong cách

- Thanh điều hướng và sidebar dùng phối màu xanh primary, với navbar/sidebar tối.
- Navbar và sidebar được cấu hình cố định khi cuộn trang.
- Form quản trị dùng bố cục tab ngang (`horizontal_tabs`).
- Các kích thước chữ nhỏ được tắt để giữ khả năng đọc.
- Bộ nút primary, secondary, info, warning, danger và success dùng các class chuẩn của giao diện.

Các giá trị cụ thể được cấu hình trong `JAZZMIN_SETTINGS` và `JAZZMIN_UI_TWEAKS` của `src/config/settings.py`; thư viện Jazzmin/AdminLTE cung cấp phần template và thành phần giao diện nền.

## 4. Nguyên tắc tham khảo cho QLHD và `nhaplieu_app`

Có thể dùng các nguyên tắc sau làm điểm xuất phát, sau đó điều chỉnh theo nghiệp vụ, nhận diện thương hiệu và công nghệ của từng dự án:

1. **Nhận diện nhất quán:** đặt tên hệ thống, logo/brand, tiêu đề trang và nội dung chào mừng ở một nơi cấu hình tập trung.
2. **Menu theo công việc:** phân nhóm theo quy trình người dùng thực hiện, đặt nhóm thường dùng lên trước và tránh đưa mọi chức năng lên cùng một cấp.
3. **Tìm thấy chức năng nhanh:** dùng nhãn rõ nghĩa, biểu tượng nhất quán và tìm kiếm cho dữ liệu/nghiệp vụ phù hợp.
4. **Phân cấp thao tác:** làm nổi bật hành động chính; dùng màu cảnh báo cho thao tác nguy hiểm và yêu cầu xác nhận ở nơi cần thiết.
5. **Form dễ nhập liệu:** chia form dài thành nhóm hoặc tab có nhãn dễ hiểu; hiển thị lỗi ngay cạnh trường và giữ dữ liệu hợp lệ khi có lỗi.
6. **Bảng dễ rà soát:** có tiêu đề cột rõ ràng, bộ lọc/tìm kiếm phù hợp, trạng thái dễ phân biệt và phân trang khi dữ liệu dài.
7. **Dùng được trên nhiều kích thước màn hình:** kiểm tra menu, bảng và form ở màn hình hẹp; không dựa vào màu sắc đơn thuần để truyền tải trạng thái.
8. **Tách giao diện khỏi quyền hạn:** ẩn menu hoặc nút chỉ cải thiện UX, không thay thế kiểm tra quyền tại server cho URL, thao tác POST, dữ liệu và từng đối tượng.
9. **Giữ nhất quán giữa các màn hình:** tái sử dụng mẫu header, điều hướng, thông báo, nút và biểu mẫu thay vì tạo phong cách riêng cho từng phân hệ.

## 5. Khi áp dụng sang dự án khác

- Trước tiên xác định `QLHD` và `nhaplieu_app` dùng Django Admin, một framework admin khác hay trang quản trị tự xây dựng. Tài liệu này không giả định hai dự án dùng cùng framework.
- Nếu dự án dùng Django Admin và Jazzmin, có thể tham khảo cách tổ chức cấu hình trong `JAZZMIN_SETTINGS`/`JAZZMIN_UI_TWEAKS`, nhưng cần kiểm tra phiên bản package và các tùy chọn được phiên bản đó hỗ trợ.
- Chỉ chuyển các ý tưởng giao diện như tên hệ thống, nhóm menu, biểu tượng và phối màu. Không sao chép nguyên các app label, model, URL, quyền, cấu hình bảo mật hoặc nhãn nghiệp vụ đặc thù IHRMS.
- Nếu cần đổi sâu template hoặc CSS, kiểm tra cơ chế override template/static của thư viện đang dùng; ưu tiên đặt phần tùy biến trong mã dự án và tránh sửa trực tiếp mã package.
- Thiết kế cuối cùng cần phản ánh quyền và quy trình thật của dự án đích; kiểm thử truy cập trực tiếp và thao tác bị cấm ở phía server, không chỉ kiểm tra hình thức menu.

## 6. Phạm vi và lưu ý

- Đây là mô tả cấu hình trong mã nguồn tại thời điểm ghi tài liệu; giao diện thực tế còn phụ thuộc package Jazzmin được cài đặt, static assets và cấu hình triển khai.
- `src/templates/base.html` cùng các CSS portal mô tả portal nội bộ, không phải nguồn template của Django Admin.
- Tài liệu này không thay thế thiết kế nghiệp vụ, ma trận phân quyền, hướng dẫn triển khai hoặc kiểm thử giao diện trên trình duyệt.
- Nhật ký thay đổi của dự án được tập trung tại [`PROJECT_WORK_LOG.md`](./PROJECT_WORK_LOG.md).
