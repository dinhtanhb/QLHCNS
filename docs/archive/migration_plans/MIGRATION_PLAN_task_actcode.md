# Kế hoạch bổ sung ActCode cho công việc

Chủ dự án yêu cầu tách mã công việc nội bộ duy nhất khỏi mã ActCode được dùng
lặp lại (tệp yêu cầu ngày 19/10/2026). Chỉ thêm cột `tblTask.ActCode`, nullable,
nvarchar(50), có chỉ mục; không đổi `TaskCode`, dữ liệu hoạt động hoặc báo cáo.
Tác nhân chỉ thử trên DB tạm/restore thử, **không áp vào DB vận hành**.

**Áp migration trước, triển khai mã sau.** Mã cũ vẫn chạy với cột nullable mới.
Hai migration là `task.0004_task_act_code` và `task.0005_backfill_act_code`.
0005 chỉ gán ActCode cho TaskCode khớp chính xác danh mục đã đóng băng bên dưới,
theo lô tối đa 100 trong transaction riêng; không suy đoán mã lịch sử khác.
Vì TaskCode unique, tối đa 18 hàng khớp tại thời điểm áp dụng.

| Bước | Lệnh/thao tác | Ai làm | Kiểm tra | Hoàn tác |
| --- | --- | --- | --- | --- |
| 1 | Xác nhận server/DB đích và cửa sổ bảo trì | Chủ dự án/DBA | Không dùng DB tạm nhầm làm đích; giữ kín kết nối | Dừng |
| 2 | Full/COPY_ONLY backup có CHECKSUM; VERIFYONLY; restore vào DB riêng | DBA | Backup có hash, restore thành công, DBCC CHECKDB sạch | Không migrate nếu chưa đạt |
| 3 | Chạy truy vấn đếm chỉ đọc dưới đây trước khi áp | Chủ dự án/DBA | Ghi tổng hàng khớp, tối đa 18; không thay TaskCode | Không đổi dữ liệu |
| 4 | `venv\Scripts\python.exe ops\check_migration_state.py --app task` | Kỹ sư | 0003 đã áp, 0004/0005 outstanding | Chỉ đọc |
| 5 | `venv\Scripts\python.exe src\manage.py sqlmigrate task 0004` và `sqlmigrate task 0005` trên cấu hình DB tạm | Kỹ sư/DBA | Chỉ thêm ActCode nullable/index; 0005 là Python, xem SQL UPDATE runtime trong nhật ký | Dừng khi SQL ngoài phạm vi |
| 6 | `venv\Scripts\python.exe src\manage.py migrate task 0005` trên restore thử | DBA | Đếm đúng hàng, UAT, rollback 0003 rồi áp lại đạt | Xem bước 10 |
| 7 | Sau backup/restore thử được xác nhận, chạy cùng lệnh bước 6 trên DB vận hành | **Chủ dự án/DBA** | Đúng đích, hàng gán bằng số bước 3; không đổi TaskCode | Xem bước 10 |
| 8 | Triển khai mã form mới sau khi migration đạt | Kỹ sư theo ủy quyền riêng | Ba task cùng ActCode có ba mã CV khác nhau, Khác lưu NULL | Quay mã trước |
| 9 | Chạy checker bước 4, đếm sau áp, QA riêng kiểm form/list/detail | Chủ dự án/QA | Không outstanding; không dùng phiên thật để UAT | Đánh giá dữ liệu mới |
| 10 | Quay về mã cũ trước, `venv\Scripts\python.exe src\manage.py migrate task 0003` | Chủ dự án/DBA | Bỏ cột/index ActCode; TaskCode và hồ sơ không đổi | Mất toàn bộ ActCode đã nhập; xuất riêng giá trị cần giữ trước rollback |

## Truy vấn chỉ đọc trước khi áp

```sql
SELECT TaskCode FROM tblTask WHERE TaskCode IN (
 N'46.9.1.1.2.1', N'46.9.1.1.2.2', N'46.9.1.1.2.3',
 N'46.9.1.1.3.1', N'46.9.1.1.3.2', N'46.9.1.1.3.3', N'46.9.1.1.3.4',
 N'46.9.1.2.1', N'46.9.1.3.1', N'46.9.1.4.1', N'46.9.1.5.1',
 N'46.9.2.1.1', N'46.9.2.1.2', N'46.9.2.1.3', N'46.9.2.1.4',
 N'46.9.3.1', N'46.9.3.2', N'46.9.3.3'
) ORDER BY TaskCode;
```

Đếm số dòng kết quả; nếu thay `SELECT TaskCode` bằng `SELECT COUNT(*) AS Total`, phải bỏ `ORDER BY TaskCode` ở cuối truy vấn đếm.
Không tham chiếu ActCode trước khi cột tồn tại. Sau áp, chạy:

```sql
SELECT TaskCode, ActCode FROM tblTask WHERE ActCode IS NOT NULL ORDER BY TaskCode;
SELECT COUNT(*) AS Matched FROM tblTask WHERE ActCode = TaskCode;
```

Ngay sau backfill, số Matched phải bằng số trước áp. TaskCode `CV01`,
`ACT-5-REPORT`, mã ngoài danh mục vẫn giữ nguyên và ActCode NULL.
Hoàn tác 0005 riêng là no-op có chủ ý; rollback đến 0003 mới bỏ cột.
Áp lại 0005 chỉ điền nơi ActCode NULL, không ghi đè giá trị đã có.

`sqlmigrate` không sinh SQL của RunPython. SQL UPDATE thực, số hàng, thời gian
trên restore thử và kết quả SQLite/SQL Server được ghi tại
[nhật ký công việc](../../PROJECT_WORK_LOG.md). Không lấy SQL sinh ra thay backup/UAT.

Admin hiển thị/lọc ActCode trong đợt giao diện kế tiếp. Không thêm cột vào export,
Dashboard/KPI/báo cáo. Đề xuất gán ActCode cho Task báo cáo hoạt động từ
activity_code được để chủ dự án quyết định; **không sửa activity/services.py**.
