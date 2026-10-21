# IHRMS: Kế hoạch các hạng mục tiếp theo

Ngày lập: 2026-09-25
Phạm vi: thông báo nghiệp vụ, checklist tiếp nhận/nghỉ việc, báo cáo tuân thủ và sơ đồ tổ chức/yêu cầu cập nhật hồ sơ.

## Kết luận và thứ tự đề xuất

Triển khai theo từng lát nhỏ, giữ nguyên kiến trúc Django modular monolith và hệ thống phân quyền hiện có. Không gộp các chức năng thành một đợt lớn. Trước hết bổ sung thông báo trong ứng dụng và nhật ký gửi; sau đó làm quy trình thay đổi hồ sơ/sơ đồ tổ chức, checklist nhân sự, rồi mới mở rộng báo cáo tuân thủ sau khi Kế toán xác nhận biểu mẫu và quy tắc số liệu. Email tự động chỉ bật khi IT xác nhận được dịch vụ gửi phù hợp với hệ thống thư thực tế của công ty.

Các hạng mục này chưa được triển khai trong mã ở đợt hiện tại. Tài liệu này là kế hoạch để chia thành PR/commit nhỏ, có kiểm thử và migration riêng; không phải xác nhận đã có chức năng.

## Hiện trạng và giới hạn đã biết

- M365 Graph hiện được cấu hình để lưu tệp SharePoint. Quyền truy cập tệp không đồng nghĩa với quyền gửi thư Exchange/Outlook.
- Quy trình hiện tại của công ty dùng POP3 và Outlook trên máy người dùng. Ứng dụng đã dùng cách mở thư nháp Outlook để người dùng xem lại và gửi. Không giả định có Microsoft 365 mailbox hoặc Graph `Mail.Send`; không đưa mật khẩu POP3/SMTP vào ứng dụng.
- Nhắc việc Windows Task Scheduler chưa được ưu tiên/kiểm thử vận hành. Trước khi dựa vào tác vụ nền, cần có cách chạy định kỳ có log, chống gửi lặp và hướng dẫn phục hồi.
- Dữ liệu lương, bảo hiểm, thuế và hồ sơ nhân viên là dữ liệu nhạy cảm. Chỉ vai trò được cấp mới được xem/xuất; file xuất phải ghi kỳ, thời điểm, người tạo và phạm vi dữ liệu.
- Người dùng yêu cầu bỏ qua check-in tự động và trang tuyển dụng công khai; hai mục đó nằm ngoài kế hoạch này.

## Hạng mục 1 — Thông báo duyệt và nhắc việc

### Mục tiêu

Người có việc cần xử lý nhận được thông báo trong IHRMS trước; email là kênh bổ sung, không thay thế trạng thái/phê duyệt trong ứng dụng. Áp dụng trước cho duyệt nghỉ phép, kỳ lương và công văn; sau đó dùng chung cho checklist và yêu cầu hồ sơ.

### Thiết kế theo giai đoạn

1. Chuẩn hóa sự kiện nghiệp vụ (đã gửi duyệt, được duyệt, yêu cầu chỉnh sửa, bị từ chối, sắp đến hạn/quá hạn) và người nhận theo vai trò/phạm vi.
2. Ghi thông báo bền vững vào cơ sở dữ liệu trong cùng transaction với thay đổi nghiệp vụ khi phù hợp; cung cấp danh sách chưa đọc, đánh dấu đã đọc và đường dẫn đến đối tượng.
3. Thêm outbox gửi thư: trạng thái chờ/gửi/failed, số lần thử, thời điểm thử lại, mã lỗi đã làm sạch, khóa idempotency và nhật ký. Không gửi thư trong request đồng bộ nếu lỗi thư có thể làm hỏng thao tác duyệt.
4. Chỉ bật email khi IT chọn và xác nhận một phương án được hỗ trợ: SMTP relay của công ty có xác thực/allowlist phù hợp, hoặc Exchange Online/Graph với mailbox, quyền ứng dụng `Mail.Send`, admin consent và giới hạn mailbox đã được phê duyệt. Nếu vẫn chỉ có POP3/Outlook cục bộ, giữ quy trình mở thư nháp Outlook; server không thể mở Outlook trên máy người nhận.
5. Kiểm thử người nhận, chống gửi lặp, retry, lỗi mạng, phân quyền URL và nội dung không làm lộ dữ liệu lương/hồ sơ nhạy cảm.

