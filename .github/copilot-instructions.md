# Quy tắc làm việc với IHRMS

Đọc [AGENTS.md](../AGENTS.md) trước khi sửa. Đây là nguồn quyết định về nhánh
`main`, một người ghi, dữ liệu thử cô lập, migration, kiểm thử và bàn giao.
Không suy ra quyền deploy, đổi schema vận hành hoặc mượn phiên/danh tính thật.

## Mã nguồn và dữ liệu

- Xem module tương tự trước khi thêm kiến trúc mới. Truy vấn đọc phức tạp đặt
  trong selector; nghiệp vụ ghi nhiều bản ghi đặt trong service với transaction.
- Giữ `db_column`, hợp đồng GET/POST, công thức và phạm vi quyền hiện có.
- `src/apps/security/permissions.py` là nguồn RBAC; kiểm truy cập đối tượng,
  không chỉ ẩn nút. Không ghi bí mật, PII hoặc chi tiết lương vào log.
- Test dùng `venv\Scripts\python.exe ops/run_tests.py --backend sqlite`
  hoặc `--backend sqlserver`; wrapper tạo DB/media tạm. Không chạy kiểm tra
  với cấu hình DB vận hành mặc định.

## Giao diện và tài liệu

- Đọc [DESIGN.md](../DESIGN.md). Dùng token `--ui-*` và thành phần hiện có;
  không thay bằng thang màu/khoảng cách riêng của skill tham khảo.
- Template ở `src/templates/` và `src/apps/*/templates/`; giữ nhãn, CSRF,
  autoescape, quyền hiển thị và khả năng dùng khi tắt JavaScript.
- Thay form/bảng/CSS phải chạy gate browser/layout/print/form contract theo
  AGENTS.md. PASS kỹ thuật không thay nghiệm thu ảnh thực.
- Nhật ký chỉ cập nhật tại `docs/PROJECT_WORK_LOG.md`; ghi kiểm tra đã chạy,
  phần chưa kiểm, snapshot nguồn an toàn và kết quả commit/push.
