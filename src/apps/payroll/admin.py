from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import (
    EmployeeSalary, InsuranceRateConfig, PersonalIncomeTaxBracket,
    TaxDeductionConfig, EmployeeDependent, PayrollPeriod, Payroll, Payslip,
)

PAYROLL_ROLES = ("SUPER_ADMIN", "FINANCE_OFFICER")


class PayrollBaseAdmin(BaseAuditAdmin):
    view_roles = PAYROLL_ROLES
    edit_roles = PAYROLL_ROLES


admin.site.register(EmployeeSalary, PayrollBaseAdmin)
admin.site.register(InsuranceRateConfig, PayrollBaseAdmin)
admin.site.register(PersonalIncomeTaxBracket, PayrollBaseAdmin)
admin.site.register(TaxDeductionConfig, PayrollBaseAdmin)
admin.site.register(EmployeeDependent, PayrollBaseAdmin)
admin.site.register(Payslip, PayrollBaseAdmin)


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(PayrollBaseAdmin):
    """C2 (đã sửa): trước đây FINANCE_OFFICER sửa được `status` (Locked → Open),
    `start_date`/`end_date` (đổi cả thế hệ tỷ lệ thuế/BH áp dụng cho kỳ) và **xóa được**
    kỳ lương đã khóa ngay trong trang Admin — bỏ qua hoàn toàn cơ chế khóa kỳ ở portal.
    Chỉ SUPER_ADMIN mới được sửa/xóa kỳ đã Locked (coi như thao tác khẩn cấp có kiểm soát);
    FINANCE_OFFICER chỉ được sửa/xóa khi kỳ còn Open — khớp đúng nghiệp vụ "khóa 1 chiều"
    đã thiết kế ở `finance_payroll_lock`."""
    list_display = ("payroll_month", "payroll_year", "start_date", "end_date", "status")
    list_filter = ("status", "payroll_year")

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj is not None and obj.status == "Locked" and not request.user.is_superuser:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is not None and obj.status == "Locked" and not request.user.is_superuser:
            return False
        return True


@admin.register(Payroll)
class PayrollAdmin(BaseAuditAdmin):
    list_display = (
        "employee", "payroll_period", "actual_working_days", "standard_working_days",
        "gross_income", "insurance_amount", "tax_amount", "net_income",
    )
    list_filter = ("payroll_period",)
    search_fields = ("employee__full_name", "employee__employee_code")
    readonly_fields = (
        "standard_working_days", "actual_working_days",
        "gross_income", "insurance_amount", "tax_amount", "net_income",
    )
    actions = ["calculate_selected"]

    view_roles = PAYROLL_ROLES
    edit_roles = PAYROLL_ROLES

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee", "payroll_period")

    def has_change_permission(self, request, obj=None):
        """C2 (đã sửa): chặn sửa dòng lương của kỳ đã Locked qua Admin — khớp với `Payroll.clean()`
        (đã chặn ở tầng model khi `self.pk` tồn tại) nhưng ẩn hẳn nút Sửa cho rõ ràng với người dùng,
        thay vì để họ bấm Lưu rồi mới dính `ValidationError`."""
        if not super().has_change_permission(request, obj):
            return False
        if obj is not None and obj.payroll_period.status == "Locked" and not request.user.is_superuser:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """C2 (đã sửa): trước đây xóa được dòng Payroll của kỳ đã Locked (model.clean() chỉ chặn
        sửa nội dung khi có `self.pk`, không chặn delete) — nay chặn luôn ở tầng Admin."""
        if not super().has_delete_permission(request, obj):
            return False
        if obj is not None and obj.payroll_period.status == "Locked" and not request.user.is_superuser:
            return False
        return True

    @admin.action(description="🧮 Tính lương cho các dòng đã chọn")
    def calculate_selected(self, request, queryset):
        """C2 (đã sửa): action trước đây không kiểm tra `payroll_period.status`, nên tính lại được
        lương của kỳ đã khóa ngay từ danh sách Admin — bỏ qua hoàn toàn nút "Khóa kỳ lương" ở portal.
        Giờ bỏ qua (và báo rõ) các dòng thuộc kỳ Locked, chỉ tính các dòng thuộc kỳ còn Open;
        SUPER_ADMIN vẫn được phép tính lại kỳ Locked (thao tác khẩn cấp có kiểm soát)."""
        count, skipped, errors = 0, 0, []
        queryset = queryset.select_related("employee", "payroll_period")
        for payroll in queryset:
            if payroll.payroll_period.status == "Locked" and not request.user.is_superuser:
                skipped += 1
                continue
            try:
                payroll.calculate()
                payroll.modified_by = request.user
                payroll.save()
                count += 1
            except Exception as e:
                errors.append(f"{payroll}: {e}")
        if count:
            self.message_user(request, f"Đã tính lương cho {count} bảng lương.")
        if skipped:
            self.message_user(
                request, f"Đã bỏ qua {skipped} dòng thuộc kỳ lương đã KHÓA (không được tính lại).",
                level="WARNING",
            )
        for err in errors:
            self.message_user(request, err, level="ERROR")