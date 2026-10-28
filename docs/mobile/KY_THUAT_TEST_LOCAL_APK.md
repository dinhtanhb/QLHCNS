# Kiểm thử cục bộ và cài APK Android

## QA trên máy phát triển

Tất cả tài khoản/DB/media dưới đây là dữ liệu giả tách biệt. Không dùng phiên hoặc tài khoản nhân viên thật. Chọn thư mục mới ngoài repository; công cụ không ghi đè thư mục QA không rỗng.

```powershell
cd D:\QLHCNS\mobile
$env:MOBILE_VARIANT='qa'
$env:EXPO_PUBLIC_ALLOW_HTTP='true'
npx expo export --platform web
cd D:\QLHCNS
venv/Scripts/python.exe ops/mobile_qa.py create --directory D:/IHRMS_Mobile_QA/run1
venv/Scripts/python.exe ops/mobile_qa.py serve --directory D:/IHRMS_Mobile_QA/run1 --port 8789
```

Mở `http://127.0.0.1:8789/`. Tên tài khoản và mật khẩu QA nằm trong `DEMO_ACCOUNTS.txt` của thư mục trên, không gửi vào Git. Có `demo-employee`, `demo-manager`, `demo-hr`, được gắn cây quản lý giả. Địa chỉ IHRMS trong bản web QA điền sẵn origin hiện tại.

Trong cửa sổ khác:

```powershell
cd D:\QLHCNS
venv/Scripts/python.exe ops/run_mobile_uat.py --directory D:/IHRMS_Mobile_QA/run1 --url http://127.0.0.1:8789 --output D:/IHRMS_Mobile_QA/evidence
venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.mobile.tests apps.portal.tests.PortalSensitiveWorkflowTests apps.leave.tests apps.notification.tests
venv/Scripts/python.exe ops/run_tests.py --backend sqlserver apps.mobile.tests apps.portal.tests.PortalSensitiveWorkflowTests apps.leave.tests apps.notification.tests
venv/Scripts/python.exe ops/sync_mobile_tokens.py --check
```

SQL Server test dùng DB có tên ngẫu nhiên và tự dọn theo `ops/run_tests.py`, không tái sử dụng DB vận hành. Browser UAT là bản React Native web export trong Edge: chứng minh tương tác/API/nghiệp vụ, không thay cho kiểm trên Android/iPhone thật.

## Build APK QA trên Windows

