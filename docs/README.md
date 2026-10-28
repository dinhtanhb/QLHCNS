# Tài liệu IHRMS

Mục lục đối chiếu ngày 28/10/2026. Quy tắc làm việc tại [AGENTS.md](../AGENTS.md); lịch sử thay đổi và bằng chứng kiểm thử chỉ ghi ở [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md).

## Đọc trước

- [Baseline kiến trúc và hiện trạng](99_Architecture_Baseline.md): phân biệt thiết kế ban đầu với thành phần đang có trong mã.
- [Việc còn mở cần chủ dự án quyết định](Viec_Cho_Chu_Du_An_Quyet_Dinh.md): phần chưa xác nhận đóng; không tự suy ra quyền triển khai.
- [Hướng dẫn review](Huong_Dan_Review_Du_An.md): FULL/CHANGES và REVIEW/FIX.
- [Hệ thống giao diện hiện hành](UI_DESIGN_SYSTEM.md): ưu tiên các quyết định mới hơn khi trùng phạm vi tài liệu UI cũ.

## Đặc tả và tiêu chuẩn nền

Các tài liệu 00–16 giữ để truy vết yêu cầu và hợp đồng. Phần công nghệ hoặc chức năng dự kiến không chứng minh đã triển khai; dùng baseline hiện hành, mã/model/migration và nhật ký để đối chiếu. Không tự tạo thêm JWT, SSO, API hay tích hợp Microsoft 365 theo ví dụ thiết kế cũ.

- [00_Project_Charter](00_Project_Charter.md)
- [01_BRD_MASTER](01_BRD_MASTER.md)
- [02_Solution_Architecture](02_Solution_Architecture.md)
- [03_Database_Design](03_Database_Design.md)
- [04_Security_Design](04_Security_Design.md)
- [05_Backend_Standards](05_Backend_Standards.md)
- [06_Frontend_Standards](06_Frontend_Standards.md)
- [07_Testing_Standards](07_Testing_Standards.md)
- [08_Deployment_Standards](08_Deployment_Standards.md)
- [09_UI_UX_Specification](09_UI_UX_Specification.md)
- [10_RBAC_Permission_Matrix](10_RBAC_Permission_Matrix.md)
- [11_Workflow_Definition](11_Workflow_Definition.md)
- [12_Report_Data_Dictionary](12_Report_Data_Dictionary.md)
- [13_Master_Data_Dictionary](13_Master_Data_Dictionary.md)
- [14_Code_Generation_Guide](14_Code_Generation_Guide.md)
- [15_API_Contract_Specification](15_API_Contract_Specification.md)
- [16_Django_Module_Blueprint](16_Django_Module_Blueprint.md)

## Hướng dẫn vận hành, sử dụng và nghiệm thu

- [HUONG_DAN_SU_DUNG_IHRMS](HUONG_DAN_SU_DUNG_IHRMS.md)
- [TAP_HUAN_IHRMS](TAP_HUAN_IHRMS.md)
- [HR_Huong_Dan_Checklist_Onboarding_Offboarding](HR_Huong_Dan_Checklist_Onboarding_Offboarding.md)
- [Huong_Dan_Bieu_Mau_HCNS](Huong_Dan_Bieu_Mau_HCNS.md)
- [Huong_Dan_Kiem_Thu_Demo_IHRMS](Huong_Dan_Kiem_Thu_Demo_IHRMS.md)
- [Huong_Dan_Test_Nhanh_4_Chuc_Nang](Huong_Dan_Test_Nhanh_4_Chuc_Nang.md)
- [UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc](UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md)
- [Server_Trial_Readiness_2026-09-27](Server_Trial_Readiness_2026-09-27.md)
- [Huong_Dan_Setup_TaskScheduler_SIT_UAT](Huong_Dan_Setup_TaskScheduler_SIT_UAT.md)
- [Ke_Hoach_UAT_May_Chu_Cong_Ty_2026-10-16](Ke_Hoach_UAT_May_Chu_Cong_Ty_2026-10-16.md)
- [Checklist_Go_Live_IHRMS](Checklist_Go_Live_IHRMS.md)

