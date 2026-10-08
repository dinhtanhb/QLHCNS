# GIÁO ÁN VÀ BÀI THỰC HÀNH TẬP HUẤN IHRMS

**Dành cho:** người hướng dẫn nội bộ và đầu mối nghiệp vụ

**Vị trí tài liệu:** bộ tài liệu dự án trong thư mục `docs/`.

**Phiên bản:** 1.3 — 26/09/2026

**Thời lượng gợi ý:** 75 phút nhân viên; thêm 45 phút quản lý; 90 phút Nhân sự cộng 35 phút checklist; 120 phút Tài chính; 60 phút quản trị. Có thể thêm 45 phút cho module tự cập nhật hồ sơ/sơ đồ tổ chức.

## 1. Mục tiêu và nguyên tắc

Kết thúc buổi học, học viên tự đăng nhập, tìm đúng menu, hoàn thành tác vụ theo vai trò, nhận biết bước cần phê duyệt và báo lỗi an toàn. Dùng tài khoản/dữ liệu demo được công ty cho phép; không chiếu dữ liệu lương/CCCD thật. Trình diễn thao tác trên môi trường đã được phê duyệt. Không cấp quyền cao chỉ để tiện đào tạo.

## 2. Chuẩn bị trước buổi học

- Xác nhận môi trường, URL/HTTPS, trình duyệt và tài khoản demo theo từng vai trò.
- Kiểm tra menu, dữ liệu mẫu, thông báo, kết nối SQL và trạng thái các chức năng sẽ trình diễn.
- Chuẩn bị nhân viên, phòng ban, quản lý, kỳ công/lương demo; không dùng dữ liệu cá nhân thật.
- Xác định đầu mối nghiệp vụ cho Nhân sự, Tài chính, phê duyệt và IT; công bố kênh hỗ trợ.
- In/gửi [Cẩm nang sử dụng IHRMS](HUONG_DAN_SU_DUNG_IHRMS.md); chuẩn bị bài kiểm tra và bảng điểm danh.
- Đối chiếu quy định công ty: hạn gửi công/nghỉ, người duyệt thay thế, lịch làm việc, quy trình sửa công, lịch chốt lương. Đánh dấu nội dung chưa được phê duyệt để không tự đặt quy tắc.
- Với buổi Nhân sự, chuẩn bị hai mẫu checklist demo đã được HR duyệt nội dung, người chịu trách nhiệm và hạn; tài khoản cấu hình mẫu phải vào được Django Admin.
- Với bài Outlook, dùng người nhận/hộp thư demo nội bộ được IT duyệt. Không gửi email thật ra ngoài trong giờ học.
- Báo trước: nhắc checklist chưa có Task Scheduler; báo cáo BHXH/PIT/chi phí lương theo phòng ban chưa được cấu hình để xuất.

## 3. Lịch buổi học nhân viên — 75 phút

| Phút | Nội dung | Cách dạy |
|---:|---|---|
| 0–5 | Mục tiêu, phạm vi dữ liệu và quy tắc bảo mật | Nêu rõ không dùng chung tài khoản/không chụp phiếu lương. |
| 5–12 | Đăng nhập, dashboard, menu, chuông, đăng xuất | Người hướng dẫn làm mẫu một lần. |
| 12–22 | Hồ sơ cá nhân | Học viên tìm trường cần đối chiếu. |
| 22–38 | Bảng công | Làm mẫu chọn tháng, ghi giờ, dự án, xem tổng và trạng thái. |
| 38–52 | Nghỉ phép | Tạo đơn demo, xem số ngày/số dư/trạng thái. |
| 52–62 | Phiếu lương và bảo mật | Trình diễn PDF bằng nhân vật demo, nhấn mạnh chỉ xem phiếu của mình. |
| 62–70 | Tệp đính kèm và bài thực hành cá nhân | Làm thử với tệp giả trên hồ sơ đào tạo; mở lại tệp từ IHRMS. |
| 70–75 | Kiểm tra nhanh, câu hỏi, kênh hỗ trợ | Dùng tiêu chí đạt ở mục 9. |

## 4. Thực hành nhân viên

Mỗi người dùng tài khoản demo riêng:

