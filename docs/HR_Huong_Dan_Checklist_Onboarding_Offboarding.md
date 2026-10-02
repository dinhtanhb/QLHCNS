# Hướng dẫn HR: Cấu hình checklist Tiếp nhận & Nghỉ việc trong IHRMS

Tài liệu này dành cho HR_OFFICER/HR_MANAGER, thao tác 1 lần để "bật" tính năng checklist
onboarding/offboarding đã code xong nhưng **chưa có dữ liệu mẫu**. Không cần biết kỹ thuật —
chỉ cần nhập đúng theo hướng dẫn dưới.

Có 2 khu vực khác nhau, đừng nhầm:
- **Django Admin** (`/admin/`) — nơi HR **tạo/sửa mẫu** checklist (làm 1 lần, ít khi sửa lại).
- **Cổng IHRMS** (`/portal/lifecycle/`) — nơi HR **mở hồ sơ** cho từng nhân viên cụ thể (làm mỗi
  khi có người vào/nghỉ việc), dùng đúng mẫu đã tạo ở Admin.

---

## Phần 1 — Tạo mẫu checklist trong Django Admin (làm 1 lần)

### Bước 1: Vào Admin
Đăng nhập `/admin/` bằng tài khoản có quyền quản trị → mục **Lifecycle** → **Checklist
templates** → **Add checklist template**.

### Bước 2: Điền thông tin mẫu (phần trên cùng của form)

| Trường trên form | Ý nghĩa | Ví dụ điền |
|---|---|---|
| Template code | Mã ngắn, duy nhất, không dấu | `ONBOARD-STD` |
| Template name | Tên hiển thị | `Checklist tiếp nhận nhân viên mới` |
| Template type | Chọn **Onboarding** hoặc **Offboarding** | Onboarding |
| Is active | Tick chọn để mẫu này hiện ra khi mở hồ sơ | ✅ |

Cần **ít nhất 2 mẫu**: 1 cái `template_type = Onboarding`, 1 cái `template_type = Offboarding`.
Có thể tạo nhiều mẫu cùng loại (ví dụ mẫu riêng cho khối văn phòng vs khối kho) — khi mở hồ sơ
HR sẽ chọn đúng mẫu.

### Bước 3: Thêm từng đầu việc (bảng "Checklist template items" ngay dưới form)

Admin hiện sẵn bảng con để thêm nhiều dòng cùng lúc, không cần lưu form chính trước. Mỗi dòng
là 1 đầu việc:

| Cột | Ý nghĩa | Lưu ý khi điền |
|---|---|---|
| Sequence | Thứ tự hiển thị (1, 2, 3...) | Không được trùng số trong cùng 1 mẫu (hệ thống sẽ báo lỗi nếu trùng) |
| Item name | Tên đầu việc, nhân viên/quản lý sẽ thấy đúng câu này | Viết rõ hành động: "Cấp tài khoản email công ty" |
| Responsible role code | **Chỉ là nhãn hiển thị**, gợi ý ai phụ trách — hệ thống không tự giao việc theo đây, HR vẫn phải vào từng hồ sơ để giao cho 1 người cụ thể (Bước 2 ở Phần 2) | Dùng đúng 1 trong các mã đang có trong hệ thống cho dễ nhận biết: `HR_OFFICER`, `HR_MANAGER`, `DEPT_MANAGER`, `SYS_ADMIN`, `FINANCE_OFFICER` |
| Due offset days | Hạn hoàn thành, tính theo **số ngày lệch so với ngày hiệu lực** (ngày vào làm với Onboarding, ngày nghỉ việc với Offboarding). Số âm = phải làm TRƯỚC ngày hiệu lực | `-3` = phải xong trước 3 ngày; `0` = đúng ngày hiệu lực; `2` = trong vòng 2 ngày sau |
| Requires asset return | Tick nếu đầu việc này gắn với thu hồi/bàn giao tài sản (máy tính, thẻ ra vào...) | ✅ cho các mục liên quan tài sản |

Bấm **thêm dòng khác** (link "Add another Checklist template item") cho từng đầu việc. Xong thì
bấm **Save** ở cuối trang.

### Bước 4: Nội dung gợi ý (HR chỉnh lại cho đúng thực tế công ty, đây chỉ là khung mẫu)

**Mẫu Onboarding — gợi ý các dòng:**

| Sequence | Item name | Responsible role code | Due offset days | Requires asset return |
|---|---|---|---|---|
| 1 | Chuẩn bị hợp đồng lao động/thử việc | HR_OFFICER | -3 | ☐ |
| 2 | Cấp tài khoản email + tài khoản hệ thống | SYS_ADMIN | 0 | ☐ |
| 3 | Bàn giao máy tính/thiết bị làm việc | HR_OFFICER | 0 | ✅ |
| 4 | Giới thiệu quy trình, nội quy công ty | DEPT_MANAGER | 1 | ☐ |
| 5 | Xác nhận hoàn tất tiếp nhận, đóng hồ sơ | HR_MANAGER | 5 | ☐ |

