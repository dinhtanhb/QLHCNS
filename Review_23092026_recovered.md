> **CẬP NHẬT 23/09/2026:** Tài liệu dưới đây là snapshot đánh giá ban đầu ngày 23/09/2026, không phải trạng thái hiện hành. Các mục I1, I4, I5, I10, I11 đã được xử lý sau snapshot; tính năng khóa kỳ và phát hành phiếu lương PDF cũng đã được triển khai. Dùng báo cáo mới tại [docs/Production_Readiness_Review_2026-09-23.md](docs/Production_Readiness_Review_2026-09-23.md) để ra quyết định hiện tại. Nội dung cũ được giữ lại để lưu lịch sử phát hiện.

---
Đã kiểm tra lại toàn bộ 16 mục Important (I1–I16) + 4 mục Critical (C1–C4) + 4 mục Performance (P1–P4) trong báo cáo, so với code thực tế (không chỉ dựa vào comment). Kết quả:
Đã sửa xong (xác nhận bằng code, không chỉ bằng comment)
Mục	Trạng thái
C1 (trộn bậc thuế)	✅ đã tự đóng effective_to thế hệ cũ, calculate() lấy đúng 1 thế hệ
C2 (admin bypass khóa kỳ)	✅ payroll/admin.py đã chặn sửa/xóa/tính lại khi Locked
C3 (tự duyệt thanh lý)	✅ tách quyền _can_approve_disposal riêng, không dùng _can_manage_asset nữa
C4 (0 test)	✅ 69 test bạn vừa chạy — đúng 3 chỗ dễ vỡ nhất: leave (30), payroll (21), security (18)
I2 (tự duyệt nghỉ phép)	✅ có guard chặn
I3 (tự khai BCC/nghỉ bù)	✅ giờ phải qua duyệt (status="Approved") mới tính
I7 (lương bỏ qua effective_date)	✅ finance_payroll_generate đã lọc đúng theo effective_date/end_date so với kỳ
I9 (dependent trùng)	✅ _validate_no_overlap() đã thêm
I12 (race duyệt nghỉ phép)	✅ select_for_update()
I13/I14	✅ (vừa sửa cùng bạn)
I15 (SECRET_KEY fallback)	✅ giờ raise lỗi nếu thiếu, không còn fallback công khai
I16 (dependency thừa)	✅ requirements.txt đã dọn, chỉ còn 4 gói thật dùng
I6 (proration lương)	🟡 một nửa — Payroll.calculate() đã tính theo join_date/leave_date, nhưng finance_payroll_generate vẫn chỉ lấy employment_status="Active" nên người nghỉ việc giữa tháng vẫn bị thiếu hẳn dòng lương (không ai tạo row cho họ để mà tính)
Trả lời thẳng câu hỏi: Dashboard có cần sửa không → Có, 1 chỗ thật (I8)
dashboard.html hiển thị latest_payroll.net_income và payslip_list.html hiển thị gross_income/net_income không lọc theo payroll_period.status. Tức là ngay khi Kế toán bấm "Tính lương" (kỳ còn Draft, số có thể còn sai/đang sửa), nhân viên đã thấy ngay lương net trên Dashboard của họ như thể là số cuối cùng — tới khi Kế toán chỉnh lại thì số trên Dashboard cũng đổi theo, gây hoang mang. Đây đúng là lỗi báo cáo I8 đã nêu, và nó nằm ngay ở Dashboard + trang xem lương, không phải chỗ nào khác.
Ngoài ra Payslip model vẫn là model chết — khai báo sẵn nhưng không có view nào Payslip.objects.create(...).
Còn lại chưa đụng tới
Important còn mở:
•	I1 — EmployeeTransfer/EmployeePromotion.save() vẫn đổi department/position ngay lập tức, bỏ qua effective_date (nhập điều chuyển hiệu lực tương lai → áp dụng luôn hôm nay).
•	I4 — Đơn nghỉ vắt qua tháng/năm (_leave_days_in_month, LeaveBalance._days_by_status) vẫn lọc theo from_date__year/month — nghỉ 28/12→03/01 tính hết vào quỹ năm cũ.
•	I5 — AssetAllocation vẫn chưa chặn cấp trùng 1 tài sản cho 2 người cùng lúc.
•	I6 (phần còn lại) — như trên.
•	I8 — như trên (Dashboard + payslip_list + model Payslip chết).
•	I10 — is_deleted vẫn không được exclude() ở bất kỳ queryset nào trong toàn bộ code (0 chỗ dùng) — xóa mềm không có tác dụng gì.
•	I11 — inventory_session_complete vẫn set Completed vô điều kiện, không kiểm tra còn dòng chưa đếm.
Performance chưa đụng: P1 (Payroll.calculate() vẫn 4 query/người), P2 (document_approve vẫn notify từng người 1 query thay vì bulk_create), P3, P4 — không cấp thiết bằng phần logic ở trên.
Minor: khóa kỳ lương 1 chiều (không unlock), allowance âm không bị chặn, hr_employee_create gọi sinh mã 2 lần — nhỏ, để sau cũng được.
________________________________________
Bạn muốn tôi làm theo thứ tự nào? Gợi ý của tôi:
1.	I8 trước — vì đụng đúng Dashboard bạn hỏi, sửa nhanh (thêm filter payroll_period__status="Locked" ở 2 view), rủi ro thấp.
2.	Rồi I1, I5, I11 — đều là kiểu "thiếu 1 điều kiện kiểm tra", sửa độc lập, không đụng chéo nhau.
3.	I4 để sau — sửa đúng cần đổi công thức tính ngày theo tháng, ảnh hưởng cả leave app lẫn payroll, nên làm riêng kèm test bổ sung.
4.	I10 cần quyết định trước: thi hành is_deleted thật (sửa nhiều queryset) hay bỏ hẳn field — cái này tôi cần bạn chốt hướng trước khi code.

> **CẬP NHẬT 23/09/2026:** Tài liệu dưới đây là snapshot đánh giá ban đầu ngày 23/09/2026, không phải trạng thái hiện hành. Các mục I1, I4, I5, I10, I11 đã được xử lý sau snapshot; tính năng khóa kỳ và phát hành phiếu lương PDF cũng đã được triển khai. Dùng báo cáo mới tại [docs/Production_Readiness_Review_2026-09-23.md](docs/Production_Readiness_Review_2026-09-23.md) để ra quyết định hiện tại. Nội dung cũ được giữ lại để lưu lịch sử phát hiện.

---


