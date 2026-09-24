"""Tạo sẵn loại nghỉ "Nghỉ bù" (mã CO) nếu chưa có."""
from django.db import migrations


def create_compensatory_leave_type(apps, schema_editor):
    LeaveType = apps.get_model("leave", "LeaveType")
    LeaveType.objects.get_or_create(
        leave_type_code="CO",
        defaults={"leave_type_name": "Nghỉ bù", "is_paid": True},
    )


def remove_compensatory_leave_type(apps, schema_editor):
    LeaveType = apps.get_model("leave", "LeaveType")
    LeaveRequest = apps.get_model("leave", "LeaveRequest")
    leave_type = LeaveType.objects.filter(leave_type_code="CO").first()
    if leave_type and not LeaveRequest.objects.filter(leave_type=leave_type).exists():
        leave_type.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0003_leavebalance_leavebalance_ux_leavebalance_emp_year"),
    ]

    operations = [
        migrations.RunPython(create_compensatory_leave_type, remove_compensatory_leave_type),
    ]
