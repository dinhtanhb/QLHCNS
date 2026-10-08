# Checklist go-live IHRMS

Bản mã nguồn đã rà soát: commit `31bf46c`, nhánh `chore/django-5.2-upgrade`, ngày 28/09/2026.
**Nguyên tắc:** chỉ go-live khi mọi mục **[BẮT BUỘC]** đã tick và có bằng chứng (log, ảnh chụp, biên bản).
Mục **[NÊN]** có thể làm sau go-live nếu có người nhận việc và hạn rõ ràng.

Người phụ trách viết tắt: **IT** (quản trị máy chủ), **HR**, **KT** (Kế toán), **GĐ** (người phê duyệt),
**CDA** (chủ dự án/đầu mối làm việc với Codex).

---

## Giai đoạn 1 — Mã nguồn và môi trường SIT

| # | Việc | Người | Xong khi | ☐ |
|---|---|---|---|---|
| 1.1 | **[BẮT BUỘC]** Push các commit local lên remote (đã hoàn tất ngày 28/09/2026) | CDA | `git log origin/chore/django-5.2-upgrade` thấy `31bf46c` | ☒ |
| 1.2 | **[BẮT BUỘC]** Máy chủ SIT tách riêng production: Windows Server, SQL Server database riêng, tài khoản dịch vụ quyền tối thiểu | IT | Kết nối được, `.env` đặt ngoài Git, không dùng `sa` | ☐ |
| 1.3 | **[BẮT BUỘC]** Cài code + venv + `pip install -r requirements.txt`; `npm ci && npm run build:css` nếu cần build lại CSS | IT | `manage.py check` không lỗi | ☐ |
| 1.4 | **[BẮT BUỘC]** Chạy `manage.py migrate` trên SQL Server SIT | IT | Không lỗi; `makemigrations --check` báo "No changes" | ☐ |
| 1.5 | **[BẮT BUỘC]** Chạy test: `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1` | IT | Dòng `Discovered tests: 235`, 0 fail. Lưu log | ☐ |
| 1.6 | **[BẮT BUỘC]** `collectstatic`, chạy Waitress/IIS thử | IT | `/portal/` trả HTTP 200, CSS và icon hiển thị đúng | ☐ |

## Giai đoạn 2 — Bảo mật và cấu hình

| # | Việc | Người | Xong khi | ☐ |
|---|---|---|---|---|
| 2.1 | **[BẮT BUỘC]** Bật HTTPS: `ENABLE_HTTPS_ENFORCEMENT=True`, chứng chỉ TLS hợp lệ, `ALLOWED_HOSTS` đúng tên miền, `DEBUG=False`, `SECRET_KEY` mới, riêng | IT | Đăng nhập được qua HTTPS, không còn truy cập HTTP | ☐ |
| 2.2 | **[BẮT BUỘC]** Chạy `manage.py check --deploy` với đúng cấu hình production | IT | Không còn cảnh báo về HTTPS, HSTS, cookie, `SECRET_KEY`, `DEBUG` | ☐ |
| 2.3 | **[BẮT BUỘC]** Xóa/đổi mật khẩu mọi tài khoản test, tài khoản mặc định; tạo tài khoản thật theo đúng vai trò (không dùng SUPER_ADMIN cho việc hằng ngày) | IT + HR | Danh sách tài khoản khớp danh sách nhân sự | ☐ |
| 2.4 | **[BẮT BUỘC]** Microsoft 365/SharePoint: xác nhận quyền Graph tối thiểu, danh sách người xem thư viện, retention, cách xử lý khi SharePoint gián đoạn | IT | Có văn bản xác nhận; file nhạy cảm không để ngoài phạm vi | ☐ |
| 2.5 | **[NÊN]** Quyết định có tắt `SharePoint` ở giai đoạn đầu (dùng lưu cục bộ) hay không | IT + GĐ | Quyết định ghi vào work log | ☐ |

## Giai đoạn 3 — Vận hành tự động và sao lưu

