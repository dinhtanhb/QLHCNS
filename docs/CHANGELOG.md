# 00A_Addendum_Changelog.md

# CHANGELOG — CÁC PHẦN BỔ SUNG CHO BỘ TÀI LIỆU IHRMS

## Ngày rà soát

18/09/2026

## Phạm vi

Bổ sung 5 khoảng trống kỹ thuật được phát hiện khi review bộ 18 tài liệu gốc, nhằm hoàn thiện bộ chuẩn trước khi bắt đầu code.

---

## Danh sách file bổ sung

| # | File | Bổ sung cho | Nội dung chính |
|---|---|---|---|
| 1 | `03A_Database_Design_Addendum_Physical_Schema.md` | 03_Database_Design.md | Kiểu dữ liệu SQL Server cho toàn bộ 72 bảng, chốt chiến lược PK (BIGINT IDENTITY), field nhạy cảm cần mã hóa, index bổ sung, cảnh báo thiết kế `tblTask` (giao nhiều người) |
| 2 | `05A_Backend_Standards_Addendum_DbTable_Mapping.md` | 05_Backend_Standards.md, 14_Code_Generation_Guide.md, 16_Django_Module_Blueprint.md | Quy tắc bắt buộc khai báo `Meta.db_table`/`db_column` để khớp DB Design, `BaseAuditModel` dùng chung, ví dụ Model `Employee` đầy đủ |
| 3 | `06A_Payroll_Statutory_Rate_Master_Data.md` | 01_BRD_MASTER.md (FR-PAY-007→010), 03_Database_Design.md | Thiết kế bảng cấu hình tỷ lệ BHXH/BHYT/BHTN và biểu thuế TNCN dạng master data có hiệu lực theo thời gian (không hardcode), kèm số liệu tham khảo hiện hành 2026 |
| 4 | `10A_Role_Naming_Mapping_Addendum.md` | 00_Project_Charter.md, 10_RBAC_Permission_Matrix.md | Đối chiếu và chuẩn hóa tên gọi vai trò bị trôi giữa Charter ("IT Administrator"/"System Administrator") và RBAC Matrix ("Super Admin"/"System Admin") |
| 5 | `13_Master_Data_Dictionary.md` (bản đã sửa) | Thay thế file gốc | Sửa lỗi escape Markdown (165 dòng bị `\#`, `\-` sai định dạng) và chuẩn hóa khoảng trắng thừa |

---

## Việc cần làm tiếp theo (không nằm trong phạm vi bổ sung lần này)

- [ ] Hoàn thiện đặc tả trường cho `09_UI_UX_Specification.md` khớp với field mới thêm (`tblEmployeeDependent`, các bảng cấu hình thuế/bảo hiểm)
- [ ] Bổ sung API endpoint cho 4 bảng master data mới vào `15_API_Contract_Specification.md`
- [ ] Rà lại toàn bộ `12_Report_Data_Dictionary.md` và `09_UI_UX_Specification.md` xem có chỗ nào khác dùng tên vai trò cũ (IT Administrator/System Administrator) cần đồng bộ theo `10A`
- [ ] Kế toán xác nhận số liệu tỷ lệ bảo hiểm/thuế ở `06A` trước khi coi là "Approved"

## Cách áp dụng

1. Đọc và xác nhận từng file theo đúng "Trạng thái phê duyệt" ghi ở cuối mỗi file (cần đúng người: HR Manager, Finance Officer, IT, Tech Lead tùy file).
2. Sau khi xác nhận, gộp nội dung vào file gốc tương ứng (ví dụ: nội dung `03A` gộp vào `03_Database_Design.md`, nâng version 1.1 → 1.2) và đánh dấu `LOCKED`.
3. Thay file `13_Master_Data_Dictionary.md` cũ bằng bản đã sửa trong gói này.
4. Cập nhật `99_Architecture_Baseline.md` để phản ánh các quyết định mới (ADR-DB-001 về PK Strategy, quy tắc db_table mapping) — vì đây là văn bản có độ ưu tiên cao nhất khi có mâu thuẫn.
