# Danh mục vấn đề chờ Chủ dự án quyết định (Owner Decision Backlog)

Tài liệu này ghi nhận các vấn đề kiến trúc, định tuyến, phân quyền và tệp tồn đọng được phát hiện trong quá trình rà soát và chuẩn hóa giao diện IHRMS nhưng nằm ngoài phạm vi được phép tự quyết định của các tác nhân (theo nguyên tắc bảo toàn quyền, URL name, model và không phá vỡ logic nghiệp vụ).

---

## 1. Hai tệp template không có view/route định tuyến

- **Tệp liên quan**:
  - `src/apps/portal/templates/portal/office_incoming_list.html` (Sổ công văn đến)
  - `src/apps/portal/templates/portal/office_outgoing_list.html` (Sổ công văn đi)
- **Hiện trạng**:
  - Kiểm tra `grep` trên toàn bộ hệ thống `urls.py` (portal, core, dispatch) cho thấy 2 template này **không được gọi bởi bất kỳ view hay URL route nào**.
  - Nghiệp vụ công văn hiện tại đang vận hành tập trung qua phân hệ Dispatch: `portal:dispatch_list`, `portal:dispatch_create` (dùng chung cho cả văn bản đến và đi với cờ `doc_type`).
- **Tác động**:
  - Hai template này là mã mồ côi (orphaned code). Dù đã được tinh chỉnh lưới biểu mẫu trong các đợt trước, các công cụ kiểm toán trình duyệt (UAT, Layout Audit) không thể quét qua vì không có URL.
- **Phương án xin ý kiến Chủ dự án**:
  - **Phương án A (Khuyến nghị)**: Lưu trữ (archive) hoặc xóa bỏ 2 file này khỏi `src/apps/portal/templates/portal/` để tránh phân mảnh mã nguồn và nhầm lẫn khi bảo trì.
  - **Phương án B**: Nếu có nhu cầu nghiệp vụ tách sổ công văn đến / đi thành 2 trang độc lập thay vì trang chung hiện tại, đăng ký view và route tương ứng trong `src/apps/portal/urls.py`.

---

## 2. Kiểm kê và đối chiếu quyền xem Báo cáo (`_can_view_reports`)

- **Tệp liên quan**:
  - `src/apps/reporting/views.py` (`_can_view_reports`)
  - `src/apps/portal/views/reports_planning.py` (`_can_view_reports`)
- **Hiện trạng & Khác biệt**:
  - Cả hai file đều có hàm tên `_can_view_reports(user)` nhưng có phạm vi kiểm tra vai trò khác nhau và phục vụ các nhóm báo cáo khác nhau:
    1. `apps/reporting/views.py`: Phục vụ báo cáo phân tích, Dashboard tổng quan và trích xuất dữ liệu của app `reporting`. Kiểm tra quyền xem qua role `HR_MANAGER`, `DIRECTOR`, `BOARD`, hoặc các permission cụ thể trên model.
    2. `apps/portal/views/reports_planning.py`: Phục vụ các báo cáo tác nghiệp nhân sự & kế hoạch trong portal (`report_headcount`, `report_timesheet`, `report_budget`, `report_personnel_changes`). Kiểm tra phân quyền truy cập kết hợp vai trò nhân sự, trưởng bộ phận (chỉ xem phòng ban mình) và kế toán trưởng/giám đốc.
- **Tác động**:
  - Việc duy trì 2 hàm cùng tên ở 2 phân hệ khác nhau phản ánh kiến trúc module độc lập hiện tại, bảo đảm bảo mật dữ liệu nhạy cảm (ngân sách, biến động nhân sự, tiền lương).
- **Quyết định bảo toàn**:
  - Giữ nguyên 100% logic của cả hai hàm độc lập, **không thực hiện hợp nhất** để tránh ảnh hưởng đến ma trận phân quyền `PERMISSION_MATRIX`.
- **Đề xuất tương lai cho Chủ dự án**:
  - Xem xét quy hoạch lại hệ thống phân quyền báo cáo vào một Policy/Service tập trung (`apps.security.policies.reporting_access`) trong đợt refactor kiến trúc bảo mật tiếp theo.

---

## 3. Quy chuẩn dải lọc và phân trang dùng chung

- **Tệp liên quan**:
  - `src/apps/portal/templates/portal/_pagination.html`
  - Các dải lọc `ui-query-card` trên toàn hệ thống
- **Hiện trạng**:
  - Phân trang `_pagination.html` hiện tại bảo toàn tất cả tham số query string hiện tại khi chuyển trang (như `page`, `year`, `month`, `department`, `keyword`).
  - Giao diện đang được nâng cấp đồng bộ với nhịp nút bấm, trạng thái active và aria-label hỗ trợ khả năng tiếp cận (Accessibility).
- **Ghi nhận**:
  - Không có xung đột nghiệp vụ; duy trì hợp đồng tham số GET URL trên toàn bộ các view danh sách và báo cáo.
