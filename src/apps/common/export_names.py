"""Deterministic, Windows-safe names for generated downloads."""
import re
import unicodedata


def token(value, fallback="ChuaCoMa"):
    value = str(value or "").replace("Đ", "D").replace("đ", "d")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-_")[:60].rstrip("-_")
    return value or fallback


def export_name(kind, subject, date_value, extension=None, *, missing_date="ChuaCoNgay"):
    date_part = date_value.strftime("%Y%m%d") if date_value else missing_date
    stem = "_".join((token(kind), token(subject), token(date_part)))
    return stem + "." + token(extension) if extension else stem
