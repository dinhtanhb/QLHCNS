---
name: optimize-mssql
description: "Rà soát và tối ưu truy vấn Django ORM (chống N+1 query, tối ưu index) và kiểm tra tương thích MS SQL Server."
disable-model-invocation: true
argument-hint: "[tên app hoặc file selectors.py / services.py]"
---

Đọc [AGENTS.md](../../../AGENTS.md). Giữ quyền/phạm vi và kết quả truy vấn;
đo trước/sau trên dữ liệu giả. Chỉ đề xuất index khi chưa được phép đổi schema;
nếu được phép thì commit migration riêng và kiểm DB tạm theo AGENTS.md.

Hãy rà soát các truy vấn ORM trong module hoặc file được chỉ định để tối ưu hiệu năng trên **Microsoft SQL Server**:

1. Phát hiện toàn bộ các vị trí gây **N+1 Query** trong vòng lặp Python hoặc Django Template và bổ sung `select_related` / `prefetch_related`.
2. Kiểm tra các truy vấn danh sách lớn xem đã có phân trang (`Paginator`) hoặc giới hạn cột (`values_list`, `only`) chưa.
3. Đề xuất bổ sung `db_index=True` hoặc `Meta.indexes` cho các trường thường xuyên dùng trong mệnh đề `filter()`, `order_by()` (như `EmployeeCode`, trạng thái đơn, ngày chấm công).
4. Đảm bảo không có hàm ORM nào gây lỗi tương thích với driver `mssql-django` và `pyodbc`.
