# Kế hoạch số hóa hoạt động dự án NGO theo quy trình MEL

**Trạng thái:** Đề xuất để Chương trình, MEL, Tài chính và Ban Giám đốc thẩm định
**Ngày:** 24/09/2026
**Phạm vi:** Thiết kế nghiệp vụ và lộ trình code; chưa thay đổi code, cơ sở dữ liệu hoặc Charter đã duyệt.

## 1. Nhận xét hiện trạng

Yêu cầu lớn hơn một màn hình giao việc/lịch. Hệ thống cần theo dõi từ kế hoạch tháng, phê duyệt và công văn gửi đối tác tới phân công, chuẩn bị, thực địa, báo cáo MEL, rà chứng từ, sửa hồ sơ và ghi nhận quyết toán.

Hiện trạng code đã được rà soát:

- apps.task.Task giao cho một nhân viên, có ngày bắt đầu/hạn, trạng thái và bình luận; chưa có phân công nhóm, khung giờ, phụ thuộc hoặc liên kết hoạt động dự án.
- apps.planning.Event là lịch sự kiện theo thời gian/phòng ban; chưa có CBDA tham gia, mục tiêu/đầu ra, dự án hoặc kiểm tra trùng lịch.
- apps.project.Project mới có mã/tên, phòng ban và thời hạn; chưa quản lý grant/đối tác, chuỗi kết quả, chỉ số hoặc hoạt động.
- AnnualBudget là ngân sách năm theo phòng ban/hạng mục nội bộ, không phải ngân sách tài trợ theo dự án/hoạt động.
- OfficialDispatch đã quản lý công văn đi/đến và lịch sử xử lý. Nên liên kết phiên bản kế hoạch được duyệt với công văn đi hiện có, không tạo sổ công văn khác.
- Ma trận RBAC chưa có quyền Chương trình, Điều phối viên, CBDA và quyết toán dự án. Phân quyền theo phòng ban hiện tại chưa đủ để giới hạn hồ sơ theo dự án/grant.

Do đó, không nên nhồi nghiệp vụ NGO vào Task, Event hoặc AnnualBudget mà thiếu mô hình hoạt động. Nên mở rộng modular monolith hiện có, tái sử dụng Project, Task, OfficialDispatch, SharePoint storage và thông báo; thêm miền dữ liệu hoạt động dự án.

### Baseline kiểm tra ngày 24/09/2026

- Đã chạy `python src/manage.py check`: không có vấn đề.
- Đã chạy `python src/manage.py makemigrations --check --dry-run`: không phát hiện thay đổi model chưa có migration.
- Đã chạy 86 test thuộc asset, common, HRM, leave, payroll, security và M365: tất cả đạt trên SQLite test database tạm. Đây là regression test, không thay thế UAT của phòng ban.
- Đã xác nhận cấu hình kết nối SQL Server hiện tại trả về `connection.vendor=microsoft` và truy vấn chỉ đọc `SELECT 1` thành công. Chưa chạy toàn bộ test suite trên SQL Server vì chưa xác nhận database đang cấu hình là SIT dùng riêng và được phép tạo/xóa test database.
- Vì vậy, có thể bắt đầu UAT nội bộ có kiểm soát trên môi trường SIT với dữ liệu giả/ẩn danh; chưa có đủ bằng chứng để mở cho nhân viên dùng thật. Còn thiếu test trên SQL Server SIT, `check --deploy` trên cấu hình máy chủ, phân quyền/UAT theo vai trò, backup/restore và phê duyệt nghiệp vụ.

Project Charter hiện loại trừ Grant, ngân sách tài trợ, hoạt động phát triển cộng đồng và MEL. Cần phê duyệt mở rộng Charter trước khi code. Phạm vi giai đoạn đầu nên là lập kế hoạch, theo dõi dự toán/chi khai báo, chứng từ, rà soát và ghi nhận số tham chiếu kế toán; chưa thay thế phần mềm kế toán, sổ cái hoặc thanh toán.

