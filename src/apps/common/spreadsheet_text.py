"""Preserve untrusted text without turning it into spreadsheet formulas.

Callers must opt in explicitly for formulas produced by the application.
Numbers/dates are assigned unchanged. CSV has no cell types, so prefix only
formula-like strings there; never coerce a numeric value into a string.
"""

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r', '\n')


def write_excel_value(cell, value, *, formula=False):
    cell.value = value
    if isinstance(value, str) and not formula:
        cell.data_type = 's'
    return cell


def csv_text(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value
