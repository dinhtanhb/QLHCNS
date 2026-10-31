# Quy ước giao diện mobile IHRMS

Ứng dụng dùng React Native/Expo, chữ và điều khiển theo cỡ chữ hệ thống. Màu giao diện luôn lấy từ `useTheme()`; ba palette VietHealth, Chàm Đông, Than Ấm do cấu hình máy chủ chọn, còn sáng/tối theo cài đặt thiết bị hoặc lựa chọn đã lưu. Không thêm mã màu trực tiếp vào màn hình.

## Nền tảng hình ảnh

- Thang dùng chung trong `mobile/src/tokens.ts`: khoảng cách 4/8/12/16/24/32, chữ 12/14/16/18/20/24/32, bo góc 12/16/20. Màn hình ưu tiên chữ 16px, nhãn ngắn, khoảng trống để nhóm nội dung.
- Surface phẳng, viền theo token; không dùng gradient, glow hoặc bóng để thay cho thứ bậc. Nút chính dùng một màu thương hiệu; nút phụ dùng bề mặt; thao tác nhẹ dùng kiểu chữ/link.
- Vùng chạm tối thiểu 44px. Giữ `allowFontScaling`; khi chữ phóng lớn, nhãn được xuống dòng, thẻ được cao thêm, danh sách vẫn cuộn dọc.
- Trạng thái luôn có chữ và biểu tượng cùng chip màu ngữ nghĩa. Không truyền đạt chỉ bằng màu. Trạng thái tải dùng skeleton ngắn, không chạy hiệu ứng liên tục.
- Nhãn tab dùng `type.caption` (12px), giữ nhãn đầy đủ và vùng chạm tối thiểu 44px.
- Thẻ Duyệt thu gọn tên tối đa hai dòng, lý do tối đa ba dòng với dấu ba chấm. **Xem thêm** dùng ngưỡng bảo thủ tên >28/lý do >80 ký tự, giảm theo fontScale, hoặc nội dung có quá 2/3 dòng ngắt rõ ràng; RN Web chưa triển khai onTextLayout nên đây là heuristic dùng chung web/native, không phải phép đo cắt chữ chính xác. Thẻ ngắn không thêm hàng nút. Sheet cuộn chứa toàn bộ tên/lý do, nút đóng cố định; giữ luồng xác nhận quyết định.
- Tìm Nghiệp vụ chuẩn hóa NFD, bỏ dấu kết hợp và đổi đ/Đ thành d trước khi so khớp; nhãn hiển thị và quyền vẫn giữ nguyên.
- `overlay` là role riêng của mobile trong `palettes.json` cho từng sáng/tối; `ops/sync_mobile_tokens.py` giữ role này khi đồng bộ các màu đặc từ web. `tokens.ts` xuất nguồn palette cho `useTheme()`. Độ mờ lớp phủ giữ nguyên; kiểm tương phản màu đặc không chứng nhận lớp alpha.
- `DateTimeInput` time dùng hàm thuần `parseTime()` đọc HH:MM theo giờ địa phương, không dùng `Date.parse()` cho chuỗi chỉ có giờ; trống/sai định dạng hiện “Chọn giờ”. Kiểm logic: `node mobile/scripts/check-input-logic.cjs` từ gốc repo; không thay cho kiểm picker native.

Hồi quy nhóm C (sau khi export web và khởi động QA tổng hợp, từ gốc repo):
`venv\Scripts\python.exe ops\run_mobile_c_uat.py --directory <QA-ngoài-repo> --url http://127.0.0.1:8810 --output <ảnh-ngoài-repo>`.
Runner chạy 18 cấu hình ba độ rộng × sáng/tối × ba palette trên tài khoản QA
trưởng phòng: thẻ dài/chi tiết cuộn, bốn truy vấn tìm kiếm, năm tab 12px,
badge, vùng chạm và lớp phủ xác nhận. Phản hồi đọc là fixture tổng hợp;
không gửi quyết định từ runner này. `--single` chỉ là probe, không thay ma trận.
`--phase before` chỉ dùng trên export baseline còn lỗi để xác nhận tái hiện.

## Nên / tránh

| Nên | Tránh |
| --- | --- |
| `SectionHeader` 20px, mô tả phụ ngắn, nhóm cách nhau 24px | Lặp tiêu đề 24px và đoạn giới thiệu dài trên từng màn |
| Một nút primary cho việc chính; secondary/text cho việc còn lại | Viền đậm giống nhau cho mọi nút |
| `StatusChip` có nhãn và icon; `EmptyState` nói rõ bước tiếp theo | Nhúng trạng thái vào tiêu đề hoặc thẻ trống chỉ có một câu |
| `ListItem` gộp tên, thông tin phụ và thao tác thành một hàng | Biến từng trường thành thẻ có nhãn–giá trị dài |
| AppBar gọn, nhãn tab đầy đủ, biểu tượng có tên trợ năng | Cắt nhãn, dùng khoảng tab trống hoặc điều hướng bằng nút chữ “Quay lại” |