Cài JDK 21 và Android SDK theo [Expo local builds](https://docs.expo.dev/guides/local-app-development/), [Android tools](https://developer.android.com/studio). SDK/NDK/build-tools theo phiên bản React Native trong lockfile; dùng Android SDK Manager để cài các gói thiếu. Bộ native được sinh bởi Expo, không sửa tay hoặc commit `mobile/android`, `mobile/ios`.

```powershell
cd D:\QLHCNS\mobile
npm ci
cd D:\QLHCNS
./ops/build_mobile_qa_apk.ps1 -JavaHome D:/IHRMS_BuildTools/jdk -AndroidSdk D:/IHRMS_BuildTools/android-sdk -OutputDirectory D:/IHRMS_Mobile_Builds/qa -AllowLocalHttp
```

Đầu ra `IHRMS-QA.apk` và `apk-manifest.json` có SHA-256, commit nền và trạng thái nguồn. APK release bundle độc lập, không cần Metro/Expo Go hay Google Play để chạy. Đây là **bản QA**, package `vn.ihrms.internal.qa`, dùng khóa debug do native template sinh, không dùng làm bản production. Bản ký chính thức dùng định danh/khóa thuộc tổ chức theo hướng dẫn phát hành. Xem [hướng dẫn APK của Expo](https://docs.expo.dev/build-reference/apk/).

Build Windows dùng compiler Hermes đúng lockfile được sao ra thư mục đầu ra, kiểm SHA-256 và phép thử ghi bytecode, rồi đặt `REACT_NATIVE_OVERRIDE_HERMES_DIR` chỉ trong tiến trình build. Máy này tái hiện lỗi ghi file khi chạy binary từ `node_modules`, trong khi cùng binary bên ngoài ghi được; không thay ACL/tắt bảo vệ hệ thống. Plugin CMake giới hạn đường dẫn object ở 240 ký tự để tránh giới hạn Windows. Khi tự export native bundles trên Windows, có thể chạy `./ops/prepare_mobile_hermes.ps1 -Directory D:/IHRMS_BuildTools/hermes` trong cùng cửa sổ PowerShell trước lệnh Expo.

## Cài lên điện thoại Android

1. Xác minh SHA-256 khớp manifest. Chuyển APK qua kênh nội bộ tin cậy tới điện thoại QA Android 7 trở lên tương thích; bản mặc định có arm64-v8a/x86_64, chưa gồm CPU 32-bit.
2. Trên thiết bị, mở APK và cho phép ứng dụng quản lý tệp đang dùng được “cài ứng dụng không rõ nguồn gốc” nếu Android yêu cầu. Sau cài có thể tắt lại quyền này. Hoặc dùng `adb install -r <đường-dẫn>/IHRMS-QA.apk` trên thiết bị QA đã bật USB debugging.
3. Khi dùng backend QA trên PC, cả hai phải ở cùng mạng. `127.0.0.1` trên điện thoại là chính điện thoại, không phải PC. Dừng server QA cũ rồi chạy `ops/mobile_qa.py serve ... --bind <IP-LAN-PC> --port 8789`, nhập `http://<IP-LAN-PC>:8789` vào app; chỉ cấp tường lửa cho mạng riêng nếu cần. Chỉ thực hiện với dữ liệu giả. Qua USB có thể `adb reverse tcp:8789 tcp:8789` rồi dùng `http://127.0.0.1:8789`.
4. Đăng nhập tài khoản QA. Thử hồ sơ/chấm công, tạo đơn, sai ngày/quỹ phép, trùng gửi, quản lý duyệt/từ chối, thông báo, đăng xuất, phiên hết hạn, mất mạng/kết nối lại và sáng/tối. Đối chiếu trạng thái, lịch sử và chỉ số web dùng cùng DB giả.
5. Ghi mẫu máy, phiên bản Android, SHA APK, backend, tài khoản vai trò QA và kết quả. Không đính kèm mật khẩu/token vào báo cáo.

Chính sách xác minh developer của Android đang thay đổi theo khu vực/thiết bị; kiểm [nguồn Android chính thức](https://developer.android.com/developer-verification) trước khi phân phối nhiều nhân viên. Việc tạo APK cục bộ không yêu cầu tài khoản store; việc cài/phân phối thực tế vẫn theo chính sách áp dụng trên thiết bị.

## Hồi quy nghiệp vụ trên APK bằng emulator

Sau khi khởi động Android emulator riêng và backend giả ở cổng 8789, chạy từ gốc repository:

```powershell
venv/Scripts/python.exe ops/run_mobile_android_uat.py --business --directory D:/IHRMS_Mobile_QA/run1 --apk D:/IHRMS_Mobile_Builds/qa/IHRMS-QA.apk --sdk D:/IHRMS_BuildTools/android-sdk --output D:/IHRMS_Mobile_QA/native-evidence
```

Runner chỉ chấp nhận serial `emulator-*`, xóa dữ liệu của package QA trên emulator để bắt đầu, dùng tài khoản giả trong thư mục đã xác minh. `--business` chọn ngày làm việc chưa có đơn trùng, tạo đơn bằng thao tác native, đăng xuất, đăng nhập quản lý và duyệt bằng native; đối chiếu trạng thái, lịch sử và thông báo trên đúng DB giả. Không in mật khẩu/token vào lỗi timeout. File validation gắn SHA-256 APK được cài; không thay thế thử điện thoại thật/iPhone.

## iPhone

Mã dùng chung nhưng file APK chỉ dành cho Android. Kiểm iOS native bằng Xcode trên macOS hoặc bản ký qua EAS/TestFlight sau khi tổ chức có tài khoản. Không coi web export/JavaScript bundle iOS là đã build, ký hoặc UAT iPhone. Làm lại cùng danh sách luồng trên iPhone thật trước nghiệm thu.
