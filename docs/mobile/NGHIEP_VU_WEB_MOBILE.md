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

Các phần **chưa triển khai**, làm tiếp theo thứ tự trong nhóm:

1. Công việc: việc được giao/đã giao, chi tiết, trạng thái, bình luận, giao việc theo phạm vi và báo cáo đính kèm.
2. Bảng công tháng: khai báo, xóa dòng theo quyền, gửi tổng hợp, duyệt/từ chối, lịch nghỉ.
3. KPI cá nhân, giao/chấm KPI theo quyền; đào tạo cá nhân và lịch sự kiện.
4. Phiếu lương đã phát hành của kỳ đã khóa và xem/tải PDF có kiểm quyền.
5. Hộp duyệt thống nhất cho các nghiệp vụ tiếp theo, tìm kiếm và điều hướng thông báo tương ứng.

## Nhóm Nhân sự — chưa triển khai

- Quản lý nhân viên, lịch sử nhân sự, hợp đồng/phụ lục/gia hạn và thông tin lương theo quyền.
- Tuyển dụng: ứng viên, phỏng vấn, offer, tiếp nhận; quy trình onboarding/offboarding.
- Quyết định nhân sự, biểu mẫu HCNS, tài liệu và tệp có kiểm quyền.

## Nhóm Hành chính — chưa triển khai

- Công văn/tài liệu: xem, tạo, duyệt và xử lý theo phạm vi; file SharePoint.
- Đặt phòng, đặt xe: tạo, hủy, duyệt và xử lý xung đột.
- Văn phòng phẩm: đề nghị, duyệt, cấp phát; mua sắm: đề nghị, duyệt, ghi nhận mua.
- Tài sản, kiểm kê, đề nghị thanh lý, phê duyệt/biên bản và tài liệu xuất.
- Công việc/lịch/hoạt động dự án: bổ sung phần quản lý, đề xuất và phê duyệt; giữ nguyên phạm vi dự án tách biệt HCNS.

## Nhóm Tài chính/quản trị — chưa triển khai

- Kỳ lương, tính/kiểm tra/khóa kỳ, phát hành phiếu; phụ thuộc, cấu hình thuế/bảo hiểm và ngân sách.
- Báo cáo nhân sự, chấm công, biến động, ngân sách; xuất có kiểm quyền.
- Các thao tác quản trị còn lại phải có đặc tả mobile phù hợp với quyền web; không tự mở quyền vì app có menu.

## Cách nghiệm thu mỗi đợt

Kiểm API/quyền và ghi dữ liệu trên DB QA cô lập, kiểm giao diện sáng/tối/rộng/hẹp và thao tác nghiệp vụ trên app chạy thật; kiểm thiết bị Android với APK QA cùng chữ ký. Tệp, thông báo, dữ liệu đã lưu và trang đích phải tương ứng với web. Không dùng dữ liệu/phiên thật và không tự deploy backend vận hành. Kết quả, phần còn thiếu và SHA bàn giao chỉ ghi tại [nhật ký dự án](../PROJECT_WORK_LOG.md).

## Dùng các chức năng mới

Trong tab **Tôi**, chọn **Nghiệp vụ**:

1. **Hồ sơ chi tiết**: xem thông tin cá nhân, hợp đồng/lương cơ bản nếu có; chọn Điều chuyển/Bổ nhiệm/Khen thưởng/Kỷ luật để xem từng loại lịch sử. Dùng Trang sau/Trang trước khi có nhiều bản ghi.
2. **Sơ đồ tổ chức**: xem danh sách nhân viên đang làm việc, phòng ban, vị trí và người quản lý trực tiếp.
3. **Yêu cầu cập nhật hồ sơ**: gửi và theo dõi yêu cầu của mình như trong Cài đặt.
4. Với tài khoản Nhân sự có quyền, chọn **Duyệt cập nhật hồ sơ**, kiểm tra giá trị cũ/mới và lý do. Chọn Duyệt/Từ chối/Yêu cầu bổ sung, nhập ý kiến trong hộp xác nhận rồi bấm **Xác nhận**. Nếu báo hồ sơ đã thay đổi sau khi gửi, nhân viên cần gửi lại yêu cầu theo thông tin mới.
5. Nhân viên mở tab **Thông báo**, bấm lời nhắc tương ứng để mở lịch sử yêu cầu. Chỉ yêu cầu đã được duyệt mới cập nhật hồ sơ; từ chối/bổ sung giữ nguyên hồ sơ hiện tại.

Với chứng từ đính kèm, hiện HR phải xem trên cổng web. Các nghiệp vụ ghi rõ “chưa triển khai” ở trên tiếp tục dùng web cho đến khi có API/màn hình và kiểm thử riêng.
