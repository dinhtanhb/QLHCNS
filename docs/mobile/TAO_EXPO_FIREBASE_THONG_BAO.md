# Tạo Expo và Firebase để thử thông báo trên Android

**Dành cho người chưa có tài khoản, thao tác bằng trình duyệt trên máy tính.** Làm trước cho bản **IHRMS QA** trên Android. Chưa cần đăng ký Google Play hoặc Apple Developer để thực hiện phần Android này.

Sau khi làm xong, người kỹ thuật vẫn cần cấu hình và tạo **APK mới**. Chỉ tạo tài khoản không làm APK đang cài tự có thông báo.

## Chuẩn bị

- Email công ty hoặc tài khoản được công ty giao quản lý; có quyền nhận thư xác minh.
- Tài khoản Google do tổ chức quản lý để dùng Firebase.
- Thư mục riêng trên máy, ngoài thư mục mã nguồn, ví dụ `D:\IHRMS_Private\push-qa`.

Không gửi mật khẩu, mã xác minh hoặc khóa dịch vụ trong chat. Nếu dịch vụ yêu cầu thanh toán, liên kết thẻ hoặc quyền quản trị mà bạn chưa được cấp, dừng ở bước đó và báo người phụ trách; không tự chọn mua gói.

## Bước 1 — Tạo tài khoản Expo

