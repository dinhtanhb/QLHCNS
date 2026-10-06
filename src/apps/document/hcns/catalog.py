"""Explicit form layouts transcribed from the supplied HCNS references.

The originals are reference material, never executable templates or public files.
Only reviewed blank labels, criteria, TOR text and the salary-scale matrix are
bundled. Exporting a draft does not create an approval or a business record.
"""
import json
from pathlib import Path
from .appointment import APPOINTMENT_ARTICLES, APPOINTMENT_BASES


REFERENCE = json.loads(Path(__file__).with_name("reference_content.json").read_text(encoding="utf-8"))
GROUPS = {
    "personnel": "Hồ sơ nhân sự và bàn giao",
    "decision": "Quyết định nhân sự",
    "leave": "Đơn nghỉ",
    "salary": "Thang bảng lương",
    "recruitment": "Tuyển dụng và mô tả công việc",
    "asset": "Kiểm kê và xử lý tài sản",
}


def field(key, label, kind="text", **options):
    return {"key": key, "label": label, "kind": kind, **options}


def section(title="", *, fields=(), paragraphs=(), table=None):
    return {"title": title, "fields": list(fields), "paragraphs": list(paragraphs), "table": table}


def table(key, title, columns, rows=(), *, fixed=False, max_rows=40):
    return {"key": key, "title": title, "columns": columns, "rows": list(rows),
            "fixed": fixed, "max_rows": len(rows) if fixed else max_rows}


NAME = field("full_name", "Họ và tên")
POSITION = field("position", "Chức vụ / vị trí")
DEPARTMENT = field("department", "Phòng / nhóm / đơn vị")
EMPLOYEE = [NAME, POSITION, DEPARTMENT]
DATE = field("document_date", "Ngày lập", "date")
LOCATION = field("location", "Địa điểm", initial="Hà Nội")
SIGNER = field("signer", "Người ký / giám đốc")
META = [LOCATION, DATE]
NATIONAL = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập – Tự do – Hạnh phúc"
ORGANIZATION = "LIÊN HIỆP CÁC HỘI KH & KT VIỆT NAM\nTRUNG TÂM PHÁT TRIỂN SỨC KHỎE BỀN VỮNG"
BASES = (
    "Căn cứ Quyết định số 1491/QĐ-LHH ngày 24/10/2008 về việc thành lập Trung tâm Phát triển Sức khỏe Bền vững;\n"
    "Căn cứ Quyết định số 1492/QĐ-LHH ngày 24/10/2008 về việc phê duyệt Điều lệ của Trung tâm Phát triển Sức khỏe Bền vững;"
)
FORMS = {}


def add(slug, title, group, source, sections, *, signatures=(), kind="docx", orientation="portrait", header="", **extra):
    FORMS[slug] = {
        "slug": slug, "title": title, "group": group, "group_label": GROUPS[group],
        "source": source, "sections": sections, "signatures": list(signatures),
        "kind": kind, "orientation": orientation, "header": header, **extra,
    }


add("employee-information", "Thông tin quản lý cán bộ", "personnel", "VH_Thong tin quan ly can bo.docx", [
    section("Thông tin cá nhân", fields=[NAME, field("nationality", "Quốc tịch"), field("date_of_birth", "Ngày sinh", "date"),
        field("qualification", "Trình độ"), field("phone", "Điện thoại"), field("email", "Email", "email"),
        field("address", "Địa chỉ thường trú / hộ khẩu", "textarea"), field("national_id", "Số CCCD"),
        field("id_issue_date", "Ngày cấp CCCD", "date"), field("id_issue_place", "Nơi cấp CCCD")]),
    section("Thông tin thanh toán và chế độ", fields=[field("account_name", "Tên tài khoản"), field("account_number", "Số tài khoản"),
        field("bank", "Ngân hàng"), field("bank_branch", "Chi nhánh"), field("tax_code", "Mã số thuế TNCN"), field("insurance_no", "Số sổ BHXH")]),
], personal=True)


