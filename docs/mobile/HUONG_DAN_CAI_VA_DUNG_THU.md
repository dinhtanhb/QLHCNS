# Cài và dùng thử IHRMS trên điện thoại Android

**Dành cho người không lập trình. Bạn không cần cài công cụ lập trình hoặc gõ lệnh.**

Làm theo thứ tự: nhận file → cài ứng dụng → đăng nhập → thử chức năng → gửi kết quả.

File hiện có là **IHRMS QA**, tức bản dùng thử. Chỉ dùng tài khoản thử và dữ liệu giả được cấp. Cài xong ứng dụng chưa đủ: máy tính cung cấp dữ liệu IHRMS cũng cần bật và kết nối được.

## 1. Cần nhận những gì?

Nhờ người phụ trách gửi đủ:

- File **IHRMS-QA.apk**, khoảng **54 MB**. Đây là file cài ứng dụng Android.
- **Địa chỉ IHRMS dùng thử** để nhập vào ứng dụng.
- **Tên đăng nhập và mật khẩu thử của nhân viên**.
- **Tên đăng nhập và mật khẩu thử của quản lý**, có quyền duyệt đơn cho nhân viên trên.
- Cách liên hệ người hỗ trợ khi có lỗi.

Nhân viên và quản lý có thể thử lần lượt trên một điện thoại bằng cách đăng xuất rồi đăng nhập lại. Nếu thiếu địa chỉ hoặc tài khoản, hãy nhờ người phụ trách chuẩn bị trước; không tự dùng tài khoản nhân viên thật.

Các tài khoản trong cùng bộ demo mới dùng chung một mật khẩu gồm **10 ký tự chữ thường và số**, không có dấu cách hoặc ký tự đặc biệt. Nhập đúng mật khẩu người phụ trách cấp; mỗi lần tạo bộ demo mới có thể có mật khẩu khác. Mật khẩu này chỉ dùng cho dữ liệu thử.

File đã tạo nằm trên máy tính phát triển tại:

```text
D:\IHRMS_Review_Exports\Mobile_20261028\apk\IHRMS-QA.apk
```

Đây là vị trí trên máy tính, không phải địa chỉ để nhập vào điện thoại. Người phụ trách cần chuyển file cho bạn qua USB hoặc kênh chia sẻ nội bộ của công ty.

## 2. Cài ứng dụng

1. Nhận hoặc tải **IHRMS-QA.apk** xuống điện thoại Android.
2. Mở **Tệp**, **File của bạn** hoặc **Quản lý tệp** trên điện thoại.
3. Vào **Tải xuống / Downloads**, chạm **IHRMS-QA.apk**. Nếu lưu nơi khác, mở thư mục đó.
4. Nếu điện thoại hỏi cho phép cài từ nguồn này, mở **Cài đặt** trên thông báo đó, bật **Cho phép từ nguồn này**, rồi quay lại. Tên mục có thể khác tùy máy.
5. Chọn **Cài đặt**, chờ hoàn tất, rồi chọn **Mở**.
6. Những lần sau, tìm biểu tượng **IHRMS QA** trong danh sách ứng dụng.
7. Sau khi cài, có thể tắt lại quyền cho phép cài từ nguồn đó.

**Kết quả đúng:** mở được màn hình có ô địa chỉ IHRMS, tên đăng nhập và mật khẩu.

APK chỉ dùng cho Android, không cài được trên iPhone. Nếu bị chặn hoặc báo không tương thích, gửi nguyên thông báo cho người hỗ trợ; không tắt các biện pháp bảo vệ chung của máy.

## 3. Kết nối và đăng nhập

Khi người phụ trách dùng máy tính làm máy chủ thử:

1. Kết nối điện thoại với **cùng mạng Wi-Fi của máy tính chạy IHRMS thử**.
2. Nhờ người phụ trách xác nhận IHRMS đã được bật và máy tính không ngủ.
3. Mở **IHRMS QA**, nhập nguyên **Địa chỉ IHRMS** được cấp, gồm cả `http://` hoặc `https://` và số cổng nếu có.

Ví dụ minh họa:

```text
http://192.168.1.20:8789
```

**Không chép nguyên ví dụ nếu người phụ trách chưa cấp đúng địa chỉ đó.** Không thêm `/portal/`, tên file APK hoặc khoảng trắng cuối địa chỉ. Khi kết nối qua Wi-Fi, không tự nhập `localhost` hay `127.0.0.1`: trên điện thoại, chúng chỉ chính điện thoại, không phải máy tính.

4. Nhập tài khoản thử **của nhân viên** và mật khẩu được cấp.
5. Chạm **Đăng nhập** một lần và chờ.

**Kết quả đúng:** thấy **Trang chủ** với số liệu tóm tắt. Tab **Tôi** mở thông tin hồ sơ; Cài đặt nằm trong tab này. Nếu ứng dụng báo tài khoản chưa gắn hồ sơ, nhờ người phụ trách chuẩn bị lại tài khoản trước khi thử nghỉ phép.