1. Đăng nhập, mở hồ sơ và chỉ ra phòng ban/quản lý.
2. Mở bảng công tháng được chỉ định; thêm một dòng công demo, chọn dự án nếu được giao; lưu và đọc tổng giờ.
3. Tạo đơn nghỉ demo trong khoảng ngày hợp lệ; nêu số ngày hệ thống tính; không gửi vào quy trình thật nếu môi trường không phải môi trường đào tạo.
4. Tìm trạng thái đơn và thông báo.
5. Mở phiếu lương demo và tải PDF. Xác nhận đây là dữ liệu demo; không gửi qua nhóm chat.
6. Trên môi trường đào tạo, đính kèm tệp giả vào đơn nghỉ phép demo, lưu rồi mở lại để xác nhận đọc được. Không dùng hồ sơ thật hoặc tự xóa tệp trong SharePoint.
7. Đăng xuất.

**Đạt khi:** làm đúng ít nhất 6/7 bước; không chia sẻ thông tin xác thực; hiểu đơn đang chờ chưa phải đã duyệt và biết báo IT nếu tệp không mở được.

## 5. Bổ sung cho quản lý — 45 phút

1. Mở danh sách **Duyệt nghỉ phép**, đọc người gửi, loại/ngày, số ngày và số dư.
2. Với dữ liệu demo, duyệt một yêu cầu hợp lệ và từ chối một yêu cầu cần bổ sung; ghi lý do rõ.
3. Mở **Duyệt chấm công**, đối chiếu tổng, dự án, nghỉ và trạng thái.
4. Nêu hậu quả nghiệp vụ: bản ghi được duyệt có thể cấp dữ liệu cho báo cáo/lương; sửa sau duyệt phải theo quy trình điều chỉnh.
5. Thực hành xử lý yêu cầu ngoài phạm vi: không cố duyệt, chuyển đúng người có thẩm quyền.

**Thảo luận:** ai duyệt khi trưởng bộ phận vắng mặt? Hạn phản hồi là bao lâu? Chốt câu trả lời theo chính sách công ty, không suy ra từ phần mềm.

## Thực hành bổ sung: Hoạt động dự án và hồ sơ xin duyệt — 45 phút

**Đối tượng:** CBDA, Điều phối viên, Giám đốc dự án/quản lý có quyền duyệt. Dùng hoạt động demo và hai PDF giả; không đưa đề xuất/dự trù thật lên môi trường đào tạo.

1. Học viên CBDA vào **Hoạt động dự án** → **Theo dõi hoạt động**, chọn một hoạt động demo, mở **Đề xuất & dự trù** và chỉ vị trí tải hai PDF. Nhắc lại Excel làm theo mẫu ngoại tuyến, chỉ hai PDF được tải lên hồ sơ IHRMS.
2. Điều phối viên kiểm tra hồ sơ, chọn Giám đốc nhận duyệt, mở thư nháp Outlook, thêm CC thử, tải hai PDF và đính kèm. Trong buổi tập huấn không gửi thư ra ngoài; dừng trước nút Gửi hoặc dùng hộp thư demo nội bộ được IT duyệt. Không xác nhận đã gửi nếu thư chưa được gửi thật.
3. Giám đốc vào **Duyệt & Xử lý** → **Duyệt đề xuất hoạt động**, mở hàng chờ của chính mình, xem PDF, chọn **Yêu cầu chỉnh sửa** và ghi ý kiến demo.
4. CBDA và Điều phối viên mở chuông/trang **Thông báo**, kiểm tra có thông báo và nội dung phản hồi; mở liên kết tới hồ sơ. Trên dashboard hoạt động, tìm đúng tháng, xác nhận trạng thái **Yêu cầu chỉnh sửa** và ý kiến hiện dưới tên hoạt động.
5. Thực hành luồng duyệt: Giám đốc phê duyệt một hồ sơ demo; các học viên tìm trạng thái mới trong dashboard.

**Đạt khi:** mỗi vai trò tìm được menu đúng; người duyệt mở hồ sơ từ hàng chờ mà không cần email; CBDA/ĐPV tìm được thông báo và ý kiến; người học hiểu Outlook cần tự đính kèm PDF và xác nhận trong IHRMS chỉ sau khi gửi thật.

