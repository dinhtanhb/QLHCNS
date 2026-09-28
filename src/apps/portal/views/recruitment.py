from django.db import transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify
from apps.organization.models import Department
from apps.recruitment.models import Candidate, Interview, Offer
from apps.hrm.models import Employee
from apps.recruitment.models import RecruitmentRequest
from apps.organization.models import Position
from .common import _friendly_error, _get_employee, _role_code
from .hr import _can_manage_hr




def _can_request_recruitment(request):
    return has_permission(request.user, "request_recruitment")


def _can_approve_recruitment(request):
    return has_permission(request.user, "approve_recruitment")


@login_required
def recruitment_list(request):
    employee = _get_employee(request)
    role_code = _role_code(request)

    if request.user.is_superuser or role_code == "HR_MANAGER":
        requests_qs = RecruitmentRequest.objects.all()
    elif role_code == "DEPT_MANAGER" and employee:
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        requests_qs = RecruitmentRequest.objects.filter(department_id__in=dept_ids)
    else:
        requests_qs = RecruitmentRequest.objects.none()

    return render(request, "portal/recruitment_list.html", {
        "requests": requests_qs.select_related("department", "position").order_by("-required_date"),
        "can_request": _can_request_recruitment(request),
        "can_approve": _can_approve_recruitment(request),
    })


@login_required
def recruitment_create(request):
    if not _can_request_recruitment(request):
        messages.error(request, "Anh/chị không có quyền đề xuất tuyển dụng.")
        return redirect("portal:recruitment_list")

    employee = _get_employee(request)
    role_code = _role_code(request)
    if not request.user.is_superuser and role_code == "DEPT_MANAGER" and employee:
        departments = employee.managed_departments.all()
    else:
        from apps.organization.models import Department
        departments = Department.objects.all()

    if request.method == "POST":
        try:
            recruitment_request = RecruitmentRequest(
                request_code=request.POST.get("request_code"),
                department_id=request.POST.get("department"),
                position_id=request.POST.get("position"),
                required_quantity=request.POST.get("required_quantity") or 1,
                request_reason=request.POST.get("request_reason", ""),
                required_date=request.POST.get("required_date"),
                created_by=request.user,
            )
            recruitment_request.full_clean()
            recruitment_request.save()
            messages.success(request, "Đã gửi đề xuất tuyển dụng, chờ Nhân sự phê duyệt.")
            return redirect("portal:recruitment_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo đề xuất.")

    return render(request, "portal/recruitment_create.html", {
        "departments": departments, "positions": Position.objects.all(),
    })


@login_required
@require_POST
def recruitment_approve(request, pk):
    if not _can_approve_recruitment(request):
        messages.error(request, "Anh/chị không có quyền duyệt đề xuất tuyển dụng.")
        return redirect("portal:recruitment_list")

    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:recruitment_list")

    with transaction.atomic():
        recruitment_request = get_object_or_404(
            RecruitmentRequest.objects.select_for_update(), pk=pk, status="Pending"
        )
        recruitment_request.status = decision
        recruitment_request.modified_by = request.user
        recruitment_request.save()

    label = "Đã duyệt" if decision == "Approved" else "Đã từ chối"

    notify(
        recruitment_request.created_by.employee if hasattr(recruitment_request.created_by, "employee") else None,
        "recruitment", f"Đề xuất tuyển dụng {label.lower()}",
        f"{recruitment_request.request_code} - {recruitment_request.position} {label.lower()}.",
        link="/portal/recruitment/",
    )
    messages.success(request, f"{label} đề xuất {recruitment_request.request_code}.")
    return redirect("portal:recruitment_list")


@login_required
def hr_candidate_list(request):
    candidates = Candidate.objects.all().order_by("-created_date")
    return render(request, "portal/hr_candidate_list.html", {"candidates": candidates, "can_manage_hr": _can_manage_hr(request)})


@login_required
def hr_candidate_create(request):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền quản lý ứng viên.")
        return redirect("portal:hr_candidate_list")
    if request.method == "POST":
        try:
            candidate = Candidate(
                candidate_code=request.POST.get("candidate_code"),
                full_name=request.POST.get("full_name"),
                phone_number=request.POST.get("phone_number"),
                email=request.POST.get("email"),
                current_address=request.POST.get("current_address", ""),
                source=request.POST.get("source", ""),
                created_by=request.user,
            )
            candidate.full_clean()
            candidate.save()
            messages.success(request, "Đã thêm ứng viên.")
            return redirect("portal:hr_candidate_detail", pk=candidate.pk)
        except Exception as e:
            _friendly_error(request, e, "Không thể thêm ứng viên.")
    return render(request, "portal/hr_candidate_form.html")


