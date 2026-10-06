"""Print layouts, independent of editor headings and source record metadata."""
import json
from pathlib import Path

from .rendering import display, interpolate


PROFILES = json.loads(Path(__file__).with_name("layout_profiles.json").read_text(encoding="utf-8"))


def date_line(values):
    day = values.get("document_date") or values.get("decision_date")
    text = f"ngày {day.day:02d} tháng {day.month:02d} năm {day.year}" if day else "ngày … tháng … năm ……"
    return display(values.get("location")) + ", " + text


def decision_layout(spec, values):
    if spec["slug"] == "appointment-decision":
        from .appointment import layout_values
        return layout_values(spec, values)
    subjects = {
        "salary-decision": "Điều chỉnh vị trí và mức lương cho {full_name}, {new_position}, Dự án {project} thuộc Trung tâm Phát triển Sức khỏe Bền vững",
        "termination-decision": "Chấm dứt hợp đồng lao động đối với {full_name}",
        "maternity-decision": "Nghỉ chế độ thai sản đối với {full_name}",
        "asset-disposal-decision": "{disposal_type} tài sản, thiết bị và công cụ dụng cụ tại văn phòng Trung tâm",
    }
    result = {"number": display(values.get("decision_no")), "date_line": date_line(values),
            "subject": interpolate(subjects[spec["slug"]], values),
            "bases": interpolate(str(values.get("bases") or ""), values).splitlines(),
            "articles": [{"number": i, "text": interpolate(values.get(f"article_{i}", ""), values)}
                         for i in range(1, 5) if f"article_{i}" in values],
            "recipients": str(values.get("recipients") or "").splitlines(),
            "signer": display(values.get("signer"))}
    if spec["slug"] == "asset-disposal-decision":
        result["articles"] = [
            {"number": 1, "text": interpolate("{disposal_type} các tài sản, thiết bị, công cụ dụng cụ theo danh mục dưới đây:", values)},
            {"number": 2, "text": "Quyết định này có hiệu lực kể từ ngày ký."},
            {"number": 3, "text": display(values.get("execution_responsibility"))},
        ]
        result["recipients"] = ["Như Điều 3;", "Lưu: VT, VP."]
    return result


