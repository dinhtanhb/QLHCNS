# Mở rộng nghiệp vụ web sang mobile

Thứ tự chủ dự án chọn ngày 29/10/2026: **Nhân viên và người duyệt → Nhân sự → Hành chính → Tài chính/quản trị**. Các nghiệp vụ trên web là nguồn quy tắc; app dùng API Django có cùng quyền và phạm vi dữ liệu. Không coi màn hình mở website là tính năng native đã triển khai.

## Đã có trước đợt mở rộng

- Đăng nhập/đăng xuất, khôi phục phiên, hồ sơ cơ bản, xem chấm công, hạn mức nghỉ phép.
- Tạo/theo dõi nghỉ phép, duyệt/từ chối theo cây quản lý, thông báo và push QA.
- Cài đặt sáng/tối, đổi mật khẩu, gửi/theo dõi yêu cầu cập nhật thông tin cá nhân.

## Nhóm nhân viên và người duyệt

Đợt hiện tại bổ sung:

- Hồ sơ chi tiết của bản thân: thông tin liên hệ, quản lý, ngày vào làm, trạng thái; lương cơ bản/hợp đồng hiện tại theo cùng truy vấn của trang hồ sơ web.
- Lịch sử điều chuyển, bổ nhiệm, khen thưởng, kỷ luật của bản thân; phân trang từng loại.
- Sơ đồ tổ chức trình bày thành danh sách nhân viên đang làm việc và quản lý trực tiếp; không đưa thông tin liên hệ cá nhân/lương vào danh bạ.
- HR duyệt/từ chối/yêu cầu bổ sung hồ sơ; kiểm dữ liệu đã đổi sau thời điểm gửi, ghi người xử lý/ý kiến, báo lại cho người gửi. Dùng cùng command nghiệp vụ với web. Chứng từ đính kèm hiện phải đọc trên web; không chuyển token vào URL trình duyệt.

Các phần đã bổ sung vào **Tôi → Nghiệp vụ** qua biểu mẫu native dùng cùng view/command web:

1. Công việc: việc được giao/đã giao, chi tiết, trạng thái, bình luận, giao việc theo phạm vi và báo cáo đính kèm.
2. Bảng công tháng: khai báo, xóa dòng theo quyền, gửi tổng hợp, duyệt/từ chối, lịch nghỉ.
3. KPI cá nhân, giao/chấm KPI theo quyền; đào tạo cá nhân và lịch sự kiện.
4. Phiếu lương đã phát hành của kỳ đã khóa và xem/tải PDF có kiểm quyền.
5. Danh mục các trang duyệt theo quyền, tìm kiếm và điều hướng thông báo tương ứng. Các hộp duyệt vẫn giữ từng quy trình của web, chưa gộp thành một danh sách duy nhất.

## Nhóm Nhân sự — truy cập qua danh mục native

- Quản lý nhân viên, lịch sử nhân sự, hợp đồng/phụ lục/gia hạn và thông tin lương theo quyền.
- Tuyển dụng: ứng viên, phỏng vấn, offer, tiếp nhận; quy trình onboarding/offboarding.
- Quyết định nhân sự, biểu mẫu HCNS, tài liệu và tệp có kiểm quyền.

## Nhóm Hành chính — truy cập qua danh mục native

- Công văn/tài liệu: xem, tạo, duyệt và xử lý theo phạm vi; file SharePoint.
- Đặt phòng, đặt xe: tạo, hủy, duyệt và xử lý xung đột.
- Văn phòng phẩm: đề nghị, duyệt, cấp phát; mua sắm: đề nghị, duyệt, ghi nhận mua.
- Tài sản, kiểm kê, đề nghị thanh lý, phê duyệt/biên bản và tài liệu xuất.
- Công việc/lịch/hoạt động dự án: bổ sung phần quản lý, đề xuất và phê duyệt; giữ nguyên phạm vi dự án tách biệt HCNS.

## Nhóm Tài chính/quản trị — truy cập qua danh mục native