Máy chủ chỉ hoạt động trong Wi-Fi nội bộ có thể không truy cập được qua 4G/5G. Phần truy cập ngoài công ty cần người kỹ thuật cấu hình riêng.

**Lưu ý về số cổng:** `8789` và `8790` là hai môi trường thử riêng. Phải dùng đúng cổng do người phụ trách cấp, không trộn tài khoản của bộ demo này với máy chủ của bộ khác. Với bộ demo 10 ký tự được tạo ngày 28/10, người phụ trách đang dùng cổng **8790**. IP máy tính có thể đổi khi đổi Wi-Fi hoặc khởi động lại, nên cần xác nhận lại địa chỉ.

## 4. Thử từng chức năng

### A. Xem thông tin cá nhân

Chạm **Tôi** ở thanh dưới cùng. Kiểm tra tên, mã nhân viên, phòng ban, email và quỹ phép nếu đã được cấp.

**Đúng khi:** dữ liệu thuộc nhân viên thử đang đăng nhập. Nếu chưa có hạn mức, ứng dụng báo chưa được cấp quỹ phép.

### Trang chủ và nghiệp vụ

Trang chủ có các ô số liệu; chạm từng ô để mở danh sách tương ứng. Nếu có nhiều ngày chấm công, biểu đồ cột thể hiện tối đa 7 bản ghi gần nhất; nếu mới có một bản ghi, ứng dụng hiện ngày và số giờ gần nhất. Mở **Nghiệp vụ** để xem các nhóm; chạm tên nhóm để bung/thu danh sách.

Admin, Trung tâm Báo cáo Excel và các màn hình cần thao tác máy tính không hiện trong menu mobile. Dùng bản web cho những việc đó.

### B. Chấm công

Chạm **Chấm công**, xem ngày, trạng thái, giờ vào/ra và số giờ nếu có. Chạm **Tải lại**.

**Đúng khi:** thấy dữ liệu của nhân viên thử. Nếu chưa có dữ liệu, ứng dụng báo chưa có chấm công. Nhờ người phụ trách xác nhận đã chuẩn bị dữ liệu nào cho bạn.

### C. Nhân viên gửi đơn nghỉ

1. Chạm **Nghỉ phép → Tạo đơn nghỉ phép**.
2. Chọn loại nghỉ được người phụ trách hướng dẫn thử.
3. Nhập từ ngày và đến ngày theo dạng **ngày/tháng/năm**, ví dụ `02/11/2026`. Chọn ngày làm việc chưa có đơn trùng, nằm trong quỹ phép được cấp.
4. Nhập lý do dễ nhận biết: **“Kiểm thử điện thoại — đơn số 1”**.
5. Chạm **Gửi đơn nghỉ phép** một lần.

**Đúng khi:** có thông báo đã gửi, trở về danh sách nghỉ phép; đơn có đúng ngày/lý do và trạng thái **Chờ duyệt**.

Nếu chờ lâu hoặc mất mạng sau khi bấm gửi, mở lại danh sách và **Tải lại** trước khi gửi tiếp: máy chủ có thể đã nhận đơn dù điện thoại chưa hiện kết quả.

### D. Quản lý duyệt đơn

1. Chạm **Tôi → Đăng xuất → Xác nhận**.
2. Đăng nhập tài khoản **quản lý thử** được cấp.
3. Chạm **Duyệt đơn**. Không thấy mục này thì nhờ người phụ trách kiểm quyền tài khoản.
4. Tìm đúng tên nhân viên, ngày nghỉ và lý do đã nhập ở bước C. Có thể cần cuộn hoặc chuyển trang.
5. Chạm **Duyệt đơn #…**, kiểm tra thông tin rồi chọn **Xác nhận**.

**Đúng khi:** có thông báo đã xử lý; đơn đó không còn trong danh sách chờ duyệt.

### E. Nhân viên kiểm tra kết quả

1. Đăng xuất quản lý, đăng nhập lại nhân viên thử.
2. Mở **Nghỉ phép → Tải lại**, tìm đơn vừa gửi.
3. Kiểm tra trạng thái **Đã duyệt**.
4. Mở **Thông báo**, tìm thông báo đơn nghỉ được duyệt.
5. Chạm **Mở thông báo #…**. Sau đó quay lại mục Thông báo kiểm tra mục vừa mở đã được đánh dấu đọc.

**Đúng khi:** đơn và thông báo khớp quyết định của quản lý; nút mở thông báo về đơn nghỉ đưa tới danh sách nghỉ phép.

### F. Thử từ chối một đơn khác

Lặp bước C với ngày làm việc khác và lý do **“Kiểm thử điện thoại — đơn số 2”**. Đăng nhập quản lý, chọn **Từ chối đơn #…** của đúng đơn mới rồi xác nhận. Đăng nhập lại nhân viên, kiểm tra trạng thái **Từ chối**.

Không dùng đơn đã duyệt ở bước D để thử từ chối.

## 5. Thử những tình huống thường gặp

