"""Render immutable, issued payroll rows as Vietnamese PDF payslips."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_fonts():
    configured = getattr(settings, "PAYSLIP_FONT_PATH", "")
    directories = [Path(configured).parent] if configured else []
    directories.extend([
        Path(r"C:\Windows\Fonts"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/liberation2"),
    ])
    for directory in directories:
        regular = Path(configured) if configured else directory / "arial.ttf"
        if not regular.is_file() and not configured:
            regular = directory / "DejaVuSans.ttf"
        bold = regular.with_name(
            "arialbd.ttf" if regular.name.lower() == "arial.ttf" else "DejaVuSans-Bold.ttf"
        )
        if regular.is_file() and bold.is_file():
            if "IHRMS-Vietnamese" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("IHRMS-Vietnamese", str(regular)))
                pdfmetrics.registerFont(TTFont("IHRMS-Vietnamese-Bold", str(bold)))
                pdfmetrics.registerFontFamily(
                    "IHRMS-Vietnamese", normal="IHRMS-Vietnamese",
                    bold="IHRMS-Vietnamese-Bold", italic="IHRMS-Vietnamese",
                    boldItalic="IHRMS-Vietnamese-Bold",
                )
            return "IHRMS-Vietnamese", "IHRMS-Vietnamese-Bold"
    raise ImproperlyConfigured(
        "Không tìm thấy font Unicode có hỗ trợ tiếng Việt cho phiếu lương. "
        "Cấu hình PAYSLIP_FONT_PATH trỏ tới tệp TTF phù hợp."
    )


def _money(value):
    return f"{value:,.0f} đ"


def render_payslip_pdf(payslip):
    """Return the PDF bytes for a Payslip whose payroll period is locked."""
    payroll = payslip.payroll
    employee = payroll.employee
    period = payroll.payroll_period
    regular_font, bold_font = _register_fonts()
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=22 * mm, leftMargin=22 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Phiếu lương {employee.employee_code} {period.payroll_month:02d}-{period.payroll_year}",
        author="IHRMS",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PayTitle", parent=styles["Title"], fontName=bold_font,
        fontSize=18, leading=23, textColor=colors.HexColor("#123B70"),
        alignment=TA_CENTER, spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name="PayText", parent=styles["Normal"], fontName=regular_font,
        fontSize=9, leading=14,
    ))
    styles.add(ParagraphStyle(
        name="PaySection", parent=styles["Heading3"], fontName=bold_font,
        fontSize=10, leading=13, textColor=colors.HexColor("#123B70"),
        spaceBefore=3 * mm, spaceAfter=1 * mm,
    ))
    styles.add(ParagraphStyle(
        name="PayRight", parent=styles["PayText"], alignment=TA_RIGHT,
    ))
    story = [
        Paragraph("PHIẾU LƯƠNG", styles["PayTitle"]),
        Paragraph(f"Kỳ lương {period.payroll_month:02d}/{period.payroll_year}", styles["PayText"]),
        Spacer(1, 4 * mm),
        Paragraph("THÔNG TIN NHÂN VIÊN", styles["PaySection"]),
    ]
    info = [
        [Paragraph("Họ và tên", styles["PayText"]), Paragraph(escape(employee.full_name), styles["PayText"])],
        [Paragraph("Mã nhân viên", styles["PayText"]), Paragraph(escape(employee.employee_code), styles["PayText"])],
        [Paragraph("Phòng ban", styles["PayText"]), Paragraph(escape(employee.department.department_name if employee.department_id else "—"), styles["PayText"])],
        [Paragraph("Vị trí", styles["PayText"]), Paragraph(escape(employee.position.position_name if employee.position_id else "—"), styles["PayText"])],
        [Paragraph("Ngày công", styles["PayText"]), Paragraph(
            f"{payroll.actual_working_days:,.1f} / {payroll.standard_working_days:,.1f} ngày", styles["PayText"]
        )],
        [Paragraph("Ngày phát hành", styles["PayText"]), Paragraph(payslip.generated_date.strftime("%d/%m/%Y"), styles["PayText"])],
    ]
    story.append(Table(info, colWidths=[48 * mm, 112 * mm], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ])))

    if payroll.standard_working_days > 0:
        work_ratio = min(payroll.actual_working_days / payroll.standard_working_days, Decimal("1"))
    else:
        work_ratio = Decimal("1")
    paid_basic = (payroll.basic_salary * work_ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    paid_allowance = (payroll.allowance * work_ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    overtime_label = "Tiền làm thêm giờ"
    if getattr(payroll, "overtime_tax_exempt_amount", 0):
        exempt = min(payroll.overtime_tax_exempt_amount, payroll.overtime_amount)
        overtime_label += f" (trong đó miễn thuế {_money(exempt)})"
    story.extend([Spacer(1, 3 * mm), Paragraph("THU NHẬP VÀ KHẤU TRỪ", styles["PaySection"])])
    rows = [[Paragraph("Khoản mục", styles["PayText"]), Paragraph("Số tiền", styles["PayRight"])]]
    for label, amount in [
        ("Lương cơ bản theo ngày công", paid_basic),
        ("Phụ cấp theo ngày công", paid_allowance),
        (overtime_label, payroll.overtime_amount),
        ("TỔNG THU NHẬP", payroll.gross_income),
        ("Lương làm căn cứ đóng bảo hiểm", payroll.insurance_salary or payroll.basic_salary),
        ("Bảo hiểm người lao động đóng", -payroll.insurance_amount),
        ("Thuế thu nhập cá nhân", -payroll.tax_amount),
        ("Khấu trừ khác", -payroll.deduction_amount),
        ("THỰC LÃNH", payroll.net_income),
    ]:
        rows.append([Paragraph(escape(label), styles["PayText"]), Paragraph(_money(amount), styles["PayRight"])])
    table = Table(rows, colWidths=[105 * mm, 55 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F8")),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#EAF0F8")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#123B70")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), bold_font),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#C8D3E0")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    story.extend([table, Spacer(1, 9 * mm), Paragraph(
        "Phiếu lương được phát hành điện tử từ hệ thống IHRMS. Vui lòng liên hệ Phòng Nhân sự hoặc Kế toán nếu cần đối chiếu.",
        styles["PayText"],
    )])
    doc.build(story)
    return output.getvalue()