## 2. Nguyên tắc nghiệp vụ

1. Tách nguồn lực/chi phí, hoạt động, đầu ra (output), kết quả (outcome) và mục tiêu. Số buổi hoặc số người dự là đầu ra, không tự chứng minh thay đổi ở người tham gia.
2. MEL được thiết kế ngay trong kế hoạch: mỗi hoạt động gắn với output/outcome hoặc nêu rõ là hoạt động hỗ trợ. Chỉ số cần có đơn vị, baseline nếu có, target, nguồn kiểm chứng, cách thu thập, người phụ trách, tần suất và phân tổ được phép.
3. Phiên bản được duyệt là căn cứ triển khai. Sau khi phát hành công văn, thay đổi ngày, ngân sách, mục tiêu hoặc đối tác phải có phiên bản điều chỉnh, lý do, người duyệt và lịch sử.
4. Dashboard dùng để điều phối tải việc, hạn, rủi ro và kết quả chương trình; không biến thành bảng xếp hạng CBDA. Xem kết quả phát triển trong bối cảnh và yếu tố ngoài kiểm soát.
5. Giai đoạn đầu lưu dữ liệu người tham gia dạng tổng hợp/phân tổ đã được duyệt. Không đưa danh sách định danh hoặc dữ liệu nhạy cảm vào ghi chú/dashboard chung. Phân quyền hồ sơ SharePoint theo nghiệp vụ.
6. Tiền dùng Decimal, giữ loại tiền và dòng ngân sách. Nếu quy đổi, cần lưu tỷ giá, ngày và nguồn theo quy định Finance/nhà tài trợ; không tự giả định.
7. SLA phải lưu mốc nộp/nhận/phản hồi/sửa/ghi sổ và tính theo lịch làm việc được cấu hình; tránh hard-code hạn ở nhiều màn hình.

## 3. Luồng nghiệp vụ mục tiêu

### Lập và duyệt kế hoạch tháng

- Ngày 25–27 tháng trước, Giám đốc dự án/nhóm Chương trình lập kế hoạch tháng tới: dự án/grant, đối tác, hoạt động, địa điểm, thời gian, mục đích, nhóm tham gia, output/outcome, chỉ số, rủi ro/giả định và dự toán.
- Chương trình rà thiết kế; MEL rà kết quả/chỉ số/nguồn kiểm chứng; Tài chính rà dòng ngân sách, trần và điều kiện chi; người có thẩm quyền phê duyệt.
- Không phát hành nếu thiếu phê duyệt bắt buộc hoặc vượt trần chưa được chấp thuận. Khi duyệt, khóa phiên bản làm căn cứ công văn và giao việc.

### Phát hành công văn và giao việc

- Đầu tháng triển khai, lập công văn đi từ kế hoạch đã duyệt, gắn người ký, đối tác nhận, ngày gửi và phụ lục. Liên kết hai chiều với kế hoạch/hoạt động.
- Sau phát hành, Điều phối viên xác nhận đối tác và giao CBDA, vai trò từng người, thời gian, checklist chuẩn bị và hạn. SLA giao việc nên cùng ngày hoặc ngày làm việc kế tiếp; cần NGO chốt.
- Chia công việc thành các gói: chuẩn bị, hậu cần, thực địa, báo cáo MEL, chứng từ, rà soát, sửa, ghi nhận quyết toán. Mỗi gói có người chính, người phối hợp, hạn, phụ thuộc và trạng thái.

### Kiểm tra trùng lịch CBDA

- Kiểm tra khi phân công/đổi người/ngày, so với hoạt động đã xác nhận, lịch bận của tổ chức và nghỉ phép đã duyệt. Chốt có đưa thời gian di chuyển/chuẩn bị vào lịch hay không.
- Hiển thị người bị trùng, hoạt động liên quan, khoảng thời gian và mức ảnh hưởng theo phạm vi quyền.
- Đề xuất: cảnh báo khi lưu nháp; chặn duyệt/phát hành nếu còn trùng; cho phép ngoại lệ bởi người được ủy quyền, có lý do và audit. Phải xét hai hoạt động cùng ngày nhưng khác địa điểm cần thời gian di chuyển.