def checklist(slug, title, source, labels):
    rows = [{"item": label} for label in labels]
    add(slug, title, "personnel", source, [section(fields=EMPLOYEE + META),
        section(table=table("documents", "Danh mục hồ sơ", [field("item", "Loại hồ sơ", locked=True),
            field("received", "Đã nhận", "choice", choices=[("", "Chưa xác nhận"), ("Có", "Có"), ("Không", "Không"), ("Không áp dụng", "Không áp dụng")]),
            field("received_date", "Ngày nhận", "date"), field("note", "Ghi chú")], rows, fixed=True))],
        signatures=["Nhân viên", "Nhân sự tiếp nhận"])


checklist("onboarding-documents", "Danh mục hồ sơ nhân viên mới", "VH_Danh muc ho so nhan vien.docx", REFERENCE["onboarding_documents"])
checklist("offboarding-documents", "Danh mục hồ sơ nghỉ việc", "VH_Danh muc ho so nghi viec.docx", REFERENCE["offboarding_documents"])

add("employee-evaluation", "Đánh giá nhân viên", "personnel", "VH_Mau danh gia nhan vien.docx", [
    section("Thông tin kỳ đánh giá", fields=EMPLOYEE + [field("evaluation_period", "Thời gian đánh giá"), field("manager", "Quản lý / giám sát viên"),
        field("manager_position", "Vị trí của quản lý"), field("discussion", "Ba chủ đề cần thảo luận", "textarea"), field("new_position", "Vị trí công việc mới"),
        field("goals", "Các mục tiêu phấn đấu", "textarea"), field("salary_note", "Mức lương / bậc")]),
    section("Tự đánh giá mức độ hoàn thành nhiệm vụ", paragraphs=["Tần suất: 1. Không bao giờ; 2. Thỉnh thoảng; 3. Thường xuyên.",
        "Chất lượng: 1. Không tốt; 2. Bình thường; 3. Tốt."], table=table("criteria", "Nội dung / nhiệm vụ", [
            field("category", "Nhóm", locked=True), field("criterion", "Nội dung / nhiệm vụ", locked=True),
            field("frequency", "Tần suất", "choice", choices=[("", "—"), ("1", "1"), ("2", "2"), ("3", "3")]),
            field("quality", "Chất lượng", "choice", choices=[("", "—"), ("1", "1"), ("2", "2"), ("3", "3")])], REFERENCE["evaluation_criteria"], fixed=True)),
    section("Nhận xét và kế hoạch", fields=[field("self_review", "Nhân viên tự nhận xét", "textarea"), field("manager_review", "Nhận xét của quản lý", "textarea"),
        field("strengths", "Những điểm mạnh", "textarea"), field("improvements", "Những điểm cần thay đổi", "textarea"),
        field("next_goals", "Mục tiêu giai đoạn tiếp theo", "textarea"), field("change_plan", "Kế hoạch thay đổi", "textarea")] + META),
], signatures=["Nhân viên", "Quản lý / giám sát viên"])

add("resignation", "Đơn xin nghỉ việc", "personnel", "VH_Don xin nghi viec.docx", [
    section(paragraphs=["Kính gửi: Ban giám đốc Trung tâm Phát triển Sức khỏe Bền vững."], fields=EMPLOYEE),
    section(fields=[field("leave_date", "Ngày đề nghị nghỉ việc", "date"), field("reason", "Lý do", "textarea")]),
    section(paragraphs=["Tôi sẽ hợp tác với bộ phận Văn phòng và bộ phận Tài chính Kế toán để bàn giao toàn bộ tài sản của Trung tâm, công cụ dụng cụ khác trước khi nghỉ.",
        "Tôi rất vinh dự khi được làm việc tại VietHealth. Tôi chân thành cảm ơn Quý Trung tâm, các đồng nghiệp đã giúp đỡ, hợp tác trong thời gian vừa qua.",
        "Kính mong Ban giám đốc Trung tâm xem xét và chấp thuận cho tôi được phép thôi việc. Tôi xin chân thành cảm ơn!"], fields=META),
], signatures=["Lãnh đạo Trung tâm", "Phụ trách bộ phận", "Người làm đơn"], header=NATIONAL, personal=True)

