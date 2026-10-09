# Sử dụng biểu mẫu hành chính nhân sự

Mở **Nhân sự → Biểu mẫu HCNS**, hoặc đường dẫn `/portal/hcns-forms/` trên máy chủ IHRMS. Biểu mẫu tuyển dụng có lối vào riêng tại **Tuyển dụng → Biểu mẫu tuyển dụng**; Thang bảng lương nằm trong **Kế toán**. Bộ layout được xây dựng từ 26 tệp tham khảo chủ dự án cung cấp tại `docs/templates/hcns/`. Nội dung được chuyển thành các trường soạn thảo, bảng dữ liệu và vùng ký; đây không phải bản sao giữ nguyên từng pixel của Word/Excel gốc.

## Soạn và xuất

1. Chọn mẫu. Có thể chọn hồ sơ nhân viên tại danh mục nếu tài khoản có quyền xem toàn bộ và xuất dữ liệu nhân sự; nhân viên có thể chọn hồ sơ của mình.
2. Nhập phần còn thiếu, kiểm tra các bảng. Dùng **Thêm dòng / Xóa dòng** cho bảng có số dòng linh hoạt. Tiêu chí đánh giá và tên các mục checklist cố định không được sửa qua trình duyệt.
3. Bấm **Cập nhật bản xem trước**, rồi **In / lưu PDF**. PDF được tạo bằng hộp thoại in của trình duyệt. Nếu vừa sửa nội dung, phải cập nhật bản xem trước trước khi in.
4. Bấm **Tải Word (.docx)** hoặc **Tải Excel (.xlsx)** để xuất trực tiếp nội dung đang nhập đã qua kiểm tra. Sau khi chỉnh sửa tiếp bằng Office, người phụ trách kiểm tra lại bố cục và nội dung trước khi ký.

Bản đang soạn không được lưu tự động. Với biểu mẫu thông thường, nội dung chỉ tồn tại trên trang; tải tệp trước khi rời trang. Các bản xuất mang nhãn **BẢN SOẠN THẢO** và không tự gửi đơn, thay đổi lương, kết thúc hợp đồng, duyệt đề nghị hoặc xác nhận xử lý tài sản.

Riêng bốn mẫu quyết định nhân sự, người có quyền quản lý HR chọn **Lưu bản nháp quyết định** để lưu nội dung vào hệ thống. Mở **Nhân sự → Quản lý quyết định** để tìm, sửa bản nháp, trình duyệt và xem lịch sử. Sau khi được duyệt, HR tải PDF đã ký lên để ghi nhận ban hành; chỉ PDF này là bản ban hành có thể tải lại. Word và chức năng in từ nội dung lưu vẫn giữ nhãn **BẢN SOẠN THẢO**. Lưu/duyệt/ban hành văn bản không tự thay đổi bản ghi lương, điều chuyển, bổ nhiệm hay hồ sơ nhân viên.

Người trình không được tự duyệt quyết định của mình. Khi bị từ chối, HR nhập nội dung sửa, lưu lại thành bản nháp rồi trình duyệt lại. PDF ban hành được giới hạn truy cập theo quyền quyết định nhân sự và nhân viên có tên trong quyết định; nhân viên chỉ thấy trạng thái cùng nút tải PDF đã ký, không thấy bản Word nháp hay lịch sử duyệt. Tệp không được đưa vào thư viện chung. Không sao chép chữ ký, tên người phê duyệt hay dữ liệu minh họa đã điền trong tệp gốc vào bản mới.

Chuông thông báo nội bộ được cập nhật khi HR trình duyệt (báo HR Manager/Giám đốc có tài khoản gắn hồ sơ nhân viên), khi duyệt hoặc từ chối (báo người trình), và khi ban hành (báo nhân viên liên quan cùng người trình). Mỗi thông báo mở đúng trang quyết định; nhân viên nhận chỉ xem/tải PDF đã ký. Đây là thông báo trong IHRMS, không tự gửi email; tài khoản chưa gắn hồ sơ nhân viên không có hộp chuông nhận thông báo.