**Ngày không hợp lệ:** tạo đơn mới, nhập ngày kết thúc trước ngày bắt đầu. Khi gửi, ứng dụng phải báo lỗi và không tạo đơn đó.

**Trùng ngày:** thử gửi đơn trùng với đơn đang chờ hoặc đã được duyệt của chính nhân viên thử. Ứng dụng phải báo trùng và không tạo thêm đơn trùng.

**Mất mạng:** khi đang xem dữ liệu, tắt Wi-Fi và dữ liệu di động. Ứng dụng phải báo không có kết nối và không thể gửi/duyệt. Bật lại đúng Wi-Fi thử, mở lại mục cần xem. Đơn chưa gửi không được tự gửi thay bạn.

**Sáng/tối:** vào Cài đặt điện thoại → Màn hình, chuyển giữa sáng và tối rồi quay lại IHRMS. Kiểm chữ, ô nhập và thanh dưới cùng đọc được, không bị che. Tên mục cài đặt có thể khác trên từng máy.

**Đăng xuất:** chọn Tôi → Đăng xuất → Xác nhận. Ứng dụng phải trở về màn hình đăng nhập.

**Hết phiên:** nếu ứng dụng báo phiên đã hết hạn, đăng nhập lại. Điều này có thể bình thường sau thời gian không sử dụng; không cần gỡ app. Muốn thử riêng tình huống này, nhờ người phụ trách hướng dẫn thời gian chờ.

## 6. Nếu gặp lỗi

**Không kết nối được:** kiểm Wi-Fi, địa chỉ đã nhập và máy tính chạy IHRMS có còn bật không. Nếu vẫn lỗi, báo người hỗ trợ kiểm máy chủ/mạng; không tự đổi cấu hình bảo mật.

Để phân biệt lỗi mạng và lỗi ứng dụng, mở Chrome trên điện thoại, nhập **cùng địa chỉ IHRMS được cấp**. Nếu trang cũng không mở, người hỗ trợ cần kiểm IP/cổng, server có cho điện thoại kết nối không và tường lửa; chưa phải lỗi mật khẩu. Cùng tên Wi-Fi vẫn có thể không kết nối giữa các máy nếu dùng mạng khách hoặc Wi-Fi có chế độ cách ly thiết bị.

**Sai tài khoản/mật khẩu:** kiểm chữ hoa và khoảng trắng. Không thử liên tục nhiều lần vì tài khoản có thể tạm bị khóa. Nhờ người hỗ trợ xác nhận lại tài khoản thử.

**Không thấy đơn chờ duyệt:** kiểm đã đăng nhập quản lý thử, đơn còn chờ và quản lý đó được giao quản lý nhân viên đã gửi. Thử Tải lại, cuộn hoặc chuyển trang rồi báo người hỗ trợ nếu vẫn thiếu.

**Không cài được APK:** gửi nguyên thông báo, tên máy và phiên bản Android cho người hỗ trợ kiểm file/tính tương thích. Không gỡ bản khác có dữ liệu cần giữ nếu chưa được hướng dẫn.

**Không thấy thông báo ngoài màn hình điện thoại:** bản hiện tại chưa được kiểm nhận thông báo đẩy thật. Hãy kiểm **Thông báo bên trong IHRMS** theo bước E; hai loại thông báo này khác nhau.

## 7. Gửi kết quả dùng thử

Sao chép mẫu dưới đây, điền **Đạt**, **Lỗi** hoặc **Chưa thử**:

```text
Ngày thử:
Tên điện thoại:
Phiên bản Android (Cài đặt → Giới thiệu điện thoại):
File đã cài: IHRMS-QA.apk

Cài ứng dụng:
Đăng nhập nhân viên:
Xem hồ sơ / chấm công:
Nhân viên gửi đơn:
Quản lý duyệt đơn:
Nhân viên thấy kết quả và thông báo:
Từ chối một đơn khác:
Chặn ngày sai / trùng ngày:
Mất mạng và kết nối lại:
Sáng / tối:
Đăng xuất:

Nếu có lỗi:
- Tôi đang ở màn hình nào:
- Tôi đã bấm/nhập gì:
- Thông báo ứng dụng hiện ra:
- Kết quả tôi mong thấy:
```

Có thể gửi ảnh lỗi nhưng che mật khẩu, thông tin cá nhân và dữ liệu không liên quan. Không gửi mật khẩu trong báo cáo.

## Dành riêng cho người phụ trách kỹ thuật

Chuẩn bị máy chủ, tài khoản thử, file cài và địa chỉ theo [hướng dẫn kỹ thuật](KY_THUAT_TEST_LOCAL_APK.md). Kiểm tra tính toàn vẹn APK trước khi gửi; xác nhận quản lý thử được duyệt đúng nhân viên thử. Người dùng điện thoại không cần chạy các lệnh trong tài liệu kỹ thuật.

Việc đăng ký tài khoản tổ chức và phát hành Android/iPhone nằm trong [hướng dẫn phát hành](TAO_TAI_KHOAN_VA_PHAT_HANH.md).