Ví dụ dùng:

```tsx
<SectionHeader title="Đơn nghỉ phép" detail="Cập nhật mới nhất" />
<ListItem title="12–13/11 · Phép năm" subtitle="Chờ duyệt" icon="calendar-outline" />
<StatusChip label="Chờ duyệt" tone="warning" />
<Button label="Tạo đơn nghỉ" onPress={openLeave} />
<Button label="Xem lịch sử" variant="text" onPress={openHistory} />
```

## Kiểm kê P0 — baseline 29/10/2026

Ảnh được chụp bằng Microsoft Edge headless trên bản Expo web export và DB/tài khoản QA tổng hợp. Ma trận gồm nhân viên và trưởng phòng; ba kích thước 360×800, 390×844, 412×915; hai chế độ sáng/tối; ba palette. Tổng cộng 342 ảnh, 0 lỗi JavaScript. Bản web chứng minh bố cục/luồng trên export, không chứng nhận Android/iOS native.

| Màn hình/route hiện tại | Quan sát baseline |
| --- | --- |
| Đăng nhập `/login` | Đầu trang và thẻ đăng nhập theo bố cục web, nhiều khoảng dọc trước trường nhập. |
| Trang chủ `/(tabs)` | Số liệu chiếm thẻ cao, nhãn xuống dòng và KPI lệch chiều cao; thiếu lời chào/tên/phòng và hành động chính nổi bật. |
| Hồ sơ `/(tabs)/profile` | Tab riêng; mở đầu bằng hai nút Cài đặt/Nghiệp vụ trước thông tin tài khoản. |
| Chấm công `/(tabs)/attendance` | Bộ điều khiển “Tải lại/Trang n”; trạng thái và số liệu trình bày thành nhiều thẻ. |
| Nghỉ phép `/(tabs)/leaves`, `/leave-new` | Nút tạo đơn, danh sách và biểu mẫu có thể cuộn dài; trạng thái nằm trong tiêu đề; ô ngày ở dạng nhập văn bản. |
| Duyệt `/(tabs)/approvals` | Route bị ẩn bằng nút tab rỗng; trưởng phòng chỉ mở được qua KPI/đường dẫn, không có tab Duyệt. Nút Duyệt/Từ chối đứng thành hàng dọc và gắn mã đơn. |
| Thông báo `/(tabs)/notifications` | Danh sách dùng thẻ dày, Tải lại/phân trang, trạng thái đọc nằm trong câu chữ. |
| Nghiệp vụ `/services` | Phải mở thêm từ Truy cập nhanh; 7 nhóm/24 mục theo vai trò, accordion đóng; thông tin hồ sơ cá nhân chiếm phần đầu danh sách. |
| Workspace `/workspace` | Không có thanh tab/app bar; có nút chữ Quay lại/Tải lại/Danh mục; tiêu đề `— IHRMS`, lọc dạng nút viền, ngày giờ thô và bảng công dài khoảng 9 màn hình. |
| Hồ sơ/cài đặt/đổi mật khẩu/tổ chức | Tiêu đề và mô tả lớn lặp lại; các thao tác dùng nút viền; trạng thái rỗng đơn giản. Những màn này thuộc P3, chưa thiết kế lại trong P2. |

Ảnh gốc và `baseline.json` nằm ngoài repository: `D:/IHRMS_Review_Exports/Mobile_Design_P0_20261029/`. Báo cáo không chứa mật khẩu, token hoặc hồ sơ thật.

## Phạm vi pha

P1 xây token và thành phần dùng chung. P2 áp dụng cho điều hướng, Trang chủ, Việc của tôi, Duyệt, Thông báo và lưới Nghiệp vụ. Workspace và các màn hồ sơ/cài đặt/đổi mật khẩu/tạo đơn chỉ làm sau khi chủ dự án duyệt P2.

## Ý nghĩa số liệu Trang chủ — M-06 phương án A