add("work-handover", "Biên bản bàn giao công việc", "personnel", "VH_BBBG cong viec.doc", [
    section(fields=[field("decision_no", "Quyết định số"), field("decision_date", "Ngày quyết định", "date")] + META),
    section("Thành phần tham gia", fields=[NAME, POSITION, field("recipient", "Bên nhận bàn giao"), field("recipient_position", "Vị trí bên nhận"), field("witnesses", "Thành viên tham gia khác", "textarea")]),
    section(table=table("handover", "Nội dung bàn giao", [field("work", "Công việc / tài liệu / tài sản"), field("status", "Hiện trạng"), field("recipient", "Người nhận"), field("deadline", "Thời hạn", "date"), field("note", "Ghi chú")], [{}])),
    section(paragraphs=["Biên bản được lập thành 03 bản: bên bàn giao, bên nhận bàn giao và Văn phòng Trung tâm mỗi bên giữ 01 bản. Các thành viên đọc, thống nhất nội dung và cùng ký tên."]),
], signatures=["Bên bàn giao", "Bên nhận bàn giao", "Quản lý dự án", "Giám đốc"], header=NATIONAL)

checklist("offboarding-handover", "Bảng kiểm bàn giao nghỉ việc", "VH_BBBG nghi viec.xls", REFERENCE["offboarding_handover"])
FORMS["offboarding-handover"]["kind"] = "xlsx"
FORMS["offboarding-handover"]["sections"].insert(1, section(fields=[field("join_date", "Ngày bắt đầu", "date"),
    field("notice_date", "Ngày thông báo nghỉ việc", "date"), field("leave_date", "Ngày làm việc cuối", "date")]))
FORMS["offboarding-handover"]["sections"].extend([
    section(paragraphs=["Tôi xin cam đoan đã hoàn trả toàn bộ tài sản của Trung tâm và không có nghĩa vụ về tài chính đối với Trung tâm sau khi nghỉ việc."]),
    section("Thông tin liên lạc sau khi nghỉ việc", fields=[field("email", "Địa chỉ email", "email"), field("address", "Địa chỉ", "textarea"), field("phone", "Điện thoại di động"), field("home_phone", "Điện thoại nhà")])])

add("exit-interview", "Phỏng vấn thôi việc", "personnel", "VH_Bo cau hoi PV nghi viec.docx", [
    section(fields=EMPLOYEE + [field("interviewer", "Người phỏng vấn")] + META),
    section("Bộ câu hỏi phỏng vấn thôi việc", fields=[field(f"answer_{i}", question, "textarea") for i, question in enumerate(REFERENCE["exit_questions"], 1)]),
], signatures=["Người phỏng vấn", "Nhân viên"])


def decision(slug, subject, source, extra_fields, articles):
    add(slug, "Quyết định " + subject, "decision", source, [
        section(fields=[field("decision_no", "Số quyết định")] + META + EMPLOYEE + [SIGNER]),
        section("Căn cứ", fields=[field("bases", "Nội dung căn cứ", "textarea", initial=BASES)],
            paragraphs=["GIÁM ĐỐC TRUNG TÂM"]),
        section("Thông tin quyết định", fields=extra_fields),
        section("QUYẾT ĐỊNH", fields=[field(f"article_{i}", f"Điều {i}", "textarea", initial=article) for i, article in enumerate(articles, 1)]),
        section("Nơi nhận", fields=[field("recipients", "Danh sách nơi nhận", "textarea", initial="Như các điều trên;\nLưu: VP, KT.")]),
    ], signatures=["GIÁM ĐỐC"], header=ORGANIZATION + "\n\n" + NATIONAL,
        note="Căn cứ được chép từ mẫu tham khảo; người ký cần kiểm tra văn bản và nội dung áp dụng trước khi ban hành.")


decision("appointment-decision", "tiếp nhận / bổ nhiệm / miễn nhiệm", "VH_QD bo nhiem, mien nhiem.doc", [
    field("decision_action", "Nội dung quyết định", "choice", choices=[("Tiếp nhận", "Tiếp nhận"), ("Bổ nhiệm", "Bổ nhiệm"), ("Tái bổ nhiệm", "Tái bổ nhiệm"), ("Miễn nhiệm", "Miễn nhiệm")]),
    field("effective_date", "Ngày hiệu lực", "date"), field("new_position", "Chức vụ mới"), field("salary", "Lương thỏa thuận", "decimal"), field("salary_words", "Lương bằng chữ")], [
    *APPOINTMENT_ARTICLES])
