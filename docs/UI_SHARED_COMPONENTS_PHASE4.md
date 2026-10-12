# Thành phần dùng chung IHRMS — Giai đoạn 4

Áp dụng opt-in cho bốn trang mẫu: Chạy lương hàng tháng, Báo cáo điều hành, danh sách nhân viên và chi tiết nhân viên. Các trang khác chưa chuyển layout; nhánh phân trang cũ vẫn giữ nguyên khi không truyền `standard=True`. Không tạo URL production cho kitchen sink, không đổi view/model/guard. Kết quả kiểm tra và việc còn mở chỉ ghi ở [nhật ký dự án](PROJECT_WORK_LOG.md).

## Tài liệu và nguồn

- `src/static/css/shared_components.css`: component `.ui-page`, `.ui-card`, `.ui-table`, `.ui-scroll`, `.ui-filter-bar`, `.ui-field`, `.ui-badge`, `.ui-pagination`, `.ui-detail-grid`, `.ui-kpi`, `.ui-dialog`. Không rải selector để đổi tất cả trang.
- `src/static/js/shared_components.js`: form opt-in `data-ui-form` và confirm opt-in `data-ui-confirm`.
- `src/templates/ui/`: partial page_header/field/error_summary/badge/kpi/detail_item/alert/empty_state/confirm_dialog.
- `src/apps/common/templatetags/ui_components.py`: `ui_badge`, `ui_date`, `ui_vnd`, `ui_bound_field`; helper hiển thị, không có query.
- `src/apps/common/ui_status.py`: registry trạng thái duy nhất. Màu và icon không thay cho nhãn.
- [Kitchen sink HTML tĩnh](ui_components.html), nguồn [template](ui_components_source.html); tái sinh bằng `venv\Scripts\python.exe ops\render_ui_components.py`. Generator cấu hình Django render-only, không dùng DB hay đọc `.env`. Mở file trực tiếp, đổi theme bằng nút; nội dung/submit chỉ mô phỏng, không nối nghiệp vụ.

## Cách gọi

```django
{% load ui_components %}
<div class="ui-page">
{% include "ui/page_header.html" with title="Tiêu đề trang" description="Mô tả ngắn" %}
<section class="ui-card">
<h2 class="ui-card-title">Tiêu đề card</h2>
{% ui_badge "payroll.payrollperiod:status" period.status %}
{{ period.start_date|ui_date }}
{{ salary.current_basic_salary|ui_vnd }}
</section>
</div>
```

Heading 24px/700, card title18px/600, card padding24px và gap24px lấy từ token. Action group trong `page_header` dùng `actions_template` với các guard gốc trong partial của trang; không truyền quyền giả.

Bảng: bọc `ui-scroll` có `role=region`, `tabindex=0`, `aria-label`; dùng `ui-table`, caption, scope col/row, colgroup `ui-col-small/medium/large`. Ô padding12×16, row min44, header14/600 sticky; control trong bảng có scroll margin để focus không bị header che. Số/tiền dùng `ui-number`, thao tác `ui-actions`. Không tự thêm aria-sort: backend chưa có sorting. Width và max-height là token component.

Filter: `method=get`, `ui-filter-bar`, field label hiển thị, nút submit và link xóa chỉ về URL hiện có; số kết quả lấy `page_obj.paginator.count`. Không sửa tên query. Phân trang gọi `{% include "portal/_pagination.html" with standard=True %}` và giữ `pagination_query` đã urlencode của view; nút trước/sau44px, aria-current page.

```django
<form method="post" data-ui-form>
{% csrf_token %}
{% include "ui/error_summary.html" with form=form %}
<fieldset class="ui-form-fieldset"><legend>Thông tin cần nhập</legend>
{% for field in form %}{% include "ui/field.html" with field=field %}{% endfor %}
</fieldset>
<button type="submit" class="ui-button ui-button--primary">Lưu</button>
</form>
```

BoundField giữ widget/value/validation gốc, thêm describedby help/error và aria-invalid khi có lỗi. Manual input gọi `ui/field.html` với id/name/label/type/value/required/min/max/step/maxlength; select truyền `options_template`. ID phải duy nhất, kể cả trong vòng lặp. Client validation không thay backend: giữ giá trị đã nhập, tạo lỗi cạnh field và summary liên kết có focus. Number proxy gửi canonical value; summary trỏ vào proxy hiển thị. Nếu view hiện tại redirect khi lỗi nghiệp vụ, giữ message/redirect đó; chưa biến view thành bound form, nên không giả định có field errors server hoặc tự lưu dữ liệu nhạy cảm ở localStorage.

