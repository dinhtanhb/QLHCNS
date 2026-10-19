# Hướng dẫn review dự án IHRMS

Quy tắc dự án và quyền thao tác có nguồn tại [AGENTS.md](../AGENTS.md).
Tài liệu này chứa quy trình/checklist/lệnh review; skill và agent của từng
client chỉ định tuyến tới đây. Khi xung đột, áp dụng yêu cầu hiện hành của
chủ dự án và AGENTS.md.

## Chọn cách review

Skill [`ihrms-review`](../.agents/skills/ihrms-review/SKILL.md) dành cho IHRMS, hỗ trợ hai phạm vi:

- **FULL**: review mã hiện tại của toàn dự án, cả khi working tree sạch. Kiểm kê tất cả phân hệ; ghi rõ phần đã đọc, đã thử và còn thiếu.
- **CHANGES**: review thay đổi chưa commit hoặc từ một commit gốc cụ thể. Phù hợp sau một tính năng/bản sửa. Trên `main`, diff `main...HEAD` có thể rỗng, không dùng nó để thay thế review FULL.

Hai chế độ thao tác:

- **REVIEW** (mặc định): chỉ đọc mã và chạy kiểm tra bằng dữ liệu/DB/media tạm; không sửa mã/tài liệu, commit hoặc push. Nếu yêu cầu không cho phép tạo báo cáo, trả kết quả trong chat.
- **FIX**: được sửa lỗi đã xác nhận và bổ sung kiểm thử. Commit/push theo ủy quyền hiện hành tại AGENTS.md, trừ khi chủ dự án yêu cầu khác. Migration/triển khai vào môi trường đang dùng là nhiệm vụ riêng, cần xác nhận đích và backup.

## Sử dụng skill

Yêu cầu dùng skill `ihrms-review`, kèm phạm vi FULL/CHANGES và chế độ REVIEW/FIX.
Skill nằm tại `.agents/skills/ihrms-review/SKILL.md`, tách biệt với skill
`code-review` chỉ rà diff theo hai trục Standards/Spec.

Nếu công cụ chưa nhận skill mới trong phiên đang mở, đọc trực tiếp tệp skill
cùng hướng dẫn này rồi thực hiện nhiệm vụ; ghi rõ công cụ thực dùng. Skill
không khai báo quyền riêng của extension; quyền thao tác theo nhiệm vụ và AGENTS.md.

Ba skill riêng `ihrms-review`, `ihrms-operations`, `ihrms-project` có bản dùng
chung trong `.agents/skills` và con trỏ trong `.claude/skills`; Cursor dùng
`.cursor/agents/ihrms-reviewer.md`. Không chép quy trình sang các con trỏ.

Kiểm discovery bằng phiên mới tại đúng workspace trong từng client (Codex,
Antigravity, Claude Code nếu dùng): yêu cầu “rà soát toàn dự án IHRMS, chế độ
REVIEW” mà không nêu tên skill; kiểm catalog/log xem có chọn `ihrms-review`
và đọc đúng nguồn. Ghi client/phiên/kết quả; tệp tồn tại hoặc đọc trực tiếp
thành công chưa chứng minh tự nhận skill. Nếu client không đọc `.agents/skills`,
dùng cơ chế discovery được client hỗ trợ hoặc đường dẫn trực tiếp. Chưa có
bằng chứng thì để việc kiểm discovery còn mở.

### Mẫu review tổng thể, chưa sửa

```text
Dùng skill ihrms-review tại D:\QLHCNS\.agents\skills\ihrms-review\SKILL.md.
Workspace: D:\QLHCNS. Phạm vi FULL, chế độ REVIEW.
Đọc AGENTS.md và docs/Huong_Dan_Review_Du_An.md trước.
Rà tất cả phân hệ hiện tại, không chỉ git diff. Không sửa mã/tài liệu,
không commit/push, không ghi dữ liệu nghiệp vụ gốc.
Chạy gate phù hợp trên DB/media tạm, gồm SQLite và SQL Server nếu có.
Báo finding theo P0-P3 với path:line, trigger, bằng chứng và đề xuất.
Liệt kê phạm vi đã rà/chưa rà, lệnh/kết quả và phần chưa kiểm thử.
Không tuyên bố 100% hoặc Bugbot đã chạy khi chưa có bằng chứng.
```