for appointment_section in FORMS["appointment-decision"]["sections"]:
    for appointment_field in appointment_section["fields"]:
        if appointment_field["key"] == "bases":
            appointment_field["initial"] = APPOINTMENT_BASES
        elif appointment_field["key"] == "recipients":
            appointment_field["initial"] = "- Như điều 4;\n- Lưu: VP, KT (4)."
decision("termination-decision", "chấm dứt hợp đồng lao động", "VH_QD cham dut HDLD.docx", [
    field("contract_no", "Số hợp đồng"), field("contract_date", "Ngày hợp đồng", "date"), field("date_of_birth", "Ngày sinh", "date"),
    field("project", "Dự án"), field("province", "Tỉnh / thành phố"), field("effective_date", "Ngày chấm dứt", "date"), field("reason", "Lý do", "textarea")], [
    "Chấm dứt hợp đồng lao động số {contract_no} ngày {contract_date} với ông/bà {full_name}, sinh ngày {date_of_birth}, hiện là {position} tại {department}. Lý do: {reason}. Thời điểm chấm dứt: {effective_date}.",
    "Lương và các khoản phụ cấp được chi trả đến thời điểm chấm dứt hợp đồng lao động.",
    "Ông/bà {full_name} hợp tác với Nhóm dự án, Văn phòng và Tài chính Kế toán để hoàn thiện chứng từ, thanh quyết toán và bàn giao trước khi nghỉ việc.",
    "Ban giám đốc, các bộ phận liên quan và ông/bà {full_name} có trách nhiệm thi hành quyết định này."])
decision("salary-decision", "điều chỉnh vị trí và mức lương", "VH_QD dieu chinh luong.docx", [
    field("effective_date", "Ngày hiệu lực", "date"), field("new_position", "Vị trí mới"), field("salary", "Mức lương mới", "decimal"),
    field("salary_words", "Lương bằng chữ"), field("project", "Dự án / nguồn ngân sách"), field("workplace", "Văn phòng làm việc")], [
    "Kể từ ngày {effective_date}, điều chuyển và bổ nhiệm ông/bà {full_name} giữ chức vụ {new_position}; điều chỉnh lương ở mức {salary} VNĐ/tháng (Bằng chữ: {salary_words}). Địa điểm làm việc: {workplace}.",
    "Nguồn lương lấy từ dòng ngân sách lương của {project}.",
    "Ban giám đốc, Văn phòng, Dự án, Tài chính Kế toán và ông/bà {full_name} có trách nhiệm thi hành quyết định này."])
decision("maternity-decision", "nghỉ chế độ thai sản", "VH_QD nghi thai san.docx", [
    field("from_date", "Ngày bắt đầu nghỉ", "date"), field("to_date", "Ngày kết thúc nghỉ", "date"), field("paid_until", "Chi trả lương đến ngày", "date"),
    field("last_working_date", "Ngày làm việc cuối", "date"), field("recipient", "Người nhận bàn giao")], [
    "Ông/bà {full_name}, {position}, được nghỉ chế độ thai sản từ ngày {from_date} đến ngày {to_date}.",
    "Lương và các khoản phụ cấp được Trung tâm chi trả đến ngày {paid_until}.",
    "Bàn giao các công việc đang thực hiện đến ngày làm việc cuối {last_working_date} cho {recipient}, nhân sự được phân công phụ trách trong thời gian nghỉ.",
    "Ban giám đốc, Văn phòng, Tài chính Kế toán, ông/bà {full_name} và người nhận bàn giao có trách nhiệm thi hành quyết định này."])

for slug, title, source in [
    ("annual-leave", "Đơn xin nghỉ phép", "VH_Don xin nghi phep.doc"),
    ("unpaid-leave", "Đơn xin nghỉ không lương", "VH_Don xin nghi khong luong.doc"),
    ("compensatory-leave", "Đơn xin nghỉ bù", "VH_Don xin nghi bu.doc"),
]:
    fields = [field("from_date", "Từ ngày", "date"), field("to_date", "Đến ngày", "date"), field("reason", "Lý do", "textarea")]
    if slug == "compensatory-leave":
        fields.append(field("overtime_period", "Thời gian làm việc ngoài giờ", "textarea"))
    add(slug, title, "leave", source, [
        section(paragraphs=["Kính gửi: Ban giám đốc Trung tâm Phát triển Sức khỏe Bền vững."], fields=EMPLOYEE),
        section("Nội dung đề nghị", fields=fields),
        section("Bàn giao trong thời gian nghỉ", fields=[field("recipient", "Tên cán bộ nhận bàn giao"), field("recipient_position", "Chức danh"), field("recipient_phone", "Số điện thoại")]),
        section(paragraphs=["Kính mong Ban giám đốc xem xét và chấp thuận. Trân trọng."], fields=META),
    ], signatures=["Lãnh đạo Trung tâm", "Quản lý trực tiếp", "Người làm đơn"], personal=True)

