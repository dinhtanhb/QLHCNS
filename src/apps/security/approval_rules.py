"""Owner-approved maker/checker rule for office and procurement, not leave."""
from django.core.exceptions import ValidationError


def request_made_by(obj, user):
    employee_id = getattr(user, 'employee_id', None)
    owner_id = getattr(obj, 'requested_by_id', getattr(obj, 'employee_id', None))
    return bool(obj.created_by_id == user.pk or (employee_id and owner_id == employee_id))


def require_independent_approver(obj, user):
    if request_made_by(obj, user):
        raise ValidationError('Không được tự duyệt hoặc từ chối đề nghị của chính mình. Vui lòng chuyển người duyệt khác cùng quyền.')


class IndependentApprovalAdminMixin:
    def save_model(self, request, obj, form, change):
        previous = type(obj).objects.filter(pk=obj.pk).first() if change else None
        if not change:
            # BaseAuditAdmin assigns the creator later; account for it before checking.
            obj.created_by = request.user
        if obj.status in ('Approved', 'Rejected') and (previous is None or previous.status != obj.status):
            require_independent_approver(obj, request.user)
            if previous is not None:
                # Changing the owner in the same POST cannot bypass maker/checker.
                require_independent_approver(previous, request.user)
        return super().save_model(request, obj, form, change)