### Chuẩn bị, thực địa và báo cáo

- Checklist chuẩn bị gồm địa điểm, vận chuyển, mua sắm, tài liệu, đối tác, an toàn và chứng từ cần thu; có CBDA phụ trách và trạng thái sẵn sàng.
- “Chuẩn bị trong vòng 5 ngày trước” cần thành hạn rõ: đề xuất hoàn tất checklist trước hoạt động ít nhất 5 ngày làm việc. Hoạt động duyệt sát ngày phải ghi ngoại lệ.
- Khi thực hiện, ghi thời gian thực tế, người tham gia là nhân sự, thay đổi, đầu ra, số liệu chỉ số, rủi ro/sự cố và bằng chứng. Ảnh, danh sách ký nhận, hóa đơn tuân thủ đồng thuận và safeguarding.
- Trong 2 ngày sau kết thúc, CBDA nộp báo cáo, chỉ số thực tế, bằng chứng, chênh lệch kế hoạch, bài học và việc theo dõi. MEL/Điều phối viên xác nhận hồ sơ đủ. Đề xuất dùng ngày làm việc.

### Rà soát và quyết toán

- CBDA nộp bộ chứng từ; lưu người nộp/thời điểm, tổng chi, dòng ngân sách, tệp và phiên bản.
- Kế toán phản hồi trong 2 ngày: chấp nhận hoặc trả lại, chỉ rõ khoản/chứng từ/lý do. Chốt đồng hồ SLA bắt đầu khi nộp hay khi bộ hồ sơ đủ.
- CBDA sửa trong 1 ngày sau phản hồi; mỗi lần nộp lại tạo phiên bản và timestamp.
- Khi chấp nhận, Kế toán ghi số tham chiếu, số đã quyết toán, chênh lệch/hoàn trả nếu có, ngày và người ghi nhận. Chỉ đóng hoạt động khi báo cáo và quyết toán bắt buộc hoàn tất.
- Trạng thái “đã quyết toán trên IHRMS” chỉ xác nhận ghi nhận theo quy trình; không đồng nghĩa đã chuyển tiền hay đã hạch toán vào sổ cái.

## 4. Mô hình dữ liệu và tích hợp

Tổ chức theo modular monolith. Trước khi chốt schema, kỹ thuật rà ERD, bảng hiện có và chuẩn đặt tên:

### Ranh giới đề xuất: nghiệp vụ riêng, trải nghiệm việc làm chung

Hoạt động dự án nên là một miền nghiệp vụ riêng, không phải một nhánh con của giao việc nhân sự. Giao việc hành chính/nhân sự tiếp tục phục vụ công việc nội bộ; miền Hoạt động dự án quản lý kế hoạch tháng, grant/đối tác, thiết kế hoạt động, lịch CBDA, MEL, dự toán, chứng từ và quyết toán. Mỗi miền có trạng thái, hồ sơ, quyền truy cập và báo cáo phù hợp với mục đích của nó.

Có thể dùng chung nền tảng và trải nghiệm người dùng ở những phần thực sự dùng chung:

- Một “Hộp việc của tôi” cho thấy việc hành chính và việc dự án, có nhãn nguồn, dự án, vai trò, hạn và trạng thái; bộ lọc cho phép CBDA/điều phối viên tập trung vào công việc của mình.
- Dùng chung thành phần giao việc, lịch, bình luận/trao đổi, tệp đính kèm, thông báo, nhắc hạn, audit và danh tính nhân viên. Dùng chung giao diện không đồng nghĩa mọi loại việc phải có cùng quy trình hoặc cùng quyền đọc.
- Việc dự án cần liên kết Activity/Milestone và membership của project/grant. Có thể tái sử dụng Task hiện có hoặc dùng một liên kết nhiệm vụ chung sau khi rà schema; luôn giữ owner chịu trách nhiệm chính, cộng tác viên, vai trò và phân quyền theo ngữ cảnh. Lịch chống trùng cần dùng các phân công có khung thời gian/địa điểm, kể cả thời gian di chuyển đã được tổ chức quy định.
- Dashboard Hoạt động dự án là không gian riêng, lấy dữ liệu theo project/grant và vai trò. Có thể dùng lại các thành phần biểu đồ/thẻ/bộ lọc từ dashboard chung, nhưng không trộn dữ liệu và quyền với dashboard nhân sự.
- Tách KPI nhân viên khỏi MEL: KPI nhân sự đánh giá trách nhiệm/hiệu suất công việc theo chính sách nhân sự; MEL theo dõi chuỗi hoạt động → output → outcome, chỉ số, mục tiêu, nguồn kiểm chứng, giả định và yếu tố ngoài kiểm soát. Có thể dùng chung thư viện hiển thị chỉ số, cảnh báo màu và bộ lọc, nhưng phải có model, công thức, chủ sở hữu, thời kỳ và báo cáo riêng. Không dùng số lượng hoạt động hoặc người tham gia làm đại diện cho outcome.