Bản Word [cẩm nang sử dụng](HUONG_DAN_SU_DUNG_IHRMS.docx) và `templates/hcns/` là tài liệu/mẫu nghiệp vụ, giữ để đối chiếu biểu mẫu và bản xuất. Các số liệu kiểm thử cũ trong runbook/demo là snapshot theo ngày, không phải kết quả của HEAD hiện tại. Nghiệm thu dùng DB/media giả và tài khoản QA riêng.

## Giao diện và dữ liệu cho công cụ

- [UI_DESIGN_SYSTEM_PHASE1](UI_DESIGN_SYSTEM_PHASE1.md)
- [UI_SHARED_COMPONENTS_PHASE4](UI_SHARED_COMPONENTS_PHASE4.md)
- [DASHBOARD_ATOMS_TECH_SPEC](DASHBOARD_ATOMS_TECH_SPEC.md)
- [ADMIN_UI_DESIGN](ADMIN_UI_DESIGN.md)
- [DESIGN_SYSTEM_STATUS](DESIGN_SYSTEM_STATUS.md)

- [UI_BUTTON_KINDS.json](UI_BUTTON_KINDS.json), [UI_FORM_REGISTRY.json](UI_FORM_REGISTRY.json): registry cho kiểm tra/hợp đồng giao diện; không xóa vì không phải tài liệu hướng dẫn đọc thường xuyên.
- [Nguồn kitchen sink](ui_components_source.html) và [bản render](ui_components.html): dùng với `ops/render_ui_components.py`.
- `screenshots/stage1_samples/`: bằng chứng baseline, không mô tả giao diện mới nhất.
- `ihrms-rollout-plan.canvas.tsx`: kế hoạch trực quan; giữ nguyên nội dung trong lượt dọn này.

## Đặc tả và kế hoạch cần giữ

- [ActCode](ActCode.md)
- [NGO_Activity_Planning_MEL_Roadmap](NGO_Activity_Planning_MEL_Roadmap.md)
- [HRMS_Next_Features_TechSpec_2026-09-26](HRMS_Next_Features_TechSpec_2026-09-26.md)
- [KE_HOACH_DAI_MAU_VIETHEALTH](KE_HOACH_DAI_MAU_VIETHEALTH.md)

- [Đặc tả trợ lý tài liệu](superpowers/specs/2026-10-19-assistant-chatbot-design.md): giữ hợp đồng và phạm vi; kế hoạch triển khai từng bước đã được xóa sau đối chiếu nhật ký.
- Kế hoạch palette đã triển khai phần đổi màu; P5 tùy chọn chưa được xác nhận hoàn tất. Giai đoạn 2 bố cục phân hệ vẫn chờ duyệt theo nhật ký.

## Hồ sơ lịch sử và yêu cầu chưa đóng đủ bằng chứng

- [Đánh giá sẵn sàng 09/2026](Production_Readiness_Review_2026-09-23.md): snapshot lịch sử, không dùng làm kết luận go-live hiện tại.
- `archive/reviews/`: báo cáo review nguồn, gồm finding và phạm vi chưa kiểm; không mặc định mọi finding đã sửa.
- `archive/migration_plans/`: giữ kế hoạch áp dụng/hoàn tác và truy vết migration, dù migration đã có trong mã.
- [Kế hoạch tính năng cũ](archive/HRMS_Next_Features_Plan.md) và [baseline UI cũ](archive/DESIGN_SYSTEM_BASELINE.md): hồ sơ lịch sử; TechSpec và chuẩn UI ở trên là nơi tra cứu hiện hành.
- [Yêu cầu sửa review 08/10](archive/requests/Yeu_Cau_Codex_Sua_Review_2026-10-08.md): Nhóm A có nhật ký sửa; Nhóm B/C chưa được xác minh đóng từng mục trong lượt này nên giữ.

Tài liệu không có liên kết vào vẫn có thể là mẫu nghiệp vụ, bằng chứng hoặc kế hoạch còn mở. Chỉ xóa khi xác định được nội dung đã được thay thế/hoàn tất và không làm mất hợp đồng còn cần dùng. Lịch sử tệp đã xóa vẫn tra cứu bằng Git; danh sách và căn cứ dọn ở nhật ký.
