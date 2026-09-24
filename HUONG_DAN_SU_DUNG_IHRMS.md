# Hướng dẫn sử dụng IHRMS

**Đối tượng:** nhân viên, quản lý bộ phận, Nhân sự, Kế toán và quản trị hệ thống tại công ty 30–50 người.  
**Phiên bản tài liệu:** 23/09/2026. Tên menu có thể thay đổi nhẹ theo quyền tài khoản và bản phát hành.

## 1. IHRMS dùng để làm gì?

IHRMS là cổng nội bộ để xem/cập nhật hồ sơ cá nhân, chấm công, xin nghỉ, theo dõi công việc và các dịch vụ nội bộ. Nhân sự và Kế toán có thêm màn hình nghiệp vụ được phân quyền. Quản trị hệ thống cấp tài khoản và cấu hình danh mục.

Hệ thống có hai địa chỉ:

- **Cổng nhân viên:** `/portal/` — dùng hàng ngày.
- **Quản trị:** `/admin/` — dành cho người được giao nghiệp vụ quản trị; không chia sẻ tài khoản này cho nhân viên thông thường.

Chỉ truy cập qua địa chỉ HTTPS nội bộ do IT cung cấp khi hệ thống đã triển khai chính thức. Địa chỉ `127.0.0.1:8000` trong tài liệu kỹ thuật chỉ dùng trên máy phát triển.

## 2. Vai trò và trách nhiệm

| Vai trò | Việc thường làm |
|---|---|
| Nhân viên | Kiểm tra hồ sơ, nhập chấm công nếu được yêu cầu, gửi đơn nghỉ, cập nhật công việc, xem phiếu lương đã phát hành của mình. |
| Trưởng bộ phận | Duyệt đơn nghỉ/chấm công trong phạm vi được giao; giao việc, cập nhật KPI hoặc gửi đề xuất tuyển dụng nếu chức năng được bật cho vai trò. |
| HR Manager / HR Officer | Quản lý hồ sơ nhân sự, hợp đồng, ngày lễ, hạn mức nghỉ; xử lý nghiệp vụ và báo cáo theo quyền. HR Manager có quyền duyệt phạm vi công ty ở một số quy trình. |
| Finance Officer | Quản lý dữ liệu lương được phép xem, lập/tính/đối soát kỳ lương và phát hành phiếu lương. |
| Director | Xem báo cáo và duyệt một số quy trình được ma trận phân quyền cho phép. |
| SYS_ADMIN / SUPER_ADMIN | Quản trị kỹ thuật, tài khoản, vai trò và cấu hình; chỉ cấp cho người phụ trách hệ thống. |

Quyền thực tế do vai trò trên tài khoản quyết định. Không dùng cách bật `is_staff` hoặc chia sẻ tài khoản chung để cấp quyền nghiệp vụ.

## 3. Đăng nhập và bảo vệ tài khoản

1. Mở đường dẫn IHRMS nội bộ, nhập tên đăng nhập và mật khẩu do HR/IT cấp.
2. Khi đăng nhập lần đầu, đổi sang mật khẩu riêng theo chính sách công ty. Không gửi mật khẩu qua nhóm chat và không lưu trên máy dùng chung.
3. Chọn **Đăng xuất** khi dùng xong, đặc biệt trên máy dùng chung.
4. Nếu chưa liên kết được hồ sơ nhân viên, không tự tạo tài khoản khác; liên hệ HR/IT để gắn tài khoản đúng hồ sơ.
5. Nếu quên mật khẩu hoặc nghi ngờ bị lộ, báo IT để khóa/đặt lại tài khoản.

## 4. Công việc của nhân viên

### Hồ sơ cá nhân

Vào **Hồ sơ** để kiểm tra thông tin cá nhân, liên hệ, phòng ban và chức danh. Báo HR khi thông tin pháp lý, tài khoản ngân hàng hoặc thông tin người phụ thuộc cần điều chỉnh. Không nhập dữ liệu nhạy cảm vào ghi chú không dành cho mục đó.

### Chấm công

Vào **Bảng công**, chọn tháng cần xem. Nhập/sửa dòng công theo quy trình nội bộ; lưu ý thời gian, dự án và số giờ. Nếu đơn vị yêu cầu khai báo tổng hợp ngày nghỉ, nhập đúng số ngày theo từng loại và lưu. Gửi quản lý/HR xử lý tổng hợp trước hạn chốt công. Sau khi được duyệt, báo người có quyền nếu cần sửa sai; không tự gửi bản ghi thay thế để né bước duyệt.

