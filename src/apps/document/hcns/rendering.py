import re
from datetime import date, time
from decimal import Decimal


BLANK = "……………………"
INTERVIEW_KEYS = ("expertise", "experience", "communication", "english", "interest", "other")
TEST_KEYS = ("plan_test", "budget_test")
DERIVED_COLUMNS = [
    {"key": "interview_total", "label": "Tổng điểm PV", "kind": "decimal"},
    {"key": "test_total", "label": "Tổng điểm KT", "kind": "decimal"},
    {"key": "average_interview", "label": "TB phỏng vấn", "kind": "decimal"},
    {"key": "average_test", "label": "TB bài KT", "kind": "decimal"},
    {"key": "combined", "label": "Tổng cộng", "kind": "decimal"},
]


def display(value, *, placeholder=True):
    if value is None or value == "":
        return BLANK if placeholder else ""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, (Decimal, int)):
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text.translate(str.maketrans({",": ".", ".": ","}))
    # Keep only characters permitted by XML 1.0 in both Office formats.
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", "", str(value))


def interpolate(text, values):
    return re.sub(r"\{([a-z_0-9]+)\}", lambda m: display(values.get(m[1])), text)


def complete_sum(row, keys):
    values = [row.get(key) for key in keys]
    return sum(values, Decimal(0)) if all(value is not None and value != "" for value in values) else None


def scored_rows(rows):
    result = [dict(row, interview_total=complete_sum(row, INTERVIEW_KEYS), test_total=complete_sum(row, TEST_KEYS)) for row in rows]
    groups = {}
    for row in result:
        # Blank worksheets must not collect unrelated anonymous rows together.
        if row.get("candidate_code"):
            groups.setdefault(row["candidate_code"], []).append(row)
    for group in groups.values():
        for total_key, average_key in (("interview_total", "average_interview"), ("test_total", "average_test")):
            totals = [row[total_key] for row in group]
            average = sum(totals, Decimal(0)) / len(totals) if all(value is not None for value in totals) else None
            for row in group:
                row[average_key] = average
        for row in group:
            row["combined"] = complete_sum(row, ("average_interview", "average_test"))
    return result


def document_context(spec, values, tables, source_label=""):
    if "salary_words" in values:
        from .money import amount_in_words
        values = dict(values, salary_words=amount_in_words(values.get("salary")))
    sections = []
    for item in spec["sections"]:
        if spec["group"] == "decision" and item["title"] == "Thông tin quyết định":
            continue
        section = {"title": item["title"], "paragraphs": [interpolate(p, values) for p in item["paragraphs"]], "fields": [], "table": None}
        for field in item["fields"]:
            if spec["group"] == "decision" and (item["title"] == "Thông tin quyết định" or field["key"] in ("full_name", "position", "department", "signer")):
                # Variables appear in the decision articles; do not repeat an
                # editor's metadata block in the issued-paper layout.
                continue
            raw = values.get(field["key"])
            text = interpolate(raw, values) if isinstance(raw, str) and (field["key"].startswith("article_") or field["key"] == "tor_content") else display(raw)
            if field["key"] in ("variant",):
                continue
            section["fields"].append({"label": field["label"], "value": text, "kind": field["kind"], "key": field["key"], "raw": raw})
        table_spec = item.get("table")
        if table_spec:
            columns = list(table_spec["columns"])
            rows = tables.get(table_spec["key"], [])
            if table_spec["key"] == "results":
                columns += DERIVED_COLUMNS
                order = ["candidate_code", "interviewer", "candidate", "position", "interview_date", "location",
                         *INTERVIEW_KEYS, "interview_total", "average_interview", *TEST_KEYS, "test_total",
                         "average_test", "combined", "expected_salary", "proposed_salary", "result"]
                by_key = {c["key"]: c for c in columns}
                columns = [by_key[key] for key in order]
                rows = scored_rows(rows)
            section["table"] = {"key": table_spec["key"], "title": table_spec["title"], "columns": columns,
                "rows": [[display(row.get(col["key"]), placeholder=False) for col in columns] for row in rows], "raw_rows": rows}
            if table_spec["key"] == "scores":
                total = complete_sum({str(i): row.get("score") for i, row in enumerate(rows)}, tuple(str(i) for i in range(len(rows)))) if len(rows) == 6 else None
                section["paragraphs"].append("Tổng điểm phỏng vấn: " + (display(total) + " / 100" if total is not None else "Chưa đủ điểm các tiêu chí"))
        sections.append(section)
    context = {"spec": spec, "sections": sections, "source_label": source_label,
            "header_lines": spec["header"].splitlines(), "signatures": spec["signatures"], "is_draft": True}
    from .layouts import PROFILES, decision_layout, print_layout
    context["profile"] = PROFILES[spec["slug"]]
    context["layout"] = print_layout(spec, values, sections)
    if spec["group"] == "decision" or spec["slug"] == "asset-disposal-decision":
        context["appointment"] = decision_layout(spec, values)
        if spec["slug"] == "asset-disposal-decision":
            source = next(s["table"] for s in sections if s["table"])
            from .layouts import with_column_widths
            context["appointment"]["articles"][0]["table"] = with_column_widths(dict(source,
                columns=[{"label": "STT"}] + source["columns"],
                rows=[[str(i)] + row for i, row in enumerate(source["rows"], 1)]), spec["slug"])
    return context