- Kỳ lương, tính/kiểm tra/khóa kỳ, phát hành phiếu; phụ thuộc, cấu hình thuế/bảo hiểm và ngân sách.
- Báo cáo nhân sự, chấm công, biến động, ngân sách; xuất có kiểm quyền.
- Quản trị mô hình theo quyền staff/model của Django; chọn quan hệ, tìm kiếm, biểu mẫu nhiều dòng và tệp có controls native. Không tự mở quyền vì app có menu.

## Phạm vi nghiệm thu

Các nhóm trên đã có đường truy cập và thao tác native dùng cùng xử lý máy chủ. Bảng web được chuyển thành thẻ, không giữ nguyên bố cục desktop hoặc chạy JavaScript trong app. Đã bổ sung riêng chọn ngày/giờ, chọn và tải tệp, in/lưu PDF, dòng hàng mua sắm, formset và mở dòng kiểm kê/thanh lý. Xem [hướng dẫn sử dụng](NGHIEP_VU_NATIVE.md).

Kiểm thử tự động bao gồm các luồng đại diện và phân quyền; quét trang GET không thay cho kiểm thử thao tác ghi của mọi màn hình. Các tích hợp SharePoint thật, máy in, iOS và nghiệm thu toàn bộ biểu mẫu trên điện thoại thật vẫn cần kiểm riêng trước khi phát hành nội bộ rộng. Chi tiết đã chạy và giới hạn nằm trong [nhật ký](../PROJECT_WORK_LOG.md).

## Cách nghiệm thu mỗi đợt

Kiểm API/quyền và ghi dữ liệu trên DB QA cô lập, kiểm giao diện sáng/tối/rộng/hẹp và thao tác nghiệp vụ trên app chạy thật; kiểm thiết bị Android với APK QA cùng chữ ký. Tệp, thông báo, dữ liệu đã lưu và trang đích phải tương ứng với web. Không dùng dữ liệu/phiên thật và không tự deploy backend vận hành. Kết quả, phần còn thiếu và SHA bàn giao chỉ ghi tại [nhật ký dự án](../PROJECT_WORK_LOG.md).

## Dùng các chức năng mới

Trong tab **Tôi**, chọn **Nghiệp vụ**:

1. **Hồ sơ chi tiết**: xem thông tin cá nhân, hợp đồng/lương cơ bản nếu có; chọn Điều chuyển/Bổ nhiệm/Khen thưởng/Kỷ luật để xem từng loại lịch sử. Dùng Trang sau/Trang trước khi có nhiều bản ghi.
2. **Sơ đồ tổ chức**: xem danh sách nhân viên đang làm việc, phòng ban, vị trí và người quản lý trực tiếp.
3. **Yêu cầu cập nhật hồ sơ**: gửi và theo dõi yêu cầu của mình như trong Cài đặt.
4. Với tài khoản Nhân sự có quyền, chọn **Duyệt cập nhật hồ sơ**, kiểm tra giá trị cũ/mới và lý do. Chọn Duyệt/Từ chối/Yêu cầu bổ sung, nhập ý kiến trong hộp xác nhận rồi bấm **Xác nhận**. Nếu báo hồ sơ đã thay đổi sau khi gửi, nhân viên cần gửi lại yêu cầu theo thông tin mới.
5. Nhân viên mở tab **Thông báo**, bấm lời nhắc tương ứng để mở lịch sử yêu cầu. Chỉ yêu cầu đã được duyệt mới cập nhật hồ sơ; từ chối/bổ sung giữ nguyên hồ sơ hiện tại.

Với chứng từ đính kèm trong màn hình duyệt hồ sơ chuyên biệt, HR có thể mở **Nghiệp vụ → trang yêu cầu hồ sơ của web được trình bày native** để tải bằng phiên hiện tại; không chuyển token vào URL trình duyệt. Tệp SharePoint cần quyền và cấu hình Microsoft 365 tương ứng, chưa được chứng nhận bằng dữ liệu thật trong đợt QA này.
