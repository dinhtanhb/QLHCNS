# Hướng dẫn tự test nhanh 4 chức năng mới — IHRMS

Dành cho người test **không cần biết code**. Mỗi mục có: đường dẫn/menu chính xác, các bước
bấm theo thứ tự, và **kết quả đúng phải thấy**. Nếu thấy khác kết quả mô tả → chụp màn hình gửi
lại, đó là dấu hiệu có lỗi.

Đăng nhập bằng tài khoản nào thì menu hiện khác nhau tùy quyền — ghi rõ trong từng mục.

---

## 0. Cách vào các menu này

Sau khi đăng nhập, thanh menu ngang phía trên có các nhóm:
- **Cá nhân** — ai đăng nhập cũng thấy, có: *Yêu cầu cập nhật hồ sơ*, *Sơ đồ tổ chức*,
  *Bảng công*...
- **Duyệt & Xử lý** — chỉ hiện nếu tài khoản có quyền duyệt gì đó (nghỉ phép, chấm công, tài
  liệu...).
- **Nhân sự** — chỉ hiện với tài khoản `HR_OFFICER`/`HR_MANAGER`, có: *Duyệt cập nhật hồ sơ*,
  *Quản lý checklist onboarding/offboarding* (checklist thủ tục giấy tờ nhân sự, chỉ HCNS sử dụng).
- **Hoạt động dự án** — hiện với tài khoản có quyền theo dõi hoạt động dự án, có *Giao việc & hoàn tất*.

Biểu tượng **chuông 🔔** góc trên bên phải, ở mọi trang → trang "Thông báo của tôi".

---

## 1. Thông báo + Bản nháp email (Outbox)

Không có menu riêng — thông báo tự sinh ra khi có sự kiện (duyệt nghỉ phép, khóa lương, duyệt
tài liệu). Cách test nhanh nhất: dùng chính đơn nghỉ phép.

**Các bước:**
1. Đăng nhập tài khoản nhân viên thường → vào **Cá nhân → Nghỉ phép** → tạo 1 đơn xin nghỉ.
2. Đăng xuất, đăng nhập tài khoản là **quản lý trực tiếp** của người ở bước 1 → vào **Duyệt &
   Xử lý → Duyệt nghỉ phép** → bấm duyệt đơn vừa tạo.
3. Đăng xuất, đăng nhập lại tài khoản nhân viên ở bước 1 → bấm chuông 🔔 góc trên phải.

**Kết quả đúng phải thấy ở bước 3:**
- Có 1 thẻ thông báo mới, tiêu đề đại loại "Đơn nghỉ phép đã được duyệt".
- Nếu nhân viên có email (công ty hoặc cá nhân) trong hồ sơ: **ngay dưới** thẻ thông báo có 2
  nút: **"Mở thư nháp trong Outlook"** và **"Đã gửi qua Outlook"**.
- Bấm **"Mở thư nháp trong Outlook"**: máy tính bật ứng dụng Outlook (hoặc trình email mặc định),
  hiện sẵn 1 email nháp — **có địa chỉ người nhận, tiêu đề, nội dung đã điền sẵn**, nhưng
  **chưa gửi** (bạn phải tự bấm Gửi trong Outlook nếu muốn gửi thật). Đọc nội dung thư: chỉ ghi
  chung chung kiểu "đơn nghỉ phép của bạn đã được xử lý, đăng nhập IHRMS để xem chi tiết" —
  **không được** có số ngày nghỉ/lý do nghỉ cụ thể trong thư.
- Sau khi bấm Gửi (hoặc chỉ đóng thư nháp lại, không bắt buộc gửi thật để test), quay lại IHRMS
  bấm **"Đã gửi qua Outlook"** → dòng 2 nút biến mất, thay bằng chữ xanh "Đã xác nhận gửi qua
  Outlook · [ngày giờ]".

**Lỗi cần báo nếu gặp:** thấy số ngày nghỉ/lý do nghỉ trong nội dung thư nháp; nút "Mở thư nháp"
không mở được gì; bấm "Đã gửi qua Outlook" xong vẫn còn 2 nút cũ.

---

## 2. Sơ đồ tổ chức

**Đường dẫn:** menu **Cá nhân → Sơ đồ tổ chức**. Ai đăng nhập cũng xem được.

