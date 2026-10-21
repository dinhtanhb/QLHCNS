# Yêu cầu Codex: sửa các finding review 2026-10-08

Workspace: `D:\QLHCNS`. Chế độ **FIX**, chỉ làm trên `main`. Đọc trước: `AGENTS.md`, `docs/Huong_Dan_Review_Du_An.md`, `docs/archive/reviews/Code_Review_Report_2026-10-08.md` (nguồn của các mã F-xx bên dưới; mỗi finding có `path:line`, trigger và hướng sửa).

## Quy tắc chung

- Trước khi sửa: `git status --short`, `git branch --show-current` (phải là `main`), `git fetch origin main`, `git rev-list --left-right --count HEAD...origin/main`. Giữ nguyên thay đổi cục bộ ngoài phạm vi; không reset/stash/đổi nhánh.
- Báo cáo review được viết từ bản ZIP, **chưa chạy test**. Với mỗi finding: đọc lại mã hiện tại, **viết test tái hiện trước** (phải fail trên mã cũ), rồi mới sửa. Nếu mã hiện tại khác báo cáo hoặc finding không tái hiện được, ghi rõ và bỏ qua, không sửa theo suy đoán.
- Không đổi quy tắc nghiệp vụ ngoài phạm vi từng mục. Không thêm migration trừ khi mục yêu cầu; có migration thì chỉ chạy trên DB thử, không `migrate` DB đang dùng.
- Không đưa `.env`, DB, media, dữ liệu thật vào Git. Dùng DB/media tạm và dữ liệu giả.
- Được **commit** các tệp thuộc nhiệm vụ trên `main`. **Không push, không deploy** trong nhiệm vụ này; để chủ dự án quyết định.
- Cập nhật `docs/PROJECT_WORK_LOG.md` trong **một mục của đợt** (đã có mục review 2026-10-08, thêm mục mới cho đợt sửa; không sao chép sang nơi khác). Ghi lệnh/kết quả thật, phân biệt đã chạy với chỉ được báo cáo.

## Nhóm A — sửa ngay (không cần quyết định thêm), mỗi mục kèm test hồi quy

1. **F-02** `portal/views/documents.py:111,158`: thay `_can_approve(request)` bằng kiểm tra `manage_office` (giữ `is_staff` nếu tài liệu hiện hành đang yêu cầu; nêu rõ trong log). Test ma trận vai trò HR_MANAGER, HR_OFFICER, SYS_ADMIN, DEPT_MANAGER, DIRECTOR, EMPLOYEE × (xem danh sách, cập nhật tiến độ công văn không được giao, tạo). DEPT_MANAGER/DIRECTOR **không** còn cập nhật được công văn không giao cho mình; HR_OFFICER/SYS_ADMIN cập nhật được.
2. **F-06** `portal/views/finance.py:149-190`: trước khi tạo dòng lương, nhận diện nhân viên không có `EmployeeSalary` hiệu lực; không tạo dòng lương cơ bản 0 một cách im lặng — hiển thị danh sách thiếu lương và bỏ qua hoặc chặn theo cách hiển thị rõ cho Kế toán. Kiểm tra `finance_payroll_lock` để không khóa kỳ có dòng lương cơ bản 0 (xem `Payroll.validate_calculated`); nếu hiện chấp nhận 0, thêm chặn kèm thông báo. Test cả luồng generate và lock.
3. **F-07** `portal/views/attendance.py:87` + `leave/models.py:128`: bọc kiểm tra trùng ngày/quỹ phép + lưu trong `transaction.atomic()` với `select_for_update()` trên `Employee` (hoặc `LeaveBalance`) của người nộp. Test đồng thời theo mẫu test công văn trong `portal/tests_review_hardening.py` (SQL Server), cộng test gửi đúp tuần tự.
4. **F-10** `portal/views/hr.py:315`: xử lý `IntegrityError` trùng `employee_code` bằng thử lại có giới hạn hoặc cơ chế sinh mã an toàn; không đổi định dạng `VH0001`. Test hai lần tạo liên tiếp/đồng thời.
5. **F-11** `lifecycle/views.py:119`: `atomic()` + `select_for_update()` cho item và case; test hoàn tất hai lần/đóng case một lần.
6. **F-15** `portal/views/hr.py:369`: chỉ gia hạn hợp đồng `Active` mới nhất; thông báo rõ khi không có. Test hợp đồng đã chấm dứt.
7. **F-16** `reporting/views.py:105-107`: validate `type` theo `OfficialDispatch.DISPATCH_TYPE_CHOICES` (mặc định `Incoming`), tên tệp đúng cho `InternalDirective`. Test.

