# Backup & Restore — QLHCNS / IHRMS

Thư mục này chứa toàn bộ script backup SQL Server Express (bản Express
**không có SQL Server Agent**, nên không lên lịch job qua SSMS được như bản
Standard/Enterprise — dùng Windows Task Scheduler thay thế) và checklist
diễn tập restore.

Đối chiếu chuẩn trong `docs/08_Deployment_Standards.md`:

| Hạng mục | Chuẩn yêu cầu |
|---|---|
| Full Backup | Hằng ngày, 22:00 |
| Transaction Log Backup | Mỗi 1 giờ |
| Giữ Daily | 30 ngày |
| Giữ Weekly | 12 tuần |
| Giữ Monthly | 12 tháng |
| Restore Verification | Bắt buộc, hàng quý |
| RPO (Recovery Point Objective) | 24 giờ |
| RTO (Recovery Time Objective) | 8 giờ |

---

## 1. Cài đặt lần đầu (chỉ làm 1 lần)

1. Tạo cấu trúc thư mục backup:
D:\QLHCNS\Backups\Daily
D:\QLHCNS\Backups\Weekly
D:\QLHCNS\Backups\Monthly
D:\QLHCNS\Backups\TransactionLog

   (Các script tự tạo nếu chưa có, bước này chỉ để bạn hình dung cấu trúc.)

2. Mở SSMS, chạy `Setup-RecoveryModel.sql` **một lần** — chuyển database
   `qlhcns` sang chế độ FULL recovery (bắt buộc để backup transaction log
   hoạt động) và tạo bản full backup đầu tiên để "mở chuỗi log".

3. Mở PowerShell **với quyền Administrator**, chạy thử tay 1 lần mỗi script
   để chắc chắn không lỗi trước khi đăng ký lịch tự động:
```powershell
   cd D:\QLHCNS\ops\backup
   .\Backup-FullDatabase.ps1 -Database "TEN_DATABASE_DA_XAC_NHAN"
   .\Backup-TransactionLog.ps1 -Database "TEN_DATABASE_DA_XAC_NHAN"
```
   Kiểm tra file `.bak` / `.trn` đã xuất hiện đúng thư mục, và file
   `D:\QLHCNS\Backups\backup-log.txt` có dòng "HOÀN TẤT" / "thành công".

   > Nếu lỗi "Access is denied" hoặc "Cannot bulk load": tài khoản chạy SQL
   > Server (thường là `NT Service\MSSQL$SQLEXPRESS`) cần quyền **Write**
   > lên thư mục `D:\QLHCNS\Backups`. Chuột phải thư mục → Properties →
   > Security → thêm quyền cho tài khoản đó.

---

## 2. Đăng ký lịch tự động qua Windows Task Scheduler

### Task 1 — Full Backup (22:00 hằng ngày)

1. Mở **Task Scheduler** (gõ vào Start Menu) → **Create Task...** (không
   dùng "Create Basic Task" vì cần tuỳ chỉnh thêm).
2. Tab **General**: Name = `QLHCNS - Full Backup`. Tích chọn **"Run whether
   user is logged on or not"** (để chạy được cả khi không ai đăng nhập máy)
   và **"Run with highest privileges"**.
3. Tab **Triggers** → New → Begin the task: **On a schedule** → Daily →
   Start time: **22:00:00** → OK.
4. Tab **Actions** → New → Action: **Start a program**:
   - Program/script: `powershell.exe`
   - Add arguments: `-NoProfile -ExecutionPolicy Bypass -File "D:\QLHCNS\ops\backup\Backup-FullDatabase.ps1" -Database "TEN_DATABASE_DA_XAC_NHAN"`
5. Tab **Conditions**: bỏ tích "Start the task only if the computer is on
   AC power" nếu đây là server luôn cắm điện.
6. OK → nhập mật khẩu tài khoản Windows đang dùng để chạy Task khi được hỏi.

### Task 2 — Transaction Log Backup (mỗi giờ)

Lặp lại các bước trên với khác biệt:
- Name = `QLHCNS - Transaction Log Backup`
- Trigger: **Daily**, Start time bất kỳ (ví dụ 00:05) → tích **"Repeat task
  every"** → chọn **1 hour** → **for a duration of** → **Indefinitely**.
- Action arguments: `-NoProfile -ExecutionPolicy Bypass -File "D:\QLHCNS\ops\backup\Backup-TransactionLog.ps1" -Database "TEN_DATABASE_DA_XAC_NHAN"`

### Kiểm tra Task đã chạy đúng