Thiết kế này cho CBDA một nơi xem và xử lý việc thống nhất, trong khi Chương trình/MEL/Tài chính vẫn truy vết được hồ sơ dự án và không làm nhiễu KPI nhân sự. Cơ sở về việc phân biệt activity/output/outcome và chỉ số tương ứng được mô tả trong [OECD Results Frameworks](https://www.oecd.org/en/publications/effective-results-frameworks-for-sustainable-development_aaa4bb52-en/full-report/component-6.html).

- Mở rộng Project; thêm Grant/Award gồm nhà tài trợ, đối tác, mã, thời hạn, loại tiền, trần và yêu cầu tuân thủ.
- Thêm Outcome, Output và IndicatorDefinition: đơn vị, baseline/target, nguồn, phương pháp, tần suất, người thu thập, phân tổ được phép.
- Thêm MonthlyWorkPlan có kỳ, phiên bản, trạng thái và lịch sử duyệt; Activity thuộc dự án/grant/kế hoạch, có đối tác, địa điểm, lịch, mục tiêu, kết quả dự kiến/thực tế, rủi ro và dữ liệu người hưởng lợi ở mức được phép.
- Thêm ActivityAssignment cho nhiều CBDA/vai trò/lịch tham gia; ActivityMilestone cho checklist, phụ thuộc, SLA, người phụ trách và lịch sử.
- Thêm ActivityBudgetLine, ActivityExpenseLine, SettlementSubmission/Review để đối chiếu ngân sách, chi thực tế, tệp, phản hồi và ghi nhận kế toán; không xóa/sửa âm thầm bản đã duyệt.
- Liên kết Task với Activity khi phù hợp; giữ tác vụ hành chính/nhân sự chung tách khỏi quy trình dự án. Có thể sinh Task từ milestone, nhưng Task đơn lẻ không thay hồ sơ hoạt động.
- Liên kết kế hoạch/hoạt động với OfficialDispatch hiện có; dùng SharePoint adapter đã có với thư viện/ACL theo chính sách.
- Dashboard riêng: lịch cá nhân/nhóm, hoạt động theo giai đoạn, việc đến hạn/quá hạn, xung đột, báo cáo/chứng từ chờ, dự toán/được duyệt/chi/đã chấp nhận, output và indicator so target, rủi ro và quyết định. Giới hạn theo project/grant.
- Thêm quyền lập kế hoạch, rà chương trình/MEL, duyệt ngân sách, ký/phát hành, điều phối, cập nhật/nộp báo cáo, rà chứng từ, ghi quyết toán, xem dashboard. Phân quyền theo thành viên dự án/grant; không suy ra quyền từ is_staff.

## 5. Lộ trình và ước lượng

Ước lượng lập kế hoạch **7–10 tuần sau khi chốt nghiệp vụ**, giả định một luồng phát triển ngắn, đại diện Chương trình/MEL/Tài chính/IT sẵn sàng phản hồi và không tích hợp phần mềm kế toán. Đây chưa phải cam kết ngày phát hành.

### Cổng 0 — Chốt quy trình/phạm vi (1–2 tuần)

Workshop theo hoạt động mẫu đã ẩn danh; ký swimlane/RACI; mở rộng Charter; chốt SLA, vai trò, chứng từ đầy đủ, ngoại lệ, tiền tệ, dữ liệu cá nhân, ma trận quyền, form và UAT. Không tạo migration trước cổng này.

### Cổng 1 — Kế hoạch và phê duyệt (1–2 tuần)

Dự án/grant/đối tác/kết quả, kế hoạch tháng có version, hoạt động/dự toán, các vòng rà soát và liên kết công văn đi. Kiểm thử phân quyền và trạng thái bất hợp lệ.

### Cổng 2 — Giao việc/lịch (1–2 tuần)

Phân công nhiều người, vai trò/khung lịch, checklist/milestone, phát hiện xung đột, ngoại lệ có audit và thông báo trong hệ thống.

### Cổng 3 — Thực địa/MEL (1–2 tuần)

Ghi kế hoạch/thực tế, chỉ số, báo cáo, rủi ro/bài học, tệp SharePoint, yêu cầu bổ sung và nhắc hạn; báo cáo tổng hợp theo project/grant/tháng/địa bàn/đối tác/indicator trong phạm vi quyền.

### Cổng 4 — Ngân sách/quyết toán (1–2 tuần)

Dự toán → duyệt → chi/chứng từ → kế toán trả/chấp nhận → CBDA sửa → kế toán ghi nhận; kiểm tra trần, số học, lịch sử và SLA. Không làm sổ cái/thanh toán nếu chưa được duyệt thành phạm vi.

### Cổng 5 — Kiểm thử/UAT/pilot (1–2 tuần)

Chạy check, migration review, unit/integration/permission tests; thử overlap và ghi đồng thời trên SQL Server SIT. UAT với Giám đốc dự án, Điều phối viên, CBDA, MEL, Kế toán, người ký và IT bằng dữ liệu giả/ẩn danh. Pilot 1 dự án/1 tháng; đối chiếu song song hồ sơ kiểm soát hiện hành và chỉ mở rộng sau biên bản nghiệm thu/rollback.

## 6. Tiêu chí nghiệm thu

- Lập được phiên bản kế hoạch tháng gắn activity với output/outcome/indicator, partner và dự toán; thiếu phê duyệt thì không phát hành.
- Công văn phát hành giữ đúng phiên bản; sửa sau phát hành phải có version/lý do/duyệt.
- Giao nhiều CBDA; trùng lịch được phát hiện; ngoại lệ có người có quyền và audit.
- Hạn 5/2/2/1 tính đúng theo lịch đã chốt; dashboard hiện người chịu trách nhiệm, hạn, quá hạn và thời gian chờ.
- Chứng từ có thể trả lại/nộp phiên bản mới; chỉ đóng quyết toán sau khi Kế toán ghi nhận tham chiếu và số liệu.
- Báo cáo output tách outcome; số liệu và thay đổi truy vết được.
- URL trực tiếp không vượt quyền project/grant; tệp SharePoint theo ACL.
- Các trường hợp tiền tệ, thời hạn, concurrency và migration được kiểm tra trên SQL Server SIT, không chỉ SQLite.

## 7. Quyết định cần NGO chốt

1. Các mốc 5/2/2/1 là ngày lịch hay ngày làm việc? Đề xuất ngày làm việc và lịch nghỉ tổ chức.
2. Ai duyệt cuối kế hoạch/ngân sách, ký công văn, phân công, báo cáo MEL và quyết toán? Có cần hai người duyệt độc lập?
3. Xung đột lịch: chấp nhận đề xuất cảnh báo bản nháp, chặn duyệt/phát hành, ngoại lệ có lý do/người duyệt?
4. Theo dõi một hay nhiều đồng tiền, tỷ giá theo quy tắc nào; IHRMS ghi nhận/đối chiếu hay phải tích hợp/hạch toán với phần mềm kế toán?
5. Giai đoạn đầu có thể chỉ lưu tổng số/phân tổ người tham gia không? Có yêu cầu lưu thông tin định danh/nhạy cảm trong IHRMS không?
6. Phân công nhóm: ai là một người chịu trách nhiệm chính (owner), ai là cộng tác viên; có cần ghi nhận vai trò CBDA theo từng hoạt động? Đề xuất một owner rõ ràng cùng danh sách cộng tác viên.
7. Checklist chứng từ: Finance cung cấp danh mục chứng từ bắt buộc theo loại chi, yêu cầu bản gốc/bản scan, cách xử lý khoản thiếu/sai và người có quyền chấp nhận ngoại lệ.
8. Pilot đầu: chọn một dự án và một tháng đã khép sổ hoặc hoạt động sắp tới có hồ sơ được phép dùng; chỉ gửi dữ liệu giả/ẩn danh cho thiết kế và UAT.

### Việc chủ dự án cần điều phối ở Cổng 0

1. Xin Ban Giám đốc xác nhận bằng văn bản việc mở rộng Project Charter để bao gồm grant/đối tác, hoạt động dự án, MEL và theo dõi quyết toán ở mức quy trình. Phần mềm kế toán, sổ cái và chuyển tiền vẫn ngoài phạm vi đợt đầu.
2. Tổ chức buổi rà soát 60–90 phút với Giám đốc dự án/Chương trình, Điều phối viên, đại diện MEL, Kế toán/Tài chính và IT. Chốt các câu 1–7 phía trên bằng câu trả lời và người phê duyệt cụ thể; có thể gửi phản hồi ngay trong tài liệu này.
3. Chọn một hoạt động mẫu, xóa tên người thụ hưởng, số định danh, thông tin sức khỏe, tài khoản ngân hàng và số liệu nhạy cảm; cung cấp quy trình, biểu mẫu và ví dụ số liệu đã ẩn danh.
4. IT xác nhận môi trường SQL Server SIT riêng, tên database không nhầm với production/ứng dụng khác, quyền tài khoản dịch vụ, cấu hình media/SharePoint và người phụ trách restore. Chưa chạy test suite SQL Server hoặc migration trước xác nhận này.
5. Gửi các quyết định và mẫu đã ẩn danh lại; sau đó mới tạo bản sao an toàn của repository trước khi bắt đầu thay đổi lớn, chốt ERD/RBAC và mở nhánh triển khai.

## 8. Tham chiếu

- OECD, [Effective Results Frameworks for Sustainable Development](https://www.oecd.org/en/publications/effective-results-frameworks-for-sustainable-development_aaa4bb52-en/full-report/component-9.html): liên kết hoạt động, output/outcome, chỉ số, nguồn, baseline/target, phương pháp, trách nhiệm và ngân sách.
- OECD DAC, [Evaluating Development Co-operation](https://www.oecd.org/en/publications/development-co-operation-tips-tools-insights-practices_be69e0cf-en/evaluating-development-co-operation_5602e1f7-en.html): đánh giá kết quả dự kiến/không dự kiến để phục vụ quyết định, học hỏi và trách nhiệm giải trình.
- USAID, [Monitoring, Evaluation, and Learning quick reference](https://www.usaid.gov/sites/default/files/2022-12/MEL_Module.QRG_.Final_.pdf): chất lượng dữ liệu và sử dụng dữ liệu theo dõi để điều chỉnh chương trình.

Các nguồn này cung cấp nguyên tắc/results framework; không thay chính sách nhà tài trợ, quy chế tài chính, safeguarding, lưu trữ dữ liệu hoặc thẩm quyền ký của NGO.
