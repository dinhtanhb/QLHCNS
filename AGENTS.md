# Hướng dẫn làm việc trong dự án IHRMS


## Nhánh làm việc duy nhất

Theo quyết định của chủ dự án ngày 02/10/2026, chỉ dùng `main` để phát triển, sửa lỗi, kiểm thử, chạy ứng dụng và triển khai. Không tạo hoặc tiếp tục làm việc trên nhánh khác trừ khi chủ dự án yêu cầu rõ ràng sau này. Trước mỗi đợt làm việc, xác nhận nhánh hiện tại là `main`, kiểm tra trạng thái working tree và đồng bộ `origin/main`; giữ nguyên mọi thay đổi cục bộ chưa commit, không reset/ghi đè để đổi nhánh. Các nhánh `master` và `chore/django-5.2-upgrade` đã hợp nhất chỉ còn để tra cứu lịch sử.

## Quy tắc một người ghi tại một thời điểm

Chỉ một tác nhân được phép thực hiện thay đổi và ghi mã tại một thời điểm. Tác nhân nào làm xong phải hoàn tất kiểm thử, commit, push lên origin/main và cập nhật nhật ký công việc đầy đủ trước khi tác nhân khác bắt đầu lượt làm việc mới. Đầu mỗi lượt, tác nhân phải xác minh trạng thái Git (git status --short, git branch --show-current là main, git fetch origin main, so origin/main với HEAD) và đọc 3 mục nhật ký mới nhất. Nếu phát hiện thay đổi chưa commit hoặc commit mới chưa có nhật ký tương ứng, phải dừng và báo chủ dự án, tuyệt đối không ghi đè.

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
5. Sau mỗi đợt sửa mã, làm sạch tệp, mã và nội dung trong phạm vi: sửa lỗi mã hóa/định dạng, bỏ phần thừa do đợt đó tạo; giữ nguyên thay đổi ngoài phạm vi và dữ liệu vận hành. Không dọn bằng reset hoặc xóa hàng loạt.
6. Kiểm thử trên nguồn cuối sau khi dọn. Tạo bản sao mã nguồn review ngoài repository từ các tệp nguồn được theo dõi/stage; loại `.env` (giữ `.env.example`), database, media/uploads, log, đầu ra runtime và thông tin đăng nhập/bí mật. Thêm manifest nguồn/commit hoặc tree, mở lại bản sao và xác minh SHA-256 từng tệp. Đây không phải backup phục hồi dữ liệu.
7. Commit các thay đổi đã kiểm và nhật ký trên `main`, push `origin main`, rồi xác minh SHA remote khớp HEAD và trạng thái ahead/behind. Theo yêu cầu chủ dự án ngày 13/10/2026, đây là bước mặc định đã được cho phép sau mỗi đợt sửa mã; không hỏi lại. Chỉ bỏ commit/push khi chủ dự án yêu cầu rõ trong đợt đó. Không force-push hoặc deploy theo quyền này.
8. Báo tệp đã đổi, kết quả kiểm tra/giới hạn, đường dẫn bản sao, SHA commit/push và việc cần người dùng làm. Nếu kiểm tra hoặc push không hoàn tất, ghi lỗi và hướng xử lý trong nhật ký; không báo hoàn tất sai.

## Migration và thay đổi schema

Model và migration phải đi trong commit riêng có kế hoạch áp dụng/hoàn tác. Trước khi giao, chạy `sqlmigrate` trên SQLite và cấu hình SQL Server tạm, đối chiếu SQL thực với phạm vi được duyệt, rồi ghi nguồn yêu cầu nghiệp vụ truy vết được trong `PROJECT_WORK_LOG.md`. Dùng `ops/check_migration_state.py` để kiểm trạng thái chỉ đọc; công cụ này không thay thế backup, restore thử, migrate trên bản sao hay UAT. Không áp migration vào DB vận hành nếu chưa xác nhận đúng đích, backup và restore xác minh.

## Kiểm thử luồng nghiệp vụ trên trình duyệt

Theo yêu cầu chủ dự án ngày 13/10/2026, sau mỗi đợt sửa mã phải kiểm thử lại các luồng nghiệp vụ bị ảnh hưởng trên ứng dụng đang chạy trong trình duyệt, không chỉ kiểm tra HTTP hoặc HTML tĩnh. Thao tác tạo/sửa/gửi/duyệt cần kiểm tra thông báo, trang đích, dữ liệu đã lưu và chỉ số Dashboard liên quan theo đặc tả đã duyệt. Với sửa giao diện, kiểm tra cả sáng/tối, màn hình rộng/hẹp, tên/nội dung dài và thao tác bàn phím.

Được tạo dữ liệu giả để kiểm thử; mặc định dùng database/media và tài khoản thử nghiệm tách biệt, không sửa/xóa hồ sơ thật. `ops/run_browser_uat.py` cung cấp các luồng hồi quy Dashboard Đợt 1 và hồ sơ/hợp đồng/nghỉ phép trên DB dùng một lần; bổ sung luồng tương ứng khi sửa phân hệ khác. Ghi lệnh, backend, luồng, kết quả, ảnh/bằng chứng và giới hạn vào cùng mục `docs/PROJECT_WORK_LOG.md`. Nếu kết nối trình duyệt không hoạt động, ghi lỗi cụ thể, tiếp tục phần kiểm tra độc lập an toàn và không tuyên bố đã UAT phiên trình duyệt của người dùng. Chỉ báo hoàn tất sau khi chạy lại các kiểm tra liên quan trên nguồn cuối.


Mọi thay đổi CSS dùng chung, `ui-card`, `ui-scroll`, dải lọc hoặc template có biểu mẫu in bắt buộc chạy `ops/run_print_layout_uat.py` và so ảnh/số đo PDF trong cùng lượt; mỗi lần sửa `print_forms.css` phải tăng `?v=` trong `base.html`. Không dùng số trang hoặc HTTP/HTML đạt để thay thế kiểm tra mẫu chuẩn, màu in, viền, ngắt trang và khoảng ký. Ghi trong nhật ký vì sao kiểm thử cũ bỏ sót lỗi in nếu đang sửa hồi quy.

Mọi thay đổi CSS dùng chung hoặc template có form/bảng/thẻ phải chạy `ops/run_layout_alignment_audit.py` trước khi commit; ghi số vi phạm trước/sau, backend, vai trò, độ rộng và thư mục bằng chứng vào nhật ký. Chỉ đóng giai đoạn khi lượt quét toàn bộ route/vai trò ở 1920/1756/1440/1280/1024/768/390px, sáng/tối có 0 vi phạm ngoài `ops/layout_waivers.json`. Miễn trừ phải có route, tiêu chí, lý do và người duyệt; không tự miễn trừ để làm xanh kiểm thử. Bàn giao kèm contact sheet trước/sau các trang chính theo mô-đun ở 1756px và 390px. So hợp đồng form/truy vấn với baseline trên cùng DB giả bằng `ops/run_form_contract_uat.py`; giữ bản in độc lập với lưới màn hình.
