# Tạo tài khoản và phát hành IHRMS nội bộ

Đối chiếu nguồn chính thức ngày 28/10/2026. Chỉ sử dụng nội bộ, điện thoại cá nhân, nhóm pilot gồm nhân viên/người duyệt/Nhân sự. Chưa có tài khoản store; tài liệu này không có nghĩa ứng dụng đã được nộp hoặc phát hành. Không đưa dữ liệu nhân sự thật vào tài khoản xét duyệt.

## Những việc tổ chức cần thực hiện

Người đại diện tổ chức thực hiện xác minh pháp nhân, điều khoản và thanh toán; Codex không có các tài khoản này. Chuẩn bị tên pháp lý, địa chỉ, website/email tên miền công ty, người có thẩm quyền, điện thoại và D-U-N-S nếu chương trình yêu cầu. Tài khoản sở hữu, mã khôi phục 2FA và khóa ký thuộc tổ chức; mời lập trình viên qua phân quyền thay vì chia sẻ mật khẩu.

Trước store, thống nhất bundle/package ID chính thức có quyền sở hữu; `vn.ihrms.internal` hiện là định danh cấu hình khởi đầu, không phải bằng chứng tên đã được đăng ký. Bản QA `.qa` tách biệt. Chốt URL HTTPS thật, chính sách riêng tư, email hỗ trợ và người chịu trách nhiệm cấp/thu hồi tài khoản IHRMS. Chưa cần làm các bước store để cài APK QA.

## Apple Developer tổ chức