### Mẫu review tổng thể, sửa và hoàn tất CI

```text
Dùng skill ihrms-review tại D:\QLHCNS\.agents\skills\ihrms-review\SKILL.md.
Workspace: D:\QLHCNS. Phạm vi FULL, chế độ FIX; chỉ làm trên main.
Đọc AGENTS.md và docs/Huong_Dan_Review_Du_An.md trước.
Rà toàn dự án hiện tại; sửa lỗi xác nhận được, giữ quy tắc nghiệp vụ.
Giữ thay đổi cục bộ ngoài phạm vi; không ghi bản ghi nghiệp vụ gốc.
Thêm regression test cần thiết và lặp sửa/test đến khi gate yêu cầu đạt.
Chạy full SQLite và SQL Server cô lập, audit dependency, framework/migration,
frontend build và 6 ca backup mô phỏng. Sửa UI thì thử trình duyệt cô lập.
Cập nhật docs/PROJECT_WORK_LOG.md trong một mục của đợt.
Được commit/push các tệp thuộc nhiệm vụ lên main, rồi xác nhận GitHub Actions
của đúng SHA cuối: cả backend, frontend, backup-command-tests đều success.
Không deploy production hay migrate DB đang dùng trong nhiệm vụ này.
Báo tệp đã sửa, bằng chứng kiểm thử, SHA/link CI, phần chưa kiểm tra và blocker.
```

### Mẫu review thay đổi

```text
Dùng skill ihrms-review cho D:\QLHCNS. Phạm vi CHANGES, chế độ REVIEW.
Review staged + unstaged + tệp mới thuộc tính năng [mô tả/tên tệp].
Nếu có thay đổi đã commit: commit gốc là [SHA cụ thể].
Đọc caller, guard, test và tài liệu nghiệp vụ liên quan.
Chạy kiểm tra phù hợp trên môi trường cô lập, báo lỗi xác nhận được;
không sửa mã/tài liệu, không commit/push.
```

## Phân biệt công cụ review

Skill `review-bugbot` dùng công cụ Bugbot riêng; `ihrms-review` không cài hoặc
thay thế công cụ đó. Chỉ ghi Bugbot đã chạy khi có kết quả thực. Với FULL,
nêu rõ toàn mã hiện tại thay vì dùng kết quả của một skill chỉ rà diff.

## Checklist phạm vi FULL

Kiểm kê `src/apps` mỗi lần; danh sách dưới là điểm xuất phát, không thay thế phân hệ mới:

- **HR/organization/lifecycle/recruitment**: phạm vi hồ sơ, ràng buộc, chuyển trạng thái và vòng đời nhân sự.
- **Attendance/leave/payroll/contract**: ngày giờ, Decimal/làm tròn, dữ liệu âm/trùng, quỹ phép, công thức đã duyệt, transaction và cập nhật đồng thời.
- **Office/asset/procurement/project/activity/planning/task/KPI**: tạo-duyệt-từ chối-hủy, gửi trùng/gửi lại, chủ thể có quyền và trạng thái không hợp lệ.
- **Portal/security/document/notification/reporting**: Axes và login, RBAC ở máy chủ, truy cập đối tượng bằng URL/ID trực tiếp, CSRF, upload/download, lọc báo cáo và N+1.
- **Common/config/migrations**: bảng/migration thiếu, FK/unique/null, dữ liệu cũ, tương thích SQLite/SQL Server, cấu hình production và tích hợp M365.
- **Template/frontend/static/ops/CI**: số theo locale, CSS build, responsive, backup/restore và đúng ba job CI hiện có.

Theo URL/view qua form/service/model đến template/test; đọc caller và guard.
Mỗi finding có path:line hiện tại, trigger, tác động, guard đã kiểm và cách tái
hiện bằng dữ liệu giả. Phân biệt lỗi xác nhận với giả thuyết. Giữ facade
`src/apps/portal/views/__init__.py` khi sửa cấu trúc; ưu tiên sửa tối thiểu lỗi
xác nhận và regression test có giá trị trước khi chạy gate rộng.

