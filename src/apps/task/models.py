from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from apps.common.models import BaseAuditModel
from apps.common.uploads import upload_to_activity_reports, validate_upload
from apps.m365.storage import activity_reports_storage


class Task(BaseAuditModel):
    STATUS_CHOICES = [
        ("Todo", "Chưa bắt đầu"),
        ("InProgress", "Đang thực hiện"),
        ("Done", "Hoàn thành"),
        ("Cancelled", "Đã hủy"),
    ]
    PRIORITY_CHOICES = [("Low", "Thấp"), ("Normal", "Bình thường"), ("High", "Cao"), ("Urgent", "Khẩn cấp")]

    task_code = models.CharField("Mã công việc", max_length=50, unique=True, db_column="TaskCode")
    task_name = models.CharField("Tên công việc", max_length=300, db_column="TaskName")
    description = models.TextField("Mô tả", null=True, blank=True, db_column="Description")

    assigned_by_employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Người giao việc", on_delete=models.PROTECT,
        db_column="CreatedByEmployeeID", related_name="tasks_assigned_by_me",
    )
    assigned_to_employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Người phụ trách", on_delete=models.PROTECT,
        db_column="AssignedToEmployeeID", related_name="tasks_assigned_to_me",
    )
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="tasks",
    )
    priority = models.CharField("Độ ưu tiên", max_length=20, choices=PRIORITY_CHOICES, default="Normal", db_column="Priority")
    start_date = models.DateField("Ngày bắt đầu", null=True, blank=True, db_column="StartDate")
    due_date = models.DateField("Hạn hoàn thành", null=True, blank=True, db_column="DueDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Todo", db_column="Status")
    completed_date = models.DateField(
        "Ngày hoàn thành thực tế", null=True, blank=True, db_column="CompletedDate",
    )

    # Liên kết tới apps.activity.Activity khi Task này là "công việc theo dõi
    # báo cáo" tự động sinh ra cho 1 Hoạt động dự án. Để trống với Task hành
    # chính thông thường không liên quan hoạt động dự án.
    activity = models.ForeignKey(
        "activity.Activity", verbose_name="Hoạt động dự án liên quan", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="ActivityID", related_name="tasks",
    )
    report_file = models.FileField(
        "Tệp báo cáo hoạt động", upload_to=upload_to_activity_reports,
        validators=[validate_upload], null=True, blank=True,
        storage=activity_reports_storage,
    )

    class Meta:
        db_table = "tblTask"
        verbose_name = "Công việc"
        verbose_name_plural = "Công việc"

    def __str__(self):
        return f"{self.task_code} - {self.task_name}"

    def clean(self):
        super().clean()
        # Với Task gắn 1 Hoạt động dự án: không cho đánh dấu "Hoàn thành" nếu
        # chưa có tệp báo cáo — đúng yêu cầu nghiệp vụ (kết quả Task = Hoàn
        # thành PHẢI đi kèm báo cáo đã upload).
        if self.activity_id and self.status == "Done" and not self.report_file:
            raise ValidationError({
                "report_file": "Phải tải lên tệp báo cáo hoạt động trước khi đánh dấu Hoàn thành.",
            })
        if (
            self.activity_id
            and self.status == "Done"
            and self.activity.end_date
            and timezone.localdate() < self.activity.end_date
        ):
            raise ValidationError({
                "status": "Chỉ có thể hoàn thành Task báo cáo sau khi hoạt động kết thúc.",
            })


class TaskComment(BaseAuditModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, db_column="TaskID", related_name="comments")
    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT, db_column="EmployeeID", related_name="task_comments"
    )
    comment_text = models.TextField("Nội dung", db_column="CommentText")
    comment_date = models.DateTimeField("Thời gian", auto_now_add=True, db_column="CommentDate")

    class Meta:
        db_table = "tblTaskComment"
        verbose_name = "Bình luận công việc"
        verbose_name_plural = "Bình luận công việc"
        ordering = ["comment_date"]

    def __str__(self):
        return f"{self.employee} - {self.task}"
