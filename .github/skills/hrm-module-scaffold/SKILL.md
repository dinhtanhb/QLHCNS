---
name: hrm-module-scaffold
description: Tạo hoặc mở rộng phân hệ IHRMS theo cấu trúc nghiệp vụ hiện có.
argument-hint: Module và tính năng cần sửa.
---

Đọc [AGENTS.md](../../../AGENTS.md) và
[hướng dẫn chung](../../copilot-instructions.md), xem module tương tự.

1. Chốt hợp đồng đầu vào, dữ liệu, quyền và phạm vi. Chỉ thêm model khi cần;
   dùng `BaseAuditModel` khi phù hợp, giữ `db_column` và validation hiện hành.
2. Nếu đổi schema: model/migration commit riêng, SQL thực, kế hoạch áp/hoàn tác,
   backup/restore và DB thử theo AGENTS.md; không tự migrate vận hành.
3. Selector lọc theo quyền; chỉ tải trước quan hệ được truy cập. Service ghi
   nhiều bản ghi dùng transaction, giữ actor/audit; không lồng transaction
   ngoài allocator có retry/transaction riêng.
4. View/form/template giữ CSRF, GET/POST và guard đối tượng. Template có ở
   `src/templates/` và `src/apps/*/templates/`.
5. Kiểm nghiệp vụ bằng `ops/run_tests.py --backend sqlite` và `--backend sqlserver`
   trên DB/media tạm; chạy các gate UI áp dụng. Nhật ký/bàn giao theo AGENTS.md.
