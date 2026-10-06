"""Reference choices and the source-specific appointment decision layout."""
from .choices import configure_choices, clean_choices
from .money import amount_in_words

APPOINTMENT_BASES = (
    "Căn cứ Quyết định số 1491/QĐ-LHH ngày 24/10/2008 của Liên hiệp các Hội Khoa học và Kỹ thuật Việt Nam về việc thành lập Trung tâm Phát triển Sức khỏe Bền vững thuộc Liên hiệp các Hội Khoa học và Kỹ thuật Việt Nam;\n"
    "Căn cứ Quyết định số 1492/QĐ-LHH ngày 24/10/2008 của Liên hiệp các Hội Khoa học và Kỹ thuật Việt Nam về việc phê duyệt bản Điều lệ của Trung tâm Phát triển Sức khỏe Bền vững;\n"
    "Xét nhu cầu công việc của tổ chức và trình độ, khả năng và tư cách đạo đức của cán bộ;"
)
APPOINTMENT_ARTICLES = (
    "Tiếp nhận ông/bà {full_name} là nhân sự thuộc Bộ phận {department} kể từ ngày {effective_date}.",
    "Ông/bà {full_name} sẽ thực hiện các chức năng, nhiệm vụ theo Bản mô tả công việc của {new_position} thuộc Trung tâm Phát triển Sức khỏe Bền vững theo đúng Quy chế Hoạt động và Quy chế Tài chính đã được Hội đồng Trung tâm phê duyệt; đồng thời tuân thủ quy định của các nhà tài trợ và quy định hiện hành của Pháp luật.",
    "Lương thoả thuận hàng tháng đối với ông/bà {full_name} được quy định ở mức: {salary} đồng (Bằng chữ: {salary_words}).",
    "Ban Giám đốc, Bộ phận Văn phòng, Bộ phận Tài chính - Kế toán của Trung tâm Phát triển Sức khỏe Bền vững và ông/bà {full_name} có trách nhiệm thi hành quyết định này./.",
)


def layout_values(spec, values):
    from .rendering import display, interpolate
    action = values.get("decision_action") or "Tiếp nhận"
    role = values.get("new_position") or values.get("position")
    values = dict(values, new_position=role, salary_words=amount_in_words(values.get("salary")))
    subject = "Tiếp nhận nhân sự thuộc Bộ phận " + display(values.get("department")) if action == "Tiếp nhận" else action + " chức vụ " + display(role)
    day = values.get("document_date")
    date_line = f"ngày {day.day:02d} tháng {day.month:02d} năm {day.year}" if day else "ngày … tháng … năm ……"
    articles = []
    for index in range(1, 5):
        text = values.get(f"article_{index}", "")
        if index == 1 and text == APPOINTMENT_ARTICLES[0] and action != "Tiếp nhận":
            text = "{decision_action} ông/bà {full_name}, nhân sự thuộc Bộ phận {department}, " + ("thôi giữ chức vụ" if action == "Miễn nhiệm" else "giữ chức vụ") + " {new_position} kể từ ngày {effective_date}."
        articles.append({"number": index, "text": interpolate(text, values)})
    return {"number": display(values.get("decision_no")), "date_line": display(values.get("location")) + ", " + date_line,
            "subject": subject, "bases": str(values.get("bases") or "").splitlines(), "articles": articles,
            "recipients": str(values.get("recipients") or "").splitlines(), "signer": display(values.get("signer"))}