**Lưu ý người hướng dẫn:** chỉ tài khoản được cấp quyền xem mới có menu Hoạt động dự án; hàng chờ duyệt chỉ hiện hồ sơ giao đúng Giám đốc. Nếu không thấy hoạt động trong dashboard, chọn đúng tháng. Quyết định cũ không được thông báo hồi tố.

## Thực hành bổ sung: Cập nhật hồ sơ và sơ đồ tổ chức — 30 phút

**Đối tượng:** toàn thể nhân viên và Nhân sự. Chỉ dùng tài khoản/hồ sơ demo, không trình chiếu địa chỉ, email hoặc số điện thoại thật.

1. Học viên đóng vai nhân viên vào **Cá nhân → Sơ đồ tổ chức**; chỉ ra họ tên, chức vụ, phòng ban và quan hệ quản lý. Xác nhận trang không phải danh bạ liên hệ.
2. Vào **Cá nhân → Yêu cầu cập nhật hồ sơ → Tạo yêu cầu**; chọn một trường trong whitelist (email cá nhân, số điện thoại, địa chỉ), nhập giá trị demo/lý do, gửi.
3. Học viên Nhân sự vào hàng chờ **Duyệt cập nhật hồ sơ**, kiểm tra thông tin và thử một trong các quyết định: duyệt, từ chối hoặc yêu cầu bổ sung; nhập ý kiến để nhân viên biết bước tiếp.
4. Nhân viên xem trạng thái và thông báo trong IHRMS. Nếu được yêu cầu bổ sung, tạo yêu cầu mới đã sửa; không sửa trực tiếp thông tin trước khi được duyệt.
5. Người hướng dẫn giải thích kiểm tra snapshot: nếu HR đã cập nhật trường gốc trong lúc yêu cầu chờ, yêu cầu cũ không được áp dụng.

**Đạt khi:** nhân viên tạo đúng yêu cầu; HR chỉ duyệt đúng quyền; học viên nêu được rằng chỉ ba trường trong danh sách hiện được hỗ trợ và thông tin chỉ đổi sau khi duyệt.

## 6. Bổ sung cho Nhân sự — 90 phút

- Thực hành tạo nhân viên demo với mã duy nhất, đơn vị, quản lý, ngày hiệu lực và trạng thái.
- Tạo hợp đồng demo, kiểm tra loại/số/ngày/lương/trạng thái.
- Ghi một thay đổi có ngày hiệu lực tương lai; xác nhận không áp dụng sớm.
- Xem quy trình ứng viên/đề xuất tuyển dụng; phân biệt đề xuất với nhu cầu đã duyệt.
- Kiểm tra ngày lễ/lịch và thảo luận ảnh hưởng tới số ngày nghỉ, chấm công.
- Tập xử lý yêu cầu sửa CCCD/mã thuế/email: xác minh căn cứ và giới hạn quyền truy cập.
- Hoàn tất bằng kiểm tra hồ sơ demo và ghi nhận người rà soát.

**Đạt khi:** không tạo trùng nhân viên; biết trường nào nhạy cảm; xử lý đúng ngày hiệu lực; biết không sửa lịch sử tùy tiện.

### Thực hành checklist onboarding/offboarding — 35 phút

**Đối tượng:** HR_OFFICER/HR_MANAGER; người được giao đầu việc; IT hỗ trợ phần tài khoản Admin và nhắc hạn.

