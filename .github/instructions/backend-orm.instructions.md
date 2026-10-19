---
name: Django backend and database contracts
description: Quy tắc cho model, selector, service và kiểm thử Django.
applyTo: 'src/apps/**/*.py'
---

Đọc [AGENTS.md](../../AGENTS.md) và module tương tự trước khi sửa.

- Model nghiệp vụ dùng `BaseAuditModel` khi phù hợp với module hiện hành.
  Giữ ánh xạ SQL Server và ràng buộc; validation liên trường thuộc model/form/service.
- Selector chỉ đọc, lọc queryset theo quyền; dùng `select_related`/`prefetch_related`
  cho quan hệ thực sự được truy cập, không tải trước quan hệ không dùng.
- Service ghi nhiều bản ghi cần transaction và kiểm nghiệp vụ; giữ cách ghi
  actor/audit của module. Không bọc transaction ngoài hàm cấp mã vốn sở hữu
  transaction/retry riêng.
- Kiểm luồng hợp lệ, dữ liệu sai, quyền/phạm vi đối tượng và số truy vấn khi liên quan.
  Dùng `ops/run_tests.py --backend sqlite` và `--backend sqlserver` bằng Python
  của venv, trên DB/media tạm do wrapper quản lý.
- Khi đổi schema: model/migration đi commit riêng; SQL thực, backup/restore và
  hoàn tác theo AGENTS.md. Quyền sửa code không cho phép migrate vận hành.
