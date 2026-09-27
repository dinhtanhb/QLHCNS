"""Các hàm dùng chung cho chấm công, ngày công chuẩn và nghỉ bù.

Quy ước của công ty (dự án cộng đồng):
- Ngày công chuẩn là Thứ 2 đến Thứ 6, trừ các ngày lễ đã khai báo.
- Làm việc vào Thứ 7, Chủ nhật hoặc ngày lễ KHÔNG tính là ngày công chuẩn,
  mà được quy đổi thành ngày nghỉ bù.
"""
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from .models import Holiday, MonthlyAttendanceSummary, TimesheetEntry, WorkingCalendar


def get_hours_per_day(year=None):
    """Số giờ làm việc chuẩn của một ngày, lấy theo lịch làm việc của năm."""
    calendar = None
    if year:
        calendar = WorkingCalendar.objects.filter(calendar_year=year).first()
    if calendar is None:
        calendar = WorkingCalendar.objects.filter(is_default=True).first()
    if calendar and calendar.working_hours_per_day:
        return calendar.working_hours_per_day
    return Decimal("8")


def holiday_dates(from_date, to_date):
    """Tập hợp các ngày lễ đang áp dụng nằm trong khoảng ngày."""
    return set(
        Holiday.objects.filter(
            is_active=True, holiday_date__gte=from_date, holiday_date__lte=to_date
        ).values_list("holiday_date", flat=True)
    )


def standard_working_days(from_date, to_date):
    """Số ngày công chuẩn trong khoảng: chỉ đếm Thứ 2–Thứ 6 và bỏ qua ngày lễ."""
    if not from_date or not to_date or to_date < from_date:
        return Decimal("0")
    holidays = holiday_dates(from_date, to_date)
    count = 0
    day = from_date
    while day <= to_date:
        if day.weekday() < 5 and day not in holidays:
            count += 1
        day += timedelta(days=1)
    return Decimal(count)


def compensatory_days_earned(employee, year):
    """Số ngày nghỉ bù kiếm được trong năm.

    Căn cứ là bảng chấm công dự án: giờ khai vào Thứ 7, Chủ nhật hoặc ngày lễ
    được quy đổi thành ngày nghỉ bù (tối đa 1 ngày bù cho mỗi ngày làm),
    rồi làm tròn xuống theo mức nửa ngày.
    """
    if not employee:
        return Decimal("0")

    holidays = set(
        Holiday.objects.filter(is_active=True, holiday_date__year=year).values_list("holiday_date", flat=True)
    )
    hours_per_day = get_hours_per_day(year) or Decimal("8")

    approved_months = MonthlyAttendanceSummary.objects.filter(
        employee=employee,
        year=year,
        status=MonthlyAttendanceSummary.STATUS_APPROVED,
    ).values_list("month", flat=True)
    hours_by_day = {}
    entries = TimesheetEntry.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month__in=approved_months,
    ).values_list("work_date", "hours")
    for work_date, hours in entries:
        if work_date.weekday() >= 5 or work_date in holidays:
            hours_by_day[work_date] = hours_by_day.get(work_date, Decimal("0")) + (hours or Decimal("0"))

    total = Decimal("0")
    for day_hours in hours_by_day.values():
        day_value = day_hours / hours_per_day
        total += min(day_value, Decimal("1"))

    return (total * 2).quantize(Decimal("1"), rounding=ROUND_DOWN) / Decimal("2")