```django
<form method="post" action="{% url 'existing_url_name' object.pk %}"
      data-ui-confirm="Mô tả hậu quả cần xác nhận"
      data-ui-confirm-title="Xác nhận thao tác"
      data-ui-confirm-label="Xóa bản ghi">
{% csrf_token %}
<button type="submit" name="action" value="delete">Xóa bản ghi</button>
</form>
{% include "ui/confirm_dialog.html" %}
```

Mặc định button xác nhận danger cho hủy/xóa; hành động duyệt thông thường truyền `data-ui-confirm-tone="primary"` để dùng brand thay vì màu nguy hiểm. Chỉ một dialog trong trang; native dialog + trap Tab/Shift+Tab, focus ban đầu ở Quay lại, Escape/hủy trả focus và không POST. Confirm gọi requestSubmit với submitter gốc, giữ action/method/CSRF/name/value. Không nhân bản field, không đổi quyền. Mẫu thực trong HR detail xác nhận ghi nhận kỷ luật; xác nhận hủy/xóa/duyệt ở các phân hệ khác dùng component này khi rollout Giai đoạn5 theo guard gốc. Trình duyệt thiếu showModal giữ POST baseline; kiểm thử hiện tại dùng Edge có native dialog.

Alert/toast dùng `ui/alert.html`: thông báo thường role=status, lỗi/cảnh báo role=alert, text+SVG, không auto-dismiss lỗi hay thông báo có hành động. Shell đã có ui-alert; chưa thêm timer hoặc notification payload. Empty/error/loading dùng `ui/empty_state.html`; action chỉ truyền khi người dùng có quyền và có đích thật. Loading là feedback tĩnh, không animation vô hạn; không dựng fetch/data source mới.

Date helper dùng dd/MM/yyyy và chuyển datetime aware sang timezone cấu hình; input/date query vẫn ISO. VND dùng floatformat0g dưới locale vi, giữ cùng rounding hiển thị như floatformat hiện có, không sửa giá trị lưu hay phép tính.

## Registry trạng thái hiện có

Tone neutral/info/success/warning/danger đi kèm icon và nhãn. Approved/Issued/Completed/... success; trạng thái đang xử lý info; chờ/bổ sung warning; lỗi/quá hạn/hư hỏng danger. Draft/Open/Locked/Active/Rejected/Cancelled/Resigned/... giữ neutral khi không có ý nghĩa cảnh báo rõ, không tự gán mức nguy hiểm. Code mới chưa có registry trả badge neutral với nhãn fallback và phải được ghi nhận để chủ dự án quyết. Dưới đây là32 nhóm/118 code hiện có; nhãn giữ đúng choices của model.