### Nghỉ phép

1. Chọn **Nghỉ phép** → **Tạo đơn mới**.
2. Chọn loại nghỉ, ngày bắt đầu/kết thúc và lý do ngắn gọn.
3. Kiểm tra số ngày hệ thống tính, gửi đơn và theo dõi trạng thái.
4. Chỉ nghỉ sau khi đơn được duyệt, trừ tình huống khẩn cấp theo quy định công ty; khi đó báo quản lý/HR theo kênh khẩn cấp.
5. Nếu ngày nghỉ hoặc loại nghỉ sai, liên hệ người duyệt/HR để xử lý; không gửi đơn chồng lấn.

### Công việc, KPI và dịch vụ văn phòng

- **Công việc:** xem hạn hoàn thành, cập nhật trạng thái và trao đổi trong phần bình luận của công việc.
- **KPI:** xem chỉ tiêu/kết quả được giao; chỉ người có quyền mới được chấm hoặc sửa.
- **Phòng họp/Đặt xe/VPP:** gửi yêu cầu với thời gian, mục đích và số lượng chính xác; chờ xác nhận/cấp phát trước khi sử dụng.
- **Tài liệu:** chỉ xem/tải tài liệu bạn được cấp quyền; không gửi file nội bộ cho bên ngoài nếu chưa được phê duyệt.

### Phiếu lương PDF

Vào **Phiếu lương** để xem các kỳ đã được khóa và phát hành. Mở phiếu của đúng kỳ rồi tải PDF. Phiếu chỉ dành cho cá nhân đăng nhập; không tải hộ hoặc chuyển tiếp qua email cá nhân. Nếu kỳ chưa xuất hiện, hỏi Kế toán xem kỳ đã khóa/phát hành chưa.

## 5. Công việc của quản lý bộ phận

- Kiểm tra người gửi và phạm vi nhân viên trước khi duyệt nghỉ/chấm công.
- Duyệt hoặc từ chối kèm lý do rõ ràng; xử lý đơn tồn trước hạn chốt công/lương.
- Theo dõi công việc được giao; không dùng tài khoản nhân viên để tự duyệt.
- Báo HR khi có điều chuyển/bổ nhiệm. Ngày hiệu lực trên quyết định cần chính xác; hệ thống áp dụng theo ngày đó.
- Chỉ xem dữ liệu thuộc phạm vi quản lý được cấp.

## 6. Quy trình Nhân sự

### Nhận nhân viên mới

1. Tạo hồ sơ chính xác, kiểm tra mã nhân viên và thông tin bắt buộc.
2. Tạo/cấp tài khoản riêng và gắn đúng hồ sơ nhân viên; cấp role tối thiểu cần thiết.
3. Khai báo phòng ban, chức danh, ngày vào làm, hợp đồng và mức lương theo phân quyền.
4. Cấp hạn mức nghỉ năm cho từng năm cần sử dụng; kiểm tra ngày lễ/lịch làm việc.
5. Hướng dẫn nhân viên đăng nhập, chấm công, xin nghỉ và tải phiếu lương.

### Điều chuyển, bổ nhiệm, nghỉ việc

Nhập sự kiện với ngày hiệu lực trên quyết định. Kiểm tra lại hồ sơ nhân viên sau khi đến ngày áp dụng. Khi nghỉ việc, khóa/thu hồi tài khoản đúng thời điểm, thu hồi thiết bị và rà soát quyền truy cập; không xóa hồ sơ lịch sử nếu cần bảo lưu theo chính sách công ty.

### Kiểm tra định kỳ

Đầu mỗi năm cập nhật ngày lễ, lịch làm việc và hạn mức phép; hàng tháng xử lý công/đơn nghỉ tồn; định kỳ rà soát tài khoản không còn sử dụng, role và hồ sơ thiếu dữ liệu.

## 7. Quy trình Kế toán: chốt kỳ lương và phát hành phiếu