Đọc tài liệu tương ứng ở `docs/01_BRD_MASTER.md`, `docs/03_Database_Design.md`, `docs/04_Security_Design.md`, `docs/07_Testing_Standards.md`, `docs/10_RBAC_Permission_Matrix.md`, `docs/11_Workflow_Definition.md` và các tiêu chuẩn backend/frontend/deployment. Ghi chênh lệch mã/tài liệu; không âm thầm sửa nghiệp vụ cho khớp suy đoán.

## Lệnh kiểm tra chuẩn

Chạy trong PowerShell tại `D:\QLHCNS`. Mỗi lệnh phải ghi exit code và lỗi thực tế; gặp lỗi thì xử lý trước khi kết luận. Không lấy số test của lần trước làm mục tiêu cố định.

### Git và môi trường

```powershell
Set-Location D:\QLHCNS
git status --short
git branch --show-current
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
git diff --check
$env:PYTHONIOENCODING = 'utf-8'
venv\Scripts\python.exe -m pip check
```

Chỉ `git pull --ff-only origin main` khi nhánh là main, working tree sạch và không phân kỳ. Không reset/stash/đổi nhánh để làm sạch. Tệp cá nhân chưa theo dõi chỉ được dọn khi nằm trong phạm vi đã cho phép.

### Framework và drift migration, không áp dụng migration

Khối sau dùng SQLite và SECRET_KEY tạm, khôi phục biến môi trường sau kiểm tra; không in bí mật và không chạy `migrate` trên DB cấu hình:

```powershell
$reviewOldEngine = $env:DB_ENGINE
$reviewOldKey = $env:SECRET_KEY
try {
    $env:DB_ENGINE = 'django.db.backends.sqlite3'
    $env:SECRET_KEY = (& venv\Scripts\python.exe -c 'import secrets; print(secrets.token_urlsafe(64))')
    & venv\Scripts\python.exe src\manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'Django check failed' }
    & venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run
    if ($LASTEXITCODE -ne 0) { throw 'Migration drift check failed' }
} finally {
    $env:DB_ENGINE = $reviewOldEngine
    $env:SECRET_KEY = $reviewOldKey
}
```

Kiểm tra drift không xác nhận migration đã áp dụng trên SQL Server. Sau khi
xác minh cấu hình/alias DB được phép kiểm chỉ đọc (hoặc bản sao cô lập), chạy:

```powershell
venv\Scripts\python.exe ops\check_migration_state.py --database default
# Thu hẹp khi cần: thêm --app task (lặp --app cho nhiều phân hệ).
```

Lệnh này đọc DB mà settings trỏ tới, không tự tạo môi trường cô lập. Exit 1
nghĩa là còn migration nguồn chưa áp dụng, exit 2 là không đọc được trạng thái;
không tự chạy migrate để làm xanh kết quả.

Khi FIX thay model/schema, áp dụng mục “Migration và thay đổi schema” trong
AGENTS.md: model và migration đi **commit riêng**, có kế hoạch áp dụng/hoàn tác
và nguồn yêu cầu nghiệp vụ truy vết trong nhật ký. Kiểm SQL thực trên cả SQLite
và cấu hình SQL Server tạm trước bàn giao, với từng migration liên quan:

```powershell
# Thay app_label/migration_name; chạy lần lượt dưới settings SQLite và SQL Server tạm.
venv\Scripts\python.exe src\manage.py sqlmigrate app_label migration_name
```

Không dùng settings vận hành cho ví dụ kiểm SQL; kiểm trạng thái/drift/SQL không
thay backup, restore thử, migrate bản sao hoặc UAT. Không áp migration khi REVIEW.

### Regression cô lập

```powershell
venv\Scripts\python.exe ops\run_tests.py --backend sqlite
venv\Scripts\python.exe ops\run_tests.py --backend sqlserver
# Ví dụ chạy tập trung trước full suite:
venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.office.tests
```

Runner tạo SQLite memory hoặc SQL Server `test_ihrms_<UUID>`, media tạm, email memory và tắt M365. SQL Server cần cấu hình backend SQL, ODBC và quyền tạo/xóa **DB test**. Nếu không đủ quyền, ghi chưa chạy SQL; không chuyển sang ghi DB thật. Runner và wrapper `ops/Run-Tests.ps1 -Backend sqlite|sqlserver` bắt buộc chỉ định backend. `configured` chỉ còn là lựa chọn tương thích khi gọi rõ; không dùng trong review để tránh chọn backend ngoài dự kiến.

