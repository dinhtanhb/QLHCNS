# Cài bản QA và thử lời nhắc Android

Chỉ dùng dữ liệu và tài khoản demo. Ngày cấu hình: 28/10/2026. Việc Expo chấp nhận khóa FCM và việc build được APK chưa chứng minh điện thoại đã nhận lời nhắc.

## 1. Cài bản mới

1. Lấy `D:\IHRMS_Review_Exports\Mobile_Push_QA_20261028\apk\IHRMS-QA.apk` trên máy tính sau khi người kỹ thuật xác nhận build thành công. Chuyển file sang điện thoại qua kênh nội bộ.
2. Mở file APK và chọn **Cập nhật/Cài đặt**. Bản mới giữ package và khóa ký QA cũ; bình thường không cần gỡ app. Nếu máy báo không tương thích chữ ký, dừng và báo người kỹ thuật, chưa gỡ app.
3. Điện thoại và PC cùng Wi-Fi, cả hai có Internet. Backend thử là **http://192.168.1.12:8790**. Giữ máy tính mở trong khi thử.
4. Mật khẩu demo nằm trong `D:\IHRMS_Review_Exports\Mobile_Demo10_20261028\qa\DEMO_ACCOUNTS.txt` trên PC. Không gửi ảnh hoặc nội dung file này vào nhóm/chat.
5. Đăng nhập `demo-hr`. Trong tab **Tôi**, cuộn xuống dưới nút Đăng xuất, bấm **Bật thông báo trên điện thoại**, chọn **Cho phép** khi Android hỏi. Chờ dòng **Đã bật thông báo trên thiết bị này**; dòng này xác nhận đăng ký thiết bị với backend, chưa xác nhận nhận lời nhắc.
6. Sau khi đã cho phép, APK mới tự đăng ký lại token khi mở ứng dụng và khi quay lại từ nền. Những lần sau không cần bấm nút này; nếu điện thoại chưa có quyền, ứng dụng không tự bật hộp thoại hỏi.

Nếu đã từ chối quyền: mở **Cài đặt điện thoại → Ứng dụng → IHRMS QA → Thông báo** và bật quyền. Nếu lời nhắc chỉ nằm trong khay, kiểm tra mục **Cập nhật IHRMS** có cho phép âm thanh/hiện nổi và điện thoại không ở chế độ Không làm phiền. Tên mục tùy hãng máy; ứng dụng không thể tự vượt lựa chọn của bạn.

## 2. Nhân viên gửi đơn → HR nhận

1. Giữ `demo-hr` trên điện thoại. Trên trình duyệt PC mở địa chỉ backend ở trên, đăng nhập `demo-employee`.
2. Nhân viên tạo một đơn nghỉ vào ngày làm việc chưa có đơn trùng, rồi gửi.
3. HR phải nhận lời nhắc chung **Bạn có cập nhật mới** trên điện thoại. Bấm lời nhắc để mở tab **Thông báo**, rồi mở mục đơn để xem đúng dữ liệu theo quyền.
4. Làm lại với ngày khác khi app đang mở; khi bấm Home để app chạy nền; và khi vuốt app khỏi danh sách gần đây để đóng bình thường. Không chọn **Buộc dừng**.

## 3. HR duyệt/từ chối → nhân viên nhận

1. Đăng xuất HR trên điện thoại, đăng nhập `demo-employee`, bấm **Bật thông báo trên điện thoại** lại. Trên PC đăng xuất nhân viên, đăng nhập `demo-hr`.
2. Nhân viên tạo đơn trên điện thoại. HR mở đơn trên PC và chọn duyệt. Kiểm tra lời nhắc và trạng thái đơn trên điện thoại.
3. Lặp lại với một đơn khác để thử từ chối; thử lại cả mở app, chạy nền và đóng bình thường.
4. Sau khi điện thoại đăng xuất, tạo sự kiện mới cho tài khoản cũ: thiết bị không được đăng ký nhận thông báo mới cho phiên đã đăng xuất. Lời nhắc đã gửi/xếp hàng trước đó có thể vẫn đến. Khi chuyển tài khoản, phải đăng ký lại cho tài khoản mới.

Hai điện thoại với hai tài khoản riêng giúp thử thuận tiện hơn. Trình duyệt PC chỉ dùng để tạo/duyệt đơn; nó không nhận push Android.

## 4. Nếu chưa nhận được