## Các nhóm được hỗ trợ

- **Nhân sự:** phiếu thông tin cán bộ; danh mục hồ sơ nhân viên mới và nghỉ việc; đánh giá nhân viên với 60 tiêu chí; đơn xin nghỉ việc; bàn giao công việc; bảng kiểm bàn giao nghỉ việc; 12 câu hỏi phỏng vấn thôi việc.
- **Quyết định:** tiếp nhận/bổ nhiệm/miễn nhiệm; chấm dứt hợp đồng; điều chỉnh vị trí và lương; nghỉ thai sản. Trường căn cứ và các điều được soạn lại trước khi xuất; người ký kiểm tra văn bản áp dụng, thẩm quyền và nội dung. Mẫu điều chỉnh lương được đánh số điều liên tục thay cho khoảng trống đánh số trong tài liệu tham khảo.
- **Nghỉ:** nghỉ phép, nghỉ không lương và nghỉ bù; có thông tin bàn giao và ba vùng ký. Nút **In / Word** xuất hiện ở các đơn có mã loại `AL`, `UL`, `CO`; các loại nghỉ khác phải chọn mẫu thủ công nếu phù hợp.
- **Kế toán:** ma trận chức vụ/cấp/bậc từ `BangLuong.xlsx`. Đây là thang bảng lương, không phải bảng tính lương tháng. Mẫu chỉ hiển thị và cho truy cập với vai trò Kế toán, Ban giám đốc và superuser. Mẫu gốc chỉ chứa giá trị, không có công thức; thay tham số tham chiếu không tự tính lại ma trận. Không liên kết các mức lương trong mẫu vào payroll.
- **Tuyển dụng:** phiếu phỏng vấn với thang điểm 20/20/20/15/15/10; tổng hợp kết quả phỏng vấn Excel; bốn TOR (cán bộ dự án, điều phối viên tỉnh, trợ lý tỉnh, kế toán dự án). Nội dung TOR mặc định lấy từ tài liệu tham khảo; cần rà lại địa bàn, nhà tài trợ và tên dự án.
- **Tài sản:** bảng kiểm kê và nhãn thiết bị Excel; đề nghị, quyết định và biên bản xử lý tài sản Word. Tệp `.xlsm` tham khảo không được thực thi; bản xuất `.xlsx` không chứa macro. Các sheet nhãn lấy mã và tên thiết bị đang soạn. Không suy diễn quy tắc phân tích mã thiết bị từ các ví dụ cũ.

## Dropdown dùng chung trên các biểu mẫu

Toàn bộ 26 trang dùng chung bộ chọn cho các trường có nguồn danh mục: nhân viên, chức vụ/vị trí, phòng ban, chức vụ mới, quản lý, người ký, người nhận bàn giao, người phỏng vấn và dự án. Mỗi lựa chọn nhân viên hiển thị tên, mã và chức vụ để phân biệt người trùng tên; bản xuất dùng tên/chức vụ, không in ID của dropdown.

Chọn nhân viên sẽ tự điền các thông tin tương ứng có trong hồ sơ và trong mẫu: chức vụ, phòng ban, quản lý, ngày sinh/ngày vào làm, liên hệ, CCCD, thuế và BHXH. Khi đổi sang người khác, các thông tin chưa có trong hồ sơ như ngân hàng, ngày cấp CCCD và các giá trị nghiệp vụ của người trước như mức lương đề xuất, ngày hiệu lực/đơn nghỉ được xóa để tránh mang nhầm dữ liệu. Kiểm tra lại các mục này trước khi xuất. Người ký luôn phải chọn riêng.

Phiếu phỏng vấn chọn từ **Ứng viên**, tự điền điện thoại/email/địa chỉ; chọn nhân viên ở danh mục chung không tự biến người đó thành ứng viên. Bảng tổng hợp điểm có dropdown ứng viên, mã ứng viên, người chấm và vị trí; chọn ứng viên liên kết đúng mã, máy chủ từ chối mã và tên thuộc hai hồ sơ khác nhau. Giới tính chọn từ danh mục hiện có; thông tin ứng viên chưa được lưu như năm sinh vẫn nhập riêng.

