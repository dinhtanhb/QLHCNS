# IHRMS Mobile nội bộ

Mã app ở `mobile/`, React Native + Expo SDK 58 + TypeScript, dùng chung backend và dữ liệu IHRMS. Android/iOS dùng cùng các màn hình native; bản web export chỉ phục vụ QA cục bộ. App không dùng WebView, không kết nối trực tiếp cơ sở dữ liệu.

Phạm vi đã duyệt: nhân viên, người duyệt và Nhân sự; hồ sơ cá nhân, xem chấm công, tạo/theo dõi nghỉ phép, duyệt/từ chối và thông báo. Nhân sự dùng quyền hiện có, không được đọc đơn ngoài cây quản lý. Quản trị hồ sơ/hạn mức và nghiệp vụ ngoài MVP vẫn thực hiện trên web. Bản đầu cần mạng; không lưu hồ sơ/chấm công/đơn nghỉ vào bộ nhớ bền vững của thiết bị, không tự gửi lại POST.

- [Kiểm thử cục bộ và APK](TEST_LOCAL_APK.md)
- [Tạo tài khoản và phát hành nội bộ](TAO_TAI_KHOAN_VA_PHAT_HANH.md)
- [API và bảo mật phiên](API.md)
- Kết quả thực tế, giới hạn và bàn giao: [nhật ký dự án](../PROJECT_WORK_LOG.md).

## Chuẩn bị mã nguồn

Node.js theo yêu cầu `expo` trong lockfile, JDK 21 và Android SDK cho build Windows. Dùng `npm ci` trong `mobile/`; không thay lockfile bằng cách nâng dependency hàng loạt. Xem `mobile/.env.example` cho các biến cấu hình công khai. Không đặt mật khẩu/token/dữ liệu nhân sự trong `EXPO_PUBLIC_*` vì chúng nằm trong bundle.

```powershell
cd D:\QLHCNS\mobile
npm ci
npm run typecheck
npm run lint
npx expo-doctor
```

Màu app sinh từ `src/static/css/ui_tokens.css` bằng `venv/Scripts/python.exe ops/sync_mobile_tokens.py`. Ba palette sáng/tối theo cấu hình máy chủ, chế độ sáng/tối theo thiết bị; không có bộ chọn palette cá nhân. Kiểm đồng bộ bằng `--check`.

`npm audit` hiện ghi nhận 8 mục (3 high, 5 low), liên quan các dependency CLI/config/lint trong cây Expo hiện tại (`zod`, `deepmerge` và gói phụ thuộc). Chưa dùng `audit fix --force` vì đề xuất đó hạ Expo về SDK khác và phá bộ phiên bản. Đây là giới hạn còn mở trước phát hành production; kết quả và phiên bản được ghi tại nhật ký, không coi APK QA là đã vượt cổng bảo mật phát hành.

Đối chiếu nguồn chính thức ngày 28/10/2026: [Zod advisory](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) liệt kê bản vá từ 4.6.6, trong khi CLI/lint đang yêu cầu Zod 3; [deepmerge advisory](https://github.com/advisories/GHSA-gcqx-w48m-w2h4) chưa liệt kê bản vá. Registry vẫn trả Expo 58.0.20 và deepmerge 4.3.1 là latest khi kiểm. Không ép đổi major hoặc bỏ advisory khỏi kết quả. Người bảo trì chạy `npm audit --json` trong `mobile/`, theo dõi bản vá của Expo/upstream, kiểm lại build và UAT sau khi thay lockfile. Không kết luận cảnh báo vô hại chỉ vì nằm ở bộ công cụ.

## Bật backend

API bị tắt mặc định. Sau kiểm thử trên môi trường phù hợp, người vận hành đặt `MOBILE_API_ENABLED=True` trong cấu hình riêng của backend và khởi động lại theo quy trình triển khai. Không cần migration mới cho mobile; dùng session/nhân sự/nghỉ phép/thông báo hiện có. Không tự chạy `migrate` trên DB vận hành.

Truy cập ngoài công ty cần tên miền HTTPS thật, chứng chỉ hợp lệ và reverse proxy bảo vệ backend. Chỉ app QA được phép dùng HTTP trên localhost/IP LAN riêng khi build với `EXPO_PUBLIC_ALLOW_HTTP=true`; bản production từ chối cấu hình này. Chưa có tên miền đích được chốt trong mã nguồn.

## Thông báo điện thoại

Thông báo trong app hoạt động qua API. Push là tích hợp tùy chọn đã có mã nhưng mặc định tắt, chưa thể chứng nhận giao nhận thật khi tổ chức chưa có Expo project/FCM/APNs. Khi bật, bên ngoài IHRMS chỉ nhận token thiết bị và lời nhắc chung, không có tên nhân viên, lý do nghỉ hoặc trạng thái đơn. Người dùng chủ động bật quyền trong màn hình Tôi sau khi cấu hình project. Xem hướng dẫn phát hành để hoàn tất và thử trên thiết bị thật.
