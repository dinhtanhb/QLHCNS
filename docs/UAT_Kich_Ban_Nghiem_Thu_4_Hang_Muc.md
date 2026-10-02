# Kịch bản UAT & Biên bản nghiệm thu — 4 hạng mục IHRMS đợt 2026-09

Phạm vi: Hạng mục 1 (Thông báo + Outbox email), Hạng mục 4 (Sơ đồ tổ chức + Tự cập nhật hồ sơ),
Hạng mục 2 (Checklist Onboarding/Offboarding). **Không bao gồm Hạng mục 3** (báo cáo tuân thủ) —
chưa code, đang chờ Kế toán xác nhận mẫu.

Môi trường test: SIT/UAT (SQL Server thật, **không phải** SQLite) — dữ liệu test, không dùng dữ
liệu nhân viên thật.

## Chuẩn bị trước khi test (Người thực hiện: IT)

Tạo tối thiểu các tài khoản test sau (đặt username có tiền tố `uat_` để dễ dọn sau khi xong):

| Username gợi ý | Vai trò (Role) | Vai trò trong kịch bản |
|---|---|---|
| `uat_nhanvien` | EMPLOYEE | Nhân viên thường |
| `uat_truongphong` | DEPT_MANAGER | Quản lý trực tiếp của `uat_nhanvien` (cùng phòng ban) |
| `uat_truongphong_b` | DEPT_MANAGER | Quản lý **phòng ban khác** (dùng để test không được duyệt chéo) |
| `uat_hr` | HR_OFFICER | Nhân sự tác nghiệp |
| `uat_hrm` | HR_MANAGER | Nhân sự quản lý |
| `uat_ketoan` | FINANCE_OFFICER | Kế toán |
| `uat_giamdoc` | DIRECTOR | Giám đốc |

Đảm bảo `uat_nhanvien` và `uat_truongphong` cùng 1 phòng ban, `uat_truongphong` được đặt làm
`manager` của phòng ban đó (Admin → Organization → Department → trường Manager).

---

## A. Hạng mục 1 — Thông báo & Outbox email

### A1. Duyệt nghỉ phép tạo thông báo + bản nháp email

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_nhanvien | Tạo 1 đơn xin nghỉ phép | Đơn ở trạng thái "Chờ duyệt" | ☐ |
| 2 | uat_truongphong | Vào danh sách chờ duyệt, duyệt đơn trên | Đơn chuyển "Đã duyệt" | ☐ |
| 3 | uat_nhanvien | Xem chuông thông báo | Có thông báo mới "đơn nghỉ đã được duyệt" | ☐ |
| 4 | uat_hr hoặc uat_nhanvien | Vào mục "Hàng chờ email" (outbox) tương ứng | Có 1 bản ghi trạng thái "Draft", bấm vào **mở được bản nháp Outlook** (không phải gửi thẳng) | ☐ |
| 5 | Người kiểm tra | Đọc nội dung bản nháp email | **Không** thấy số ngày nghỉ/lý do cá nhân chi tiết trong nội dung thư — chỉ có câu chung "vui lòng đăng nhập IHRMS để xem" | ☐ |

### A2. Không tự duyệt đơn của chính mình

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_truongphong | Tự tạo 1 đơn xin nghỉ phép cho chính mình | Đơn "Chờ duyệt" | ☐ |
| 2 | uat_truongphong | Thử tự duyệt đơn của chính mình | Hệ thống **từ chối**, đơn vẫn "Chờ duyệt" | ☐ |

---

## B. Hạng mục 4 — Sơ đồ tổ chức & Tự cập nhật hồ sơ

### B1. Sơ đồ tổ chức

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_nhanvien | Vào trang Sơ đồ tổ chức | Hiển thị đúng cây quản lý — `uat_nhanvien` nằm dưới `uat_truongphong` | ☐ |
| 2 | Người kiểm tra | Quan sát thông tin hiển thị trên sơ đồ | Chỉ thấy họ tên, chức danh, phòng ban — **không** thấy SĐT/email cá nhân | ☐ |

### B2. Yêu cầu tự cập nhật hồ sơ — luồng bình thường

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_nhanvien | Gửi yêu cầu đổi số điện thoại di động | Tạo yêu cầu "Chờ duyệt" | ☐ |
| 2 | uat_hr | Vào danh sách yêu cầu, duyệt | Yêu cầu "Đã duyệt", hồ sơ `uat_nhanvien` cập nhật đúng số mới | ☐ |
| 3 | uat_nhanvien | Xem chuông thông báo | Có thông báo kết quả duyệt | ☐ |

