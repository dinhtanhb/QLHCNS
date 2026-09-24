from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payroll", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="insurancerateconfig",
            name="base_salary_reference",
            field=models.DecimalField(
                db_column="BaseSalaryReference",
                decimal_places=2,
                default=Decimal("2340000"),
                help_text="Dùng để tính trần đóng BHXH/BHYT = 20 lần mức này.",
                max_digits=18,
                verbose_name="Lương cơ sở (đ/tháng)",
            ),
        ),
        migrations.AddField(
            model_name="insurancerateconfig",
            name="regional_minimum_wage",
            field=models.DecimalField(
                db_column="RegionalMinimumWage",
                decimal_places=2,
                default=Decimal("4960000"),
                help_text="Dùng để tính trần đóng BHTN = 20 lần mức này.",
                max_digits=18,
                verbose_name="Lương tối thiểu vùng (đ/tháng)",
            ),
        ),
        migrations.AddField(
            model_name="payroll",
            name="overtime_tax_exempt_amount",
            field=models.DecimalField(
                db_column="OvertimeTaxExemptAmount",
                decimal_places=2,
                default=0,
                help_text=(
                    "Phần tiền làm thêm giờ TRẢ CAO HƠN mức lương giờ làm việc bình thường "
                    "(phần chênh lệch) được miễn thuế TNCN. Ví dụ: làm thêm ngày thường trả 150%, "
                    "thì 50% chênh lệch nhập vào đây. Để 0 nếu không có."
                ),
                max_digits=18,
                verbose_name="Tiền tăng ca được miễn thuế",
            ),
        ),
        migrations.AddField(
            model_name="payroll",
            name="insurance_salary",
            field=models.DecimalField(
                db_column="InsuranceSalary",
                decimal_places=2,
                default=0,
                help_text=(
                    "Tiền lương ghi trong hợp đồng dùng làm căn cứ đóng BHXH/BHYT/BHTN. "
                    "Để trống (0) thì hệ thống tự lấy bằng Lương cơ bản."
                ),
                max_digits=18,
                verbose_name="Lương đóng bảo hiểm",
            ),
        ),
    ]