def print_layout(spec, values, sections):
    """Return one ordered block stream used by HTML and Office exports."""
    blocks = []

    def paragraph(text, *, heading=False, centered=False, right=False):
        blocks.append({"text": text, "heading": heading, "centered": centered, "right": right})

    def field(key, label):
        paragraph(label + ": " + display(values.get(key)))

    def table(item, title=True):
        if title and item["title"]:
            paragraph(item["title"], heading=True)
        blocks.append({"table": with_column_widths(item, spec["slug"])})

    def asset_list():
        source = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "assets")
        return dict(source, columns=[{"label": "STT"}] + source["columns"], rows=[[str(i)] + row for i, row in enumerate(source["rows"], 1)])

    def members():
        source = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "members")
        for i, person in enumerate(source["raw_rows"], 1):
            paragraph(f"{i}. " + display(person.get("name")) + "    Chức vụ: " + display(person.get("position")) + "    " + display(person.get("role"), placeholder=False) + "    Tham gia: " + display(person.get("participation")))

    slug = spec["slug"]
    title = spec["title"].upper()
    signatures = spec["signatures"]
    signature_columns = len(signatures) or 1
    header_kind = "center"
    if slug == "employee-information":
        for key, label in [("full_name", "Họ tên"), ("nationality", "Quốc tịch"), ("date_of_birth", "Sinh ngày"),
                           ("qualification", "Trình độ"), ("phone", "Điện thoại"), ("email", "Email"),
                           ("address", "Địa chỉ thường trú / Hộ khẩu")]:
            field(key, label)
        paragraph("Số CCCD: " + display(values.get("national_id")) + "    ngày " + display(values.get("id_issue_date")) + "    cấp tại " + display(values.get("id_issue_place")))
        field("account_name", "Tên tài khoản")
        field("account_number", "Số tài khoản")
        paragraph("Tại Ngân hàng: " + display(values.get("bank")) + " – Chi nhánh: " + display(values.get("bank_branch")))
        field("tax_code", "Mã số thuế TNCN")
        field("insurance_no", "Số sổ BHXH")
    elif spec["group"] == "leave" or slug == "resignation":
        paragraph("Kính gửi: Ban giám đốc Trung tâm Phát triển Sức khỏe Bền vững.")
        for key, label in [("full_name", "Tôi tên"), ("position", "Chức danh"), ("department", "Thuộc đơn vị")]:
            field(key, label)
        if slug == "resignation":
            field("leave_date", "Nay tôi làm đơn này xin được nghỉ việc kể từ ngày")
        else:
            paragraph("Nay tôi làm đơn này xin được " + spec["title"].lower().replace("đơn xin ", "") + ".")
            paragraph("Thời gian: Từ ngày " + display(values.get("from_date")) + " đến ngày " + display(values.get("to_date")))
        field("reason", "Lý do")
        if slug == "compensatory-leave":
            field("overtime_period", "Thời gian làm việc ngoài giờ")
        if slug != "resignation":
            paragraph("Trong thời gian xin nghỉ tôi đã bàn giao công việc cho:")
            for key, label in [("recipient", "Tên cán bộ"), ("recipient_position", "Chức danh"), ("recipient_phone", "Số điện thoại")]:
                field(key, label)
        else:
            for text in sections[-1]["paragraphs"]:
                paragraph(text)
        paragraph("Kính mong Ban giám đốc xem xét và chấp thuận. Trân trọng." if slug != "resignation" else "")
        paragraph(date_line(values), right=True)
    elif slug in ("onboarding-documents", "offboarding-documents"):
        if slug == "offboarding-documents" or values.get("full_name"):
            field("full_name", "Cán bộ")
            field("position", "Chức vụ")
        original = next(s["table"] for s in sections if s["table"])
        # Tracking columns stay available in the editor; print them within the
        # source's two-column checklist so no recorded information disappears.
        rows = []
        for i, record in enumerate(original["raw_rows"], 1):
            text = display(record.get("item"))
            notes = [display(record.get(k), placeholder=False) for k in ("received", "received_date", "note") if record.get(k)]
            if notes:
                text += "\n" + "; ".join(notes)
            rows.append([str(i), text])
        table(dict(original, columns=[{"label": "STT"}, {"label": "Loại hồ sơ"}], rows=rows), False)
        signatures = []
    elif slug.startswith("tor-"):
        title = "BẢN MÔ TẢ CÔNG VIỆC"
        paragraph(spec["title"].split(" – ", 1)[-1], heading=True, centered=True)
        field("project", "Dự án")
        field("workplace", "Địa điểm làm việc")
        field("manager", "Người quản lý trực tiếp")
        for text in str(values.get("tor_content") or "").splitlines():
            if not text.strip():
                continue
            # Source TOR title and role are already presented above.
            if text.strip() in ("BẢN MÔ TẢ CÔNG VIỆC", spec["title"].split(" – ", 1)[-1]):
                continue
            paragraph(interpolate(text, values), heading=(text.strip().endswith(":") or text.strip().isupper()))
    elif slug == "candidate-interview":
        field("position", "Vị trí")
        field("project", "Dự án")
        paragraph("I. Ban tuyển dụng nhân sự VietHealth", heading=True)
        panel = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "panel")
        for i, record in enumerate(panel["raw_rows"], 1):
            paragraph(f"{i}. Họ tên: " + display(record.get("name")) + "    Vị trí: " + display(record.get("position")))
        paragraph("II. Thông tin của ứng viên", heading=True)
        paragraph("Họ và tên: " + display(values.get("full_name")) + "    Giới tính: " + display(values.get("gender")) + "    Năm sinh: " + display(values.get("birth_year")))
        field("address", "Địa chỉ")
        paragraph("Số điện thoại: " + display(values.get("phone")) + "    Email: " + display(values.get("email")))
        paragraph("III. Nội dung phỏng vấn", heading=True)
        scores = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "scores")
        for record in scores["raw_rows"]:
            paragraph(display(record.get("criterion")) + " (" + display(record.get("maximum")) + " điểm)", heading=True)
            paragraph("Điểm: " + display(record.get("score")) + "    Nhận xét: " + display(record.get("comment")))
        from .rendering import complete_sum
        total = complete_sum({str(i): record.get("score") for i, record in enumerate(scores["raw_rows"])}, tuple(str(i) for i in range(len(scores["raw_rows"]))))
        paragraph("Tổng điểm phỏng vấn: " + display(total) + " / 100")
        field("expected_salary", "Mức lương kỳ vọng")
        paragraph(date_line(values), right=True)
        field("interviewer", "Người phỏng vấn")
    elif slug == "exit-interview":
        field("full_name", "Tên cán bộ")
        field("position", "Vị trí")
        field("document_date", "Ngày phỏng vấn")
        paragraph("Bộ câu hỏi phỏng vấn thôi việc", heading=True)
        for section in sections:
            for item in section["fields"]:
                if item["key"].startswith("answer_"):
                    paragraph(item["label"], heading=True)
                    paragraph(item["value"])
        # Added interviewer's identification is retained for traceability.
        field("interviewer", "Người phỏng vấn")
        signatures = []
    elif slug == "work-handover":
        signature_columns = 2
        title = "BIÊN BẢN BÀN GIAO"
        paragraph(interpolate("Căn cứ Quyết định số: {decision_no} ngày {decision_date} của Trung tâm Phát triển Sức khỏe Bền vững về việc cho cán bộ {full_name} nghỉ việc.", values))
        paragraph("Hôm nay, " + date_line(values) + "; tại Văn phòng Trung tâm VietHealth.")
        paragraph("Chúng tôi gồm có:")
        paragraph("1. Bên bàn giao:", heading=True)
        paragraph(interpolate("{full_name}, chức vụ / vị trí công tác: {position}", values))
        paragraph("2. Bên nhận bàn giao:", heading=True)
        paragraph(interpolate("{recipient}, chức vụ / vị trí công tác: {recipient_position}", values))
        paragraph("3. Các thành phần khác tham gia bàn giao:", heading=True)
        paragraph(display(values.get("witnesses")))
        paragraph("Sau khi xem xét chúng tôi thống nhất bàn giao công việc, gồm các nội dung sau:")
        handover = next(s["table"] for s in sections if s["table"])
        for i, record in enumerate(handover["raw_rows"], 1):
            paragraph(f"{i}. " + display(record.get("work")), heading=True)
            paragraph("Hiện trạng: " + display(record.get("status")) + "; Người nhận: " + display(record.get("recipient")) + "; Thời hạn: " + display(record.get("deadline")) + "; Ghi chú: " + display(record.get("note")))
        for text in sections[-1]["paragraphs"]:
            paragraph(text)
    elif slug == "employee-evaluation":
        title = "MẪU ĐÁNH GIÁ NHÂN VIÊN"
        metadata = {"columns": [{"label": "Thông tin nhân viên"}, {"label": "Nội dung"}, {"label": "Thông tin kỳ đánh giá"}, {"label": "Nội dung"}],
                    "rows": [["Họ tên nhân viên", display(values.get("full_name")), "Thời gian đánh giá", display(values.get("evaluation_period"))],
                             ["Vị trí / nhiệm vụ", display(values.get("position")), "Phòng / Nhóm", display(values.get("department"))],
                             ["Họ tên Quản lý / Giám sát viên", display(values.get("manager")), "Vị trí công tác", display(values.get("manager_position"))]], "title": ""}
        table(metadata, False)
        paragraph("Ba (03) chủ đề / nội dung quan trọng cần thảo luận trong kỳ đánh giá", heading=True)
        paragraph(display(values.get("discussion")))
        for key, label in [("new_position", "Vị trí công việc mới"), ("goals", "Các mục tiêu phấn đấu trong công việc"), ("salary_note", "Mức lương / bậc")]:
            field(key, label)
        paragraph("Tự đánh giá về mức độ hoàn thành mục tiêu, nhiệm vụ của nhân viên", heading=True)
        paragraph("Cách đánh giá: Tần suất: 1. Không bao giờ; 2. Thỉnh thoảng; 3. Thường xuyên. Chất lượng: 1. Không tốt; 2. Bình thường; 3. Tốt.")
        source = next(s["table"] for s in sections if s["table"])
        rows = []
        category = None
        number = 0
        for record in source["raw_rows"]:
            if record.get("category") != category:
                category = record.get("category")
                rows.append(["", display(category)] + [""]*6)
            number += 1
            rows.append([str(number), display(record.get("criterion"))] + ["✓" if str(record.get(key)) == str(score) else "" for key in ("frequency", "quality") for score in (1, 2, 3)])
        table(dict(source, columns=[{"label": x} for x in ("TT", "Nội dung / Nhiệm vụ", "1", "2", "3", "1", "2", "3")], rows=rows,
                   header_groups=[{"label": "TT", "rowspan": 2}, {"label": "Nội dung / Nhiệm vụ", "rowspan": 2},
                                  {"label": "Tần suất", "colspan": 3}, {"label": "Chất lượng", "colspan": 3}],
                   subheaders=[{"label": x} for x in ("1", "2", "3", "1", "2", "3")]), False)
        for key, label in [("self_review", "Nhân viên tự nhận xét, đánh giá chung về mức độ hoàn thành công việc của kỳ đánh giá"),
                           ("manager_review", "Nhận xét, đánh giá của Quản lý / Giám sát viên"), ("strengths", "Những điểm mạnh"),
                           ("improvements", "Những điểm cần thay đổi"), ("next_goals", "Mục tiêu phấn đấu"), ("change_plan", "Kế hoạch thay đổi")]:
            paragraph(label, heading=True)
            paragraph(display(values.get(key)))
        paragraph(date_line(values), right=True)
    elif slug == "asset-disposal-proposal":
        header_kind = "right"
        committee = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "members")
        signatures = ["Phụ trách bộ phận"] + ["Thành viên"]*max(3, len(committee["raw_rows"])-1) + ["Người đề nghị"]
        signature_columns = min(5, len(signatures))
        title = "ĐỀ NGHỊ " + display(values.get("disposal_type")).upper() + " TÀI SẢN"
        paragraph(date_line(values), right=True)
        field("request_no", "Số đề nghị")
        paragraph("Kính gửi: Ban giám đốc Trung tâm Phát triển Sức khỏe Bền vững")
        paragraph("Chúng tôi gồm:")
        members()
        paragraph("Tại " + display(values.get("location")) + ", chúng tôi tiến hành kiểm tra xác định tình trạng hư hỏng tài sản, trang thiết bị văn phòng sau:")
        table(asset_list(), False)
        paragraph(display(values.get("reason")))
        paragraph("Chúng tôi thống nhất đề nghị phương án xử lý là: " + display(values.get("disposal_type")) + " các tài sản thiết bị nêu trên.")
        paragraph("Kính đề nghị Ban giám đốc Trung tâm xem xét và phê duyệt phương án xử lý tài sản, thiết bị nêu trên.")
    elif slug == "asset-destruction-minutes":
        committee = next(s["table"] for s in sections if s["table"] and s["table"]["key"] == "members")
        signatures = ["Trưởng ban"] + ["Thành viên"]*max(3, len(committee["raw_rows"])-1)
        signature_columns = 2
        title = "BIÊN BẢN " + display(values.get("disposal_type")).upper() + " TRANG THIẾT BỊ, CÔNG CỤ DỤNG CỤ"
        field("execution_date", "Ngày thực hiện")
        paragraph(interpolate("Căn cứ Quyết định số {decision_no} ngày {decision_date} về việc {disposal_type} tài sản, thiết bị và công cụ dụng cụ tại văn phòng Trung tâm;", values))
        paragraph(interpolate("Căn cứ Quyết định số {committee_decision_no} về việc thành lập Hội đồng xử lý tài sản, thiết bị và công cụ dụng cụ;", values))
        paragraph(interpolate("Hôm nay, vào hồi {start_time}, ngày {execution_date}, tại {location}, tiến hành {disposal_type} tài sản, trang thiết bị với chi tiết như sau:", values))
        paragraph("Thành phần tham gia", heading=True)
        paragraph("Chúng tôi gồm:")
        members()
        paragraph("Nội dung", heading=True)
        paragraph("Mô tả tài sản theo danh sách sau đây:")
        table(asset_list(), False)
        for key, label in [("reason", "Lý do xử lý tài sản, thiết bị, CCDC"), ("destroy_form", "Hình thức tiêu hủy"), ("handling_method", "Biện pháp xử lý sau tiêu hủy")]:
            field(key, label)
        paragraph("Thời gian kết thúc quá trình xử lý vào hồi " + display(values.get("end_time")) + " cùng ngày.")
        paragraph("Tất cả thành viên tham gia cam kết đã chứng kiến và hoàn thành quá trình xử lý tài sản, thiết bị nêu trên.")
    elif slug == "salary-scale":
        for key, label in [("minimum_salary", "Lương tối thiểu"), ("step_rate", "Bậc (step)"), ("rounding_digits", "Làm tròn đến số trước dấu phẩy")]:
            field(key, label)
        paragraph("O: Cán bộ; SO: Cán bộ cao cấp; M: Quản lý; L: Lãnh đạo. Đơn vị: VNĐ.")
        source = next(s["table"] for s in sections if s["table"])
        table(dict(source, header_groups=[{"label": "Chức vụ", "rowspan": 2}, {"label": "Cấp", "rowspan": 2}, {"label": "Bậc", "colspan": 10}], subheaders=source["columns"][2:]), False)
    elif slug == "candidate-score-summary":
        title = "BẢNG TỔNG HỢP KẾT QUẢ PHỎNG VẤN"
        paragraph(interpolate("Vị trí: {position} – Dự án: {project}", values))
        paragraph("Mẫu vị trí: " + display(values.get("variant")) + " – " + date_line(values))
        source = next(s["table"] for s in sections if s["table"])
        groups = [{"label": col["label"], "rowspan": 2} for col in source["columns"][:6]]
        groups.append({"label": "Tiêu chí và kết quả phỏng vấn", "colspan": len(source["columns"])-6})
        table(dict(source, header_groups=groups, subheaders=source["columns"][6:]), False)
    elif slug == "asset-inventory":
        title = "DANH SÁCH TRANG THIẾT BỊ VĂN PHÒNG ĐẾN NGÀY " + display(values.get("inventory_date"))
        paragraph("Trung tâm Phát triển Sức khỏe Bền vững – VietHealth", heading=True)
        paragraph(interpolate("Văn phòng: {location} – Mã đợt: {session_no}", values))
        table(asset_list(), False)
        paragraph("Thành phần tham gia", heading=True)
        members()
    elif slug == "offboarding-handover":
        for key, label in [("full_name", "Họ tên nhân viên"), ("department", "Phòng ban"), ("position", "Chức vụ"), ("join_date", "Ngày bắt đầu"), ("notice_date", "Ngày thông báo nghỉ việc"), ("leave_date", "Ngày làm việc cuối")]:
            field(key, label)
        paragraph("Các mục dưới đây cần được điền đầy đủ trước khi hoàn tất thủ tục cho nghỉ việc của Người lao động:")
        table(next(s["table"] for s in sections if s["table"]), False)
        paragraph("Tôi xin cam đoan đã hoàn trả toàn bộ tài sản của Trung tâm và không có nghĩa vụ về tài chính đối với Trung tâm sau khi nghỉ việc.")
        for key, label in [("email", "Địa chỉ email"), ("address", "Địa chỉ"), ("phone", "Điện thoại di động"), ("home_phone", "Điện thoại nhà")]:
            field(key, label)
        paragraph(date_line(values), right=True)
    else:
        for section in sections:
            if section["title"]:
                paragraph(section["title"], heading=True)
            for text in section["paragraphs"]:
                paragraph(text)
            for item in section["fields"]:
                if item["key"] in ("location", "document_date"):
                    continue
                paragraph(item["label"] + ": " + item["value"])
            if section["table"]:
                table(section["table"], section["title"] != section["table"]["title"])
        if "document_date" in values or "decision_date" in values:
            paragraph(date_line(values), right=True)
    return {"title": title, "blocks": blocks, "signatures": signatures,
            "signature_columns": signature_columns, "header_kind": header_kind}


def with_column_widths(table, slug):
    """Keep browser print columns stable instead of assigning equal widths."""
    count = len(table["columns"])
    if table.get("key") == "criteria":
        weights = [6, 52, 7, 7, 7, 7, 7, 7]
    elif count == 2:
        weights = [8, 92]
    elif slug in ("salary-scale", "candidate-score-summary", "asset-inventory"):
        weights = PROFILES[slug]["column_widths"]
    elif count == 6:
        weights = [5, 30, 8, 17, 10, 30]
    elif count == 4 and table.get("key") == "documents":
        weights = [54, 12, 14, 20]
    else:
        weights = [1]*count
    total = sum(weights)
    # CSS requires a decimal point even when Django's active locale is vi.
    return dict(table, css_widths=[f"{w*100/total:.4f}" for w in weights])
