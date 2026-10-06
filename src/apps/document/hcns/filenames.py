from apps.common.export_names import export_name


PREFIXES = {
    "employee-information": "HS_ThongTinNhanVien",
    "onboarding-documents": "DS_HoSoNhanVienMoi",
    "offboarding-documents": "DS_HoSoNghiViec",
    "employee-evaluation": "Phieu_DanhGiaNhanVien",
    "resignation": "Don_NghiViec",
    "work-handover": "BB_BanGiaoCongViec",
    "exit-interview": "Phieu_PhongVanThoiViec",
    "offboarding-handover": "BK_BanGiaoNghiViec",
    "appointment-decision": "QD_TiepNhan",
    "termination-decision": "QD_ChamDutHopDong",
    "salary-decision": "QD_NangLuong",
    "maternity-decision": "QD_ThaiSan",
    "annual-leave": "Don_NghiPhep",
    "unpaid-leave": "Don_NghiKhongLuong",
    "compensatory-leave": "Don_NghiBu",
    "salary-scale": "Bang_ThangLuong",
    "candidate-interview": "Phieu_PhongVanUngVien",
    "candidate-score-summary": "Bang_TongHopDiemTuyenDung",
    "tor-project-officer": "TOR_CanBoDuAn",
    "tor-accountant": "TOR_KeToan",
    "tor-provincial-assistant": "TOR_TroLyTinh",
    "tor-provincial-coordinator": "TOR_DieuPhoiTinh",
    "asset-inventory": "BB_KiemKeTaiSan",
    "asset-disposal-proposal": "DN_ThanhLyTaiSan",
    "asset-disposal-decision": "QD_ThanhLyTaiSan",
    "asset-destruction-minutes": "BB_ThanhLyTaiSan",
}


def draft_name(context, identity="", values=None):
    spec = context["spec"]
    slug = spec["slug"]
    if values is None:
        values = {f["key"]: f["raw"] for section in context["sections"] for f in section["fields"]}
    prefix = PREFIXES[slug]
    date_key = {"asset-inventory": "inventory_date", "asset-disposal-decision": "decision_date",
                "asset-destruction-minutes": "execution_date"}.get(slug, "document_date")
    subject = identity or "ChuaChonNV"
    if slug == "appointment-decision":
        prefix = {"Tiếp nhận": "QD_TiepNhan", "Bổ nhiệm": "QD_BoNhiem", "Tái bổ nhiệm": "QD_TaiBoNhiem",
                  "Miễn nhiệm": "QD_MienNhiem"}.get(values.get("decision_action"), prefix)
    if spec["group"] == "asset":
        subject = values.get("session_no") or values.get("request_no") or values.get("decision_no") or "ChuaCoMa"
        if values.get("disposal_type") == "Tiêu hủy":
            prefix = prefix.replace("ThanhLy", "TieuHuy")
    elif slug == "candidate-score-summary":
        records = next(s["table"]["raw_rows"] for s in context["sections"] if s["table"] and s["table"]["key"] == "results")
        codes = {r.get("candidate_code") for r in records if r.get("candidate_code")}
        subject = next(iter(codes)) if len(codes) == 1 else "TongHop" if codes else "ChuaChonUV"
    elif slug == "candidate-interview":
        subject = identity or "ChuaChonUV"
    elif slug.startswith("tor-") or slug == "salary-scale":
        subject = "ToanTrungTam"
    return export_name(prefix, subject, values.get(date_key), missing_date="ChuaKy" if prefix.startswith("QD_") else "ChuaCoNgay")