1. Mở [Enroll Apple Developer](https://developer.apple.com/programs/enroll/), dùng Apple Account có 2FA của người được ủy quyền; chọn tổ chức.
2. Khai pháp nhân, quyền đại diện, D-U-N-S/website và thông tin liên hệ theo yêu cầu đang hiển thị. Hoàn thành xác minh, chấp nhận thỏa thuận và phí do Apple công bố tại lúc đăng ký.
3. Sau duyệt, vào App Store Connect, mời nhóm phát triển với quyền cần thiết; tạo App ID/app bằng bundle ID chính thức đã chốt. Bảo vệ certificate/APNs key/provisioning trong kho bí mật của tổ chức hoặc EAS credentials, không commit vào Git.
4. Chọn đường phân phối **trước khi nộp**. Apple có giới hạn chuyển đổi cách phân phối sau phê duyệt, nên đọc [Set distribution methods](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/set-distribution-methods).

Với yêu cầu giới hạn tổ chức, ưu tiên đánh giá **Custom Apps**: đăng ký Apple Business Manager, lấy Organization ID và khai bên nhận trong App Store Connect; đội IT phải xác nhận cách cấp app cho điện thoại cá nhân, enrollment/MDM hoặc cơ chế phân phối phù hợp. Xem [Custom Apps](https://support.apple.com/guide/deployment/distribute-custom-apps-dep0113f6e18/web).

Nếu không triển khai quản lý thiết bị và muốn nhân viên tự cài trên máy cá nhân, có thể đề nghị Apple cho **Unlisted App** sau khi chủ dự án chốt. App không xuất hiện khi tìm kiếm nhưng **ai có link vẫn có thể tải**; đây không phải cơ chế giới hạn cài đặt cho tổ chức. Quyền dùng dữ liệu vẫn được kiểm qua tài khoản IHRMS. Apple cần xét duyệt và chấp thuận riêng; không cam kết tự động đủ điều kiện. Xem [Unlisted distribution](https://developer.apple.com/support/unlisted-app-distribution).

Pilot iPhone dùng TestFlight sau khi có app đã ký; nhóm ngoài có thể cần beta review. Không coi TestFlight là kênh vận hành lâu dài. Chưa chọn Enterprise Program: điều kiện và quản trị riêng, không suy ra phù hợp chỉ vì app nội bộ.

## Google Play tổ chức và Android

1. Vào [Play Console](https://play.google.com/console/signup), dùng tài khoản Google do tổ chức quản lý, chọn loại **Organization**.
2. Khai hồ sơ thanh toán/pháp nhân, D-U-N-S và liên hệ theo [Required information](https://support.google.com/googleplay/android-developer/answer/13628312?hl=en). Hoàn thành xác minh email/điện thoại, giấy tờ, phí và bước xác minh đang được Google yêu cầu; không dùng danh tính cá nhân thay pháp nhân cho nhanh.
3. Tạo app và chốt package ID. Nếu dùng Play, cấu hình Play App Signing/upload key và lưu bản khôi phục trong kho khóa tổ chức. APK QA không có định danh ký production này.
4. Pilot qua internal/closed testing với nhóm QA được mời sau khi cấu hình đạt. Nếu vận hành qua managed Google Play private app, cần xác minh Android Enterprise/EMM/work profile phù hợp trên điện thoại cá nhân trước; không mở production public listing theo mặc định.

Phân phối APK ký chính thức qua kênh riêng là một phương án Android khác: tổ chức phải tự quản lý tải xuống, tính toàn vẹn, cập nhật và thu hồi quyền backend. Kiểm [Android developer verification](https://developer.android.com/developer-verification) cho cách đăng ký developer/package và điều kiện theo khu vực. Lộ trình đang triển khai; không dùng việc sideload được trên một máy để suy ra mọi nhân viên đều cài được. Chỉ chủ dự án quyết định kênh vận hành sau pilot.

## Expo và bản ký

1. Tạo Expo account/organization do công ty quản lý, mời người build; trong `mobile/` chạy `npx eas-cli@latest login`, `npx eas-cli@latest init`. Lưu project ID vào cấu hình build công khai `EXPO_PUBLIC_EAS_PROJECT_ID`. Không đưa access token vào app.
2. Bản QA cloud có thể dùng `npx eas-cli@latest build --platform android --profile preview`; quy trình cục bộ ở [TEST_LOCAL_APK](TEST_LOCAL_APK.md) không cần Expo account. EAS upload mã nguồn lên dịch vụ bên ngoài: trước khi dùng cần chốt việc sử dụng dịch vụ này và giới hạn gói upload, tuyệt đối loại `.env`, dữ liệu, log và khóa cục bộ. Lệnh ở tài liệu không phải quyền tự upload.
3. Cho production đặt `MOBILE_VARIANT=production`, `EXPO_PUBLIC_ALLOW_HTTP=false` và `EXPO_PUBLIC_API_URL=https://<tên-miền-IHRMS>`. App config từ chối production thiếu HTTPS cố định.
4. Build Android bằng `npx eas-cli@latest build --platform android --profile production` để tạo AAB; iOS bằng `... --platform ios --profile production` để ký bằng Apple team của tổ chức. Local iOS cần macOS/Xcode. Chỉ submit sau khi chủ dự án duyệt đúng file/phiên bản/kênh.
5. Chuẩn bị icon/ảnh chụp, mô tả nội bộ, URL hỗ trợ/riêng tư, khai báo dữ liệu và credentials QA xét duyệt trên backend sandbox HTTPS truy cập được. Không cung cấp tài khoản thật.

## Hoàn tất push điện thoại

Theo [Expo push setup](https://docs.expo.dev/push-notifications/push-notifications-setup/): cấu hình FCM v1 cho Android và APNs/Apple credentials cho iOS của đúng app ID; giữ service-account/key ngoài Git. Với Android thêm `google-services.json` bằng cấu hình build bí mật và `android.googleServicesFile` phù hợp trước build, không dùng file của dự án khác. Đặt EAS project ID, build lại native, bật `MOBILE_PUSH_ENABLED=True` trên backend; nếu dùng Expo enhanced push security, đặt access token chỉ trên backend. Không bật khi chưa thống nhất việc gửi token thiết bị qua nhà cung cấp push.

Người dùng vào Tôi → Bật thông báo trên điện thoại để cấp quyền và đăng ký. Thử thiết bị thật đang khóa màn hình, app nền/đóng, quyền bị từ chối, token đổi, đăng xuất/chuyển tài khoản. Nội dung push chỉ là lời nhắc chung. Kiểm chứng APNs/FCM/Expo delivery và receipt trước khi xem push là đã nghiệm thu; hiện chưa có credentials để thực hiện bước này. Thông báo trong app vẫn dùng được khi push chưa bật.

## Trước khi mở rộng khỏi nhóm pilot

App config đã hỗ trợ `MOBILE_GOOGLE_SERVICES_FILE` để nhận đường dẫn file cấu hình Firebase riêng của môi trường build và ánh xạ vào `android.googleServicesFile`. Cung cấp bằng biến file của dịch vụ build hoặc đường dẫn cục bộ ngoài Git; không đặt nội dung file trong `EXPO_PUBLIC_*`.

Người phụ trách ghi kết quả thiết bị Android/iPhone, sáng/tối, mất mạng, phiên hết hạn, tạo/duyệt/từ chối và đồng bộ web. Xác nhận URL production, tên app/định danh, khóa ký, quyền riêng tư và kênh phân phối đã duyệt. Không dùng khóa QA cho production, không coi build/export thành công là đã phát hành.