### Điều kiện nghiệm thu

- Sự kiện tạo một thông báo ứng dụng duy nhất cho đúng người/nhóm có quyền.
- Link thông báo vẫn kiểm tra quyền server-side; người không có quyền không xem được đối tượng bằng cách sửa URL.
- Sự cố email không làm mất yêu cầu duyệt; có trạng thái lỗi dễ tra cứu và hướng dẫn xử lý.
- Không có thông tin lương, thông tin định danh hoặc tệp đính kèm nhạy cảm trong log thư mặc định.

## Hạng mục 2 — Checklist onboarding/offboarding

### Phạm vi nghiệp vụ

Tạo hồ sơ checklist theo nhân viên và ngày hiệu lực, gồm mẫu có thể cấu hình, các mục việc, người phụ trách, hạn, trạng thái, ghi chú và lịch sử hoàn thành. Checklist onboarding khởi tạo khi HR xác nhận tuyển/tiếp nhận; offboarding khởi tạo khi quyết định nghỉ việc đã được duyệt. Không tự kích hoạt chỉ vì tạo một hồ sơ nháp.

### Luồng đề xuất

- HR mở checklist theo mẫu và xác nhận ngày bắt đầu/ngày nghỉ.
- Hệ thống giao đầu việc cho HR, quản lý trực tiếp, IT/hành chính và kế toán theo vai trò đã cấu hình.
- Các mục có thể gồm hồ sơ, tài khoản/quyền truy cập, bàn giao công việc, tài sản cấp phát/thu hồi, xác nhận của quản lý và đóng hồ sơ.
- Tài sản liên kết tới bản ghi `asset` hiện có; thu hồi tài sản phải cập nhật trạng thái qua nghiệp vụ asset hiện có, không ghi đè/xóa lịch sử cấp phát.
- Quá hạn được hiển thị trong dashboard và dùng chung cơ chế thông báo.

### Dữ liệu và kiểm soát

Thiết kế các thực thể như `ChecklistTemplate`, `ChecklistTemplateItem`, `EmployeeLifecycleCase`, `LifecycleChecklistItem` theo chuẩn audit/soft delete đang dùng. Bảo đảm một sự kiện nhân sự không tạo checklist trùng; lưu người hoàn tất, thời điểm, lý do bỏ qua và liên kết tài sản. Chỉ HR được mở/đóng hồ sơ; người được giao chỉ cập nhật mục được giao; quản lý chỉ xem phạm vi phù hợp.

### Điều kiện nghiệm thu

- Mẫu onboarding/offboarding có thể chỉnh mà không làm thay đổi checklist đã phát sinh.
- Tạo lại sự kiện không sinh hồ sơ hoặc mục việc trùng.
- Hoàn tất/thu hồi tài sản thể hiện đúng liên kết và audit.
- Nhân viên không thể xem checklist của người khác qua URL hoặc POST trực tiếp.

## Hạng mục 3 — Báo cáo tuân thủ và chi phí lương

### Biểu mẫu pháp lý cần xác nhận trước khi code