Bảng thành viên/hội đồng có dropdown nhân viên, chức vụ, vai trò và hình thức tham gia. Bảng tài sản chọn tên hoặc mã thiết bị, tự điền mã/tên còn lại cùng loại, nhãn hiệu, số lượng và các thuộc tính đã ghi nhận. Dòng thêm mới cũng dùng dropdown; máy chủ từ chối tên và mã thuộc hai tài sản khác nhau. Tình trạng kiểm kê dùng danh mục hiện có; mô tả hư hỏng trên biên bản xử lý vẫn là nội dung tự do.

Danh sách tuân theo quyền của người dùng, không mở thêm quyền xem hồ sơ. Người chỉ có quyền tài sản vẫn đọc/xuất được thành viên đã ghi trong đợt kiểm kê được phép xem, nhưng không nhận toàn bộ danh bạ hoặc thông tin cá nhân HR. Hồ sơ đã xóa không được chọn; dữ liệu nguồn có danh mục không còn phù hợp được báo để kiểm tra. Khi chưa có hồ sơ/danh mục cần thiết, tạo tại phân hệ nguồn trước khi chọn. Các ô không có danh mục lưu trữ (căn cứ, lý do, nhận xét, ngân hàng, địa điểm tự do, số quyết định...) tiếp tục cho nhập.

## Quyết định tiếp nhận / bổ nhiệm / miễn nhiệm

Họ tên cán bộ và người ký chọn từ danh sách hồ sơ chưa xóa trong phạm vi quyền của người dùng, hiển thị kèm mã cán bộ và chức vụ để phân biệt người trùng tên. Chọn cán bộ sẽ tự điền chức vụ hiện tại và phòng ban. Có thể chọn lại phòng ban/chức vụ từ danh mục và chọn chức vụ mới phù hợp quyết định. Nếu để trống chức vụ mới, bản soạn dùng chức vụ hiện tại; cần kiểm tra lại trước khi ký. Hồ sơ chưa có trong hệ thống cần được tạo qua phân hệ Nhân sự trước khi chọn.

Lương thỏa thuận nhập bằng số đồng nguyên (không nhập dấu phân cách hàng nghìn vào ô số). Lương bằng chữ tự cập nhật khi nhập và được máy chủ tính lại khi xem trước/xuất; không nhập tay. Quy tắc này cũng áp dụng mẫu quyết định điều chỉnh lương. Để trống lương thì phần bằng chữ trống; nhập 0 được đọc là “Không đồng chẵn”.

Bản xem trước/in và Word của mẫu này dùng bố cục hai cột tổ chức/quốc hiệu, số quyết định/ngày ở đầu trang, tiêu đề “QUYẾT ĐỊNH” và dòng V/v theo hành động đã chọn; căn cứ in nghiêng, điều khoản cùng dòng nhãn, nơi nhận và chữ ký ở hai phía. Tên người ký được in dưới khoảng trống ký, không chèn chữ ký thật. Nội dung điều khoản vẫn có thể chỉnh trước khi xuất; khi tự sửa Điều 1, cần tự đối chiếu với hành động tiếp nhận/bổ nhiệm/miễn nhiệm đã chọn. Không tự thực hiện quyết định hay cập nhật hồ sơ nhân sự.

## Điểm tuyển dụng

Theo xác nhận của chủ dự án ngày 06/10/2026, **tính trung bình cả điểm phỏng vấn và điểm bài kiểm tra**.