1. Mở [trang đăng ký Expo](https://expo.dev/signup).
2. Đăng ký bằng email được giao quản lý, đặt tên đăng nhập và mật khẩu riêng cho Expo.
3. Mở email để hoàn tất xác minh nếu được yêu cầu, rồi đăng nhập Expo.
4. Trong menu tài khoản, chọn **Create Organization** để tạo tổ chức của công ty. Điền tên, ví dụ **VietHealth**, và tên ngắn nếu được yêu cầu; nếu tên đã có người dùng thì chọn tên khác phù hợp.
5. Ghi lại tên ngắn của tổ chức (**organization slug**). Không chuyển tài khoản cá nhân thành tổ chức nếu không có nhu cầu.

**Đạt khi:** đã đăng nhập và thấy tổ chức vừa tạo. Cách tạo tổ chức và mời thành viên theo [hướng dẫn tài khoản của Expo](https://docs.expo.dev/accounts/account-types/). Chỉ mời người kỹ thuật có tài khoản cụ thể được công ty chỉ định; không chia sẻ mật khẩu.

## Bước 2 — Tạo dự án Expo cho bản QA

1. Trong dashboard, chuyển sang đúng tổ chức ở bước 1.
2. Nếu giao diện có nút tạo project, chọn tạo project mới, tên **IHRMS QA**, slug **ihrms-internal** nếu tên đó còn dùng được trong tổ chức.
3. Mở **Project settings → General** của project, tìm **Project ID** và ghi lại. Đây là chuỗi định danh project, không phải mật khẩu hay access token.

Nếu giao diện không có cách tạo hoặc không thấy Project ID, **dừng tại đây và báo đã tạo xong tổ chức**. Người kỹ thuật có thể liên kết project bằng EAS trên máy; bạn không cần tự tìm lệnh hoặc tải mã nguồn lên Expo.

**Cần bàn giao:** organization slug và Project ID nếu đã có. Không tạo **Access Token** chỉ để gửi cho người hỗ trợ.

## Bước 3 — Tạo dự án Firebase

1. Mở [Firebase Console](https://console.firebase.google.com/), đăng nhập Google bằng tài khoản được tổ chức giao quản lý.
2. Chọn **Create a project** hoặc **Add project**; tên nút có thể thay đổi theo ngôn ngữ/giao diện.
3. Đặt tên dễ nhận biết, ví dụ **IHRMS QA**. Ghi lại **Project ID** mà Firebase đề xuất hoặc bạn đã chọn.
4. Nếu được hỏi Google Analytics, đây không phải bước bắt buộc của luồng cấu hình FCM trong tài liệu này; có thể để chưa bật và tiếp tục. Không tạo database, nhập dữ liệu nhân sự hoặc bật đăng nhập Firebase: IHRMS vẫn dùng backend và tài khoản hiện có.
5. Đọc điều khoản, chỉ xác nhận nếu bạn được tổ chức cho phép; hoàn tất tạo project.

**Đạt khi:** vào được trang tổng quan của project Firebase. Tham khảo [hướng dẫn Android chính thức của Firebase](https://firebase.google.com/docs/android/setup).

## Bước 4 — Đăng ký ứng dụng Android và tải file cấu hình

1. Trong project Firebase, chọn biểu tượng **Android** hoặc **Add app → Android**.
2. Ở ô **Android package name**, nhập đúng:

```text
vn.ihrms.internal.qa
```

3. App nickname có thể đặt **IHRMS QA**. Nếu có ô SHA-1 tùy chọn, chưa cần tự nhập một giá trị bất kỳ; người kỹ thuật sẽ xử lý khi cần.
4. Chọn **Register app**.
5. Chọn **Download google-services.json** và lưu vào thư mục riêng đã chuẩn bị, giữ tên file **google-services.json**.
6. Các màn hình tiếp theo có thể hướng dẫn thêm SDK/Gradle vào mã nguồn. **Bạn không cần sửa mã hoặc làm các lệnh đó**; người kỹ thuật sẽ cấu hình Expo rồi build lại.

Package phân biệt chữ hoa/chữ thường và không đổi được cho app Firebase đã đăng ký; cần dùng đúng package QA phía trên, không bỏ `.qa`. File `google-services.json` chứa thông tin định danh cấu hình, **khác với file khóa bí mật** ở bước sau. Quy tắc dự án vẫn giữ cả hai file ngoài Git.

## Bước 5 — Chuẩn bị quyền gửi thông báo FCM

Phần này tạo khóa cho dịch vụ gửi thông báo, nên chỉ người được phép quản lý project thực hiện. Nếu không có quyền, nhờ quản trị viên hỗ trợ; không tìm cách vượt chính sách tổ chức.

1. Trong Firebase project, chọn biểu tượng bánh răng → **Project settings → Service accounts**.
2. Kiểm tra đúng project QA. Chọn **Generate new private key**, đọc cảnh báo rồi xác nhận **Generate key** nếu bạn được phép.
3. Lưu file JSON tải xuống vào thư mục riêng, ví dụ `D:\IHRMS_Private\push-qa`. **Đây là khóa bí mật**, không gửi qua chat/email nhóm, không đặt trong `D:\QLHCNS` và không chụp nội dung file.
4. Trong dashboard Expo của đúng project QA, mở **Project settings → Credentials**.
5. Ở Android, chọn hoặc thêm application identifier **vn.ihrms.internal.qa**.
6. Trong **Service credentials → FCM V1 service account key**, chọn **Add a service account key → Upload new key**.
7. Chọn file khóa JSON vừa tải, kiểm tra đúng project rồi **Save**. Bạn đang cấp khóa gửi thông báo cho Expo; chỉ thực hiện nếu tổ chức cho phép sử dụng dịch vụ này.

Nếu chưa có mục Credentials/project Expo, hoặc dịch vụ không cho tạo khóa, dừng và báo đúng bước đang vướng. Người kỹ thuật sẽ hướng dẫn bằng EAS hoặc phối hợp quản trị viên; không dùng “Legacy server key” thay cho FCM V1.

Các tên menu trên theo [hướng dẫn FCM V1 của Expo](https://docs.expo.dev/push-notifications/fcm-credentials/); nếu trang khác, ghi lại tên mục đang thấy, không tự chọn quyền Owner hoặc nới hạn chế API cho nhanh.

## Sau khi tạo xong — gửi lại thông tin nào?

Sao chép mẫu sau và điền các thông tin công khai/trạng thái:

```text
Expo organization slug:
Expo Project ID (nếu đã có):
Firebase Project ID:
Android package đã đăng ký: vn.ihrms.internal.qa
Đường dẫn google-services.json trên máy:
Khóa FCM V1 đã lưu an toàn trên máy: Có / Chưa
Khóa FCM V1 đã tải lên đúng project Expo: Có / Chưa
Đang vướng bước nào (nếu có):
```

**Không dán nội dung khóa, mật khẩu hoặc mã xác minh vào mẫu.** Nếu người kỹ thuật làm trên cùng máy, chỉ cần đường dẫn file; nếu khác máy, dùng kênh quản lý bí mật được công ty cho phép.

## Người kỹ thuật sẽ làm phần còn lại

- Kiểm đúng package/project và quyền FCM, liên kết Expo owner/project; không tự upload toàn repository hoặc chạy cloud build khi chưa chốt phạm vi.
- Đặt Project ID công khai vào `EXPO_PUBLIC_EAS_PROJECT_ID`, đường dẫn file Android vào `MOBILE_GOOGLE_SERVICES_FILE`, rồi build APK QA mới. Không đưa private key vào app.
- Bật dịch vụ gửi thông báo trên backend QA đúng đích, kiểm đăng ký token thiết bị và cấu hình dịch vụ; không chỉ bật một cờ rồi coi là hoàn tất.
- Cài APK mới, đăng nhập, vào **Tôi → Bật thông báo trên điện thoại** và chọn cho phép khi Android hỏi. Bản cũ có thể chưa có nút này vì chưa được cấu hình project.
- Thử nhân viên gửi đơn → HR nhận, HR duyệt/từ chối → nhân viên nhận khi đang mở, chạy nền và đóng app bình thường. Thử cả mở lời nhắc, đăng xuất/chuyển tài khoản và phiên hết hạn. **Chỉ xác nhận đạt sau khi nhận thông báo thật trên thiết bị.**

Thử bằng hai tài khoản trên hai thiết bị/phiên riêng sẽ rõ nhất; khi đăng xuất HR để đổi sang nhân viên trên cùng điện thoại, thiết bị không còn đăng ký nhận push cho tài khoản vừa đăng xuất. Cần mạng Internet cho Expo/Google; chỉ cùng Wi-Fi với PC không đủ. Nội dung lời nhắc dự kiến chỉ là “Bạn có cập nhật mới”, không hiện lý do nghỉ hay tên nhân viên. Android “Buộc dừng” và các hạn chế pin/thông báo của thiết bị có thể ngăn nhận cho đến khi mở lại app.

Đăng ký Expo/Firebase **không hoàn tất phần iPhone**: iOS còn cần tài khoản Apple/APNs và bản ký riêng. Xem [hướng dẫn phát hành](TAO_TAI_KHOAN_VA_PHAT_HANH.md).