### B3. Chặn thay đổi trường không được phép + chặn race condition (kỹ thuật, cần người rành thao tác trình duyệt hỗ trợ)

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_nhanvien | Gửi yêu cầu đổi địa chỉ (`address`) | Yêu cầu "Chờ duyệt" | ☐ |
| 2 | uat_hr (Admin) | **Trước khi duyệt**, vào Django Admin sửa thẳng địa chỉ nhân viên đó thành 1 giá trị khác | Sửa thành công (giả lập tình huống 2 người cùng sửa) | ☐ |
| 3 | uat_hr | Quay lại duyệt yêu cầu ở bước 1 | Hệ thống báo **"giá trị đã thay đổi, vui lòng từ chối và yêu cầu gửi lại"**, không áp giá trị cũ đè lên | ☐ |

### B4. Không xem được yêu cầu của người khác

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_nhanvien | Gửi 1 yêu cầu, ghi lại ID trên URL | — | ☐ |
| 2 | uat_truongphong_b (không liên quan) | Sửa URL, thử truy cập thẳng ID yêu cầu đó | Bị từ chối truy cập | ☐ |

---

## C. Hạng mục 2 — Checklist Onboarding/Offboarding

*(Yêu cầu: đã có ít nhất 1 mẫu Onboarding và 1 mẫu Offboarding cấu hình trong Admin — xem tài
liệu `HR_Huong_Dan_Checklist_Onboarding_Offboarding.md`)*

| Bước | Người thực hiện | Thao tác | Kết quả mong đợi | Đạt/Không đạt |
|---|---|---|---|---|
| 1 | uat_hr | Mở checklist Onboarding cho `uat_nhanvien` | Hệ thống sinh đủ các đầu việc theo đúng mẫu, tính đúng hạn theo `Due offset days` | ☐ |
| 2 | uat_hr | Mở lại checklist Onboarding cho **đúng** `uat_nhanvien` lần 2 | Hệ thống **không** tạo hồ sơ trùng (báo đã tồn tại hoặc mở lại hồ sơ cũ) | ☐ |
| 3 | uat_hr | Giao 1 đầu việc cho `uat_truongphong` | `uat_truongphong` thấy đầu việc này trong danh sách của mình | ☐ |
| 4 | uat_nhanvien | Thử vào xem checklist của người khác (sửa URL ID) | Bị từ chối truy cập | ☐ |
| 5 | uat_truongphong | Đánh dấu đầu việc được giao là "Hoàn tất" | Trạng thái cập nhật, ghi nhận người hoàn tất + thời điểm | ☐ |
| 6 | uat_hr | Với 1 đầu việc có tick "Requires asset return", liên kết tới 1 bản ghi cấp phát tài sản có sẵn | Liên kết thành công, **không** phát sinh/xóa lịch sử tài sản | ☐ |

---

## Biên bản nghiệm thu

**Dự án:** IHRMS — 4 hạng mục bổ sung tháng 09/2026 (Thông báo, Sơ đồ tổ chức, Tự cập nhật hồ
sơ, Checklist Onboarding/Offboarding)

**Ngày thực hiện UAT:** _______________  **Môi trường:** ☐ SIT   ☐ UAT   ☐ Khác: __________

**Tổng số kịch bản:** 12   **Số đạt:** _____   **Số không đạt:** _____

**Danh sách lỗi phát sinh trong quá trình test (nếu có):**

| STT | Kịch bản | Mô tả lỗi | Mức độ (Nghiêm trọng/Trung bình/Nhẹ) | Người ghi nhận |
|---|---|---|---|---|
| | | | | |
| | | | | |

**Kết luận:**
☐ Đạt yêu cầu, đồng ý đưa vào sử dụng chính thức
☐ Đạt có điều kiện — cần khắc phục các lỗi liệt kê trên trước khi go-live
☐ Không đạt — cần làm lại UAT sau khi khắc phục

**Chữ ký xác nhận:**

| Vai trò | Họ tên | Chữ ký | Ngày |
|---|---|---|---|
| HR_MANAGER (nghiệp vụ nhân sự) | | | |
| FINANCE_OFFICER (nếu có kịch bản liên quan lương/outbox) | | | |
| DIRECTOR / Người phê duyệt đưa vào sử dụng | | | |
| IT (xác nhận môi trường, hạ tầng) | | | |
