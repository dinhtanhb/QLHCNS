# Việc còn mở cần chủ dự án quyết định

Đối chiếu tài liệu và mã ngày 28/10/2026. Kết quả công việc chỉ ghi tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md); tài liệu này giữ câu hỏi còn mở và ràng buộc, không thay thế nhật ký hoặc cấp quyền sửa mã.

## 1. Hai template công văn chưa có tuyến sử dụng

`src/apps/portal/templates/portal/office_incoming_list.html` và `office_outgoing_list.html` vẫn tồn tại. Không tìm thấy tên hai template trong các view; nghiệp vụ hiện dùng `dispatch_list.html` và tuyến `portal:dispatch_list`.

Cần chọn giữ để thiết kế trang riêng hay xóa mã mồ côi trong một đợt sửa mã có kiểm thử. Lượt dọn `docs` không thay template hoặc route.

## 2. Phân quyền hai nhóm báo cáo

Mã hiện tại dùng hai quyền khác nhau:

- `src/apps/reporting/views.py`: `_can_view_reports(request)` gọi `has_permission(request.user, "view_report_center")`.
- `src/apps/portal/views/reports_planning.py`: `_can_view_reports(request)` gọi `has_permission(request.user, "view_reports")`.

Giữ hợp đồng hai quyền hiện tại; chỉ xem xét hợp nhất policy khi có yêu cầu riêng và ma trận kiểm quyền tương ứng. Chuẩn quyền ở [10_RBAC_Permission_Matrix.md](10_RBAC_Permission_Matrix.md).

## 3. Phần giao diện và palette chưa xác nhận hoàn tất

- Giai đoạn 1 token/component/Dashboard đã có kết quả trong nhật ký ngày 27/10; các bố cục phân hệ giai đoạn 2 vẫn chờ duyệt. Dọn tài liệu không thay cho phê duyệt giai đoạn 2.
- [Kế hoạch palette VietHealth](KE_HOACH_DAI_MAU_VIETHEALTH.md) đã được triển khai ở phần palette; P5 là tùy chọn riêng, chưa được xác nhận hoàn tất. Không tự đổi logo/topbar hoặc icon PWA.

## 4. Yêu cầu review cũ cần đối chiếu trước khi đóng toàn bộ

[Yêu cầu review 08/10](archive/requests/Yeu_Cau_Codex_Sua_Review_2026-10-08.md) có Nhóm B (quyết định nghiệp vụ/quyền) và Nhóm C. Nhật ký xác nhận đã sửa Nhóm A; lượt dọn tài liệu này chưa xác minh riêng từng mục B/C là đã đóng, nên giữ yêu cầu và [báo cáo nguồn](archive/reviews/Code_Review_Report_2026-10-08.md). Không coi checkbox hoặc chỉ dẫn cũ là yêu cầu chạy lại trên mã hiện tại; phải đối chiếu quyết định mới hơn, mã và test trước.

## 5. SIT/UAT và phát hành

Vẫn cần bằng chứng trên đúng máy chủ đích về cấu hình, backup/restore và UAT bằng tài khoản QA riêng. Dùng [runbook SIT](Server_Trial_Readiness_2026-09-27.md), [kế hoạch UAT máy chủ](Ke_Hoach_UAT_May_Chu_Cong_Ty_2026-10-16.md) và [checklist go-live](Checklist_Go_Live_IHRMS.md). Kết quả local/CI không thay thế nghiệm thu máy chủ.