**Kết quả đúng phải thấy:**
- 1 danh sách dạng cây, thụt lề theo cấp bậc: quản lý ở trên, nhân viên trực thuộc thụt vào bên
  dưới.
- Mỗi người chỉ hiện: **họ tên, chức danh, phòng ban**.
- **Không được** hiện số điện thoại, email cá nhân của bất kỳ ai trên trang này.
- Nhân viên đã nghỉ việc (`employment_status` không phải "Active") **không** xuất hiện trên sơ
  đồ.

**Lỗi cần báo nếu gặp:** trang trắng dù công ty đã có dữ liệu nhân viên; thấy SĐT/email hiển
thị; thấy nhân viên đã nghỉ việc vẫn còn trên cây.

---

## 3. Yêu cầu tự cập nhật hồ sơ

**Đường dẫn gửi yêu cầu:** menu **Cá nhân → Yêu cầu cập nhật hồ sơ** (ai cũng thấy, dùng cho hồ
sơ của chính mình).
**Đường dẫn duyệt:** menu **Nhân sự → Duyệt cập nhật hồ sơ** (chỉ tài khoản HR mới thấy menu
này).

### 3.1. Gửi và duyệt bình thường

1. Đăng nhập tài khoản nhân viên → **Cá nhân → Yêu cầu cập nhật hồ sơ** → bấm tạo yêu cầu mới.
2. Ở ô **"Thông tin cần thay đổi"**, chỉ có đúng 3 lựa chọn trong danh sách xổ xuống: **Email cá
   nhân**, **Số điện thoại**, **Địa chỉ** — không có lựa chọn nào khác (không thể tự đổi lương,
   chức danh...).
3. Chọn 1 mục, ví dụ "Số điện thoại", nhập số mới vào ô nội dung, có thể ghi lý do, bấm gửi.
4. Đăng nhập tài khoản HR (`HR_OFFICER`/`HR_MANAGER`) → **Nhân sự → Duyệt cập nhật hồ sơ** →
   thấy yêu cầu vừa gửi, trạng thái "Chờ duyệt" → bấm duyệt.

**Kết quả đúng:** sau khi duyệt, vào lại hồ sơ nhân viên đó (hoặc để chính nhân viên xem hồ sơ cá
nhân) → số điện thoại đã đổi thành giá trị mới. Nhân viên nhận được thông báo kết quả duyệt (bấm
chuông 🔔 kiểm tra).

### 3.2. Test tình huống 2 người cùng sửa (nên nhờ người biết dùng trình duyệt hỗ trợ)

1. Nhân viên gửi yêu cầu đổi **Địa chỉ**.
2. **Trước khi HR duyệt**, vào Django Admin (`/admin/`) sửa thẳng địa chỉ nhân viên đó thành 1
   giá trị khác bất kỳ (giả lập tình huống ai đó đã sửa trước).
3. Quay lại duyệt yêu cầu ở bước 1.

**Kết quả đúng:** hệ thống báo dạng "giá trị đã thay đổi kể từ lúc gửi yêu cầu, vui lòng từ chối
và yêu cầu gửi lại" — **không** tự động ghi đè lên giá trị Admin vừa sửa ở bước 2.

**Lỗi cần báo nếu gặp:** danh sách xổ xuống có thêm trường lạ; duyệt xong hồ sơ không đổi; ở
tình huống 3.2 hệ thống vẫn cho duyệt bình thường mà không cảnh báo gì.

---

## 4. Checklist Onboarding / Offboarding

**Điều kiện cần trước:** đã có ít nhất 1 mẫu "Onboarding" và 1 mẫu "Offboarding" tạo sẵn trong
Django Admin (xem tài liệu `HR_Huong_Dan_Checklist_Onboarding_Offboarding.md` nếu chưa có).

**Đường dẫn:** menu **Nhân sự → Onboarding / Offboarding** (tài khoản HR).

### 4.1. Mở checklist cho 1 nhân viên

1. Vào menu trên → bấm tạo mới.
2. Chọn **Nhân viên**, chọn **Loại checklist** (Tiếp nhận/Nghỉ việc) — lưu ý: chọn loại trước,
   thì ô **Mẫu checklist** phía dưới tự lọc chỉ hiện đúng các mẫu cùng loại (mẫu Onboarding sẽ
   không hiện khi chọn loại "Nghỉ việc").