**Mẫu Offboarding — gợi ý các dòng:**

| Sequence | Item name | Responsible role code | Due offset days | Requires asset return |
|---|---|---|---|---|
| 1 | Bàn giao công việc cho người kế nhiệm | DEPT_MANAGER | -7 | ☐ |
| 2 | Thu hồi máy tính/thiết bị/thẻ ra vào | HR_OFFICER | 0 | ✅ |
| 3 | Khóa tài khoản email + tài khoản hệ thống | SYS_ADMIN | 0 | ☐ |
| 4 | Chốt công nợ, tạm ứng, quyết toán lương | FINANCE_OFFICER | 3 | ☐ |
| 5 | Xác nhận hoàn tất, đóng hồ sơ nghỉ việc | HR_MANAGER | 5 | ☐ |

**Đây chỉ là gợi ý để có dữ liệu chạy thử ngay** — HR nên rà lại với quy trình thực tế đang làm
tay hiện nay (đúng như đã trao đổi ở kế hoạch trước: "HR cung cấp checklist hiện dùng"), rồi
sửa/thêm/bớt dòng cho khớp. Sửa mẫu sau này **không ảnh hưởng** các hồ sơ đã mở trước đó — mỗi
hồ sơ giữ bản chụp riêng tại thời điểm mở.

---

## Phần 2 — Mở checklist cho một nhân viên cụ thể (làm mỗi khi có người vào/nghỉ)

Không làm trong Admin — vào thẳng cổng IHRMS.

### Bước 1: Mở hồ sơ
Vào `/portal/lifecycle/cases/create/` (hoặc menu **Nhân sự → Checklist tiếp nhận/nghỉ việc**).
Chọn:
- **Nhân viên** cần mở checklist.
- **Loại hồ sơ**: Onboarding hoặc Offboarding.
- **Mẫu checklist**: chỉ hiện các mẫu đang "Is active" và đúng loại vừa chọn.
- Nếu là **Offboarding**, hệ thống sẽ hỏi thêm **ngày nghỉ việc hiệu lực** (không tự lấy ngày
  hôm nay).

Bấm **Mở checklist**. Hệ thống tự sinh toàn bộ đầu việc theo đúng mẫu, tính sẵn hạn cho từng
mục dựa trên `Due offset days` đã cấu hình ở Phần 1.

⚠️ **Lưu ý:** nếu bấm mở checklist 2 lần cho cùng 1 nhân viên + cùng loại hồ sơ, hệ thống **tự
nhận ra đã có rồi và không tạo hồ sơ trùng** — không cần lo bấm nhầm 2 lần.

### Bước 2: Giao việc cho từng người phụ trách
Vào chi tiết hồ sơ (`/portal/lifecycle/cases/<id>/`), với mỗi đầu việc, chọn đúng người thật
(không phải nhóm vai trò) ở cột "Người phụ trách" rồi lưu. Người được giao sẽ thấy đầu việc này
trong danh sách của họ.

### Bước 3: Theo dõi
- Người được giao (hoặc HR) vào cùng trang để đánh dấu **Hoàn tất** hoặc **Bỏ qua** (phải ghi lý
  do khi bỏ qua).
- Mục nào có tick "Requires asset return" thì có thêm ô chọn liên kết tới đúng bản ghi cấp phát
  tài sản đã có sẵn của nhân viên đó (không tạo bản ghi tài sản mới, chỉ liên kết).
- Đầu việc quá hạn mà chưa xong sẽ tự tạo thông báo trong IHRMS cho người được giao — **nhưng
  chỉ khi có ai đó chạy lệnh nhắc việc**; xem lưu ý vận hành bên dưới.

---

## Việc IT/quản trị hệ thống cần làm thêm (không phải HR)

Lệnh nhắc việc quá hạn (`send_lifecycle_reminders`) đã code xong nhưng **chưa được lên lịch chạy
tự động**. Trước mắt có thể chạy tay:
```
python src\manage.py send_lifecycle_reminders
```
Khi nào sẵn sàng, cấu hình Windows Task Scheduler chạy lệnh này 1 lần/ngày (cùng cơ chế với
`send_activity_report_reminders` đã có).

---

## Tóm tắt điều cần bạn xác nhận/làm
1. **HR:** rà lại 2 bảng gợi ý ở Phần 1, chỉnh cho khớp quy trình thật, nhập vào Admin.
2. **HR:** xác định ai sẽ là người bấm "Mở checklist" mỗi khi có nhân viên vào/nghỉ (đề xuất:
   HR_OFFICER, vì đây là quyền `manage_lifecycle_case`).
3. **IT:** lên lịch Task Scheduler cho `send_lifecycle_reminders` khi đã sẵn sàng.