1. Tài khoản có quyền Django Admin mở **Lifecycle → Checklist templates**; trình diễn một mẫu Onboarding và một mẫu Offboarding. Xác nhận mã mẫu, loại, các dòng, thứ tự, mã vai trò chịu trách nhiệm, số ngày lệch hạn và cờ liên quan đến tài sản. Đây là cấu hình demo; HR chỉ nhập mẫu nghiệp vụ sau khi đã thống nhất chính thức.
2. HR vào **Nhân sự → Onboarding / Offboarding** → **Mở checklist**, chọn nhân viên demo, đúng loại và mẫu. Với Offboarding nhập ngày hiệu lực; không dùng ngày thật nếu đây là môi trường đào tạo.
3. Mở chi tiết, giao một mục cho tài khoản đang hoạt động có đúng mã vai trò; xác nhận vai trò trên mẫu lọc danh sách người có thể nhận việc.
4. Người được giao mở checklist, đánh dấu một mục **Hoàn tất**; thử **Bỏ qua** một mục khác và xác nhận hệ thống yêu cầu lý do. HR theo dõi trạng thái và hạn.
5. Với mục liên quan tài sản, liên kết một bản ghi cấp phát demo đã tồn tại. Không tạo/xóa lịch sử tài sản trong checklist. Chỉ thử Offboarding khi có bản ghi thu hồi phù hợp.
6. Trình diễn sửa một dòng trong mẫu rồi xác nhận checklist đã mở không bị thay đổi (bản chụp theo hồ sơ).
7. IT/HR xem số cảnh báo quá hạn trên dashboard. Nếu cần thử lệnh nhắc, chỉ chạy trên dữ liệu demo: `python src\manage.py send_lifecycle_reminders`. Không khẳng định đã có nhắc tự động hằng ngày cho đến khi Task Scheduler được IT cấu hình và kiểm tra.

**Đạt khi:** HR mở hồ sơ đúng loại mà không tạo trùng; đầu việc giao đúng vai trò; người được giao chỉ cập nhật việc của mình; bỏ qua có lý do; lịch sử tài sản được giữ nguyên.

**Việc sau buổi học:** HR xác nhận nội dung hai mẫu và người chịu trách nhiệm; IT xác nhận quyền Admin và quyết định khi nào lên lịch lệnh nhắc. Chưa nhập mẫu chính thức nếu nghiệp vụ chưa duyệt.

## 7. Thực hành hồ sơ có tệp đính kèm — 30 phút

Dành cho Nhân sự, văn thư và người được giao quản lý hồ sơ. Chỉ dùng môi trường đào tạo cùng tài khoản demo; IT chuẩn bị một tệp giả không chứa dữ liệu thật.

1. Tạo hoặc mở bản ghi công văn/đơn nghỉ phép demo theo vai trò được cấp.
2. Đính kèm tệp giả từ màn hình IHRMS, lưu bản ghi và ghi nhận mã hồ sơ.
3. Mở lại liên kết tệp từ bản ghi IHRMS; xác nhận đúng nội dung và có quyền truy cập.
4. Người hướng dẫn/IT kiểm tra tệp nằm trong thư viện `Documents` và đúng thư mục nghiệp vụ đã cấu hình, ví dụ `CongVanDen`, `CongVanDi` hoặc `DonNghiPhep`.
5. Thử bằng một tài khoản không được cấp quyền phù hợp nếu môi trường có sẵn; học viên phải dừng lại khi bị từ chối, không tìm cách mở trực tiếp bằng URL khác.
6. Ghi cách báo lỗi nếu upload hoặc xem tệp thất bại. Không xóa tệp hồ sơ từ SharePoint; việc xóa/retention do người quản trị xử lý theo chính sách.

**Đạt khi:** đính kèm được tệp demo, mở lại đúng tệp trong IHRMS, chỉ ra được kênh báo sự cố và không chia sẻ liên kết/tệp ra ngoài phạm vi.

## 8. Bổ sung cho Tài chính — 120 phút

Chỉ dùng kỳ và số liệu demo. Người hướng dẫn phải có người rà soát nghiệp vụ đồng hành.

1. Tạo kỳ lương demo, bổ sung bảng lương còn thiếu.
2. Kiểm tra công đã duyệt, hợp đồng/lương hiệu lực, người phụ thuộc, cấu hình thuế/bảo hiểm và các khoản phụ cấp/tăng ca/khấu trừ.
3. Chạy tính lương; đọc các cột Lương CB, Lương đóng BH, Phụ cấp, Tăng ca, TC miễn thuế, Khấu trừ khác, Gross, Bảo hiểm, Thuế, Net.
4. Đối chiếu một nhân viên và tổng kỳ với bảng tính kiểm soát do công ty phê duyệt.
5. Thực hành phát hiện một sai lệch demo và ghi cách xử lý; chưa khóa.
6. Trình diễn **Khóa kỳ lương** và **Phát hành phiếu lương PDF** trên kỳ demo đã được duyệt, giải thích khóa là bước chốt và phiếu là dữ liệu mật.
7. Cấu hình hiệu lực: thêm bản ghi mới theo ngày hiệu lực; không chỉnh cấu hình quá khứ để tác động kỳ đã chốt.

