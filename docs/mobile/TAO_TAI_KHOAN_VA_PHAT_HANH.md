# Tạo tài khoản và phát hành IHRMS nội bộ

**Trạng thái mới nhất — 04/11/2026:** chủ dự án đã bỏ kế hoạch lên cửa hàng và chọn build APK Android để dùng nội bộ. Không thực hiện đăng ký/nộp store theo các bước dưới đây. Giữ tài liệu này làm phương án tham khảo; luồng đang dùng ở [kiểm thử và build APK](TEST_LOCAL_APK.md). Đổi kênh phân phối không thay các yêu cầu HTTPS, bảo vệ khóa ký, kiểm thử thiết bị và kiểm quyền backend.

Đối chiếu nguồn chính thức ngày 04/11/2026. Chủ dự án xác nhận chỉ phân phối nội bộ và chưa có tài khoản phân phối. Điện thoại cá nhân, nhóm pilot gồm nhân viên/người duyệt/Nhân sự. Chưa nộp hoặc phát hành lên cửa hàng. Không đưa dữ liệu nhân sự thật vào tài khoản xét duyệt.

## Thứ tự thực hiện cho đợt phát hành đầu

1. **Chủ tổ chức đăng ký:** [Google Play Console Organization](https://play.google.com/console/signup) và [Apple Developer Organization](https://developer.apple.com/programs/enroll/). Người đại diện tự xác minh pháp nhân, điều khoản, 2FA và thanh toán trên trang chính thức. Expo/Firebase QA hiện có không thay thế hai tài khoản này. Khi tài khoản được duyệt, mời người build bằng quyền phù hợp, không gửi mật khẩu/khóa qua chat.
2. **IT chốt cách cấp app:** Android thử qua internal testing; iPhone thử qua TestFlight. Để vận hành lâu dài có giới hạn tổ chức, đánh giá managed Google Play private app và Apple Custom Apps với hệ thống quản lý thiết bị. Nếu dùng máy cá nhân không có quản lý thiết bị, Apple Unlisted là phương án cần chủ dự án chốt và Apple chấp thuận; người có link vẫn tải được. Không tự chuyển sang niêm yết công khai. Pilot không thay cho kênh vận hành lâu dài.
3. **IT cung cấp cấu hình đích:** URL backend HTTPS cố định; package/bundle ID thuộc tổ chức; Expo project production đã xác nhận owner/slug/project ID. Hiện production dùng slug `ihrms-internal`, còn project QA là `@viethealth.org.vn/ihrms`; không gán ID QA sang production khi chưa kiểm liên kết. Chưa có URL đích được chủ dự án cung cấp; không dùng URL giả để tạo bản phát hành.
4. **Chủ dữ liệu hoàn tất hồ sơ:** URL hỗ trợ, email liên hệ, chính sách riêng tư công khai và truy cập được trong app; khai Data safety/App Privacy khớp dữ liệu HR, file và nhà cung cấp push thực tế. Đánh giá quy trình yêu cầu xóa tài khoản và nghĩa vụ lưu hồ sơ theo mô hình tài khoản do tổ chức cấp; không tự xóa hồ sơ nhân sự. Hiện chưa tìm thấy liên kết riêng tư trong mã `mobile/src`, cần triển khai khi có URL chính thức. Tạo tài khoản xét duyệt riêng trên sandbox HTTPS với dữ liệu tổng hợp, đủ hướng dẫn cho reviewer truy cập.
5. **Người build đóng các cổng kỹ thuật:** xử lý dependency advisory với bộ phiên bản Expo tương thích; ba kiểm tra mobile bắt buộc; build AAB Android và iOS ký chính thức. Rà gói EAS upload trước khi dùng cloud: loại toàn bộ backend/dữ liệu/khóa và đầu ra cục bộ, xác nhận archive chỉ có nguồn cần build. Không dùng APK/chữ ký QA làm production. Kiểm versionCode/buildNumber với lịch sử store trước mỗi upload; chưa tự tăng khi chưa có app record.
6. **QA thử bản native đã ký:** Android/iPhone thật, hai vai, đăng nhập/hết phiên/đăng xuất, tạo và duyệt nghỉ, file/PDF, đồng bộ web, sáng/tối, chữ lớn, mất mạng và push nếu bật. Lưu bằng chứng trên DB/media/tài khoản QA riêng. Web export và kiểm tra helper không thay cho nghiệm thu native.
7. **Nộp đúng artifact:** ghi SHA-256, phiên bản, app ID và kênh; upload internal testing/TestFlight trước. Sau nghiệm thu và chốt cách phân phối, hoàn tất nội dung cửa hàng, ảnh thật và review. Không tự mở public listing hoặc cam kết ngày được duyệt. Kết quả từng đợt chỉ ghi tại [nhật ký dự án](../PROJECT_WORK_LOG.md).

Yêu cầu nền tảng cần kiểm trên artifact cuối: [Google Play](https://developer.android.com/google/play/requirements/target-sdk) yêu cầu app mới/cập nhật Android thông thường target API 36 trở lên từ 31/08/2026; [Apple](https://developer.apple.com/news/upcoming-requirements/) yêu cầu Xcode 26 trở lên với SDK iOS/iPadOS 26 trở lên từ 28/04/2026. Cấu hình/bản QA cũ không chứng minh artifact store đã đạt. Chính sách riêng tư và khai báo dữ liệu đối chiếu [Google User Data](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en); khai theo thực tế, không chọn “không thu thập dữ liệu” chỉ vì app nội bộ.

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

Nếu chưa có Expo/Firebase, làm theo [hướng dẫn tạo từng bước cho người không lập trình](TAO_EXPO_FIREBASE_THONG_BAO.md). Tạo xong tài khoản vẫn cần cấu hình và build APK mới, sau đó thử nhận thông báo thật.

Theo [Expo push setup](https://docs.expo.dev/push-notifications/push-notifications-setup/): cấu hình FCM v1 cho Android và APNs/Apple credentials cho iOS của đúng app ID; giữ service-account/key ngoài Git. Với Android thêm `google-services.json` bằng cấu hình build bí mật và `android.googleServicesFile` phù hợp trước build, không dùng file của dự án khác. Đặt EAS project ID, build lại native, bật `MOBILE_PUSH_ENABLED=True` trên backend; nếu dùng Expo enhanced push security, đặt access token chỉ trên backend. Không bật khi chưa thống nhất việc gửi token thiết bị qua nhà cung cấp push.

Người dùng vào Tôi → Bật thông báo trên điện thoại để cấp quyền và đăng ký. Thử thiết bị thật đang khóa màn hình, app nền/đóng, quyền bị từ chối, token đổi, đăng xuất/chuyển tài khoản. Nội dung push chỉ là lời nhắc chung. Kiểm chứng APNs/FCM/Expo delivery và receipt trước khi xem push là đã nghiệm thu. Android QA đã có project/khóa FCM; xem [cách cài và thử lời nhắc](THU_THONG_BAO_ANDROID_QA.md), không tạo lại project. iOS/APNs và kiểm giao nhận thật vẫn là các bước riêng. Thông báo trong app vẫn dùng được khi push chưa bật.

## Trước khi mở rộng khỏi nhóm pilot

App config đã hỗ trợ `MOBILE_GOOGLE_SERVICES_FILE` để nhận đường dẫn file cấu hình Firebase riêng của môi trường build và ánh xạ vào `android.googleServicesFile`. Cung cấp bằng biến file của dịch vụ build hoặc đường dẫn cục bộ ngoài Git; không đặt nội dung file trong `EXPO_PUBLIC_*`.

Người phụ trách ghi kết quả thiết bị Android/iPhone, sáng/tối, mất mạng, phiên hết hạn, tạo/duyệt/từ chối và đồng bộ web. Xác nhận URL production, tên app/định danh, khóa ký, quyền riêng tư và kênh phân phối đã duyệt. Không dùng khóa QA cho production, không coi build/export thành công là đã phát hành.