- Mỗi người chấm có một dòng; dùng cùng mã ứng viên để nhóm đúng người. Cùng mã phải có cùng họ tên.
- Điểm phỏng vấn của một dòng là tổng đủ sáu tiêu chí; bài kiểm tra là tổng đủ hai điểm lập kế hoạch và ngân sách (tối đa 25 điểm mỗi mục).
- Điểm trung bình tính trên tất cả các dòng của ứng viên. Một dòng còn thiếu điểm thì điểm trung bình tương ứng và tổng cộng chưa được tính. Số 0 được coi là điểm hợp lệ.
- Tổng cộng là trung bình phỏng vấn cộng trung bình bài kiểm tra. Không có ngưỡng tuyển/loại tự động; kết quả tuyển dụng do người có trách nhiệm nhập.
- Excel chứa công thức có điều kiện kiểm tra điểm thiếu và yêu cầu tính lại khi mở. Nhóm ứng viên trong công thức được xác định khi xuất; nếu đổi mã ứng viên hoặc thêm người chấm trong Excel, cần xuất lại từ trang soạn mẫu để cập nhật phạm vi nhóm.

## Hồ sơ nguồn và quyền

Tại danh sách mẫu, chọn nhân viên ở ô “Điền thông tin từ hồ sơ nhân viên” sẽ áp dụng ngay (nút “Chọn hồ sơ” vẫn có thể dùng). Mọi liên kết mẫu giữ nhân viên đã chọn; nút quay lại “Biểu mẫu HCNS” giữ lựa chọn này. Chọn “Mẫu trắng” để bỏ nhân viên.

Mỗi mẫu chỉ điền các trường tương ứng có trong dữ liệu nguồn: tên, vị trí, phòng ban, ngày sinh/năm sinh/giới tính, CCCD, thuế/BHXH, điện thoại/email/địa chỉ, ngày vào/nghỉ và quản lý trực tiếp nếu mẫu có các ô đó. Các mẫu có lương lấy lương cơ bản đang hiệu lực tại ngày mở mẫu khi người dùng có quyền xem lương; trường hợp không có hoặc có nhiều mức chồng lấn sẽ để trống. Lương/chức vụ hiện hành là dữ liệu tham khảo để người soạn xác nhận mức/chức vụ mới, không phải quyết định tự động. Đổi cán bộ trong dropdown của mẫu bổ nhiệm sẽ bỏ lương đã điền của cán bộ trước; có thể mở lại từ danh sách mẫu để lấy lương tham khảo của người mới.

Quyết định chấm dứt điền số hợp đồng nếu có đúng một hợp đồng Active trong thời hạn; ngày hợp đồng để trống vì hệ thống hiện chỉ lưu ngày bắt đầu, chưa lưu ngày ký. Không tự chọn đơn nghỉ, ngày hiệu lực, người ký, tài khoản ngân hàng, kết quả đánh giá, điểm tuyển dụng hoặc tài sản để thanh lý. Các trường chưa có dữ liệu cần nhập bổ sung. Mẫu thang bảng lương, TOR hoặc tài sản không có trường nhân viên tương ứng vẫn giữ hồ sơ đang chọn để chuyển mẫu, không biến tên nhân viên thành người ký/thành viên hội đồng hay tự chọn tài sản của người đó. Bảng tổng hợp tuyển dụng phải chọn ứng viên từ phân hệ Tuyển dụng; không dùng mã nhân viên thay mã ứng viên.

Các liên kết được thêm tại trang chi tiết nhân viên, ứng viên, hồ sơ vòng đời, đơn nghỉ, đợt kiểm kê, đề nghị thanh lý và danh sách lương cơ bản. Máy chủ kiểm tra quyền và phạm vi hồ sơ mỗi lần xem/xuất; cờ `is_staff` không cấp quyền xuất nhân sự.

Thông tin cá nhân chỉ lấy cho chính người dùng hoặc người có cả quyền xem toàn bộ nhân viên và xuất dữ liệu nhân sự. Tuyển dụng yêu cầu quyền HR; quyết định yêu cầu quyền tương ứng; riêng Thang bảng lương chỉ cho Kế toán, Ban giám đốc và superuser; tài sản dùng quyền xem tài sản; đơn nghỉ áp dụng phạm vi đọc đơn hiện có. Hồ sơ nguồn bị xóa không được dùng. Tên trường, tiêu chí, nhãn và đường dẫn nguồn được xác định trong mã, không đọc tùy ý tệp từ tham số URL.