Task Scheduler → chọn Task → tab **History** (nếu không thấy, bấm "Enable
All Tasks History" ở panel bên phải) → xem có dòng "Task completed" mã
`0x0` (thành công) hay không, hoặc mở lại `backup-log.txt`.

---

## 3. Diễn tập Restore (bắt buộc — hàng quý)

Đây là bước **quan trọng nhất và dễ bị bỏ quên nhất**: có backup mà chưa
từng thử restore thì không thể chắc chắn backup đó dùng được khi thật sự
cần. Làm theo checklist này mỗi quý (tháng 1, 4, 7, 10 — hoặc theo lịch
công ty chọn), trên một SQL Server **khác** máy Production (ví dụ máy dev,
hoặc 1 instance SQL Server test riêng) để không ảnh hưởng dữ liệu thật.

### Checklist diễn tập

- [ ] **Bước 1 — Chọn bản backup để test**: lấy 1 file `.bak` Daily mới
      nhất + các file `.trn` log backup phát sinh sau đó (nếu muốn test khôi
      phục đến 1 thời điểm cụ thể).
- [ ] **Bước 2 — Restore trên máy test**:
```sql
      RESTORE DATABASE qlhcns_restoretest
      FROM DISK = 'D:\QLHCNS\Backups\Daily\qlhcns_full_XXXXXXXX.bak'
      WITH MOVE 'qlhcns' TO 'D:\SQLData\qlhcns_restoretest.mdf',
           MOVE 'qlhcns_log' TO 'D:\SQLData\qlhcns_restoretest_log.ldf',
           NORECOVERY;

      RESTORE LOG qlhcns_restoretest
      FROM DISK = 'D:\QLHCNS\Backups\TransactionLog\qlhcns_log_XXXXXXXX.trn'
      WITH RECOVERY;
```
      (Tên logical file `qlhcns`/`qlhcns_log` — kiểm tra tên thật bằng
      `RESTORE FILELISTONLY FROM DISK = '...'` nếu khác.)
- [ ] **Bước 3 — Ghi lại thời gian thực hiện** từ lúc bắt đầu restore đến
      lúc database `ONLINE` và query được — đây là số liệu để đối chiếu với
      RTO 8 giờ. Nếu lâu hơn nhiều so với 8 giờ khi dữ liệu còn nhỏ, cần
      cảnh báo sớm vì dữ liệu càng lớn restore càng lâu.
- [ ] **Bước 4 — Kiểm chứng dữ liệu**: chạy vài query đối chiếu số dòng
      (`SELECT COUNT(*) FROM tblEmployee`, v.v.) và mở thử ứng dụng Django
      trỏ tạm vào database vừa restore, đăng nhập thử, xem 1 vài bản ghi có
      đúng như mong đợi không.
- [ ] **Bước 5 — Viết Restore Report** (bắt buộc theo mục 21): ghi vào file
      `RestoreDrillLog.md` cùng thư mục — ngày thực hiện, người thực hiện,
      bản backup dùng test, thời gian restore thực tế, kết quả kiểm chứng
      (đạt/không đạt), vấn đề phát sinh nếu có.
- [ ] **Bước 6 — Dọn dẹp**: xoá database `qlhcns_restoretest` trên máy test
      sau khi xong, để không nhầm lẫn với database thật.

### Ghi RPO/RTO thực tế đo được

Sau vài lần diễn tập, so sánh với mục tiêu:
- **RPO 24 giờ**: vì Full backup 22:00 + Log backup mỗi giờ, RPO thực tế
  của hệ thống này là **~1 giờ** (tốt hơn nhiều so với mục tiêu 24 giờ) —
  vì luôn có log backup gần nhất trong vòng 1 giờ trước sự cố.
- **RTO 8 giờ**: cần đo thực tế qua diễn tập ở trên. Nếu vượt 8 giờ, cần
  xem lại: máy restore có đủ mạnh không, dung lượng backup có quá lớn
  không, hay cần restore song song nhiều file log cùng lúc.

## Kiểm soát lỗi và bảo vệ dữ liệu

`-Database` bắt buộc: thay TEN_DATABASE_DA_XAC_NHAN bằng đúng tên DB đã đối chiếu; Setup-RecoveryModel.sql vẫn là ví dụ qlhcns, phải sửa tên/path nếu cấu hình khác. Script dùng Windows Authentication, sqlcmd `-b -V 11 -x`, nhận diện edition và NO_COMPRESSION cho Express. Chỉ ghi thành công/dọn retention sau khi backup mới, RESTORE VERIFYONLY WITH CHECKSUM và kiểm tra file đạt; Weekly/Monthly kiểm tra SHA256 sau copy. Dọn theo prefix đúng database. Log backup giữ tối thiểu 30 ngày, đồng bộ cửa sổ Daily; DBA cần giữ toàn bộ chuỗi phù hợp mốc phục hồi yêu cầu. Không chạy đồng thời các job cùng database.

Chạy trên máy SQL Server hoặc dùng UNC mà cả service SQL và tài khoản Task đọc/ghi được. Tệp .sha256 là metadata kiểm chứng, bảo quản cùng backup. VERIFYONLY kiểm tra khả năng đọc/cấu trúc; không thay thế khôi phục database và đối chiếu nghiệp vụ. Nếu backup/verify/copy lỗi, mã thoát khác 0 và chưa dọn bản cũ. Theo dõi History/log và cảnh báo job thất bại.

Backup chứa dữ liệu nhân sự/lương: IT phải đặt ACL, mã hóa ổ/backup và sao chép sang đích độc lập được bảo vệ. SharePoint/local uploads cần kế hoạch sao lưu/khôi phục riêng cùng database; script SQL không sao lưu media. Chưa được phép ghi nhận restore drill đạt khi chưa chạy thật tại SIT.

## Kiểm thử script không dùng database

PowerShell 7: `./Test-BackupSafety.ps1 -Kind Full -Scenario Express`. Chạy cả Full/Log và Express/Standard/Failure (6 ca). Harness giả lập sqlcmd và chỉ tạo/xóa tệp ở thư mục tạm riêng; kiểm tra cú pháp, ngưỡng compression theo edition, failure exit, giữ bản cũ khi lỗi và không xóa backup của DB khác. CI chạy cùng harness. Kết quả này không xác nhận SQL Server, Windows ACL hoặc restore thật.
