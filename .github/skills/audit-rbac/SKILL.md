---
name: audit-rbac
description: "Kiểm tra ma trận phân quyền 11 vai trò RBAC và lỗ hổng IDOR/CSRF cho một module hoặc chức năng trong QLHCNS."
disable-model-invocation: true
argument-hint: "[tên module hoặc đường dẫn file views.py cần kiểm tra]"
---

Đọc [AGENTS.md](../../../AGENTS.md) và
[hướng dẫn review](../../../docs/Huong_Dan_Review_Du_An.md). Chỉ đọc trừ khi
người dùng cho phép FIX; không mượn phiên/danh tính thật hoặc ghi DB vận hành.

Hãy kiểm tra toàn diện cơ chế phân quyền và bảo mật cho module hoặc file được chỉ định:

1. Đối chiếu quyền truy cập trong `views.py` và `selectors.py` với ma trận 11 vai trò tại `src/apps/security/permissions.py`.
2. Kiểm tra nguy cơ **IDOR (Insecure Direct Object Reference)**: Nhân viên (`EMPLOYEE`) hoặc Trưởng bộ phận (`DEPT_MANAGER`) có thể xem/sửa/duyệt hồ sơ, đơn nghỉ phép, phiếu lương của nhân sự thuộc phòng ban khác bằng cách thay đổi ID trên URL hay không?
3. Kiểm tra bảo vệ CSRF trên các biểu mẫu và tính hiệu lực của `SensitiveResponseMiddleware` (`src/apps/security/middleware.py`).
4. Đề xuất đoạn code khắc phục cụ thể cho từng điểm chưa an toàn.
