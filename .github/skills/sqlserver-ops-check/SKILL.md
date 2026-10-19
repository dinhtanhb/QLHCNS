---
name: sqlserver-ops-check
description: Kiểm tra sẵn sàng SQL Server và kế hoạch backup/restore IHRMS.
argument-hint: Môi trường và phạm vi kiểm tra được phép.
---

Đọc [AGENTS.md](../../../AGENTS.md) và
[hướng dẫn backup](../../../ops/backup/README.md). Quyền review/test không phải
quyền đổi schema, backup hoặc restore vào DB vận hành.

1. Xác định đúng server/DB và phạm vi được phép, không in kết nối/bí mật.
   Đọc guard trong `src/config/settings.py` và `.env.example`, không đoán cấu hình.
2. Kiểm migration chỉ đọc bằng `ops/check_migration_state.py` khi xác nhận đích.
   Công cụ này không thay backup, restore thử hoặc UAT.
3. Test qua `venv\Scripts\python.exe ops/run_tests.py --backend sqlserver`
   hoặc `--backend sqlite`; wrapper dùng DB/media tạm.
4. Rà `ops/backup/Backup-FullDatabase.ps1`, `Backup-TransactionLog.ps1`
   và `Test-BackupSafety.ps1` trước khi đề xuất; không tự chạy vào đích thật.
5. Khi được phép schema: SQL thực, backup/restore thử, áp/hoàn tác trên bản sao,
   kế hoạch và commit riêng theo AGENTS.md. Áp vận hành cần xác nhận riêng.
6. Ghi kiểm đã chạy/không chạy, backend, đích thử và giới hạn trong nhật ký duy nhất.