scale_cols = [field("position_code", "Chức vụ", locked=True), field("level", "Cấp", "integer", locked=True)]
scale_cols += [field(f"step_{i}", roman, "decimal") for i, roman in enumerate(["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"], 1)]
add("salary-scale", "Thang bảng lương", "salary", "BangLuong.xlsx", [
    section(fields=[field("minimum_salary", "Lương tối thiểu tham chiếu", "decimal", initial=REFERENCE["salary_scale"]["minimum"]),
        field("step_rate", "Bậc (step) tham chiếu", "decimal", initial=REFERENCE["salary_scale"]["step"]),
        field("rounding_digits", "Làm tròn đến số trước dấu phẩy", "integer", initial=REFERENCE["salary_scale"]["rounding"])]),
    section(paragraphs=["O: Cán bộ; SO: Cán bộ cao cấp; M: Quản lý; L: Lãnh đạo. Đơn vị: VNĐ."],
        table=table("scale", "Chức vụ – cấp – bậc", scale_cols, REFERENCE["salary_scale"]["rows"], fixed=True)),
], kind="xlsx", orientation="landscape", note="Mẫu gốc chứa giá trị, không có công thức. Thay tham số tham chiếu không tự tính lại ma trận hoặc cập nhật lương nhân viên; hãy sửa từng mức lương sau khi được duyệt.")

score_columns = [field("criterion", "Tiêu chí", locked=True), field("maximum", "Điểm tối đa", "integer", locked=True),
    field("score", "Điểm", "decimal"), field("comment", "Nhận xét")]
score_rows = [{"criterion": label, "maximum": maximum} for label, maximum in [
    ("Chuyên môn", 20), ("Kinh nghiệm hoạt động dự án", 20), ("Giao tiếp / phong thái", 20),
    ("Tiếng Anh", 15), ("Các quan tâm của ứng viên với công việc, tổ chức", 15), ("Khác", 10)]]
add("candidate-interview", "Phiếu chấm điểm phỏng vấn ứng viên", "recruitment", "VH_Phong van ung vien.docx", [
    section("Vị trí ứng tuyển", fields=[POSITION, field("project", "Dự án")] + META),
    section(table=table("panel", "Ban tuyển dụng", [field("name", "Họ tên"), field("position", "Vị trí")], [{}, {}, {}], max_rows=10)),
    section("Thông tin ứng viên", fields=[NAME, field("gender", "Giới tính"), field("birth_year", "Năm sinh", "integer"), field("address", "Địa chỉ", "textarea"), field("phone", "Điện thoại"), field("email", "Email", "email")]),
    section("Nội dung phỏng vấn", table=table("scores", "Điểm phỏng vấn", score_columns, score_rows, fixed=True)),
    section(fields=[field("expected_salary", "Mức lương kỳ vọng", "decimal"), field("interviewer", "Người phỏng vấn")]),
], signatures=["Người phỏng vấn"])

summary_cols = [field("candidate_code", "Mã ứng viên"), field("interviewer", "Người phỏng vấn / chấm điểm"), field("candidate", "Họ tên ứng viên"), field("position", "Vị trí ứng tuyển"),
    field("interview_date", "Ngày phỏng vấn", "date"), field("location", "Địa điểm / hình thức")]
summary_cols += [field(key, label, "decimal", maximum=maximum) for key, label, maximum in [
    ("expertise", "Chuyên môn", 20), ("experience", "Kinh nghiệm", 20), ("communication", "Giao tiếp", 20),
    ("english", "Tiếng Anh", 15), ("interest", "Quan tâm tổ chức", 15), ("other", "Khác", 10),
    ("plan_test", "Bài KT lập KH", 25), ("budget_test", "Bài KT ngân sách", 25)]]
