# Hướng dẫn làm việc trong dự án IHRMS

## Nhật ký thay đổi bắt buộc

Sau mỗi đợt thay đổi lớn (tính năng, sửa lỗi ảnh hưởng nghiệp vụ, migration, cấu hình triển khai, nâng dependency hoặc cập nhật bộ tài liệu), cập nhật **một nơi duy nhất**: [`docs/PROJECT_WORK_LOG.md`](docs/PROJECT_WORK_LOG.md).

Mỗi mục nhật ký cần có ngày, mục tiêu/phạm vi, tệp hoặc phân hệ liên quan, các bước đã làm, kiểm tra và kết quả, nhánh/commit nếu đã tạo, việc còn mở, và hành động cụ thể chủ dự án cần tự thực hiện nếu Codex không thể hoàn tất. Phân biệt rõ việc đã chạy/xác nhận với việc chỉ được người dùng báo cáo; không ghi bí mật, mật khẩu, token, nội dung `.env` hoặc dữ liệu cá nhân.

Ghi lại công việc trong cùng đợt ở một mục, không tạo nhật ký rải rác theo từng thao tác nhỏ. Cập nhật mục đó trước khi kết thúc hoặc bàn giao công việc. README, changelog, Review và hướng dẫn nghiệp vụ chỉ liên kết tới nhật ký này khi cần; không sao chép nhật ký sang nhiều nơi.

## Khi bị giới hạn công cụ hoặc quyền

Không dừng ở câu “không làm được”. Trong nhật ký, ghi rõ thao tác chưa thực hiện, lý do cụ thể, công cụ/quyền còn thiếu và hướng dẫn từng bước người phụ trách có thể làm; ghi lệnh chính xác khi phù hợp. Nếu có thể tiếp tục phần độc lập an toàn, hãy làm trước. Sau khi chủ dự án thực hiện, ghi kết quả và tiếp tục kiểm tra.

## Quy trình hoàn tất

1. Đọc trạng thái Git và tài liệu liên quan trước khi sửa.
2. Thực hiện thay đổi trong phạm vi đã yêu cầu; không đưa `.env`, database, dữ liệu thật hay bí mật vào Git.
3. Chạy kiểm tra phù hợp và ghi chính xác lệnh/kết quả trong nhật ký.
4. Cập nhật `docs/PROJECT_WORK_LOG.md` cùng đợt thay đổi.
5. Báo rõ tệp đã đổi, kiểm tra đạt/chưa đạt, commit/push nếu có, và bước tiếp theo cần người dùng làm.