**Điểm kiểm soát:** luôn rà soát độc lập trước khóa; xác minh đúng kỳ; chỉ người được ủy quyền khóa/phát hành. Quy tắc tính pháp lý cần được bộ phận chuyên môn xác nhận.

Sau khi khóa kỳ, một số người nhận thông báo trong IHRMS có thể thấy **Mở thư nháp trong Outlook**. Nếu trình diễn, dùng kỳ demo: mở nháp, kiểm tra người nhận/nội dung, tự gửi trong Outlook theo quy trình email nội bộ, rồi mới xác nhận **Đã gửi qua Outlook**. Không xác nhận nếu chưa gửi thật. IHRMS không gửi thư tự động. Báo cáo BHXH, PIT và chi phí lương theo phòng ban chưa được bật; không dùng khung kỹ thuật làm đầu ra nghiệp vụ.

## 9. Kiểm tra nhanh và tiêu chí hoàn thành

Hỏi ngẫu nhiên:
- Đơn nghỉ “chờ duyệt” có cho phép nghỉ ngay không?
- Bạn xử lý thế nào nếu bảng công đã duyệt bị sai?
- Nhân viên có được xem phiếu lương đồng nghiệp không?
- Trước khi khóa kỳ lương cần đối chiếu những gì?
- IT cần thông tin nào để tái hiện lỗi; thông tin nào tuyệt đối không gửi?
- Khi tệp SharePoint báo lỗi, người dùng nên tự xóa/thử gửi nhiều lần hay ghi mã hồ sơ và báo IT?

**Hoàn thành:** học viên thực hiện đúng tác vụ cốt lõi theo vai trò, trả lời đúng ít nhất 4/6 câu, biết kênh hỗ trợ và không vi phạm bảo mật. Người chưa đạt được kèm 1:1 và thực hành lại; lưu kết quả theo quy trình đào tạo.

### Phiếu xác nhận

| Trường | Ghi nhận |
|---|---|
| Họ tên/mã nhân viên | |
| Bộ phận/vai trò | |
| Ngày và người hướng dẫn | |
| Bài thực hành hoàn tất | Đạt / Cần kèm thêm |
| Nội dung cần đào tạo lại | |
| Xác nhận học viên/người hướng dẫn | |

## 10. Kịch bản hỗ trợ sau đào tạo

Yêu cầu gửi: người báo/mã NV; thời điểm; menu/URL; bước thao tác; kết quả mong đợi và thực tế; thông báo lỗi; mức ảnh hưởng. Che dữ liệu cá nhân khi chụp ảnh. Không yêu cầu học viên gửi mật khẩu, SECRET_KEY, chuỗi kết nối hay bản PDF lương qua kênh chung.

## 11. Danh sách trước khi đào tạo diện rộng

- [ ] Chủ quy trình đã xác nhận luồng và hạn xử lý.
- [ ] Tài khoản và quyền từng nhóm đã được kiểm tra.
- [ ] Dữ liệu demo không chứa dữ liệu thật.
- [ ] Môi trường, PDF, thông báo và các luồng trình diễn hoạt động.
- [ ] Tài khoản demo có quyền SharePoint phù hợp; thư mục upload đúng nghiệp vụ; tệp giả được chuẩn bị sẵn.
- [ ] Mẫu onboarding/offboarding demo và người chịu trách nhiệm đã được HR rà soát; người cấu hình có quyền Admin.
- [ ] Người hướng dẫn đã giải thích trạng thái email nháp Outlook, xác nhận gửi thủ công và tình trạng Task Scheduler.
- [ ] Báo cáo tuân thủ chưa bật được nói rõ; không dùng dữ liệu demo để tạo biểu mẫu pháp lý.
- [ ] Người hỗ trợ nghiệp vụ và IT đã được phân công.
- [ ] Cẩm nang, giáo án, phiếu điểm danh và phản hồi đã sẵn sàng.
- [ ] Các nội dung chưa được quyết định đã được nêu rõ thay vì hướng dẫn như chính sách.