@login_required
def hr_candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, "portal/hr_candidate_detail.html", {
        "candidate": candidate, "can_manage_hr": _can_manage_hr(request),
        "interviews": candidate.interviews.select_related("interviewer"),
        "offers": candidate.offers.all(),
        "interviewers": Employee.objects.filter(employment_status="Active"),
    })


@login_required
@require_POST
def hr_interview_create(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_candidate_detail", pk=pk)
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        interview = Interview.objects.create(
            candidate=candidate, interview_date=request.POST.get("interview_date"),
            interview_type=request.POST.get("interview_type"),
            interviewer_id=request.POST.get("interviewer"),
            created_by=request.user,
        )
        candidate.status = "Interviewing"
        candidate.save(update_fields=["status"])
        if interview.interviewer_id:
            notify(
                interview.interviewer, "recruitment", "Bạn được phân công phỏng vấn",
                f"Ứng viên {candidate.full_name} - lúc {interview.interview_date}.",
                link=f"/portal/hr/candidates/{candidate.pk}/", created_by=request.user,
            )
        messages.success(request, "Đã lên lịch phỏng vấn.")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")
    return redirect("portal:hr_candidate_detail", pk=pk)


@login_required
@require_POST
def hr_interview_result(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_candidate_list")
    interview = get_object_or_404(Interview, pk=pk)
    interview.result = request.POST.get("result")
    interview.comments = request.POST.get("comments", "")
    interview.modified_by = request.user
    interview.save()
    messages.success(request, "Đã cập nhật kết quả phỏng vấn.")
    return redirect("portal:hr_candidate_detail", pk=interview.candidate_id)


@login_required
@require_POST
def hr_offer_create(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_candidate_detail", pk=pk)
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        Offer.objects.create(
            candidate=candidate, offer_date=request.POST.get("offer_date"),
            expected_join_date=request.POST.get("expected_join_date"),
            salary_offer=request.POST.get("salary_offer"),
            created_by=request.user,
        )
        candidate.status = "Offered"
        candidate.save(update_fields=["status"])
        messages.success(request, "Đã tạo thư mời làm việc.")
    except Exception as e:
        _friendly_error(request, e, "Không thể tạo offer.")
    return redirect("portal:hr_candidate_detail", pk=pk)


@login_required
@require_POST
def hr_offer_update_status(request, pk):
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_candidate_list")
    offer = get_object_or_404(Offer, pk=pk)
    offer.status = request.POST.get("status")
    offer.modified_by = request.user
    offer.save()
    messages.success(request, "Đã cập nhật trạng thái Offer.")
    return redirect("portal:hr_candidate_detail", pk=offer.candidate_id)


@login_required
@require_POST
def hr_candidate_onboard(request, pk):
    """Tạo hồ sơ nhân viên từ ứng viên đã có Offer 'Đã chấp nhận' — điền sẵn thông tin."""
    if not _can_manage_hr(request):
        messages.error(request, "Anh/chị không có quyền.")
        return redirect("portal:hr_candidate_detail", pk=pk)

    candidate = get_object_or_404(Candidate, pk=pk)
    accepted_offer = candidate.offers.filter(status="Accepted").order_by("-offer_date").first()
    if not accepted_offer:
        messages.error(request, "Ứng viên chưa có Offer ở trạng thái 'Đã chấp nhận'.")
        return redirect("portal:hr_candidate_detail", pk=pk)

    candidate.status = "Hired"
    candidate.save(update_fields=["status"])

    name_parts = candidate.full_name.strip().split(" ")
    last_name = name_parts[-1] if name_parts else ""
    first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else candidate.full_name

    params = {
        "first_name": first_name, "last_name": last_name, "full_name": candidate.full_name,
        "personal_email": candidate.email, "mobile_phone": candidate.phone_number,
        "address": candidate.current_address or "", "join_date": accepted_offer.expected_join_date.isoformat(),
    }
    import urllib.parse
    query = urllib.parse.urlencode(params)
    messages.success(request, "Đã đánh dấu Trúng tuyển. Vui lòng hoàn tất hồ sơ nhân viên bên dưới.")
    return redirect(f"/portal/hr/employees/create/?{query}")
