# Hướng dẫn làm việc trong dự án IHRMS

## Nhánh làm việc duy nhất

Theo quyết định của chủ dự án ngày 02/10/2026, chỉ dùng `main` để phát triển, sửa lỗi, kiểm thử, chạy ứng dụng và triển khai. Không tạo hoặc tiếp tục làm việc trên nhánh khác trừ khi chủ dự án yêu cầu rõ ràng sau này. Trước mỗi đợt làm việc, xác nhận nhánh hiện tại là `main`, kiểm tra trạng thái working tree và đồng bộ `origin/main`; giữ nguyên mọi thay đổi cục bộ chưa commit, không reset/ghi đè để đổi nhánh. Các nhánh `master` và `chore/django-5.2-upgrade` đã hợp nhất chỉ còn để tra cứu lịch sử.

## Nhật ký thay đổi bắt buộc

Sau mỗi đợt thay đổi lớn (tính năng, sửa lỗi ảnh hưởng nghiệp vụ, migration, cấu hình triển khai, nâng dependency hoặc cập nhật bộ tài liệu), cập nhật **một nơi duy nhất**: [`docs/PROJECT_WORK_LOG.md`](docs/PROJECT_WORK_LOG.md).

Mỗi mục nhật ký cần có ngày, mục tiêu/phạm vi, tệp hoặc phân hệ liên quan, các bước đã làm, kiểm tra và kết quả, nhánh/commit nếu đã tạo, việc còn mở, và hành động cụ thể chủ dự án cần tự thực hiện nếu Codex không thể hoàn tất. Phân biệt rõ việc đã chạy/xác nhận với việc chỉ được người dùng báo cáo; không ghi bí mật, mật khẩu, token, nội dung `.env` hoặc dữ liệu cá nhân.

Ghi lại công việc trong cùng đợt ở một mục, không tạo nhật ký rải rác theo từng thao tác nhỏ. Cập nhật mục đó trước khi kết thúc hoặc bàn giao công việc. README, changelog, Review và hướng dẫn nghiệp vụ chỉ liên kết tới nhật ký này khi cần; không sao chép nhật ký sang nhiều nơi.

## Khi bị giới hạn công cụ hoặc quyền

Không dừng ở câu “không làm được”. Trong nhật ký, ghi rõ thao tác chưa thực hiện, lý do cụ thể, công cụ/quyền còn thiếu và hướng dẫn từng bước người phụ trách có thể làm; ghi lệnh chính xác khi phù hợp. Nếu có thể tiếp tục phần độc lập an toàn, hãy làm trước. Sau khi chủ dự án thực hiện, ghi kết quả và tiếp tục kiểm tra.

## Quy trình hoàn tất

Khi được giao review, đọc [hướng dẫn review dự án](docs/Huong_Dan_Review_Du_An.md). Phân biệt FULL (toàn mã hiện tại) với CHANGES (diff), REVIEW (không sửa) với FIX (được sửa). Mặc định REVIEW nếu yêu cầu chưa cho phép sửa; không dùng diff rỗng trên `main` để kết luận review tổng thể đã hoàn tất. Reviewer Sixth tại [`.sixth/agents/code-review.md`](.sixth/agents/code-review.md) là định nghĩa riêng của Sixth, không đồng nghĩa đã có hoặc đã chạy Bugbot.

1. Đọc trạng thái Git và tài liệu liên quan trước khi sửa.
2. Thực hiện thay đổi trong phạm vi đã yêu cầu; không đưa `.env`, database, dữ liệu thật hay bí mật vào Git.
3. Chạy kiểm tra phù hợp và ghi chính xác lệnh/kết quả trong nhật ký.
4. Cập nhật `docs/PROJECT_WORK_LOG.md` cùng đợt thay đổi.
5. Báo rõ tệp đã đổi, kiểm tra đạt/chưa đạt, commit/push nếu có, và bước tiếp theo cần người dùng làm.
