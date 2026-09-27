# Yêu cầu Codex: sửa tận gốc lỗi UnicodeEncodeError (cp1252) khi output bị redirect trên Windows

## Bối cảnh (đã tái hiện thực tế trên máy chủ Windows)

Khi chạy management command in ra chữ tiếng Việt có dấu (vd `"Đã tạo {n} thông báo..."`) và
output của `python.exe` bị **redirect ra file/qua Task Scheduler** (không còn là console tương
tác), Python rơi về bảng mã hệ thống mặc định của Windows (ở máy chủ này là `cp1252` — Tây Âu),
bảng mã này không có các ký tự tiếng Việt có dấu → crash:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u0110' in position 0
```

Chạy tay trong cửa sổ PowerShell (console thật) thì **không** lỗi — vì Python dùng API console
Unicode riêng khi output gắn với console thật. Lỗi chỉ lộ ra khi output bị redirect (file, pipe,
Task Scheduler) — đúng chính là cách 2 lệnh nhắc việc (`send_activity_report_reminders`,
`send_lifecycle_reminders`) sẽ chạy trong production.

**Đã vá tạm ở mức PowerShell** (đặt `$env:PYTHONIOENCODING='utf-8'` +
`$env:PYTHONUTF8='1'` trước khi gọi `python.exe`) cho `Run-LifecycleReminders.ps1`, và cần vá
tương tự cho `Run-ActivityReportReminders.ps1` (đang dùng nguyên `f"Đã tạo {sent} thông báo nhắc
việc."` — chắc chắn dính đúng lỗi này).

## Vấn đề với cách vá tạm ở trên

Vá từng file `.ps1` là **vá vào triệu chứng, không phải nguyên nhân**. Rủi ro còn lại:

- **Bất kỳ management command nào khác** in tiếng Việt có dấu, chạy qua Task Scheduler / CI / bị
  redirect trong tương lai, sẽ dính lại **đúng lỗi này** — không có cách nào một người không
  phải dev nhận ra trước, chỉ phát hiện khi nó crash trên production.
- Người vận hành không phải lập trình viên (không nên phải sửa từng script PowerShell mỗi khi
  phát sinh command mới) — nhu cầu thực tế là "sửa 1 lần, ở đúng 1 chỗ, áp dụng cho toàn bộ hệ
  thống".

## Yêu cầu: sửa tận gốc tại `src/manage.py` (áp dụng cho MỌI management command, không chỉ 2 lệnh nhắc việc)

Thêm đoạn sau vào `src/manage.py`, ngay sau `import sys`, trước khi gọi bất kỳ lệnh Django nào:

```python
import os
import sys

# Sửa tận gốc UnicodeEncodeError khi output bị redirect (Task Scheduler, pipe, file) trên
# Windows với bảng mã hệ thống không phải UTF-8 (vd cp1252). Áp dụng cho MỌI management
# command chạy qua manage.py, không chỉ 2 lệnh nhắc việc — không cần sửa riêng từng script
# PowerShell/Task Scheduler nữa.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main():
    ...
```

`reconfigure()` có sẵn từ Python 3.7+ (dự án đang dùng 3.12), không cần cài thêm gì. Cách này
**không phụ thuộc biến môi trường hệ thống** do IT cấu hình (dễ bị thiếu/quên khi dựng máy chủ
mới) — logic nằm trong code, luôn được áp dụng bất kể ai chạy, chạy từ đâu, qua Task Scheduler
hay chạy tay.

## Việc cần làm cụ thể

1. Thêm đoạn code trên vào `src/manage.py`.
2. Có thể **giữ nguyên** phần vá `$env:PYTHONIOENCODING`/`$env:PYTHONUTF8` đã thêm trong
   `ops/scheduler/Run-LifecycleReminders.ps1` (vô hại, có cũng không sao — phòng hờ 2 lớp) —
   không bắt buộc gỡ ra.
3. Vá tương tự (thêm 2 dòng `$env:PYTHONIOENCODING`/`$env:PYTHONUTF8`) vào
   `ops/scheduler/Run-ActivityReportReminders.ps1` — dù đã sửa gốc ở `manage.py`, giữ lại lớp vá
   này ở script cũ cho nhất quán với `Run-LifecycleReminders.ps1`, phòng trường hợp về sau có ai
   gọi `python.exe` trực tiếp mà không qua `manage.py`.
4. Rà xem `src/config/wsgi.py`/`asgi.py` có in log tiếng Việt ra stdout lúc khởi động không (nếu
   sau này server chạy qua IIS/waitress trên Windows) — nếu có, áp dụng cùng cách `reconfigure()`
   ở đó.
5. Cập nhật `docs/PROJECT_WORK_LOG.md` theo đúng quy ước đang dùng, ghi rõ: lỗi gặp phải, nguyên
   nhân gốc, đã sửa ở đâu, và lưu ý đây là **sửa tận gốc — không cần vá thêm cho command mới
   phát sinh sau này**.

## Cách xác nhận đã sửa đúng (không cần máy Windows thật, làm được trên máy dev thường)

```powershell
# Giả lập điều kiện gây lỗi: chạy 1 lệnh có in tiếng Việt, redirect ra file
.\venv\Scripts\python.exe src\manage.py send_lifecycle_reminders > test_output.log 2>&1
type test_output.log
```
Kỳ vọng: không còn `UnicodeEncodeError`, thấy đúng dòng `Đã tạo N thông báo nhắc checklist.` với
dấu tiếng Việt hiển thị đúng (hoặc `?`/ký tự thay thế nếu terminal hiển thị không hỗ trợ, nhưng
**không được crash**).

Sau khi sửa xong, chạy lại toàn bộ test suite hiện có (`python manage.py test`) để đảm bảo không
ảnh hưởng gì khác — thay đổi này chỉ tác động tới stdout/stderr, không đụng logic nghiệp vụ.