### Gate giao diện, hợp đồng form, bản in và cache

Chọn gate theo thay đổi và quy tắc bắt buộc trong mục “Kiểm thử luồng nghiệp vụ
trên trình duyệt” của AGENTS.md. FULL phải ghi rõ mỗi gate đã chạy hoặc lý do
không áp dụng/chưa chạy. Thay CSS dùng chung/template form/bảng/thẻ chạy layout
và form; phạm vi in chạy print, thay asset/CSS/JS/service worker chạy cache;
thay nút/token/màu chạy audit tương ứng. Audit tĩnh không thay browser.

Mẫu sau cần runtime **giả, ngoài repo**, QA riêng, tắt M365/email thật;
Playwright/Edge và thư viện PDF QA cài riêng ngoài dependency ứng dụng.
Thay đường dẫn mẫu bằng đường dẫn thực đã kiểm:

```powershell
$reviewRuntime = Join-Path $env:TEMP 'ihrms-review-synthetic_only'
$reviewPackages = Join-Path $env:TEMP 'ihrms-review-packages'
$reviewPdfPackages = Join-Path $env:TEMP 'ihrms-review-pdf-packages'
$reviewBaseline = Join-Path $env:TEMP 'ihrms-review-baseline'
# Chỉ create runtime mới; không tái dùng DB/media vận hành.
venv\Scripts\python.exe ops\dashboard_demo.py create --directory $reviewRuntime
venv\Scripts\python.exe ops\run_browser_uat.py --backend sqlite --packages-dir $reviewPackages
venv\Scripts\python.exe ops\run_browser_uat.py --backend sqlserver --packages-dir $reviewPackages

# Baseline: snapshot nguồn trước sửa, đã loại secrets/DB/media.
# Seed fixture layout trước, rồi đo form trên cùng DB giả ổn định.
venv\Scripts\python.exe ops\run_layout_alignment_audit.py --directory $reviewRuntime --packages-dir $reviewPackages --source-root $reviewBaseline --phase before --seed
venv\Scripts\python.exe ops\run_form_contract_uat.py --directory $reviewRuntime --source-root $reviewBaseline --phase before
# Chạy after sau sửa, giữ nguyên DB giả/baseline để so sánh có ý nghĩa.
venv\Scripts\python.exe ops\run_layout_alignment_audit.py --directory $reviewRuntime --packages-dir $reviewPackages --phase after
venv\Scripts\python.exe ops\run_form_contract_uat.py --directory $reviewRuntime --phase after
venv\Scripts\python.exe ops\run_print_layout_uat.py --directory $reviewRuntime --packages-dir $reviewPackages --pdf-packages-dir $reviewPdfPackages
venv\Scripts\python.exe ops\audit_button_kinds.py --directory $reviewRuntime --packages-dir $reviewPackages --output (Join-Path $reviewRuntime 'button-kinds.json')
venv\Scripts\python.exe ops\audit_design_tokens.py --check
venv\Scripts\python.exe ops\check_ui_contrast.py
```

Layout mặc định quét toàn route/vai trò, bảy độ rộng và sáng/tối theo AGENTS.md;
`--only`, `--accounts`, `--widths` chỉ phục vụ probe, không thay lượt quét đóng
giai đoạn. Ghi số vi phạm trước/sau, backend, vai trò, độ rộng, thư mục bằng
chứng và contact sheet trước/sau 1756/390px theo mô-đun. Đối chiếu waiver được
duyệt trong `ops/layout_waivers.json`; không tự thêm để bỏ lỗi. Form so hợp
đồng gửi/query với baseline cùng DB giả; cờ `--allow-*` cần nguồn yêu cầu được
duyệt, không dùng để bỏ khác biệt chưa giải thích.

Print phải so ảnh/số đo PDF với mẫu chuẩn: màu, viền, ngắt trang, khoảng ký;
không chỉ đếm trang. Đổi `print_forms.css` phải tăng `?v=` trong `base.html`.
Nếu sửa hồi quy, ghi vì sao kiểm cũ bỏ sót. Bản in độc lập với lưới màn hình.