Loại đơn nguồn phải khớp mẫu: `AL` cho nghỉ phép, `CO` cho nghỉ bù, `UL` cho nghỉ không lương và `ML` cho quyết định thai sản. Ngày/giờ kết thúc phải từ ngày/giờ bắt đầu trở đi, kể cả dữ liệu lấy từ hồ sơ nguồn. Dòng nhập số 0 được giữ nguyên; dòng chấm điểm có điểm 0 vẫn phải có mã, tên ứng viên và người chấm.

Nếu đợt kiểm kê vượt 50 tài sản hoặc danh sách thành viên vượt giới hạn soạn, trang cho xem và xuất đầy đủ, không cắt mất dòng; chỉnh sửa tại phân hệ nguồn. Xuất tệp ghi sự kiện audit với tên loại mẫu, không ghi nội dung nhập, mã định danh cá nhân hoặc query string. Trang và phản hồi tải tệp không được cache.

Các tệp tham khảo gốc vẫn thuộc chủ dự án, không được dùng làm tài nguyên tải công khai. Không đưa tệp có thông tin nhân viên/ứng viên thật hoặc chữ ký lên Git. Mã layout dùng `src/apps/document/hcns/reference_content.json` chỉ chứa nội dung mẫu trắng, tiêu chí, TOR và ma trận lương tham khảo đã trích chọn; không phụ thuộc việc triển khai thư mục tài liệu gốc.

## Từ NV & Hồ sơ sang thủ tục / biểu mẫu

Trong **Nhân sự → NV & Hồ sơ → Thao tác**, chọn Điều chuyển, Bổ nhiệm, Nâng lương, Khen thưởng, Kỷ luật, Gia hạn HĐ hoặc Biểu mẫu HCNS. Sửa hồ sơ vẫn mở trang cập nhật thông tin nhân viên; sau khi lưu, liên kết Biểu mẫu HCNS trên hồ sơ lấy các giá trị mới đã ghi nhận.

Điều chuyển, Bổ nhiệm và Nâng lương có hai cách lưu: **Ghi nhận** quay lại hồ sơ; **Ghi nhận và soạn quyết định** lưu thành công rồi mở bản soạn tương ứng. Nhập lỗi sẽ giữ nguyên luồng báo lỗi, không chuyển sang quyết định. Trang Lịch sử & Hợp đồng có liên kết soạn lại từng bản ghi, kể cả mức lương cũ và thay đổi chưa tới ngày hiệu lực.

- Nâng lương → Quyết định điều chỉnh vị trí và mức lương: lấy chính mức lương và ngày hiệu lực của dòng đã chọn, tự đổi lương bằng chữ.
- Bổ nhiệm → Quyết định tiếp nhận / bổ nhiệm / miễn nhiệm: chọn sẵn Bổ nhiệm, chức vụ cũ, chức vụ mới và ngày hiệu lực đã ghi nhận.
- Điều chuyển → Quyết định điều chỉnh vị trí và mức lương: lấy phòng ban đích, văn phòng làm việc và ngày hiệu lực đã ghi nhận. Kiểm tra/sửa các điều vì mẫu gốc kết hợp điều chuyển, bổ nhiệm và lương; thao tác điều chuyển riêng không ghi nhận một quyết định tăng lương hay bổ nhiệm.
- Khen thưởng / Kỷ luật: ghi nhận và xem lịch sử; bộ 26 mẫu hiện chưa có mẫu quyết định riêng cho hai thủ tục này.
- Hợp đồng: Tạo hợp đồng mới từ hồ sơ chọn sẵn đúng nhân viên. Gia hạn ghi nhận phụ lục và ngày kết thúc mới; mở từng hợp đồng trong lịch sử để xem hoặc thêm phụ lục. Bộ mẫu hiện chưa có mẫu hợp đồng / phụ lục để xuất Word theo mẫu tham khảo.