- **Bản ghi chấm công** — dòng phụ **Toàn bộ dữ liệu**: tổng số bản ghi của tài khoản, không phải số ngày công trong tháng.
- **Giờ làm** — dòng phụ **30 bản ghi gần nhất**: tổng giờ trong cửa sổ bản ghi chấm công mới nhất.
- **Đơn chờ** — dòng phụ **30 đơn gần nhất**: đếm đơn chờ trong cửa sổ đơn nghỉ phép mới nhất.
- **Chưa đọc** (nhân viên) — dòng phụ **30 thông báo gần nhất**: đếm chưa đọc trong cửa sổ thông báo mới nhất, có thể chưa bao gồm toàn bộ thông báo chưa đọc.
- **Cần duyệt** (người duyệt) — dòng phụ **Toàn bộ dữ liệu**: tổng đơn đang chờ thuộc quyền duyệt, dùng chung số đếm với huy hiệu tab.

Phạm vi được đặt ngay dưới nhãn, trước con số; không lặp lại bằng đoạn chú thích dưới lưới. Nhãn dùng token `type.label` (14px), dòng phụ dùng `type.caption` (12px), màu `muted` từ theme. Nhãn một dòng ở cỡ chữ chuẩn/360px; khi tăng cỡ chữ, nhãn và dòng phụ được xuống dòng, không giới hạn số dòng hoặc cắt chữ. Thẻ có chiều cao tối thiểu 136px, dùng chung chiều cao nội dung lớn nhất đo được để giữ đồng đều khi chữ tăng; icon ở hàng con số để nhãn có đủ chiều rộng.

Nhãn truy cập gộp cả ba phần, ví dụ `Giờ làm, 30 bản ghi gần nhất, 234`. `RECENT_KPI_LIMIT` là nguồn duy nhất của số giới hạn trong mã hiển thị. Hai hành động Trang chủ là **Tạo đơn nghỉ** và **Chấm công** (giữ icon đồng hồ); ở 360px/cỡ chữ chuẩn, hai nút cùng hàng và chữ trên mỗi nút một dòng. Không đổi cách tính, thêm bộ lọc tháng hoặc API tổng hợp.

### Chạy lại kiểm tra KPI

`ops/check_mobile_kpi_limit.py` dùng thư viện chuẩn Python, đọc hằng số `RECENT_KPI_LIMIT` và AST của `page()`/`Paginator`; không import Django hoặc kết nối database. Lệnh trả exit 1 nếu không đọc được giới hạn hoặc hai số lệch nhau:

```powershell
python ops/check_mobile_kpi_limit.py
```

`ops/run_mobile_home_uat.py` chạy 36 trường hợp trên bản Expo Web đang phục vụ cùng backend QA. Runner kiểm nhãn/dòng phụ theo vai, giá trị phân trang, tên truy cập đủ phạm vi và con số, màu/cỡ chữ, thẻ đồng chiều cao, cắt chữ/overflow và hai nút cùng hàng/một dòng. Có thêm 12 mô phỏng phóng chữ KPI 200% bằng CSS ở 360px và kiểm Tab giữa hai nút cho hai vai. Hàm assertion dùng chung cũng được `ops/run_mobile_settings_uat.py` chạy cho cả hai vai trên dữ liệu QA không giả lập. Ma trận dùng fixture các API đọc có trang sau; đăng nhập/quyền lấy từ tài khoản demo. Mô phỏng CSS không chứng nhận font scale, trình đọc màn hình trên thiết bị hoặc Android/iOS native. Mật khẩu đọc từ tệp QA, không ghi trong mã.

Chuẩn bị QA theo hướng dẫn mobile hiện có, export web với `EXPO_PUBLIC_ALLOW_HTTP=true` khi dùng HTTP loopback và chạy `ops/mobile_qa.py serve`. Truyền thư mục QA có marker `synthetic_only`, origin loopback và thư mục ảnh ngoài repo; ví dụ với QA hiện có:

```powershell
# Cửa sổ 1: phục vụ backend QA và bản web export đã chuẩn bị.
venv/Scripts/python.exe ops/mobile_qa.py serve --directory D:/IHRMS_Review_Exports/Mobile_Design_P2b_20261030/qa --port 8810

# Cửa sổ 2: chạy ma trận Trang chủ, giữ server QA đang mở.
venv/Scripts/python.exe ops/run_mobile_home_uat.py --directory D:/IHRMS_Review_Exports/Mobile_Design_P2b_20261030/qa --url http://127.0.0.1:8810 --output D:/IHRMS_Review_Exports/Mobile_M06_Polish_20261030
```

Mặc định runner dùng Microsoft Edge (`--channel msedge`). Có thể chỉ định channel trình duyệt đã cài khác. Tất cả đường dẫn QA/output là tham số; runner từ chối thư mục trong repo và origin ngoài loopback.
