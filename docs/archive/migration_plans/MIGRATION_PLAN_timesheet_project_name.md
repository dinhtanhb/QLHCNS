# Tên dự án nhập tay trên dòng chấm công

Nguồn yêu cầu: chủ dự án ngày 20/10/2026 yêu cầu nhập tên dự án khi danh sách không có.
Migration `attendance.0009_timesheetentry_project_name` thêm `ProjectName` (255 ký tự,
blank/default rỗng) vào `tblTimesheetEntry`; không tạo Project hay đổi công thức giờ/lương.
Model và migration đi commit riêng trước mã giao diện/view dùng cột mới.

## Áp dụng

1. Xác nhận đúng alias/instance/tên DB với chủ dự án; dừng ghi ứng dụng trong cửa sổ bảo trì.
2. Backup DB đích và restore thử sang DB cô lập; ghi kiểm tra số dòng/khóa/giờ công.
3. Trên bản restore, chạy `python ops/check_migration_state.py --app attendance`,
   `python src/manage.py migrate attendance 0009`, kiểm dữ liệu cũ có tên rỗng,
   số dòng/giờ/FK giữ nguyên; thử tạo dòng có dự án danh mục, tên nhập tay và tháng đã duyệt.
4. Chỉ khi đã được duyệt đích và backup/restore đạt, áp cùng migration vào DB đích;
   kiểm lại trạng thái và khởi động lại ứng dụng bằng nguồn đã kiểm thử.

## Hoàn tác

Trước khi có tên nhập tay mới, trở về mã trước đợt và `python src/manage.py migrate attendance 0008`
trong cửa sổ bảo trì. Sau khi có dữ liệu mới, xuất/bảo toàn cột ProjectName trước;
rollback migration sẽ xóa cột và mất tên nhập tay. Ưu tiên sửa tiến hoặc restore backup
đã xác minh theo kế hoạch vận hành; không tự hoàn tác dữ liệu thật.

## Bằng chứng phát triển

`sqlmigrate` đã đối chiếu SQLite memory và SQL Server DB test UUID: SQL Server thêm
cột và giá trị rỗng cho dòng cũ; SQLite dựng bảng tạm, sao chép đầy đủ cột/khóa/chỉ mục,
đổi tên lại bảng. Không sửa bảng khác. Kiểm drift đạt, 185 test tập trung SQLite đạt.
Chỉ migrate DB QA dùng một lần; chưa áp trên DB vận hành.
