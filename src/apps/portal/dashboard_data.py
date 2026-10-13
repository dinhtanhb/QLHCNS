"""Phase-one read-only homepage data. Gates precede queries; no monetary DTOs."""
from datetime import timedelta
from decimal import Decimal
import logging
import math

from django.db import DatabaseError
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from apps.contract.models import Contract
from apps.hrm.models import Employee
from apps.organization.models import Department
from apps.planning.models import HeadcountPlan, with_headcounts
from apps.security.data_access import managed_departments_for
from apps.security.permissions import get_role_code, has_permission
from apps.portal.selectors import approvable_leave_requests
from apps.common.number_format import vi_number

logger = logging.getLogger(__name__)
LIVE_PARENT = Q(department__is_deleted=False) | Q(department__isnull=True)
LIVE_CONTRACT_PARENT = (
    Q(employee__is_deleted=False) &
    (Q(employee__department__is_deleted=False) | Q(employee__department__isnull=True)) &
    Q(contract_type__is_deleted=False)
)


def metric(key, label, value, scope, note, period="Hiện tại"):
    return dict(key=key, label=label, value=value, unit="người", state="ready" if value else "empty",
                scope_label=scope, period_label=period, source_label="Employee",
                formula_label=note, note=note, numerator=None, denominator=None, href=None)


def _read_block(builder):
    try:
        return builder()
    except DatabaseError as exc:
        logger.warning("Dashboard block unavailable: %s", type(exc).__name__)
        return {"state": "error", "rows": [], "message": "Không tải được dữ liệu"}


def capacity_rows(departments, plans):
    """Pure mapping, also supports detecting duplicate legacy plan rows."""
    by_department = {}
    for plan in plans:
        by_department.setdefault(plan.department_id, []).append(plan)
    scale = max([1] + [d["actual"] for d in departments] +
                [max(0, p.planned_headcount) for p in plans if p.planned_headcount is not None])
    rows = []
    partial = False
    for department in departments:
        matches = by_department.get(department["id"], [])
        invalid = len(matches) > 1 or bool(matches and (matches[0].planned_headcount is None or matches[0].planned_headcount < 0))
        partial |= invalid
        planned = matches[0].planned_headcount if len(matches) == 1 and not invalid else None
        actual = matches[0].actual_headcount if len(matches) == 1 and not invalid else department["actual"]
        rows.append(dict(department, actual=actual, planned=planned,
            actual_width=actual * 100 // scale, planned_width=(planned or 0) * 100 // scale,
            ratio=Decimal(actual) * 100 / Decimal(planned) if planned else None,
            ratio_display=(Decimal(actual) * 100 / Decimal(planned)).quantize(Decimal("0.1")) if planned else None,
            note="Dữ liệu chưa đầy đủ" if invalid else "Chưa nhập kế hoạch" if planned is None else "Kế hoạch 0; không tính tỷ lệ" if planned == 0 else "",
            gap=planned - actual if planned is not None else None))
    return {"rows": rows, "state": "partial" if partial else "ready" if plans else "unconfigured"}


def _headcount(today):
    # All live departments, including those with no employees or no plan.
    departments = list(Department.objects.annotate(actual=Count("employees", filter=Q(
        employees__is_deleted=False, employees__employment_status="Active"))).values(
            "id", "department_name", "actual").order_by("department_name", "pk"))
    unassigned = Employee.objects.filter(department__isnull=True, employment_status="Active").count()
    if unassigned:
        departments.append({"id": None, "department_name": "Chưa xác định", "actual": unassigned})
    plans = list(with_headcounts(HeadcountPlan.objects.filter(year=today.year, department__is_deleted=False)))
    return capacity_rows(departments, plans)


def _contracts(today):
    qs = Contract.objects.filter(LIVE_CONTRACT_PARENT, status="Active", start_date__lte=today)
    upcoming = Q(end_date__gte=today, end_date__lte=today + timedelta(days=60))
    overdue = Q(end_date__lt=today)
    effective = Q(end_date__isnull=True) | Q(end_date__gte=today)
    groups = list(qs.values("contract_type_id", "contract_type__contract_type_name").annotate(
        total=Count("pk", filter=effective), upcoming=Count("pk", filter=upcoming),
        overdue=Count("pk", filter=overdue)).order_by("contract_type__contract_type_name", "contract_type_id"))
    types = [g for g in groups if g["total"]]
    total = sum(g["total"] for g in types)
    offset = Decimal(0)
    for i, group in enumerate(types):
        share = Decimal(group["total"]) * 100 / Decimal(total)
        angle = math.radians(float(offset + share / 2) * 3.6 - 90)
        group.update(label_x=f"{50 + 36 * math.cos(angle):.3f}", label_y=f"{50 + 36 * math.sin(angle):.3f}", index=i + 1, share=share, share_display=share.quantize(Decimal("0.1")), dash=f"{share:.6f} {100-share:.6f}", offset=f"{-offset:.6f}",
                     variant=("series", "series-soft", "series-strong")[i % 3])
        offset += share
    fields = ("pk", "contract_no", "end_date", "contract_type__contract_type_name", "employee__full_name", "employee__employee_code")
    def rows(condition):
        result = list(qs.filter(condition).order_by("end_date", "pk").values(*fields)[:5])
        for row in result:
            days = (row["end_date"] - today).days
            row.update(days=days, badge="overdue" if days < 0 else "today" if days == 0 else "urgent" if days <= 7 else "soon" if days <= 30 else "later")
        return result
    return dict(state="ready" if total or groups else "empty", types=types, total=total,
                upcoming_count=sum(g["upcoming"] for g in groups), overdue_count=sum(g["overdue"] for g in groups),
                upcoming_rows=rows(upcoming), overdue_rows=rows(overdue), href=None)