Các quyết định lấy dữ liệu qua `salary_id`, `promotion_id` hoặc `transfer_id`, chỉ một nguồn mỗi bản soạn. Máy chủ kiểm tra quyền xuất dữ liệu, phạm vi nhân viên và quyền xem lương; không ghép tùy ý mã nhân viên với mã bản ghi. Ngày hiệu lực trong tương lai vẫn dùng đúng bản ghi, không lấy mức lương/chức vụ/phòng ban mới nhất thay thế. Các thông tin không có snapshot ở dòng nghiệp vụ được tham khảo từ hồ sơ hiện tại; lý do điều chuyển/bổ nhiệm hiển thị để người soạn kiểm tra và bổ sung vào nội dung phù hợp. Số quyết định, ngày ký và người ký cần nhập/xác nhận riêng.

**Mẫu cần bổ sung:** quyết định khen thưởng, quyết định kỷ luật, hợp đồng lao động và phụ lục gia hạn. Đặt bản mẫu trắng tại `docs/templates/hcns/`, tránh dữ liệu thật và chữ ký; chưa đưa các tệp này vào Git. Không dùng quyết định miễn nhiệm thay cho kỷ luật hoặc mẫu điều chỉnh lương thay cho phụ lục hợp đồng.

Kết quả kiểm tra và các phần chưa xác nhận nằm tại [nhật ký công việc](PROJECT_WORK_LOG.md).

## Quy tắc tên tệp xuất

Tệp được tạo mới dùng cú pháp **`LoạiTàiLiệu_MãHồSơ_YYYYMMDD.ext`**, không dấu, không chứa ký tự cấm của Windows. Ví dụ `QD_NangLuong_VH-999_20261006.docx`. Word và Excel lấy cùng tên hiển thị trên trang; sau khi đổi người/ngày/nội dung quyết định, bấm **Cập nhật bản xem trước** để kiểm tra lại. Khi in/lưu PDF, trang đặt tên này làm tên gợi ý của trình duyệt; hộp thoại lưu có thể cho người dùng đổi tên.

- Quyết định nhân sự dùng mã nhân viên đã chọn và **Ngày lập trên văn bản** làm ngày ký dự kiến, không dùng ngày tải hoặc ngày hiệu lực. Mẫu bổ nhiệm đổi tiền tố theo Tiếp nhận/Bổ nhiệm/Tái bổ nhiệm/Miễn nhiệm (`QD_TiepNhan`, `QD_BoNhiem`, `QD_TaiBoNhiem`, `QD_MienNhiem`); điều chỉnh lương dùng `QD_NangLuong`, chấm dứt HĐ dùng `QD_ChamDutHopDong`, thai sản dùng `QD_ThaiSan`.
- Hồ sơ, đơn nghỉ, đánh giá, bàn giao dùng mã nhân viên và ngày lập. Chưa chọn nhân viên ghi `ChuaChonNV`; chưa có ngày quyết định ghi `ChuaKy`, ngày của mẫu khác ghi `ChuaCoNgay`. Không suy ra mã từ họ tên, không tự đổi ngày trống thành ngày tải.
- Phỏng vấn dùng mã ứng viên. Bảng điểm có một mã ứng viên dùng mã đó; nhiều mã dùng `TongHop`, bảng trắng dùng `ChuaChonUV`. TOR/thang lương dùng phạm vi `ToanTrungTam`.
- Tài sản dùng mã/tên đợt kiểm kê hoặc số đề nghị/quyết định; chưa có mã ghi `ChuaCoMa`. Ngày lấy từ ngày kiểm kê, ngày đề nghị, ngày quyết định hoặc ngày thực hiện đúng loại văn bản. Chọn Tiêu hủy đổi tiền tố `ThanhLy` thành `TieuHuy` khi mẫu có trường này.
- Báo cáo dùng tiền tố `DS_NhanSu`, `DS_HopDongSapHetHan`, `So_CongVan`, phạm vi/lọc và ngày xuất theo giờ Việt Nam. Phiếu lương PDF dùng `Phieu_Luong_MãNV-KỳYYYYMM_NgàyPhátHành.pdf`; xuất kiểm kê trực tiếp dùng `BB_KiemKeTaiSan_Đợt_NgàyKiểmKê.xlsx`.

