# Thiết kế: Chatbot trợ lý tài liệu IHRMS + rà soát thông báo/email

Ngày: 2026-10-19
Trạng thái: đã duyệt chủ dự án (phương án A — chatbot trong portal, không dùng LLM ngoài)
Nguồn yêu cầu: chủ dự án — "tạo chatbot phục vụ dự án IHRMS, VD tìm công văn nhanh chóng"; mở rộng thông báo/email + kiểm thử; dùng nội bộ.

## 1. Mục tiêu và phạm vi

### Trong phạm vi

1. App Django mới `apps/assistant`: chatbot tìm kiếm tài liệu bằng câu hỏi tiếng Việt, nguồn:
   - Database IHRMS (SQL Server): `OfficialDispatch`, `Document`, `PersonnelDecision`.
   - SharePoint qua Microsoft Graph (thư mục cấu hình hiện có + Graph search khi được cấp quyền).
2. UI chatbot: nút nổi trên portal + trang `/assistant/`.
3. Log truy vấn `SearchQueryLog` (không lưu nội dung tài liệu).
4. Rà soát độ phủ thông báo trong ứng dụng + outbox email hiện có; vá lỗ hổng nhỏ nếu phát hiện.
5. Kiểm thử đầy đủ theo AGENTS.md và ghi nhật ký.

### Ngoài phạm vi (đã thống nhất)

- Không dùng LLM/API AI bên ngoài; dữ liệu không rồi khỏi hệ thống.
- OneDrive: giai đoạn 2 (cần Graph consent riêng từ IT).
- Không tìm trong email Outlook.
- Server không tự gửi email; giữ cơ chế mở nháp Outlook, chờ IT chốt kênh gửi (theo HRMS_Next_Features_Plan).
- Báo cáo tuân thủ BHXH/thuế, checklist onboarding/offboarding, SSO/Teams — thuộc kế hoạch khác.

## 2. Kiến trúc

```
Portal (template base.html)
  └─ nút chat nổi + trang /assistant/  (assistant/templates, static JS/CSS)
       └─ POST /assistant/api/search/  (login required, rate limit)
            └─ services.ask(question, user)
                 ├─ nlp.parse(question) → ParsedQuery
                 ├─ db_search.search(ParsedQuery, user)     → ORM, SQL Server
                 ├─ sharepoint_search.search(ParsedQuery)    → GraphClient (mở rộng)
                 └─ rank + trả SearchResponse {results[], parsed, took_ms}
```

- Module hóa theo modular monolith hiện có; không đổi kiến trúc, không thêm service ngoài.
- `apps/m365/graph_client.py`: thêm `search_files()`; giữ nguyên các phương thức hiện có.

## 3. Thành phần chi tiết

### 3.1 `apps/assistant/nlp.py`

Parser quy tắc, deterministic, không học máy:

| Nhận diện | Mẫu | Đầu ra |
|---|---|---|
| Số hiệu văn bản | `1234/QĐ-VH`, `CV 12/2026` | `doc_number` |
| Khoảng thừơng gian | "tháng 6", "quý 2", "năm 2025", "từ ... đến ...", "tuần trước" | `date_from`, `date_to` |
| Loại văn bản | công văn đi/đến, quyết định, hợp đồng, đơn nghỉ phép, biên bản, tờ trình | `doc_type` |
| Cụm trích yếu | ngoặc kép `"nghỉ phép không lương"` | `phrases[]` |
| Từ khóa còn lại | sau loại bỏ stopword tiếng Việt | `keywords[]` |

Quy tắc ưu tiên: số hiệu > cụm trích yếu > từ khóa. Không parse được gì → toàn bộ câu làm `keywords` (fallback tìm tự do).

### 3.2 `apps/assistant/search/db_search.py`

- Tìm trên 3 model chính (trường đích chốt khi implement sau khi đọc model hiện hữu):
  - `OfficialDispatch`: số hiệu, trích yếu, đơn vị gửi/nhận, ngày văn bản.
  - `Document`: tiêu đề, danh mục, ghi chú.
  - `PersonnelDecision`: số quyết định, loại, ngày hiệu lực.
- Truy vấn ORM (`icontains`, `range`), không raw SQL; mỗi kết quả gắn `url` tới trang chi tiết hiện có.
- **Phân quyền:** áp dụng đúng bộ lọc quyền của view danh sách tương ứng (đọc kỹ view hiện hữu trước khi code; trích hàm chung nếu chưa có). Ngưởi dùng không thấy tài liệu ngoài quyền kể cả khi hỏi trúng từ khóa.

### 3.3 `apps/m365/graph_client.py` — bổ sung

- `search_files(query, folder=None)`: gọi Graph `POST /search/query` (entityType `driveItem`, giới hạn site SharePoint IHRMS). Timeout mặc định của `_request`.
- Nếu lỗi 403/404 (chưa được cấp quyền search): fallback duyệt các thư mục cấu hình (`M365_FOLDER_*`), lọc theo tên file chứa `query`; ghi log một lần mỗi phiên để admin biết cần consent.
- Trả về `[{name, web_url, last_modified, folder}]` — không tải nội dung file.

### 3.4 `apps/assistant/services.py`

- `ask(question, user)`: parse → tìm song song DB + SharePoint (chịu lỗi từng nguồn) → gộp → xếp hạng → `SearchResponse`.
- Xếp hạng: trùng số hiệu (đầu tiên, cố định đứng đầu) > trùng cụm trích yếu > số từ khóa trùng > ngày mới nhất.
- Kết quả SharePoint lỗi: trả kết quả DB + cờ `partial=True`, UI hiển thị cảnh báo "SharePoint tạm không khả dụng".