1. Kiểm tra dữ liệu công đã được duyệt, nhân viên đang làm, ngày hiệu lực lương, người phụ thuộc và cấu hình thuế/bảo hiểm của kỳ.
2. Vào phần **Lương** → chọn kỳ đúng tháng/năm.
3. Tạo các dòng nhân viên còn thiếu; kiểm tra không bỏ sót trường hợp đi làm/nghỉ giữa kỳ theo chính sách.
4. Chạy **Tính lương toàn bộ kỳ**; rà soát gross, bảo hiểm, thuế, khấu trừ và net từng người.
5. Đối chiếu báo cáo/tệp kiểm soát ngoài hệ thống và xin người có thẩm quyền kiểm tra trước khi khóa.
6. Chỉ bấm **Khóa kỳ lương** sau khi được duyệt. Khóa kỳ không phải nút thử; dữ liệu khóa không chỉnh sửa theo luồng thông thường.
7. Hệ thống tạo phiếu lương khi khóa kỳ. Nếu một kỳ đã khóa từ trước còn thiếu phiếu, dùng hành động phát hành PDF của kỳ đó sau khi xác minh danh sách.
8. Nhân viên tải phiếu tại **Phiếu lương**. Xử lý sai lệch qua quy trình điều chỉnh có phê duyệt, không sửa trực tiếp PDF.

Công thức và mức thuế/bảo hiểm phải được Finance/đơn vị tư vấn xác nhận trước khi dùng trả lương thật.

## 8. Quản trị tài khoản và dữ liệu

- Mỗi người một tài khoản; không dùng tài khoản dùng chung.
- Cấp role theo công việc, rà soát tối thiểu khi nhân viên chuyển bộ phận và khi nghỉ việc.
- Tạo tài khoản: xác minh yêu cầu của HR, tạo user, gắn Employee, cấp role, thử đăng nhập bằng tài khoản người dùng.
- Khóa tài khoản khi chấm dứt quan hệ lao động hoặc khi có sự cố; giữ hồ sơ theo chính sách lưu trữ.
- Xóa mềm có thể ẩn bản ghi khỏi danh sách thường và có thể khôi phục qua Admin. Chỉ dùng hành động xóa sau khi xác minh; không dùng xóa vật lý cho dữ liệu nghiệp vụ.
- Không xuất hoặc chia sẻ danh sách lương/hồ sơ ra ngoài nhóm được phép.

## 9. Sao lưu và khôi phục — dành cho IT

Thực hiện theo lịch vận hành đã được duyệt: sao lưu database và thư mục file tải lên `media/` tới vị trí độc lập, giới hạn quyền và mã hóa theo chính sách. Theo dõi kết quả mỗi lần chạy. Định kỳ khôi phục **bản sao** lên SIT và kiểm tra đăng nhập, hồ sơ, file đính kèm, chấm công và phiếu lương. Không thử restore đè lên production. Ghi lại thời điểm, người thực hiện và kết quả.

## 10. Xử lý sự cố

| Hiện tượng | Việc cần làm |
|---|---|
| Không đăng nhập được | Kiểm tra địa chỉ nội bộ/tài khoản; liên hệ IT nếu mật khẩu bị khóa hoặc quên. |
| Không thấy menu | Role có thể không bao gồm chức năng; gửi HR/IT tên chức năng và công việc cần thực hiện. |
| Sai hồ sơ, chấm công, nghỉ phép | Gửi mã nhân viên, kỳ/ngày và mô tả cho HR; không gửi dữ liệu lương vào nhóm chung. |
| Kỳ lương sai hoặc PDF sai người | Báo ngay Finance và IT; tạm ngừng tải/chia sẻ các phiếu liên quan; không tự sửa dữ liệu đã khóa. |
| Tệp tải lên lỗi | Kiểm tra dung lượng/định dạng và thử lại; nếu lỗi tiếp diễn, gửi tên module và thời điểm cho IT, không gửi file nhạy cảm qua kênh không an toàn. |
| Hệ thống không truy cập được | Báo IT thời điểm, địa chỉ đã dùng và ảnh lỗi đã che dữ liệu cá nhân; không chạy lệnh server/database. |

## 11. Hỗ trợ

Khi báo sự cố, cung cấp: tên tài khoản/mã nhân viên, module, ngày giờ, thao tác ngay trước lỗi và mã kỳ/đơn liên quan. Không gửi mật khẩu, SECRET_KEY, số định danh cá nhân đầy đủ hoặc phiếu lương vào ticket không bảo mật.

Tài liệu này mô tả chức năng hiện có trong bản IHRMS đã rà soát; tích hợp hoặc chức năng chưa được nghiệm thu ở công ty không nên coi là quy trình chính thức.