- `hrm.employee:employment_status`: `Active` → Đang làm việc (neutral/info); `Probation` → Thử việc (info/info); `OnLeave` → Đang nghỉ dài hạn (info/info); `Resigned` → Đã nghỉ việc (neutral/info).
- `hrm.employeeprofilechangerequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `NeedsMoreInfo` → Yêu cầu bổ sung (warning/warning).
- `attendance.attendance:status`: `Present` → Đủ công (success/success); `Late` → Đi muộn (warning/warning); `Absent` → Vắng (neutral/info); `HalfDay` → Nửa ngày (neutral/info).
- `attendance.monthlyattendancesummary:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success).
- `leave.leaverequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Cancelled` → Đã hủy (neutral/info).
- `contract.contract:status`: `Draft` → Nháp (neutral/info); `Active` → Đang hiệu lực (neutral/info); `Expired` → Hết hạn (neutral/info); `Terminated` → Chấm dứt trước hạn (neutral/info).
- `payroll.employeesalary:status`: `Active` → Đang áp dụng (neutral/info); `Ended` → Đã kết thúc (neutral/info).
- `payroll.payrollperiod:status`: `Open` → Đang mở (neutral/info); `Locked` → Đã khóa (neutral/info).
- `task.task:status`: `Todo` → Chưa bắt đầu (neutral/info); `InProgress` → Đang thực hiện (info/info); `Done` → Hoàn thành (success/success); `Cancelled` → Đã hủy (neutral/info).
- `document.document:status`: `Draft` → Nháp (neutral/info); `PendingApproval` → Chờ phê duyệt (warning/warning); `Approved` → Đã ban hành (success/success); `Rejected` → Từ chối (neutral/info).
- `document.personneldecision:status`: `Draft` → Bản nháp (neutral/info); `PendingApproval` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Issued` → Đã ban hành (success/success); `Cancelled` → Đã hủy (neutral/info).
- `document.officialdispatch:status`: `Pending` → Chờ phân công / xử lý (warning/warning); `Processing` → Đang xử lý (info/info); `Completed` → Đã hoàn thành (success/success); `Archived` → Đã lưu trữ (neutral/info); `Overdue` → Quá hạn (danger/danger).
- `asset.asset:condition`: `Normal` → Bình thường (success/success); `Damaged` → Hư hỏng (danger/danger); `Lost` → Mất/Thất lạc (danger/danger).
- `asset.asset:status`: `Available` → Sẵn sàng cấp phát (neutral/info); `InUse` → Đang sử dụng (neutral/info); `Maintenance` → Đang bảo trì (warning/warning); `Disposed` → Đã thanh lý (neutral/info).
- `asset.inventorysession:status`: `Draft` → Đang kiểm kê (neutral/info); `Completed` → Đã hoàn tất (success/success).
- `asset.assetdisposalrequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Completed` → Đã hoàn tất (success/success).
- `recruitment.recruitmentrequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Closed` → Đã hoàn tất tuyển dụng (neutral/info).
- `recruitment.jobposting:status`: `Open` → Đang tuyển (neutral/info); `Closed` → Đã đóng (neutral/info).
- `recruitment.candidate:status`: `New` → Mới ứng tuyển (neutral/info); `Screening` → Đang sàng lọc (info/info); `Interviewing` → Đang phỏng vấn (info/info); `Offered` → Đã gửi offer (info/info); `Hired` → Đã tuyển (success/success); `Rejected` → Không phù hợp (neutral/info).
- `recruitment.offer:status`: `Sent` → Đã gửi (info/info); `Accepted` → Đã chấp nhận (success/success); `Declined` → Đã từ chối (neutral/info).
- `procurement.procurementrequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Purchased` → Đã mua (success/success).
- `notification.notificationemailoutbox:status`: `Draft` → Nháp — chưa gửi (neutral/info); `Pending` → Đang chờ gửi (warning/warning); `Sent` → Đã gửi (info/info); `Failed` → Gửi lỗi (danger/danger).
- `office.incomingdocument:status`: `New` → Mới nhận (neutral/info); `Processing` → Đang xử lý (info/info); `Done` → Đã xử lý xong (success/success).
- `office.roombooking:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Rejected` → Từ chối (neutral/info); `Cancelled` → Đã hủy (neutral/info).
- `office.vehiclebooking:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã đặt (success/success); `Rejected` → Từ chối (neutral/info); `Cancelled` → Đã hủy (neutral/info).
- `office.supplyrequest:status`: `Pending` → Chờ duyệt (warning/warning); `Approved` → Đã duyệt (success/success); `Issued` → Đã cấp phát (success/success); `Rejected` → Từ chối (neutral/info).
- `planning.trainingcourse:status`: `Planned` → Kế hoạch (neutral/info); `Ongoing` → Đang diễn ra (info/info); `Completed` → Đã hoàn thành (success/success); `Cancelled` → Đã hủy (neutral/info).
- `planning.trainingenrollment:status`: `Registered` → Đã đăng ký (info/info); `Completed` → Đã hoàn thành (success/success); `Cancelled` → Đã hủy (neutral/info).
- `activity.activity:status`: `Planned` → Đã lên kế hoạch (neutral/info); `DispatchIssued` → Đã có Công văn (info/info); `InProgress` → Đang triển khai (info/info); `Completed` → Đã hoàn thành (success/success); `Cancelled` → Đã hủy (neutral/info).
- `activity.activityproposal:status`: `Draft` → Bản nháp (neutral/info); `Submitted` → Đã gửi xin phê duyệt (warning/warning); `Approved` → Đã phê duyệt (success/success); `ChangesRequested` → Yêu cầu chỉnh sửa (warning/warning).
- `lifecycle.employeelifecyclecase:status`: `Open` → Đang xử lý (neutral/info); `Completed` → Hoàn tất (success/success); `Cancelled` → Đã hủy (neutral/info).
- `lifecycle.lifecyclechecklistitem:status`: `Pending` → Chưa làm (warning/warning); `Done` → Hoàn tất (success/success); `Skipped` → Bỏ qua (neutral/info).
