# Kế hoạch áp dụng nhật ký trợ lý tài liệu

Nguồn yêu cầu: [thiết kế đã duyệt ngày 19/10/2026](superpowers/specs/2026-10-19-assistant-chatbot-design.md), mục nhật ký truy vấn. Bằng chứng thực chạy và giới hạn nằm tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md), mục đóng phần còn mở ngày 20/10/2026.

Hai migration của app `assistant`:

- `0001_initial`: tạo `tblAssistantSearchLog`, khóa ngoại người dùng/audit và chỉ mục khóa ngoại. Không sửa bảng công văn, hồ sơ hoặc nội dung tài liệu.
- `0002_searchquerylog_assistant_log_created_idx`: thêm chỉ mục `assistant_log_created_idx` trên `CreatedDate`.

Mã nguồn model và migration đã được tác nhân trước commit tại các mốc riêng. Kế hoạch này bổ sung hướng dẫn vận hành; không sửa lịch sử Git, không áp migration vào DB vận hành.

## Trước khi áp dụng

1. Chủ dự án/DBA xác nhận đích server, database và cửa sổ bảo trì. Không đưa chuỗi kết nối hoặc bí mật vào báo cáo.
2. Sao lưu DB và media theo quy trình hiện hành; kiểm backup và restore thử vào DB riêng. Kết quả test trên DB trống không thay việc restore thử dữ liệu vận hành.
3. Trên bản restore thử, cấu hình DB/media riêng, tắt M365/email thật; dùng tài khoản QA riêng. Kiểm trạng thái chỉ đọc:

```powershell
venv\Scripts\python.exe ops\check_migration_state.py --app assistant
venv\Scripts\python.exe src\manage.py migrate assistant --plan
```

Checker exit 1 khi còn migration nguồn chưa áp dụng; đó là kết quả dự kiến trước khi triển khai, không phải quyền tự chạy migrate trên DB vận hành.

4. Đối chiếu SQL trên cấu hình SQLite và SQL Server tạm:

```powershell
venv\Scripts\python.exe src\manage.py sqlmigrate assistant 0001
venv\Scripts\python.exe src\manage.py sqlmigrate assistant 0002
```

Chỉ chấp nhận tạo bảng nhật ký, khóa ngoại/chỉ mục liên quan; dừng nếu có DROP/UPDATE/DELETE đối với bảng nghiệp vụ. Các lệnh dùng settings đang cấu hình, không tự cách ly DB.

## Áp dụng và kiểm tra

Trên bản restore thử trước, sau đó trên DB vận hành **chỉ khi chủ dự án/DBA đã duyệt đúng đích và backup/restore**:

```powershell
venv\Scripts\python.exe src\manage.py migrate assistant 0002
venv\Scripts\python.exe ops\check_migration_state.py --app assistant
```

Áp schema trước khi đưa mã có truy vấn `SearchQueryLog` vào phục vụ. Bảng mới không yêu cầu backfill công văn/hồ sơ. Dùng QA kiểm `/assistant/` và nút nổi: truy vấn được lọc quyền, ghi đúng một dòng log, CSRF/rate limit hoạt động, không gửi email. DB thành công không chứng minh SharePoint đã có consent; nguồn DB vẫn phải dùng được khi Graph chưa cấu hình.

Mọi quyết định cấp Graph consent hoặc mở rộng quyền nguồn SharePoint là bước riêng. Giữ cửa quyền hiện hành cho tới khi chủ dự án quyết định; không bỏ bộ lọc để làm UAT xanh.

## Hoàn tác

Đưa ứng dụng về mã chưa dùng app assistant trước khi gỡ schema. Chỉ DBA chạy trên đích đã xác nhận:

```powershell
venv\Scripts\python.exe src\manage.py migrate assistant zero --plan
venv\Scripts\python.exe src\manage.py migrate assistant zero
```

Hoàn tác xóa bảng và **mất nhật ký câu hỏi đã lưu**; sao lưu riêng nếu cần giữ. Không gỡ `0001` khi mã chatbot còn phục vụ vì API cần bảng này. Hoàn tác riêng `0002` về `0001` chỉ gỡ chỉ mục thời gian, vẫn giữ log. Đối chiếu `--plan` trước để phát hiện dependency mới ngoài hai migration này.

Lệnh `purge_search_logs` là thao tác dữ liệu khác: mặc định chỉ đếm; `--apply` xóa cứng. Đợt bàn giao mã không cho phép tự chạy nó trên dữ liệu vận hành.
