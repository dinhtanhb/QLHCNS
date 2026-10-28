# API mobile v1

Gốc `/api/mobile/v1/`, JSON, UTF-8. `MOBILE_API_ENABLED=False` trả 404. Danh sách phân trang 30 dòng, `page`, trả `items`, `page`, `count`, `has_next`; tham số employee trên client không quyết định phạm vi dữ liệu.

## Phiên

`POST login/` với `username`, `password`: xác thực qua Axes/ModelBackend hiện hành, trả `token`, `expires_at`, `idle_timeout`. Dùng `Authorization: Bearer <token>` trên các lệnh sau. Đây là session Django có marker mobile trong bảng session hiện có, không phải JWT. Cookie web và session web đưa vào bearer đều không được dùng để xác thực API. Đăng nhập mobile không đổi cookie đăng nhập/CSRF web.

Thời hạn tuyệt đối dùng `SESSION_COOKIE_AGE` (hiện 8 giờ), không kéo dài bởi đọc dữ liệu; thời gian không hoạt động theo `SESSION_IDLE_TIMEOUT` (hiện 30 phút). Hết hạn, vô hiệu hóa tài khoản hoặc đổi mật khẩu làm mất hiệu lực phiên. `POST logout/` thu hồi phiên phía server. Native lưu phiên bằng Expo SecureStore, không lưu mật khẩu; web QA chỉ giữ token trong RAM. Backend phải giữ `SESSION_ENGINE=django.contrib.sessions.backends.db` khi dùng thiết kế này.

## Các endpoint

- `GET me/`: hồ sơ tài khoản đang đăng nhập, cờ `can_approve`, `can_manage_hr`, palette máy chủ. Không trả CCCD, lương hay hồ sơ người khác.
- `GET attendance/`: chấm công của chính nhân viên gắn tài khoản.
- `GET leave-options/`: loại nghỉ, năm, phép năm còn có thể đăng ký; `null` nếu chưa có hạn mức.
- `GET leaves/`: đơn bản thân/cấp dưới theo selector hiện hành.
- `POST leaves/`: `leave_type` (số nguyên), `from_date`, `to_date` (YYYY-MM-DD), `reason` (tối đa 500). Server tự xác định nhân viên, trạng thái, số ngày và người tạo. Dùng cùng `apps.leave.services.submit_leave` với web, khóa nhân viên, full_clean và kiểm trùng/quỹ phép; lỗi không tạo bản ghi hoặc thông báo dở dang.
- `GET approvals/`: đơn Pending trong phạm vi hiện hành, chỉ người có quyền duyệt và hồ sơ nhân viên.
- `POST leaves/<id>/decision/`: `decision` là `Approved` hoặc `Rejected`. Cùng `decide_leave` với web, khóa đơn Pending, chặn tự duyệt của DEPT_MANAGER, ghi lịch sử và thông báo trong cùng giao dịch. Lặp sau xử lý trả 404, không tạo lịch sử lần hai.
- `GET notifications/`: thông báo của chính nhân viên. `destination` chỉ dùng giá trị điều hướng được cho phép; không mở URL tùy ý từ thông báo.
- `POST notifications/<id>/read/`: chỉ đánh dấu thông báo của bản thân.
- `POST push-token/`: đăng ký Expo token với phiên hiện tại; trả 503 khi push chưa bật. Đăng ký trên tài khoản mới tháo địa chỉ push khỏi phiên cũ. Đăng xuất thu hồi phiên đồng thời bỏ đăng ký đó.

Ứng dụng native kiểm tra quyền thông báo hiện tại khi phiên đăng nhập được khôi phục và mỗi lần trở lại foreground. Nếu quyền đã được cấp, ứng dụng lấy token Expo và đăng ký lại vào phiên hiện tại; nếu chưa cấp thì không tự bật hộp thoại. Người dùng chỉ cần chọn **Bật thông báo trên điện thoại** một lần sau khi cấp quyền; thao tác này cũng thử đăng ký ngay.

POST yêu cầu `Content-Type: application/json`, không quá 16 KiB. API không dùng cookie nên các endpoint này miễn CSRF; web portal vẫn giữ CSRF hiện có. Không bật CORS rộng: QA web được phục vụ cùng origin với backend cô lập.

Lỗi gồm `error` để hiển thị: 400 dữ liệu, 401 hết phiên/đăng nhập sai, 403 thiếu quyền, 404 ngoài phạm vi hoặc không tồn tại, 405 sai method, 413 quá lớn, 415 sai content type. Axes có thể trả trang khóa 403; client cũng xử lý phản hồi không phải JSON mà không hiển thị chi tiết kỹ thuật. Tất cả phản hồi API không được cache.

## Push tùy chọn

`MOBILE_PUSH_ENABLED=False` mặc định. Khi bật, token gắn với session DB, giới hạn theo tài khoản đang hoạt động, hash mật khẩu và thời hạn/idle của phiên. Sau commit thông báo, gửi HTTPS tới Expo, timeout 3 giây, lời nhắc chung. Lỗi push không hoàn tác nghiệp vụ; thông báo trong IHRMS là nguồn chính. Không có hàng đợi retry/đảm bảo giao nhận hay bộ xử lý receipt dài hạn trong MVP này. Cần thêm nếu yêu cầu giao nhận push được nâng thành cam kết nghiệp vụ. Cấu hình `MOBILE_EXPO_ACCESS_TOKEN` chỉ trên backend, không trong app/Git.
