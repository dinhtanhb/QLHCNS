# Quy ước giao diện mobile IHRMS

Ứng dụng dùng React Native/Expo, chữ và điều khiển theo cỡ chữ hệ thống. Màu giao diện luôn lấy từ `useTheme()`; ba palette VietHealth, Chàm Đông, Than Ấm do cấu hình máy chủ chọn, còn sáng/tối theo cài đặt thiết bị hoặc lựa chọn đã lưu. Không thêm mã màu trực tiếp vào màn hình.

## Nền tảng hình ảnh

- Thang dùng chung trong `mobile/src/tokens.ts`: khoảng cách 4/8/12/16/24/32, chữ 12/14/16/18/20/24/32, bo góc 12/16/20. Màn hình ưu tiên chữ 16px, nhãn ngắn, khoảng trống để nhóm nội dung.
- Surface phẳng, viền theo token; không dùng gradient, glow hoặc bóng để thay cho thứ bậc. Nút chính dùng một màu thương hiệu; nút phụ dùng bề mặt; thao tác nhẹ dùng kiểu chữ/link.
- Vùng chạm tối thiểu 44px. Giữ `allowFontScaling`; khi chữ phóng lớn, nhãn được xuống dòng, thẻ được cao thêm, danh sách vẫn cuộn dọc.
- Trạng thái luôn có chữ và biểu tượng cùng chip màu ngữ nghĩa. Không truyền đạt chỉ bằng màu. Trạng thái tải dùng skeleton ngắn, không chạy hiệu ứng liên tục.

## Nên / tránh

| Nên | Tránh |
| --- | --- |
| `SectionHeader` 20px, mô tả phụ ngắn, nhóm cách nhau 24px | Lặp tiêu đề 24px và đoạn giới thiệu dài trên từng màn |
| Một nút primary cho việc chính; secondary/text cho việc còn lại | Viền đậm giống nhau cho mọi nút |
| `StatusChip` có nhãn và icon; `EmptyState` nói rõ bước tiếp theo | Nhúng trạng thái vào tiêu đề hoặc thẻ trống chỉ có một câu |
| `ListItem` gộp tên, thông tin phụ và thao tác thành một hàng | Biến từng trường thành thẻ có nhãn–giá trị dài |
| AppBar gọn, nhãn tab đầy đủ, biểu tượng có tên trợ năng | Cắt nhãn, dùng khoảng tab trống hoặc điều hướng bằng nút chữ “Quay lại” |

Ví dụ dùng:

```tsx
<SectionHeader title="Đơn nghỉ phép" detail="Cập nhật mới nhất" />
<ListItem title="12–13/11 · Phép năm" subtitle="Chờ duyệt" icon="calendar-outline" />
<StatusChip label="Chờ duyệt" tone="warning" />
<Button label="Tạo đơn nghỉ" onPress={openLeave} />
<Button label="Xem lịch sử" variant="text" onPress={openHistory} />
```

## Kiểm kê P0 — baseline 29/10/2026

Ảnh được chụp bằng Microsoft Edge headless trên bản Expo web export và DB/tài khoản QA tổng hợp. Ma trận gồm nhân viên và trưởng phòng; ba kích thước 360×800, 390×844, 412×915; hai chế độ sáng/tối; ba palette. Tổng cộng 342 ảnh, 0 lỗi JavaScript. Bản web chứng minh bố cục/luồng trên export, không chứng nhận Android/iOS native.

| Màn hình/route hiện tại | Quan sát baseline |
| --- | --- |
| Đăng nhập `/login` | Đầu trang và thẻ đăng nhập theo bố cục web, nhiều khoảng dọc trước trường nhập. |
| Trang chủ `/(tabs)` | Số liệu chiếm thẻ cao, nhãn xuống dòng và KPI lệch chiều cao; thiếu lời chào/tên/phòng và hành động chính nổi bật. |
| Hồ sơ `/(tabs)/profile` | Tab riêng; mở đầu bằng hai nút Cài đặt/Nghiệp vụ trước thông tin tài khoản. |
| Chấm công `/(tabs)/attendance` | Bộ điều khiển “Tải lại/Trang n”; trạng thái và số liệu trình bày thành nhiều thẻ. |
| Nghỉ phép `/(tabs)/leaves`, `/leave-new` | Nút tạo đơn, danh sách và biểu mẫu có thể cuộn dài; trạng thái nằm trong tiêu đề; ô ngày ở dạng nhập văn bản. |
| Duyệt `/(tabs)/approvals` | Route bị ẩn bằng nút tab rỗng; trưởng phòng chỉ mở được qua KPI/đường dẫn, không có tab Duyệt. Nút Duyệt/Từ chối đứng thành hàng dọc và gắn mã đơn. |
| Thông báo `/(tabs)/notifications` | Danh sách dùng thẻ dày, Tải lại/phân trang, trạng thái đọc nằm trong câu chữ. |
| Nghiệp vụ `/services` | Phải mở thêm từ Truy cập nhanh; 7 nhóm/24 mục theo vai trò, accordion đóng; thông tin hồ sơ cá nhân chiếm phần đầu danh sách. |
| Workspace `/workspace` | Không có thanh tab/app bar; có nút chữ Quay lại/Tải lại/Danh mục; tiêu đề `— IHRMS`, lọc dạng nút viền, ngày giờ thô và bảng công dài khoảng 9 màn hình. |
| Hồ sơ/cài đặt/đổi mật khẩu/tổ chức | Tiêu đề và mô tả lớn lặp lại; các thao tác dùng nút viền; trạng thái rỗng đơn giản. Những màn này thuộc P3, chưa thiết kế lại trong P2. |

Ảnh gốc và `baseline.json` nằm ngoài repository: `D:/IHRMS_Review_Exports/Mobile_Design_P0_20261029/`. Báo cáo không chứa mật khẩu, token hoặc hồ sơ thật.

## Phạm vi pha

P1 xây token và thành phần dùng chung. P2 áp dụng cho điều hướng, Trang chủ, Việc của tôi, Duyệt, Thông báo và lưới Nghiệp vụ. Workspace và các màn hồ sơ/cài đặt/đổi mật khẩu/tạo đơn chỉ làm sau khi chủ dự án duyệt P2.