3. Nếu chọn loại **"Nghỉ việc"**, phải nhập thêm ngày nghỉ việc hiệu lực (không tự lấy ngày hôm
   nay). Nếu chọn "Tiếp nhận", hệ thống tự dùng ngày vào làm có sẵn trong hồ sơ nhân viên, không
   cần nhập.
4. Bấm mở checklist.

**Kết quả đúng:** vào trang chi tiết, thấy đủ toàn bộ đầu việc theo đúng mẫu đã chọn, mỗi đầu
việc có sẵn hạn hoàn thành (tính tự động).

### 4.2. Test chống mở trùng

Lặp lại đúng bước 4.1 cho **cùng 1 nhân viên, cùng loại checklist** lần thứ 2.

**Kết quả đúng:** hệ thống **không** tạo ra 2 hồ sơ riêng — báo đã tồn tại hoặc dẫn thẳng về hồ
sơ cũ, không tạo trùng danh sách đầu việc.

### 4.3. Checklist thủ tục nhân sự chỉ dành cho HCNS

Đăng nhập bằng tài khoản `HR_OFFICER` hoặc `HR_MANAGER`, mở **Nhân sự → Quản lý checklist onboarding/offboarding**.
Trong checklist, kiểm tra các giấy tờ và thủ tục tiếp nhận/nghỉ việc theo mẫu HCNS đã cấu hình.
Đây là quy trình hồ sơ nhân sự, không phải nơi giao việc chung hoặc giao việc hoạt động dự án.

**Kết quả đúng:** chỉ HCNS/quản trị được mở danh sách và cập nhật checklist; người dùng dự án hoặc nhân viên thường không thấy mục checklist trong menu và bị từ chối nếu thử mở URL trực tiếp.

### 4.4. Giao việc dự án và cập nhật hoàn tất

Với tài khoản Điều phối viên/Quản lý dự án, tạo hoặc cập nhật một hoạt động, chọn CBDA phụ trách và liên kết một công văn đi. Hệ thống tự tạo Task báo cáo cho CBDA; Điều phối viên được ghi là người giao, hạn 10 ngày làm việc từ ngày gửi công văn. Đăng nhập bằng tài khoản có quyền **Hoạt động dự án**, mở **Hoạt động dự án → Giao việc & hoàn tất**.

CBDA mở Task, cập nhật trạng thái và tải báo cáo lên SharePoint trước khi chọn **Hoàn thành**. Điều phối viên/Quản lý dự án cũng thấy các Task thuộc phạm vi hoạt động họ được phép xem để theo dõi tiến độ; họ không cần tạo Task báo cáo bằng nút giao việc thủ công.

**Kết quả đúng:** Task xuất hiện trong danh sách của CBDA nhận việc và trong danh sách giám sát của Điều phối viên/Quản lý dự án. Ngày bắt đầu, hạn và ngày hoàn thành thực tế hiển thị riêng theo định dạng `ngày/tháng/năm`; khi hoàn thành trong ngày bắt đầu, ngày hoàn thành phải đúng ngày đó. Task chỉ được hoàn thành sau khi có tệp báo cáo; task dự án được tách khỏi checklist thủ tục HCNS.

**Lỗi cần báo nếu gặp:** mở mẫu Offboarding nhưng vẫn thấy mẫu Onboarding trong danh sách chọn;
mở trùng tạo ra 2 checklist riêng biệt; nhân viên không liên quan vẫn xem được checklist người
khác.

---

## Mẹo test nhanh, đỡ mất công tạo tài khoản

- Tối thiểu **3 tài khoản**: 1 nhân viên thường, 1 tài khoản có quyền dự án (CBDA/Điều phối viên),
  1 tài khoản HR_OFFICER. Dùng để xác nhận menu công việc dự án và checklist HCNS tách biệt.
- Nếu công ty chưa có sẵn nhiều tài khoản test, nhờ IT tạo 3 tài khoản kiểu `test_nhanvien`,
  `test_quanly`, `test_hr` — dùng xong test có thể xóa, không ảnh hưởng dữ liệu thật.
- Luôn **đăng xuất hẳn** trước khi đổi sang tài khoản khác (đừng chỉ đổi tab), để chắc chắn đang
  xem đúng góc nhìn của tài khoản đó.
