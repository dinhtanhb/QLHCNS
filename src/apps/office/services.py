"""Atomic stock issue shared by Portal and Admin."""
from collections import defaultdict
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from apps.security.permissions import has_permission
from .models import SupplyItem, SupplyRequest, SupplyRequestItem


@transaction.atomic
def issue_supply_request(pk, *, actor, approve_first=False):
    if not actor.is_active or not has_permission(actor, "approve_office_request"):
        raise PermissionDenied
    request = SupplyRequest.objects.select_for_update().get(pk=pk)
    expected = "Pending" if approve_first else "Approved"
    if request.status != expected:
        raise ValidationError("Đề nghị không còn ở trạng thái được phép cấp phát.")
    lines = list(request.items.select_for_update().order_by("pk"))
    if not lines:
        raise ValidationError("Đề nghị chưa có vật tư.")
    totals = defaultdict(int)
    for line in lines:
        if line.quantity_requested <= 0 or not 0 <= line.quantity_issued <= line.quantity_requested:
            raise ValidationError("Số lượng đề nghị/đã cấp không hợp lệ.")
        totals[line.item_id] += line.quantity_requested - line.quantity_issued
    items = {item.pk: item for item in SupplyItem.objects.select_for_update().filter(pk__in=totals).order_by("pk")}
    for item_id, quantity in totals.items():
        item = items.get(item_id)
        if item is None:
            raise ValidationError("Vật tư đã xóa hoặc không tồn tại.")
        if item.quantity_in_stock < quantity:
            raise ValidationError(f"Không đủ tồn kho cho {item.item_name} (còn {item.quantity_in_stock}, cần {quantity}).")
    for item_id, quantity in totals.items():
        item = items[item_id]
        item.quantity_in_stock -= quantity
        item.modified_by = actor
        item.save(update_fields=["quantity_in_stock", "modified_by", "modified_date"])
    for line in lines:
        line.quantity_issued = line.quantity_requested
        line.modified_by = actor
        line.save(update_fields=["quantity_issued", "modified_by", "modified_date"])
    request.status = "Issued"
    request.modified_by = actor
    request.save(update_fields=["status", "modified_by", "modified_date"])
    return request
