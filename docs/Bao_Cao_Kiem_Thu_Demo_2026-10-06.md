# Báo cáo kiểm thử demo toàn hệ thống IHRMS — 06/10/2026

## Phạm vi và môi trường

Kiểm thử chạy trên nhánh `main`, commit cơ sở `9fa7760`, với CSDL SQLite/SQL Server kiểm thử dùng một lần và media tạm. Dữ liệu tạo trong các bài kiểm thử là giả; không dùng CSDL, media, tài khoản hoặc hồ sơ nghiệp vụ đang vận hành. M365 bị tắt trong các lượt tự động.

Phạm vi gồm toàn bộ ứng dụng Django đã được discovery: nhân sự, biểu mẫu HCNS, vòng đời, nghỉ phép/chấm công, lương, tài sản/kho/mua sắm, công việc/KPI, hoạt động dự án, văn bản, báo cáo, phân quyền, thông báo và tệp riêng tư.

## Kết quả tự động

| Hạng mục | Cách kiểm tra | Kết quả |
| --- | --- | --- |
| Toàn hệ thống SQLite | `ops/run_tests.py --backend sqlite` | 376 ca đạt; 4 ca SQL Server-only được skip |
| Toàn hệ thống SQL Server | `ops/run_tests.py --backend sqlserver` | 376/376 ca đạt; 0 skip, 0 lỗi |
| Giao diện HCNS đăng nhập | Edge headless, DB/media giả | Đạt: 26 mẫu preview/tải tệp, tự điền, dropdown, in, mobile, cache cũ, validation/CSRF, 0 lỗi JavaScript |
| Luồng NV & Hồ sơ | Edge headless, DB/media giả | Đạt: nâng lương, bổ nhiệm, điều chuyển, khen thưởng/kỷ luật, hợp đồng, mobile, không lỗi JavaScript |
| Danh mục và xuất 26 biểu mẫu | Edge headless, DB/media giả | Đạt: dropdown, tự điền, xuất 26 tệp, mobile, không lỗi JavaScript |

Log SQLite: `%TEMP%\\ihrms-demo-full-sqlite-20261006.log`; log SQL Server: `%TEMP%\\ihrms-demo-full-sqlserver-20261006.log`; log browser: `%TEMP%\\ihrms-demo-live-browser-final-20261006.log`. Các log và tệp xuất dùng dữ liệu giả, không nằm trong Git.

## Luồng đã kiểm tra

- Phân quyền và giới hạn phạm vi theo vai trò; hành động không có quyền, CSRF và các trường hợp lỗi được kiểm tra cùng bộ hồi quy.
- Hồ sơ nhân sự, hợp đồng, lương, điều chuyển/bổ nhiệm/khen thưởng/kỷ luật và liên kết sang bản soạn quyết định.
- 26 biểu mẫu HCNS: danh mục nguồn, tự điền theo hồ sơ, ứng viên tách khỏi nhân viên, preview, Word/Excel, in PDF, tên tệp, di động và cache static cũ.
- Vòng đời nhân sự, nghỉ phép, chấm công, bảng công, kỳ lương/phiếu lương, báo cáo, thông báo/outbox.
- Tài sản, kiểm kê, thanh lý, vật tư, mua sắm, đặt phòng/xe và ngăn duyệt trùng lịch.
- Công việc, KPI, hoạt động dự án, đề xuất, văn bản đến/đi và tệp riêng tư.

## Phát hiện trong lượt này

Không phát hiện lỗi sản phẩm từ bộ hồi quy SQLite. Hai lỗi ban đầu thuộc harness trình duyệt ngoài Git: harness vẫn dùng `fill()`/kỳ vọng text cho các trường nay đã chuẩn hóa thành dropdown. Harness đã được sửa để chọn giá trị danh mục và để trống đúng các trường ứng viên của mẫu tuyển dụng; không sửa quy tắc nghiệp vụ hoặc mã sản phẩm.

## Phần cần xác nhận bằng UAT/tích hợp

- Microsoft Word/Excel desktop và bố cục in trên máy người dùng.
- Outlook/Microsoft 365, SharePoint/OneDrive, gửi thư thật và quyền tenant.
- SQL Server/IIS/HTTPS, backup/restore, phân quyền thư mục, hiệu năng dữ liệu lớn và thiết bị in PDF.
- Các báo cáo BHXH, PIT và chi phí phòng ban đang fail-closed chờ quy tắc tài chính được xác nhận; không có kết luận nghiệp vụ tài chính từ dữ liệu demo.

Thực hiện tiếp theo của người dùng: chạy các kịch bản trong [Hướng dẫn kiểm thử demo](Huong_Dan_Kiem_Thu_Demo_IHRMS.md) trên SIT bằng dữ liệu ẩn danh và ghi lại các điểm khác biệt theo vai trò.
