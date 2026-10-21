# Kế hoạch áp dụng `planning.0003_event_attendance_mode`

## Mục đích và giới hạn

Migration này bổ sung cột nullable `AttendanceMode` cho `tblEvent`. Sự kiện
lịch sử giữ `NULL` và portal/admin hiển thị **Chưa xác định**; sự kiện mới mặc
định `Offline` sau khi dữ liệu được ghi. Không suy đoán hay cập nhật hình thức
của sự kiện cũ. Kế hoạch này phải được thực hiện **trước khi triển khai mã có
phụ thuộc cột mới**.

Không chạy `migrate` vào DB vận hành trong lượt chuẩn bị tài liệu này.

| Bước | Lệnh hoặc thao tác | Chủ sở hữu | Xác minh | Hoàn tác |
| --- | --- | --- | --- | --- |
| 1. Chốt đích | Xác nhận server, database, catalog và cửa sổ bảo trì bằng kênh vận hành | Chủ dự án + DBA | Tên đích khớp runbook, không đưa chuỗi kết nối vào ticket/log | Dừng trước khi chạm DB |
| 2. Backup | Tạo full backup theo chính sách SQL Server và kiểm `RESTORE VERIFYONLY`; restore thử vào bản sao cô lập | DBA | Có thời điểm backup, SHA/checksum và restore thử thành công | Giữ backup, không migrate |
| 3. Sao chép UAT | Restore bản backup vào SQL Server tạm riêng, chặn email/tích hợp ghi | DBA | Ứng dụng UAT chỉ trỏ DB tạm | Xóa DB tạm theo quy trình DBA |
| 4. Kiểm trạng thái | `venv\\Scripts\\python.exe ops\\check_migration_state.py --app planning` | Kỹ sư triển khai | `planning.0002` applied, `planning.0003` outstanding trước khi áp dụng | Không có thay đổi vì lệnh chỉ đọc |
| 5. So SQL | `venv\\Scripts\\python.exe src\\manage.py sqlmigrate planning 0003` với cấu hình SQL Server tạm | Kỹ sư + DBA | Chỉ có bổ sung cột nullable được duyệt ở dưới | Dừng nếu có SQL khác |
| 6. Áp dụng UAT | `venv\\Scripts\\python.exe src\\manage.py migrate planning 0003 --database default` | DBA | `check_migration_state.py --app planning` hết outstanding | `migrate planning 0002`; chỉ mất giá trị Hình thức đã nhập sau migration |
| 7. UAT | Tạo Event Online/Offline, mở danh sách/admin, kiểm sự kiện legacy `NULL` | QA + chủ nghiệp vụ | Lưu/đọc lại đúng; legacy là Chưa xác định | Quay mã rồi migration 0002 nếu cần |
| 8. Vận hành | Lặp bước 1–7 trên DB đích trong cửa sổ đã duyệt | DBA + chủ dự án | Backup/restore, UAT và người phụ trách ký nhận | Theo bước 6, đánh giá dữ liệu phát sinh trước khi rollback |

## SQL cần xác nhận trên cấu hình SQL Server tạm

Lệnh bắt buộc chạy lại ngay trước bước 6 với cấu hình DB tạm là:

```powershell
venv\Scripts\python.exe src\manage.py sqlmigrate planning 0003
```

Ngày 17/10/2026 đã chạy `sqlmigrate` trên cấu hình SQL Server đang được đặt cho
nguồn và nhận đúng đầu ra dưới đây. Kết quả này chỉ xác nhận SQL sinh ra; DBA vẫn
phải chạy lại trên SQL Server tạm ở bước 5 trước khi cho phép áp dụng UAT:

```sql
ALTER TABLE [tblEvent] ADD [AttendanceMode] nvarchar(10) NULL;
```

Nếu đầu ra có `UPDATE`, `DELETE`, `DROP`, đổi kiểu cột khác hoặc bảng ngoài
`tblEvent`, dừng triển khai và mở lại review. `sqlmigrate` chỉ sinh SQL; không
thay thế bước backup, restore thử hay `migrate` trên bản sao.

## Kiểm đếm và UAT sau migration

DBA chạy các truy vấn chỉ đọc trong DB tạm và DB đích sau UAT:

```sql
SELECT AttendanceMode, COUNT(*) AS Total
FROM tblEvent
GROUP BY AttendanceMode;

SELECT COUNT(*) AS NullCount FROM tblEvent WHERE AttendanceMode IS NULL;
SELECT COUNT(*) AS OnlineCount FROM tblEvent WHERE AttendanceMode = N'Online';
SELECT COUNT(*) AS OfflineCount FROM tblEvent WHERE AttendanceMode = N'Offline';
```

Kết quả mong đợi: sự kiện cũ vẫn ở `NULL`; Event mới Online/Offline tăng đúng
theo thao tác UAT. Mở danh sách Event và Django admin để xác nhận `NULL` hiển
thị **Chưa xác định**, và hai giá trị mới hiển thị đúng nhãn.

## Nguồn yêu cầu

`attendance_mode` (Online/Offline, legacy NULL, default Offline) là yêu cầu
chủ dự án cung cấp trong kế hoạch giao diện ngày 17/10/2026. Các thay đổi liên
quan đã đi cùng commit `031fbdd`: `ui/text_choice.html`/`common.ui_choices`
(gợi ý và nhập mới), giữ form lỗi qua session, và tìm select dài. Không có
nguồn yêu cầu nghiệp vụ độc lập hơn được cung cấp cho ba thay đổi phụ này;
không gỡ bỏ chúng trong lượt chuẩn bị migration.