### 3.5 `apps/assistant/models.py`

```python
class SearchQueryLog(BaseAuditModel):
    user            # FK security.User
    question        # CharField 500
    parsed_filters  # JSONField (bộ lọc sau parse)
    result_count    # int
    sources         # CharField: "db", "sharepoint", "db+sharepoint"
    took_ms         # int
    error_note      # CharField, nullable
```

Không lưu kết quả/nội dung tài liệu. Admin chỉ đọc.

### 3.6 Views, URLs, UI

- `GET /assistant/` — trang chat (login required).
- `POST /assistant/api/search/` — JSON `{question}` → `{results[], parsed, took_ms, partial}`; rate limit 30 req/phút/user (cache đếm đơn giản); validate độ dài câu hỏi ≤ 500 ký tự.
- Nút chat nổi chèn qua `base.html`; panel chat lazy-load JS khi ngưởi dùng mở lần đầu.
- UI theo design system hiện hữu (docs/UI_DESIGN_SYSTEM.md): gợi ý nhanh "Công văn gần đây", "Quyết định tháng này"; thẻ kết quả có icon nguồn (IHRMS/SharePoint), tiêu đề, dòng metadata, link; hỗ trợ bàn phím (Enter gửi, Esc đóng); trạng thái loading/empty/error.

### 3.7 Thông báo/email (rà soát, không xây mới)

- Đối chiếu từng luồng duyệt: nghỉ phép, kỳ lương, công văn (`document/hcns`), activity → xác nhận đã gọi `notify`/`notify_with_email_draft`, đúng ngưởi nhận, đúng idempotency.
- Phát hiện lỗ hổng → vá trong phạm vi nhỏ, test tương ứng. Không đổi cơ chế gửi thư; không bật server send.

## 4. Phân quyền và bảo mật

- Toàn bộ endpoint yêu cầu đăng nhập; kết quả DB lọc theo RBAC hiện có (kiểm server-side, không tin client).
- Kết quả SharePoint chỉ tên + `webUrl`; ngưởi dùng mở file bằng quyền M365 của chính mình.
- Không gọi API ngoài trừ Graph đã cấu hình; không đưa dữ liệu nhân sự ra ngoài.
- ORM chống injection; chuỗi gửi Graph giới hạn độ dài, escape theo chuẩn JSON.
- `SearchQueryLog` chỉ admin/HR quản trị xem được; có cơ chế dọn log cũ (management command đơn giản, chạy thủ công).

## 5. Dữ liệu và migration

- 1 migration mới cho `SearchQueryLog` (app `assistant`).
- Quy trình migration theo AGENTS.md: commit riêng, `sqlmigrate` trên SQLite + SQL Server tạm, đối chiếu phạm vi, ghi nguồn yêu cầu trong work log. Không áp migration production.
- Không thay đổi model hiện hữu; chỉ đọc.

## 6. Kiểm thử

1. Unit test:
   - Parser: ≥30 câu tiếng Việt (số hiệu, ngày tháng đủ dạng, loại văn bản, cụm ngoặc kép, fallback).
   - db_search: matching, xếp hạng, lọc quyền (user thường/HR), biên (chuỗi rỗng, dài, không dấu).
   - sharepoint_search: mock Graph (thành công, 403 fallback, timeout), không rò token vào log.
   - services: gộp nguồn, `partial=True`, rate limit, log tạo đúng.
2. Integration/API: endpoint với tài khoản QA trên DB cô lập; phân quyền URL; không làm lộ dữ liệu ngoài quyền.
3. Backend đôi: chạy module liên quan trên SQLite và SQL Server tạm; `check`, `makemigrations --check --dry-run`, `pip check`.
4. Browser UAT: `ops/run_browser_uat.py` (luồng cũ) + luồng chatbot mới bằng tài khoản QA; `ops/run_layout_alignment_audit.py` vì đổi `base.html`/CSS dùng chung; nếu động template có form/bảng/in: thêm `run_print_layout_uat.py`. Ảnh chứng, số đo, độ rộng màn ghi vào work log.

## 7. Rủi ro đã biết

- Graph `/search/query` có thể thiếu consent (403) → fallback duyệt thư mục vẫn chạy; cần IT cấp `Sites.Read.All` (hoặc tương đương) để search đầy đủ — ghi hướng dẫn trong work log.
- Quy tắc quyền chi tiết của từng phân hệ tài liệu sẽ được đọc kỹ trước khi code trích hàm lọc chung; nếu các view chưa thống nhất, dùng quy tắc chung nhất và liệt kê ngoại lệ vào spec cập nhật.
- Parser quy tắc có giới hạn so LLM — ghi log truy vấn để rà soát và mở rộng quy tắc sau.

## 8. Điều kiện nghiệm thu

- Tài khoản QA hỏi "công văn nghỉ phép tháng 9" nhận đúng kết quả trong phạm vi quyền, kèm link mở; user không quyền không thấy tài liệu ngoài phạm vi kể cả đoán URL.
- SharePoint lỗi → chatbot vẫn trả kết quả DB + cảnh báo rõ ràng.
- Test pass cả 2 backend; audit layout 0 vi phạm ngoài waiver; work log đầy đủ; commit/push `main` xong, SHA remote khớp HEAD.
- Server gửi email vẫn tắt; outbox chỉ ghi nháp Outlook như hiện tại.

## 9. Quy trình làm việc

Theo AGENTS.md: một lượt ghi duy nhất, xác minh Git đầu lượt, work log một nơi, commit riêng cho migration, không đưa `.env`/dữ liệu thật vào Git, kiểm thử browser bằng tài khoản QA trên DB/media cô lập, không mượn danh tính ngưởi dùng thật.
