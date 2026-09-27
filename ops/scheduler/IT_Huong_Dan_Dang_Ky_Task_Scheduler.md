# Hướng dẫn IT: Đăng ký Task Scheduler cho 2 lệnh nhắc việc IHRMS

Áp dụng cho máy chủ Windows đang chạy IHRMS. Có 2 script đã sẵn trong `ops/scheduler/`:

| Script | Lệnh Django gọi | Mục đích |
|---|---|---|
| `Run-ActivityReportReminders.ps1` | `send_activity_report_reminders` | Nhắc hạn báo cáo hoạt động dự án (NGO) |
| `Run-LifecycleReminders.ps1` | `send_lifecycle_reminders` | Nhắc đầu việc onboarding/offboarding quá hạn (mới thêm) |

Cả 2 dùng chung 1 cơ chế: tự tạo file log theo ngày trong thư mục `Logs/` ở gốc dự án, tự thoát
với mã lỗi khác 0 nếu lệnh Django lỗi (để Task Scheduler ghi nhận "Last Run Result" khác 0).

---

## Bước 0: Xác nhận biến môi trường Python (chỉ cần làm 1 lần)

Script tự tìm Python theo thứ tự:
1. Biến môi trường `IHRMS_PYTHON` (nếu có).
2. Mặc định `<gốc dự án>\venv\Scripts\python.exe`.

Nếu virtualenv của bạn nằm đường dẫn khác, đặt biến môi trường hệ thống (System, không phải
User, để Task Scheduler chạy dưới tài khoản dịch vụ vẫn đọc được):

```powershell
[Environment]::SetEnvironmentVariable("IHRMS_PYTHON", "D:\QLHCNS\venv\Scripts\python.exe", "Machine")
```

## Bước 1: Chạy thử tay trước khi đăng ký lịch (bắt buộc)

Mở PowerShell **với quyền Administrator** tại gốc dự án:

```powershell
cd D:\QLHCNS
powershell -ExecutionPolicy Bypass -File .\ops\scheduler\Run-ActivityReportReminders.ps1
powershell -ExecutionPolicy Bypass -File .\ops\scheduler\Run-LifecycleReminders.ps1
```

Kiểm tra:
- Không có lỗi đỏ trên console.
- Có file log mới trong `Logs\activity-reminders-YYYYMMDD.log` và
  `Logs\lifecycle-reminders-YYYYMMDD.log`.
- Nội dung log có dòng `Đã tạo N thông báo...` (N có thể là 0 nếu hôm đó không có gì đến hạn —
  vậy là bình thường, không phải lỗi).

Chỉ đăng ký lịch tự động sau khi cả 2 lệnh chạy tay thành công.

## Bước 2: Đăng ký Task Scheduler

Có thể dùng GUI (`taskschd.msc`) hoặc lệnh `schtasks` dưới đây (chạy trong PowerShell
Administrator, sửa đường dẫn `D:\QLHCNS` cho đúng máy chủ thật):

```powershell
schtasks /Create /TN "IHRMS - Activity Report Reminders" `
  /TR "powershell.exe -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\scheduler\Run-ActivityReportReminders.ps1`"" `
  /SC DAILY /ST 07:30 /RU "SYSTEM" /RL HIGHEST /F

schtasks /Create /TN "IHRMS - Lifecycle Checklist Reminders" `
  /TR "powershell.exe -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\scheduler\Run-LifecycleReminders.ps1`"" `
  /SC DAILY /ST 07:35 /RU "SYSTEM" /RL HIGHEST /F
```

Giải thích tham số:
- `/SC DAILY /ST 07:30` — chạy hằng ngày lúc 7:30 sáng (trước giờ làm việc, để nhân viên vào là
  thấy thông báo mới nhất). Đặt lệch 5 phút giữa 2 task để tránh tranh chấp ghi log cùng lúc.
- `/RU "SYSTEM"` — chạy dưới tài khoản hệ thống, không phụ thuộc user đăng nhập; đổi thành tài
  khoản dịch vụ riêng nếu chính sách bảo mật công ty yêu cầu (khi đó thêm `/RP <mật khẩu>`).
- `/RL HIGHEST` — chạy quyền cao nhất khả dụng của tài khoản đó (không phải Administrator tuyệt
  đối, chỉ là "Run with highest privileges" trong Task Scheduler).
- `/F` — ghi đè nếu task cùng tên đã tồn tại (an toàn khi chạy lại lệnh này để cập nhật).

⚠️ **Lưu ý quan trọng — 2 lệnh KHÔNG đối xứng nhau, đã kiểm tra lại trong code:**
- `send_activity_report_reminders`: tự bỏ qua thứ Bảy/Chủ nhật (coi là ngày nghỉ).
- `send_lifecycle_reminders`: **không** kiểm tra ngày trong tuần — chỉ xét "đầu việc đã quá hạn
  + hôm nay chưa nhắc lần nào", nên **sẽ chạy và gửi nhắc cả vào thứ Bảy/Chủ nhật** nếu Task
  Scheduler kích hoạt đúng ngày đó.

Đây có thể là chủ ý (ví dụ thu hồi tài sản/khóa tài khoản khi nghỉ việc thì hạn không nên bị lùi
chỉ vì rơi vào cuối tuần) hoặc là điểm cần bổ sung logic sau này — **nên hỏi lại bên nghiệp vụ
xem có mong muốn 2 lệnh nhất quán với nhau không**, trước khi coi đây là bug cần sửa. Nếu công
ty/NGO có làm việc thứ Bảy, nhắc luôn để chỉnh `send_activity_report_reminders` cho khớp lịch
làm việc thật (`Holiday`/lịch công ty) — không tự sửa giờ chạy Task Scheduler để né vấn đề này.

## Bước 3: Kiểm tra sau khi đăng ký

Ngày hôm sau, kiểm tra:
1. Task Scheduler → chọn task → tab **History**: có sự kiện "Task completed" (mã 0), không có
   "Task failed".
2. `Logs\activity-reminders-*.log` và `Logs\lifecycle-reminders-*.log` có dòng log mới của ngày
   hôm đó.
3. Trong IHRMS, chuông thông báo của (các) nhân viên có việc quá hạn hiển thị đúng thông báo mới
   (dùng tài khoản test có 1 task/timesheet cố tình để trễ hạn để kiểm tra).

## Xử lý khi task báo lỗi

1. Mở đúng file log ngày báo lỗi trong `Logs\` — script đã ghi lại toàn bộ output/traceback của
   lệnh Django vào đó.
2. Lỗi thường gặp nhất: sai đường dẫn `IHRMS_PYTHON`, hoặc chưa activate đúng virtualenv có cài
   `requirements.txt` (script gọi thẳng `python.exe` trong venv nên không cần activate, nhưng
   venv đó phải được tạo và cài đặt đầy đủ trước).
3. Nếu lỗi liên quan kết nối SQL Server (`django.db.utils.OperationalError`), đây không phải lỗi
   của 2 script này — kiểm tra dịch vụ SQL Server trên máy chủ có đang chạy không.

## Việc chưa nằm trong phạm vi 2 script này (nhắc để không nhầm)

- Backup SQL Server (`ops/backup/`) đã có Task Scheduler riêng, xem `ops/backup/README.md` —
  không gộp chung task với 2 lệnh nhắc việc ở trên.
- Gửi email thật (SMTP/Graph) chưa được cấu hình — 2 lệnh trên chỉ tạo thông báo **trong ứng
  dụng IHRMS**, chưa gửi email/Outlook tự động (xem phần "Hạng mục 1" trong
  `docs/HRMS_Next_Features_TechSpec_2026-09-26.md`).