Các tiền tố của 26 mẫu nằm tại `src/apps/document/hcns/filenames.py`; mọi bản xuất được tạo dùng bộ chuẩn hóa chung `src/apps/common/export_names.py`. Tệp đính kèm đã tải lên giữ tên lưu trữ hiện có khi tải lại. Tên tệp không chứng minh văn bản đã được ký/phê duyệt; nhãn BẢN SOẠN THẢO vẫn giữ nguyên.

## Bố cục bản xem trước và bản xuất

Mỗi mẫu có khổ giấy, lề và cỡ chữ riêng tại `src/apps/document/hcns/layout_profiles.json`, đối chiếu từ tệp tham khảo. Phần nhập liệu và dropdown vẫn dùng chung; bản in dùng bố cục riêng tại `layouts.py`. Các tiêu đề của ô nhập như “Nội dung căn cứ”, “Danh sách nơi nhận”, thông tin hồ sơ nguồn và thông báo hướng dẫn không được đưa vào nội dung văn bản.

Quyết định nhân sự và quyết định xử lý tài sản dùng hai cột ở đầu trang, tiêu đề QUYẾT ĐỊNH và trích yếu, căn cứ in nghiêng, nội dung từng điều liền dòng; nơi nhận và vùng ký chia hai cột cuối trang. Đơn nghỉ trình bày thông tin người làm đơn, thời gian, lý do, bàn giao, ngày ký và ba vùng ký. Phiếu thông tin cán bộ giữ các dòng thông tin như mẫu, CCCD/ngày cấp/nơi cấp và ngân hàng/chi nhánh cùng dòng.

Danh mục hồ sơ in hai cột STT/Loại hồ sơ; thông tin đã nhận, ngày nhận và ghi chú được giữ bên dưới nội dung hồ sơ tương ứng. Phiếu đánh giá có bảng thông tin đầu trang, các nhóm nhiệm vụ và sáu ô đánh dấu mức 1–2–3 của tần suất/chất lượng. Phiếu phỏng vấn ứng viên dùng các phần I/II/III và từng tiêu chí, điểm, nhận xét. Biên bản bàn giao dùng các bên tham gia và từng nội dung bàn giao, giữ hiện trạng/người nhận/thời hạn/ghi chú.

Excel có bố cục riêng cho thang bảng lương, tổng hợp tuyển dụng, kiểm kê và bàn giao nghỉ việc, gồm vùng tiêu đề, ô gộp và hàng tiêu đề lặp khi in. Phiếu tổng hợp tuyển dụng đặt tổng và trung bình sát từng nhóm điểm; điểm phỏng vấn và điểm kiểm tra đều tính trung bình theo mã ứng viên. Bản xuất kiểm kê giữ đầy đủ dòng nguồn; không chạy macro hoặc dùng dữ liệu minh họa của tệp gốc.

Các bản xuất vẫn ghi **BẢN SOẠN THẢO**, không chép chữ ký hoặc hình ảnh riêng tư từ tài liệu tham khảo. Số dòng thay đổi theo dữ liệu; nội dung dài có thể sang trang. Word, Excel và trình duyệt có cơ chế ngắt trang khác nhau, cần kiểm tra lần cuối trước khi ký. Khi lưu PDF từ trình duyệt, chọn tỷ lệ 100% và tắt đầu/chân trang do trình duyệt thêm. Sau cập nhật mã, khởi động lại ứng dụng nếu đang chạy không có autoreload và nhấn `Ctrl+F5` để tải CSS mới.
