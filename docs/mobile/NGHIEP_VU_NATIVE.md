# Nghiệp vụ native dùng cùng quy tắc với web

Vào **Tôi → Nghiệp vụ**. Danh mục hiển thị theo quyền của tài khoản. Bảng trên web được trình bày thành thẻ bản ghi; biểu mẫu là các trường và nút native.

## Cài bản QA và thử nhanh

1. Lấy APK QA mới nhất tại `D:\IHRMS_Review_Exports\Mobile_ActCode_QA_20261029\apk\IHRMS-QA.apk` trên máy tính, gửi sang điện thoại bằng cáp hoặc cách chia sẻ tệp nội bộ.
2. Mở tệp trên điện thoại và chọn **Cập nhật/Cài đặt**. Bản QA giữ cùng khóa ký; không cần gỡ bản đang dùng. Nếu Android hỏi quyền cài từ ứng dụng quản lý tệp, cấp cho đúng ứng dụng đó.
3. Điện thoại và máy tính cùng mạng. Bản APK này dùng cố định `http://192.168.1.12:8790`; đây là backend với dữ liệu giả, không phải hệ thống vận hành. Dùng tài khoản trong `D:\IHRMS_Review_Exports\Mobile_Demo10_20261028\qa\DEMO_ACCOUNTS.txt` trên máy tính; không đưa tệp tài khoản vào Git hoặc gửi chung APK.
4. Đăng nhập nhân viên, vào **Tôi → Nghiệp vụ → Bảng công**, tạo một dòng thử với `2,5` giờ. Kiểm tra thông báo thành công và dữ liệu trong đúng tháng.
5. Mở **Phiếu lương → Tải PDF → Mở hoặc lưu tệp**. Thử quay lại app, đóng/mở lại và chuyển sáng/tối.
6. Thử tiếp tài khoản HR, hành chính và tài chính đúng quyền. Với các thao tác duyệt, dùng hai tài khoản QA khác nhau và kiểm tra cả trạng thái đã lưu lẫn thông báo của người gửi.

Nếu máy tính đã khởi động lại và server QA chưa chạy, mở PowerShell tại `D:\QLHCNS` rồi chạy một lần:

```powershell
& .\venv\Scripts\python.exe ops/mobile_qa.py serve --directory D:/IHRMS_Review_Exports/Mobile_Demo10_20261028/qa --bind 192.168.1.12 --port 8790 --enable-push
```

Giữ cửa sổ đó mở trong lúc thử. Nếu báo cổng đã được sử dụng, kiểm tra cửa sổ QA đang chạy; không tự đổi sang cổng khác vì APK đã ghi cố định cổng `8790`. Nếu IP máy tính đổi, cần cấu hình/build lại APK QA tương ứng.

## Nhân viên và người duyệt

- **Giao việc & hoàn tất:** mở tên công việc để xem, đổi trạng thái và bình luận. Người có quyền chọn **+ Giao việc mới**, chọn ActCode hoặc Khác, người nhận, thời hạn và độ ưu tiên. Báo cáo hoạt động cần tệp trước khi hoàn thành theo quy tắc hệ thống.
- **Bảng công:** chọn tháng/năm; nhập ngày, dự án hoặc tên dự án ngoài danh sách, nội dung và giờ, rồi bấm **Thêm dòng chấm công**. Ví dụ giờ lẻ: `2,5`. Xóa dòng, tổng hợp và duyệt tiếp tục áp dụng quyền/điều kiện web.
- **KPI:** xem kết quả cá nhân; người có quyền tạo chỉ tiêu/chấm Thực tế qua các nút tương ứng.
- **Phiếu lương:** chỉ có phiếu đã phát hành của kỳ khóa. Bấm **Tải PDF**, đợi tệp sẵn sàng, chọn **Mở hoặc lưu tệp**.
- **Lịch công tác/Đào tạo:** xem và xử lý dữ liệu theo quyền hiện có.

## Nhân sự, Hành chính, Tài chính/quản trị

Mở nhóm tương ứng để truy cập nhân viên/hợp đồng/lịch sử, tuyển dụng/checklist, công văn/tài liệu, phòng/xe/VPP/mua sắm, tài sản/kiểm kê/thanh lý, hoạt động dự án, kỳ lương/cấu hình và báo cáo. Chọn bản ghi để mở thao tác; máy chủ tiếp tục kiểm quyền đối tượng, quy trình và trạng thái.

Tài khoản quản trị có thể mở **Trang Quản Trị (Admin)**. Quyền từng mô hình vẫn được kiểm. Danh sách lựa chọn có tìm kiếm; dùng **Tải thêm lựa chọn** nếu máy chủ còn kết quả.

Liên kết thêm danh mục mở thành trang riêng trên app. Nên tạo danh mục cần dùng trước khi điền biểu mẫu chính; khi quay lại trang trước, app tải lại dữ liệu và không tự giữ bản nhập chưa lưu. Biểu đồ dựng bằng JavaScript của web chưa được tái hiện nguyên dạng trên mobile; dùng các bảng, thẻ số liệu và tệp báo cáo tương ứng để tra cứu.

## Nhập biểu mẫu

1. Ô có `*` là bắt buộc. Trường bị khóa không sửa được.
2. Mở danh sách để tìm/chọn; với nhiều lựa chọn, bấm **Xong** sau khi chọn.
3. Ngày dùng `YYYY-MM-DD`, giờ `HH:MM`, ngày kèm giờ `YYYY-MM-DDTHH:MM`. Điện thoại có nút mở bộ chọn ngày/giờ hệ thống.
4. Số tiền dùng dạng `1.000.000` hoặc `12,5`; không nhập đơn vị “đồng”.
5. Biểu mẫu nhiều dòng có **Thêm dòng/Xóa dòng**; mua sắm có **Thêm dòng hàng hóa**. Biểu mẫu HCNS tự điền các trường liên quan khi chọn nhân viên/ứng viên/tài sản trong phạm vi quyền. Kiểm tra lại sau khi chọn; lương/ngày hiệu lực phải xác nhận riêng. **In / lưu PDF** kiểm tra và dùng nội dung đang nhập, không tự lưu bản nháp quyết định. Lương bằng chữ được tính khi cập nhật bản xem trước hoặc xuất/in.
6. **Chọn tệp** mở trình chọn tài liệu. Mỗi tệp tối đa20 MB; máy chủ vẫn kiểm định dạng. Bấm **Bỏ tệp** nếu chọn nhầm.
7. Tệp tải chỉ có sau khi kiểm quyền; chọn **Mở hoặc lưu tệp** để dùng ứng dụng phù hợp. Bản tạm được dọn khi mở lại/đăng xuất; bản bạn chủ động lưu/gửi ra ngoài do bạn quản lý.
8. Sau lỗi mạng, tải lại và kiểm tra trạng thái trước khi gửi lại. App không tự gửi lại thao tác ghi.

Các màn hình cần backend có API `workspace/`. Chỉ dùng APK/backend QA bàn giao để thử. Xem [nhật ký](../PROJECT_WORK_LOG.md) để phân biệt luồng đã kiểm, phần chưa nghiệm thu trên điện thoại thật và giới hạn tích hợp SharePoint/thiết bị in.
