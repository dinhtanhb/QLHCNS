from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.security.permissions import has_permission
from .models import AssetDisposalItem, AssetDisposalRequest, AssetDisposalRequestMember


@transaction.atomic
def update_disposal_request(pk, action, data, user, *, eligible_signers):
    """Lock the approved contents and persist each documented disposal step."""
    permission = "approve_asset_disposal" if action == "approve" else "manage_asset"
    if not has_permission(user, permission):
        raise PermissionDenied("Anh/chị không có quyền thực hiện thao tác này.")
    request = AssetDisposalRequest.objects.select_for_update().get(pk=pk)
    if action in ("add_member", "add_item", "approve") and request.status != "Pending":
        raise ValidationError("Đề nghị đã được xử lý; không thể thay đổi nội dung hoặc duyệt lại.")
    if action == "add_member":
        member = AssetDisposalRequestMember(
            request=request, employee_id=data.get("employee"), participation=data.get("participation", "Direct"),
            role=data.get("role", "Member"), created_by=user,
        )
        member.full_clean()
        member.save()
        return request, "Đã thêm thành viên."
    if action == "add_item":
        item = AssetDisposalItem(
            request=request, asset_id=data.get("asset"), damage_description=data.get("damage_description"), created_by=user,
        )
        item.full_clean()
        if item.asset.status == "Disposed" or request.items.filter(asset_id=item.asset_id).exists():
            raise ValidationError("Tài sản đã thanh lý hoặc đã có trong đề nghị.")
        item.save()
        return request, "Đã thêm tài sản vào đề nghị thanh lý."
    if action == "approve":
        request.status = "Approved"
        message = "Đã duyệt đề nghị thanh lý."
    elif action == "issue_decision":
        if request.status != "Approved" or request.decision_no:
            raise ValidationError("Chỉ ban hành quyết định một lần cho đề nghị đã duyệt.")
        if not request.items.exists() or request.items.filter(minutes__isnull=True).exists():
            raise ValidationError("Cần lập đủ biên bản tài sản trước khi ban hành quyết định.")
        if not data.get("decision_no", "").strip() or not data.get("decision_date"):
            raise ValidationError("Nhập số và ngày quyết định.")
        signer = eligible_signers.filter(pk=data.get("decided_by") or None).first()
        if signer is None:
            raise ValidationError("Chọn người ký quyết định trong danh sách có thẩm quyền.")
        request.decision_no = data["decision_no"].strip()
        request.decision_date = data["decision_date"]
        request.committee_decision_no = data.get("committee_decision_no", "").strip()
        request.decided_by = signer
        message = "Đã ban hành quyết định thanh lý."
    elif action == "record_execution":
        if request.status != "Approved" or not request.decision_no:
            raise ValidationError("Cần ban hành quyết định trước khi ghi nhận thực hiện.")
        started = parse_datetime(data.get("execution_datetime", ""))
        if started is None:
            raise ValidationError("Nhập thời điểm thực hiện hợp lệ.")
        request.execution_datetime = timezone.make_aware(started) if timezone.is_naive(started) else started
        request.execution_end_time = data.get("execution_end_time") or None
        request.disposal_reason = data.get("disposal_reason") or request.disposal_reason
        request.destroy_form = data.get("destroy_form", "")
        request.handling_method = data.get("handling_method", "")
        request.status = "Completed"
        message = "Đã ghi nhận thực hiện thanh lý."
    else:
        raise ValidationError("Thao tác thanh lý không hợp lệ.")
    request.modified_by = user
    request.full_clean()
    request.save()
    return request, message