summary_cols += [field("expected_salary", "Lương kỳ vọng", "decimal"), field("proposed_salary", "Lương đề xuất", "decimal"), field("result", "Kết quả đã xác nhận")]
add("candidate-score-summary", "Tổng hợp kết quả phỏng vấn", "recruitment", "VH_Phieu cham diem kiem tra ung vien.xlsx", [
    section(fields=[POSITION, field("project", "Dự án"), field("variant", "Mẫu vị trí", "choice", choices=[("CBDA - TN", "CBDA - TN"), ("CV PHCN", "CV PHCN")])] + META),
    section(table=table("results", "Tiêu chí và kết quả phỏng vấn", summary_cols, [{}], max_rows=30)),
], kind="xlsx", orientation="landscape", note="Mỗi người chấm một dòng. Cùng mã ứng viên: trung bình điểm phỏng vấn và trung bình điểm bài kiểm tra; tổng cộng = hai điểm trung bình. Điểm thiếu để trống; không tự quyết định đạt / không đạt.")

for slug, title, source in [
    ("tor-project-officer", "Cán bộ dự án", "TOR - CRS_CBDA.docx"),
    ("tor-provincial-coordinator", "Điều phối viên dự án tỉnh", "TOR - CRS_DPVDA tinh.docx"),
    ("tor-provincial-assistant", "Trợ lý dự án tỉnh", "TOR - CRS_TLDA tinh.docx"),
    ("tor-accountant", "Kế toán dự án", "TOR - Ke toan.docx"),
]:
    add(slug, "Bản mô tả công việc – " + title, "recruitment", source, [
        section(fields=[field("project", "Dự án"), field("workplace", "Địa điểm làm việc"), field("manager", "Người quản lý trực tiếp")]),
        section("Mô tả công việc", fields=[field("tor_content", "Nội dung TOR", "textarea", initial=REFERENCE["tor"][source], max_length=30000)]),
    ], signatures=["Người nhận nhiệm vụ", "Người phê duyệt"], public_internal=True,
        note="Nội dung mặc định lấy từ TOR bạn cung cấp. Rà lại tên dự án, địa bàn, nhà tài trợ và yêu cầu vị trí trước khi ban hành.")

ASSET_COLUMNS = [field("name", "Tên thiết bị"), field("quantity", "Số lượng", "decimal"), field("code", "Mã TB"), field("brand", "Nhãn hiệu"), field("condition", "Tình trạng / hư hỏng")]
MEMBERS = table("members", "Thành phần tham gia", [field("name", "Họ tên"), field("position", "Chức vụ"), field("role", "Vai trò"), field("participation", "Hình thức tham gia")], [{}], max_rows=15)
inventory_cols = [field("name", "Tên thiết bị"), field("code", "Mã số thiết bị"), field("type", "Loại trang thiết bị"), field("location", "Nơi sử dụng"),
    field("brand", "Nhãn hiệu"), field("serial", "Số Seri"), field("funding", "Nguồn mua sắm"), field("purchase_date", "Ngày mua / bàn giao", "date"),
    field("quantity", "Số lượng", "decimal"), field("unit", "Đơn vị tính"), field("value", "Giá trị (VNĐ)", "decimal"), field("condition", "Tình trạng"), field("note", "Ghi chú")]
add("asset-inventory", "Biên bản kiểm kê trang thiết bị", "asset", "1. BBKK TSCD - yyyy.mm.dd.xlsm", [
    section(fields=[field("session_no", "Mã đợt kiểm kê"), field("inventory_date", "Ngày kiểm kê", "date"), LOCATION]),
    section(table=MEMBERS), section(table=table("assets", "Danh sách trang thiết bị", inventory_cols, [{}], max_rows=50)),
], kind="xlsx", orientation="landscape", note="Xuất .xlsx không macro. Các sheet nhãn chỉ lấy mã và tên tài sản đang soạn; không dùng lại dữ liệu minh họa trong tệp gốc.")

