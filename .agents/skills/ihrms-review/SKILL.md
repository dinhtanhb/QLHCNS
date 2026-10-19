---
name: ihrms-review
description: "Rà soát, review toàn dự án hoặc thay đổi IHRMS Django/SQL Server: lỗi chức năng, dữ liệu, phân quyền, migration, giao diện và CI. Chỉ sửa khi được cho phép."
---

Đọc [AGENTS.md](../../../AGENTS.md) để áp dụng quy tắc dự án và
[hướng dẫn review IHRMS](../../../docs/Huong_Dan_Review_Du_An.md) để thực hiện
quy trình, chọn gate và lập báo cáo bằng tiếng Việt.

1. Chọn FULL khi rà toàn dự án, CHANGES khi rà thay đổi; mặc định REVIEW.
   Chỉ dùng FIX khi nhiệm vụ cho phép sửa.
2. Thực hiện checklist và lệnh trong hướng dẫn theo phạm vi đã chọn;
   FULL rà mã hiện tại kể cả khi diff rỗng.
3. Bàn giao finding có bằng chứng và phần chưa kiểm thử theo mục
   “Điều kiện kết thúc và báo cáo” của hướng dẫn.