def _queue(user):
    qs = approvable_leave_requests(user)
    live = Q(employee__is_deleted=False, leave_type__is_deleted=False) & (
        Q(employee__department__is_deleted=False) | Q(employee__department__isnull=True))
    totals = qs.aggregate(total=Count("pk"), live=Count("pk", filter=live))
    # Do not change approval behavior to repair deleted-parent records silently.
    # With such records, withhold the new queue rather than link a different count.
    if totals["total"] != totals["live"]:
        return {"state": "partial", "rows": [], "message": "Dữ liệu chưa đầy đủ; phạm vi đơn nghỉ cần được rà soát tại trang nghiệp vụ."}
    return {"state": "ready" if totals["total"] else "empty", "rows": [dict(
        label="Đơn nghỉ đang chờ trong phạm vi duyệt", value=totals["total"],
        href=reverse("portal:leave_approval_list"), note="Theo danh sách Pending; không phải số đơn có thể tự duyệt.") ]}


def dashboard_snapshot(user, employee=None):
    today = timezone.localdate()
    result = dict(generated_at=timezone.now(), operational_date=today, plan_year=today.year,
                  metrics=[], sections={}, scope_label="Cá nhân")
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return result
    can_status = has_permission(user, "view_all_employees")
    dept_scope = not can_status and get_role_code(user) == "DEPT_MANAGER" and employee and not employee.is_deleted
    if can_status or dept_scope:
        qs = Employee.objects.filter(LIVE_PARENT)
        scope = "Toàn Trung tâm" if can_status else "Phòng ban đang quản lý"
        result["scope_label"] = scope
        if dept_scope:
            qs = qs.filter(department__in=managed_departments_for(user))
        def status_block():
            counts = {s.lower(): Count("pk", filter=Q(employment_status=s), distinct=True) for s in ("Active", "Probation", "OnLeave")}
            if has_permission(user, "view_reports"):
                counts["approved"] = Count("pk", distinct=True, filter=Q(
                    leave_requests__is_deleted=False, leave_requests__leave_type__is_deleted=False,
                    leave_requests__status="Approved", leave_requests__from_date__lte=today, leave_requests__to_date__gte=today))
            return dict(state="ready", counts=qs.aggregate(**counts))
        status = _read_block(status_block)
        result["sections"]["status"] = status
        c = status.get("counts")
        if c is not None:
            result["metrics"] = [metric("managed", "Nhân sự đang quản lý", c["active"] + c["probation"] + c["onleave"], scope,
                f'Active {vi_number(c["active"])} · Thử việc {vi_number(c["probation"])} · Nghỉ dài hạn {vi_number(c["onleave"])}; không gồm Resigned.'),
                metric("active", "Đang làm việc (Active)", c["active"], scope, "Trạng thái Active; không phải có mặt hôm nay.")]
            if "approved" in c:
                m = metric("approved", "Nghỉ được duyệt trong ngày", c["approved"], scope,
                           "Theo khoảng ngày đơn nghỉ, không phải số người vắng.", today.strftime("%d/%m/%Y"))
                m["source_label"] = "LeaveRequest Approved"; result["metrics"].append(m)
            result["metrics"].append(metric("probation", "Thử việc", c["probation"], scope, "Trạng thái Probation hiện tại."))
    if has_permission(user, "view_reports"):
        result["sections"]["headcount"] = _read_block(lambda: _headcount(today))
    if has_permission(user, "manage_hr"):
        result["sections"]["contracts"] = _read_block(lambda: _contracts(today))
    if has_permission(user, "approve_leave") and (
        has_permission(user, "approve_leave_all_departments") or
        (employee is not None and not employee.is_deleted)
    ):
        result["sections"]["queue"] = _read_block(lambda: _queue(user))
    return result