Cache cần **hai server QA đang chạy** trên cùng DB/media giả, mã baseline và
mã cuối có phiên bản asset khác nhau. Mở hai terminal riêng; layout/print tự
quản server của chúng, không chiếm cổng 8770/8771 dưới đây:

```powershell
# Terminal baseline, dùng venv dự án với script từ snapshot trước sửa:
venv\Scripts\python.exe "$reviewBaseline\ops\dashboard_demo.py" serve --directory $reviewRuntime --port 8771
# Terminal nguồn cuối:
venv\Scripts\python.exe ops\dashboard_demo.py serve --directory $reviewRuntime --port 8770
# Terminal kiểm thử; khai báo lại biến đường dẫn nếu là shell mới:
venv\Scripts\python.exe ops\run_asset_cache_uat.py --directory $reviewRuntime --packages-dir $reviewPackages --port 8770 --baseline-port 8771
```

Cache kiểm phiên có cache cũ cập nhật mà không xóa dữ liệu. Nếu hai bản asset
không khác nhau hoặc chưa có server/baseline, ghi gate chưa chạy/không áp dụng
với lý do; không tạo baseline giả để lấy PASS. Runtime demo của gate
layout/form/print/cache dùng SQLite, không chứng minh SQL Server UAT.
Luồng ngoài phạm vi runner browser cần bổ sung ca nghiệp vụ tương ứng, kiểm
thông báo, trang đích, dữ liệu đã lưu và Dashboard theo đặc tả đã duyệt.

### Dependency, frontend và backup mock

```powershell
# pip-audit phải có trong venv; CI hiện pin 2.9.0, đối chiếu ci.yml mỗi lần.
venv\Scripts\python.exe -m pip_audit -r requirements.txt
npm ci
npm audit --audit-level=low
npm run build:css
foreach ($reviewKind in @('Full', 'Log')) {
    foreach ($reviewScenario in @('Express', 'Standard', 'Failure')) {
        & .\ops\backup\Test-BackupSafety.ps1 -Kind $reviewKind -Scenario $reviewScenario
        if ($LASTEXITCODE -ne 0) { throw "Backup mock failed: $reviewKind/$reviewScenario" }
    }
}
git diff --check
git status --short
```

`npm ci` ghi node_modules; build ghi CSS được Git theo dõi. Trong REVIEW không đổi mã, chạy frontend trong bản sao tạm **đã loại secrets/DB/media và giữ đúng thay đổi cần review**, hoặc dùng CI đúng SHA; không chạy build rồi reset/ghi đè CSS người dùng. Không audit bằng cách đưa token vào lệnh/chat. Backup mock không thay restore drill với SQL Server thật.

### GitHub Actions khi được giao commit/push

```powershell
git rev-parse HEAD
gh run list --branch main --commit (git rev-parse HEAD) --limit 5
gh run view <RUN_ID> --json headSha,status,conclusion,jobs,url
gh run view <RUN_ID> --log-failed
```

Thay `<RUN_ID>` bằng ID thật. Nếu CLI lỗi 401 hoặc thiếu quyền, dùng connector/trang Actions bằng tài khoản có quyền; đối chiếu `headSha` đúng HEAD. Cả ba job phải **completed/success**, không chỉ một job xanh. CI hiện dùng SQLite, không chứng minh SQL Server/Windows/IIS/M365 đã đạt. Không có run, bị cancel, queued hoặc in_progress phải ghi chưa đạt/chưa xác nhận đúng trạng thái.

## Điều kiện kết thúc và báo cáo

Báo phạm vi đã đọc, finding xác nhận, các sửa đổi nếu có, lệnh/exit code, số test và lý do skip; tách HTTP tự động, browser thật, local, CI và production. “Tất cả gate đã chạy đạt” không đồng nghĩa “không còn lỗi” hay “coverage 100%”. Không thêm skip hoặc giảm gate để đạt số đẹp.

Với FIX, ghi một mục của đợt trong [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md), stage đúng tệp được giao, kiểm tra staged diff rồi mới commit nếu được phép. Báo commit/push thực tế và phần còn mở. Với REVIEW chỉ đọc, trả báo cáo trong chat; chỉ ghi báo cáo/nhật ký khi nhiệm vụ cho phép.