| # | Việc | Người | Xong khi | ☐ |
|---|---|---|---|---|
| 3.1 | **[BẮT BUỘC]** Đăng ký Task Scheduler cho 2 lệnh nhắc việc (`Run-ActivityReportReminders.ps1`, `Run-LifecycleReminders.ps1`), chạy tay trước 1 lần | IT | Ngày hôm sau có file log trong `Logs\`, Task Scheduler ghi kết quả `0` | ☐ |
| 3.2 | **[BẮT BUỘC]** Lập lịch backup SQL Server (full + transaction log) và backup thư mục tệp hồ sơ; bản sao đặt ở nơi độc lập, giới hạn quyền | IT | Có ít nhất 1 bản full + 1 bản log chạy tự động thành công | ☐ |
| 3.3 | **[BẮT BUỘC]** Diễn tập restore trên máy khác production, ghi vào `ops/backup/RestoreDrillLog.md` | IT | Restore thành công, đăng nhập thử được, thời gian ≤ 8 giờ (RTO) | ☐ |
| 3.4 | **[NÊN]** Theo dõi dung lượng đĩa, dung lượng log SQL Server, cảnh báo khi Task Scheduler lỗi | IT | Có người nhận cảnh báo | ☐ |

## Giai đoạn 4 — Nghiệp vụ và UAT

| # | Việc | Người | Xong khi | ☐ |
|---|---|---|---|---|
| 4.1 | **[BẮT BUỘC]** Kế toán đối chiếu **độc lập** kết quả lương của hệ thống với bảng tính đã được công ty phê duyệt: nhân viên vào/nghỉ giữa kỳ (lỗi I6 vừa sửa), nghỉ không lương, người phụ thuộc, thuế, bảo hiểm, làm tròn | KT | Biên bản đối chiếu ít nhất 1 kỳ, chênh lệch = 0 hoặc đã giải trình | ☐ |
| 4.2 | **[BẮT BUỘC]** Xác nhận quy tắc ngày làm việc: nhân viên dự án làm Thứ Bảy/Chủ Nhật, nghỉ bù chỉ tính khi bảng công tháng được duyệt | HR + GĐ | Quy tắc ghi văn bản, khớp cấu hình hệ thống | ☐ |
| 4.3 | **[BẮT BUỘC]** Chốt ma trận quyền và người duyệt thay thế (khi trưởng phòng/giám đốc vắng) | GĐ + HR | Danh sách vai trò → người thật, đã ký | ☐ |
| 4.4 | **[BẮT BUỘC]** Chạy UAT theo kịch bản `UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md` và `Huong_Dan_Test_Nhanh_4_Chuc_Nang.md` trên dữ liệu ẩn danh; thêm kịch bản đăng nhập từ **điện thoại** (menu, bảng cuộn ngang, mở thư nháp Outlook) | HR + KT + quản lý | Biên bản UAT có chữ ký, mọi lỗi mức nghiêm trọng đã đóng | ☐ |
| 4.5 | **[BẮT BUỘC]** HR nhập 2 mẫu checklist Onboarding/Offboarding thật (theo `HR_Huong_Dan_Checklist_Onboarding_Offboarding.md`) | HR | Mỗi loại có ≥ 1 mẫu, đã mở thử 1 hồ sơ | ☐ |
| 4.6 | **[NÊN]** Hạng mục 3 (báo cáo BHXH/PIT/chi phí lương): chờ Kế toán xác nhận mẫu. **Không chặn go-live** nếu công ty chưa dùng các báo cáo này trong tháng đầu; tiếp tục làm thủ công | KT | Có phản hồi Kế toán, hoặc ghi nhận "làm thủ công đến khi có" | ☐ |

## Giai đoạn 5 — Đào tạo, cutover và quay lui

| # | Việc | Người | Xong khi | ☐ |
|---|---|---|---|---|
| 5.1 | **[BẮT BUỘC]** Tập huấn HR, Kế toán, quản lý, nhân viên theo `docs/TAP_HUAN_IHRMS.md` trên môi trường demo | HR | Danh sách người đã tập huấn | ☐ |
| 5.2 | **[BẮT BUỘC]** Chốt kế hoạch cutover: nhập dữ liệu thật (nhân viên, hợp đồng, phép năm còn lại, lương hiện hành), thời điểm dừng nhập tay | HR + IT | Có kế hoạch từng bước, có ngày giờ | ☐ |
| 5.3 | **[BẮT BUỘC]** Kế hoạch quay lui: nếu lỗi nghiêm trọng trong tuần đầu thì quay về quy trình cũ; giữ bản sao dữ liệu trước cutover | IT + GĐ | Nêu rõ điều kiện quay lui và người quyết định | ☐ |
| 5.4 | **[BẮT BUỘC]** Tuần đầu sau go-live: 1 đầu mối IT + 1 đầu mối HR trực nhận lỗi; ghi mọi sự cố | IT + HR | Danh sách sự cố cập nhật hằng ngày | ☐ |
| 5.5 | **[NÊN]** Rà lại sau 2 tuần: sự cố, phản hồi người dùng, việc cần Codex sửa | CDA | Danh sách việc cho đợt sau | ☐ |

---

## Biên bản chấp thuận phát hành

☐ Đủ điều kiện go-live   ☐ Go-live có điều kiện (ghi rõ): ______________________   ☐ Chưa đạt

| Vai trò | Họ tên | Chữ ký | Ngày |
|---|---|---|---|
| Chủ nghiệp vụ (HR) | | | |
| Kế toán | | | |
| IT vận hành | | | |
| Người phê duyệt (GĐ) | | | |

## Thứ tự làm gợi ý

1.1 → 1.2–1.6 → 2.1–2.2 → 3.1–3.3 (làm song song với 4.1–4.5) → 5.1–5.3 → ký biên bản → go-live.
Việc dài nhất thường là **3.3 (restore)** và **4.1 (đối chiếu lương)**: nên bắt đầu sớm.