- Đầu bài nêu D02-TS. Tài liệu BHXH hiện hành được tìm thấy dùng mẫu **D02-LT**; cần kế toán/đơn vị dịch vụ BHXH xác nhận mẫu, phiên bản và kênh nộp áp dụng cho doanh nghiệp trước khi chốt đặc tả. Không xây mới theo tên D02-TS nếu biểu mẫu đó không còn được chấp nhận.
- Đầu bài nêu 05/QTT-TNCN. Cần Kế toán xác nhận mẫu quyết toán, phụ lục và phiên bản áp dụng cho đúng năm quyết toán; không mặc định mẫu cũ còn phù hợp khi quy định thuế thay đổi.
- Báo cáo chi phí lương theo phòng ban phải chốt định nghĩa: theo phòng ban hiện tại hay tại thời điểm kỳ lương; gross/net; phần doanh nghiệp đóng; phụ cấp; phân bổ nhân viên điều chuyển; loại khoản loại trừ. Không tự suy diễn các quy tắc này từ màn hình hiện tại.

Tham khảo ban đầu: [thủ tục BHXH và biểu mẫu D02-LT](https://baohiemxahoi.gov.vn/thu-tuc-hanh-chinh/Pages/default.aspx?ItemID=71), [hướng dẫn BHXH về D02-LT thay D02-TS](https://binhthuan.baohiemxahoi.gov.vn/content/tintuc/Lists/News/Attachments/4251/27674_Cong%20van%20huong%20dan%20lap%20mau%20D02-LT.pdf), [Luật Thuế thu nhập cá nhân 109/2025/QH15 trên Cổng văn bản Chính phủ](https://vanban.chinhphu.vn/?docid=216495&pageid=27160). Đây là căn cứ để yêu cầu xác minh phiên bản, không thay cho ý kiến của Kế toán/cơ quan thuế.

### Cách triển khai

1. Kế toán cung cấp mẫu trống chính thức/đầu ra HTKK đang dùng, năm áp dụng, quy tắc đối chiếu và 3–5 bộ số liệu giả đã kiểm tra.
2. Lập data mapping từ mô hình nhân viên, hợp đồng, mức đóng, người phụ thuộc và bảng lương; đánh dấu rõ trường không có hoặc không đủ căn cứ.
3. Làm báo cáo xem trước với tổng đối chiếu và cảnh báo thiếu/sai dữ liệu trước khi xuất.
4. Xuất theo định dạng cơ quan/HTKK chấp nhận; nếu chưa có API nộp được hỗ trợ, xuất file để kế toán rà soát và tự nộp. Không tự động gửi hồ sơ lên cổng thuế/BHXH.
5. Chốt kỳ/snapshot số liệu để tái tạo đúng bản đã xuất; ghi người xuất, thời gian, bộ lọc và tổng kiểm soát.

### Điều kiện nghiệm thu

- Kế toán đối chiếu từng chỉ tiêu với bộ mẫu chuẩn và ký xác nhận trước phát hành.
- Tổng theo nhân viên/phòng ban khớp bảng lương đã chốt; nhân viên đổi phòng ban được xử lý theo quy tắc đã duyệt.
- Người không có quyền payroll không xem được màn hình, endpoint hoặc file xuất.
- Có test dữ liệu biên và kiểm thử trên SQL Server; không thay đổi công thức lương/thuế hiện có.

## Hạng mục 4 — Sơ đồ tổ chức và yêu cầu cập nhật thông tin cá nhân

### Sơ đồ tổ chức

Trước tiên làm trang tra cứu nội bộ dựa trên phòng ban, quản lý và vị trí hiện có. Hiển thị tối thiểu tên, chức danh, phòng ban và quản lý theo quyền; không đưa thông tin liên lạc cá nhân/nhạy cảm lên sơ đồ mặc định. Cần kiểm tra dữ liệu quản lý và chu kỳ hiệu lực để tránh hiển thị sai khi có điều chuyển.

### Yêu cầu tự cập nhật hồ sơ

- Nhân viên tạo yêu cầu thay đổi cho danh sách trường được cho phép (ví dụ địa chỉ liên hệ, điện thoại, thông tin liên hệ khẩn cấp), nêu lý do và đính kèm chứng từ nếu quy trình yêu cầu.
- Không cho nhân viên sửa trực tiếp trường nhạy cảm hoặc trường do HR quản lý như mã nhân viên, lương, phòng ban, chức danh, trạng thái làm việc, quyền truy cập.
- Lưu giá trị hiện tại/đề xuất, người gửi, thời điểm, người xử lý, quyết định, lý do yêu cầu sửa/từ chối và audit. Chỉ áp dụng thay đổi lên Employee sau khi HR duyệt.
- Trạng thái: Nháp → Chờ duyệt → Đã duyệt/Từ chối/Yêu cầu bổ sung. Thông báo trong ứng dụng cho nhân viên và HR.

### Điều kiện nghiệm thu

- Chặn cập nhật trường ngoài whitelist kể cả khi gửi POST thủ công.
- Phê duyệt có transaction, kiểm tra bản ghi chưa bị thay đổi kể từ lúc gửi và lưu audit.
- Nhân viên chỉ xem yêu cầu của mình; HR chỉ xem theo quyền được cấp.
- Sơ đồ chỉ hiển thị trường đã phê duyệt cho người xem và không làm lộ dữ liệu hồ sơ.

## Trình tự triển khai và cổng quyết định

| Giai đoạn | Phạm vi | Đầu ra/cổng qua giai đoạn |
|---|---|---|
| 0 | Bugfix activity và regression tests | 112 test module được chỉ định pass trên SQLite; chạy module tương đương trên SQL Server SIT trước khi phát hành |
| 1 | Notification in-app + outbox/email adapter được cấu hình tắt mặc định | Phê duyệt ma trận sự kiện/người nhận; IT xác nhận kênh thư trước khi bật gửi thật |
| 2 | Sơ đồ tổ chức + yêu cầu cập nhật hồ sơ | HR chốt trường tự sửa, chứng từ, người duyệt, thời hạn xử lý |
| 3 | Checklist onboarding/offboarding và liên kết asset | HR/IT/quản lý chốt hai mẫu checklist và chủ sở hữu từng mục |
| 4 | Báo cáo BHXH/PIT/payroll department | Kế toán xác nhận mẫu/phiên bản, data mapping và bộ số đối chiếu; chạy SQL Server SIT và UAT |

Mỗi giai đoạn: backup theo quy ước dự án trước thay đổi lớn; migration nhỏ, portable; kiểm thử quyền trực tiếp; `check`, `makemigrations --check --dry-run`, test module liên quan; kiểm thử SQL Server SIT khi có thay đổi phụ thuộc backend; cập nhật `docs/PROJECT_WORK_LOG.md`; commit riêng. Không chạy migration lên production trong giai đoạn phát triển.

## Thông tin cần chủ dự án/đơn vị cung cấp trước khi bắt đầu từng giai đoạn

1. **Email:** IT xác nhận có Exchange Online mailbox và cấp được Graph Mail.Send hay chỉ có SMTP relay nội bộ; cung cấp tên mailbox gửi, người nhận theo nghiệp vụ, chính sách CC và giới hạn nội dung. Không gửi mật khẩu/token qua chat hoặc commit.
2. **On/offboarding:** HR cung cấp checklist hiện dùng cho nhân viên mới/nghỉ việc, vai trò chịu trách nhiệm, hạn chuẩn, điều kiện bỏ qua và danh mục tài sản/quyền phải bàn giao.
3. **Báo cáo:** Kế toán cung cấp biểu mẫu chính thức đang nộp, năm áp dụng, hướng dẫn ghi từng chỉ tiêu và dữ liệu giả đã đối chiếu; xác nhận cách phân bổ chi phí khi điều chuyển.
4. **Cơ cấu/cập nhật hồ sơ:** HR xác nhận nguồn dữ liệu sơ đồ, phạm vi hiển thị, trường tự cập nhật được, trường cần chứng từ, người duyệt thay thế và SLA xử lý.

Không cần gửi dữ liệu nhân viên thật; dùng bản mẫu đã ẩn danh.