## Nhóm B — CHƯA LÀM cho đến khi chủ dự án trả lời (ghi câu hỏi vào log, không tự quyết)

Chủ dự án điền quyết định vào đây trước khi giao Codex (hoặc nhắn trong chat):

- **F-01**: Nhân viên `Probation` có tính lương/phiếu lương không? `OnLeave` xử lý thế nào? → Quyết định: `____________`. Sau khi có: tạo hằng dùng chung (ví dụ `EMPLOYED_STATUSES`), sửa `finance.py:120-125` và các danh sách Active-only đã liệt kê trong báo cáo (tài sản, thông báo, dashboard, người phỏng vấn…) theo từng nơi có chủ đích, kèm test cho kỳ lương có nhân viên thử việc.
- **F-03**: Ai được xem công văn đến? (đề xuất mặc định: HR_MANAGER, HR_OFFICER, SYS_ADMIN, DIRECTOR, và người được giao/cùng phòng) → `____________`. Sau đó sửa `security/data_access.py:48`, cập nhật `docs/10_RBAC_Permission_Matrix.md` và chú thích `permissions.py`.
- **F-04**: Cấm tự duyệt đề nghị của chính mình cho mua sắm/VPP/đặt phòng/đặt xe? Nghỉ phép của HR_MANAGER/DIRECTOR giữ như hiện tại? → `____________`.
- **F-05**: Bản xuất Excel nhân sự: bỏ/che CCCD, hay chỉ HR mới xuất đủ? `national_id` hiện có được mã hóa khi lưu không? → `____________`.
- **F-08/F-09**: Thống nhất một quyền báo cáo; thêm menu cho mua sắm, các trang duyệt phòng/xe/VPP, Trung tâm Báo cáo, Giao việc theo quyền → chỉ làm sau F-03.

## Nhóm C — ghi nhận, làm khi rảnh (không bắt buộc đợt này)

F-12 (kiểm tra magic bytes upload), F-13 (hiệu năng `private_file`), F-14 (`CompanyMedia` không có trạng thái xuất bản), F-17 (kiểm tra nhân viên còn làm việc khi nghỉ phép, hủy đơn).

## Kiểm tra bắt buộc sau sửa

Chạy trong PowerShell tại `D:\QLHCNS`; ghi exit code thật:

```powershell
git diff --check
venv\Scripts\python.exe -m pip check
# với DB_ENGINE=sqlite3 và SECRET_KEY tạm (xem hướng dẫn review):
venv\Scripts\python.exe src\manage.py check
venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run
venv\Scripts\python.exe ops\run_tests.py --backend sqlite
venv\Scripts\python.exe ops\run_tests.py --backend sqlserver
```

Nếu SQL Server không chạy được, ghi rõ lý do và hướng dẫn chủ dự án chạy lệnh tương ứng; không báo đạt khi chưa chạy. Không dùng số test cũ làm kết quả.

## Báo cáo cuối

Liệt kê: tệp đã đổi; từng mã F-xx đã sửa/không tái hiện/bỏ qua và vì sao; test mới; lệnh + kết quả; SHA commit; phần chưa kiểm tra; việc chủ dự án cần làm (bao gồm quyết định Nhóm B và push). Không tuyên bố đã review 100% hoặc đã chạy Bugbot/Sixth khi chưa có bằng chứng.
