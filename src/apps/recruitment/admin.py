from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from apps.common.admin import BaseAuditAdmin
from .models import RecruitmentRequest, JobPosting, Candidate, Interview, Offer

HR_ROLES = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")


@admin.register(RecruitmentRequest)
class RecruitmentRequestAdmin(BaseAuditAdmin):
    list_display = ("request_code", "department", "position", "required_quantity", "required_date", "status")
    list_filter = ("status", "department")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER", "DIRECTOR")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(department_id__in=dept_ids)
        return qs


class JobPostingAdmin(BaseAuditAdmin):
    list_display = ("posting_title", "recruitment_request", "open_date", "close_date", "status")
    view_roles = HR_ROLES
    edit_roles = HR_ROLES


admin.site.register(JobPosting, JobPostingAdmin)


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


class OfferInline(admin.StackedInline):
    model = Offer
    extra = 0
    exclude = ("created_by", "modified_by", "deleted_by", "deleted_date", "is_deleted")


@admin.register(Candidate)
class CandidateAdmin(BaseAuditAdmin):
    list_display = ("candidate_code", "full_name", "phone_number", "email", "source", "status")
    list_filter = ("status", "source")
    search_fields = ("candidate_code", "full_name", "email")
    inlines = [InterviewInline, OfferInline]
    view_roles = HR_ROLES
    edit_roles = HR_ROLES
    actions = ["create_employee_from_candidate"]

    @admin.action(description="🎉 Tạo hồ sơ nhân viên (điền sẵn thông tin ứng viên)")
    def create_employee_from_candidate(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Chỉ chọn đúng 1 ứng viên mỗi lần để tạo hồ sơ.", level="ERROR")
            return
        candidate = queryset.first()
        accepted_offer = candidate.offers.filter(status="Accepted").order_by("-offer_date").first()
        if not accepted_offer:
            self.message_user(
                request,
                "Ứng viên này chưa có Offer ở trạng thái 'Đã chấp nhận' — cần cập nhật Offer trước khi tạo hồ sơ.",
                level="ERROR",
            )
            return

        name_parts = candidate.full_name.strip().split(" ")
        last_name = name_parts[-1] if name_parts else ""
        first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else candidate.full_name

        candidate.status = "Hired"
        candidate.save(update_fields=["status"])

        params = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": candidate.full_name,
            "personal_email": candidate.email,
            "mobile_phone": candidate.phone_number,
            "address": candidate.current_address or "",
            "join_date": accepted_offer.expected_join_date.isoformat(),
        }
        url = reverse("admin:hrm_employee_add") + "?" + "&".join(f"{k}={v}" for k, v in params.items() if v)
        return HttpResponseRedirect(url)