add("asset-disposal-proposal", "Đề nghị thanh lý / tiêu hủy tài sản", "asset", "2. HN_De nghi TL, tieu huy TTB VP.docx", [
    section(fields=[field("request_no", "Số đề nghị"), field("disposal_type", "Hình thức xử lý", "choice", choices=[("Thanh lý", "Thanh lý"), ("Tiêu hủy", "Tiêu hủy")])] + META),
    section(paragraphs=["Kính gửi: Ban giám đốc Trung tâm Phát triển Sức khỏe Bền vững."], table=MEMBERS),
    section(table=table("assets", "Tài sản / thiết bị kiểm tra", ASSET_COLUMNS, [{}])),
    section(fields=[field("reason", "Nội dung kiểm tra / lý do đề nghị", "textarea")], paragraphs=["Kính đề nghị Ban giám đốc xem xét và phê duyệt phương án xử lý tài sản, thiết bị nêu trên."]),
], signatures=["Phụ trách bộ phận", "Thành viên", "Người đề nghị"], header=ORGANIZATION)

add("asset-disposal-decision", "Quyết định thanh lý / tiêu hủy tài sản", "asset", "3. HN_Quyet dinh thanh ly TTB VP.doc", [
    section(fields=[field("decision_no", "Số quyết định"), field("decision_date", "Ngày quyết định", "date"), LOCATION,
        field("disposal_type", "Hình thức xử lý", "choice", choices=[("Thanh lý", "Thanh lý"), ("Tiêu hủy", "Tiêu hủy")]), field("request_no", "Đề nghị số"),
        field("committee_decision_no", "Số quyết định thành lập Hội đồng"), SIGNER]),
    section("Căn cứ", fields=[field("bases", "Căn cứ và đề nghị", "textarea", initial=BASES + "\nXét đề nghị của bộ phận Hành chính văn phòng về việc xử lý tài sản.")]),
    section("Điều 1", paragraphs=["{disposal_type} các tài sản, thiết bị, công cụ dụng cụ theo danh mục dưới đây:"], table=table("assets", "Danh mục tài sản", ASSET_COLUMNS, [{}])),
    section("Điều 2", paragraphs=["Quyết định này có hiệu lực kể từ ngày ký."]),
    section("Điều 3", fields=[field("execution_responsibility", "Trách nhiệm thi hành", "textarea", initial="Hội đồng xử lý tài sản, Bộ phận Văn phòng và Tài chính Kế toán chịu trách nhiệm thi hành quyết định này.")]),
    section("Nơi nhận", paragraphs=["Như Điều 3;\nLưu: VT, VP."]),
], signatures=["GIÁM ĐỐC / NGƯỜI ĐƯỢC ỦY QUYỀN"], header=ORGANIZATION + "\n\n" + NATIONAL,
    note="Kiểm tra căn cứ và thẩm quyền ký trước khi ban hành. Bản xuất không thay thế thao tác phê duyệt đề nghị.")

add("asset-destruction-minutes", "Biên bản thanh lý / tiêu hủy tài sản", "asset", "4. Bien ban tieu huy TSCD.docx", [
    section(fields=[field("decision_no", "Số quyết định xử lý"), field("decision_date", "Ngày quyết định", "date"),
        field("committee_decision_no", "Số quyết định thành lập Hội đồng"), field("disposal_type", "Hình thức xử lý", "choice", choices=[("Thanh lý", "Thanh lý"), ("Tiêu hủy", "Tiêu hủy")]),
        LOCATION, field("execution_date", "Ngày thực hiện", "date"), field("start_time", "Giờ bắt đầu", "time"), field("end_time", "Giờ kết thúc", "time")]),
    section(table=MEMBERS), section("Nội dung", table=table("assets", "Danh mục tài sản", ASSET_COLUMNS, [{}])),
    section(fields=[field("reason", "Lý do xử lý", "textarea"), field("destroy_form", "Hình thức tiêu hủy"), field("handling_method", "Biện pháp xử lý sau tiêu hủy")],
        paragraphs=["Tất cả thành viên tham gia cam kết đã chứng kiến và hoàn thành quá trình xử lý tài sản, thiết bị nêu trên."]),
], signatures=["Trưởng ban", "Các thành viên tham gia"])


def tables_for(spec):
    return [item["table"] for item in spec["sections"] if item.get("table")]


def fields_for(spec):
    return [item for section_spec in spec["sections"] for item in section_spec["fields"]]