- Kiểm tra bấm bật thông báo có báo thành công hay hiện lỗi; ghi lại nguyên văn lỗi, không gửi token.
- Thử ngay sau đăng nhập. Chính sách hiện tại ngừng gửi push khi phiên không hoạt động quá **30 phút**, hết hạn tuyệt đối **8 giờ**, bị đăng xuất, đổi mật khẩu hoặc khóa tài khoản. Mở app, đăng nhập lại và bấm bật lại nếu cần. Bản QA này chưa cung cấp lời nhắc dài ngày sau khi phiên hết hạn.
- Cần Internet tới Expo/Google và PC backend vẫn chạy. Cùng Wi-Fi chỉ giúp truy cập IHRMS, chưa đủ cho push. Không bật tiết kiệm pin chặn IHRMS khi thử; không dùng **Buộc dừng**.
- Ghi mẫu điện thoại, Android, giờ thử, tài khoản vai trò, trạng thái app, thao tác tạo/duyệt/từ chối, có lời nhắc/âm thanh không và bấm vào có mở đúng nơi không. Chỉ kết luận đạt cho trạng thái đã thử thực tế.

## Dành cho người phụ trách máy tính

Project Expo đã có: `@viethealth.org.vn/ihrms`, ID `53634c3e-75ad-4a4c-895c-28e298b63256`. Firebase `ihrms-qa`, Android `vn.ihrms.internal.qa`. Không tạo project mới, không dùng khóa dịch vụ làm Android keystore.

Chỉ chạy **một** server cho bộ demo ở cổng 8790. Nếu cần mở lại server sau khi đã đóng, trong PowerShell tại `D:\QLHCNS` chạy:

```powershell
venv/Scripts/python.exe ops/mobile_qa.py serve --directory D:/IHRMS_Review_Exports/Mobile_Demo10_20261028/qa --bind 192.168.1.12 --port 8790 --enable-push
```

Cờ `--enable-push` chỉ hoạt động với thư mục dữ liệu giả có marker hợp lệ. Không thay cấu hình backend vận hành. Mặc định công cụ QA tắt push và không kế thừa Expo access token của vận hành; nếu project bật enhanced push security, người kỹ thuật cấp `MOBILE_QA_EXPO_ACCESS_TOKEN` riêng cho tiến trình QA, ngoài Git/app/log.

Build lại cục bộ, giữ hai JSON bên ngoài repository:

```powershell
$env:EXPO_PUBLIC_EAS_PROJECT_ID='53634c3e-75ad-4a4c-895c-28e298b63256'
$env:MOBILE_GOOGLE_SERVICES_FILE='D:/IHRMS_Private/push-qa/google-services.json'
$env:GRADLE_USER_HOME='D:/IHRMS_BuildTools/gradle'
./ops/build_mobile_qa_apk.ps1 -JavaHome D:/IHRMS_BuildTools/jdk -AndroidSdk D:/IHRMS_BuildTools/android-sdk -OutputDirectory D:/IHRMS_Review_Exports/Mobile_Push_QA_20261028/apk -BuildDirectory D:/IHRMS_BuildTools/qa-push -ApiUrl http://192.168.1.12:8790 -AllowLocalHttp
```

Script dùng workspace native bên ngoài repository và giữ keystore QA hiện có trong `mobile/android/app/debug.keystore`; nếu thiếu thì dừng để khôi phục, không tự đổi khóa ký. JSON cấu hình Firebase được Gradle chuyển thành tài nguyên Android trong workspace đó; khóa dịch vụ FCM không tham gia build. Không chạy cloud build trong quy trình này. Đây là APK thử, không phải bản production.

Backend gửi lời nhắc có `priority: high` và ứng dụng dùng kênh thông báo mức cao để giảm trì hoãn khi điện thoại ngủ; đây vẫn không phải cam kết giao nhận hoặc cách vượt cài đặt người dùng. Xem [ưu tiên thông báo Expo](https://docs.expo.dev/push-notifications/sending-notifications/) và [ưu tiên Android/FCM](https://firebase.google.com/docs/cloud-messaging/android-message-priority).

Nguồn đối chiếu: [Expo FCM V1](https://docs.expo.dev/push-notifications/fcm-credentials/), [Expo Notifications SDK 58](https://docs.expo.dev/versions/v58.0.0/sdk/notifications/). Kết quả và giới hạn kiểm tra ghi một nơi tại [nhật ký dự án](../PROJECT_WORK_LOG.md).
