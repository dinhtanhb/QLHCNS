from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payroll", "0002_insurance_caps_and_tax_exempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="payroll",
            name="standard_working_days",
            field=models.DecimalField(
                db_column="StandardWorkingDays",
                decimal_places=1,
                default=0,
                help_text=(
                    "Số ngày công chuẩn (T2–T6, đã trừ ngày lễ) của cả kỳ lương — "
                    "do calculate() tự tính."
                ),
                max_digits=4,
                verbose_name="Ngày công chuẩn của kỳ",
            ),
        ),
        migrations.AddField(
            model_name="payroll",
            name="actual_working_days",
            field=models.DecimalField(
                db_column="ActualWorkingDays",
                decimal_places=1,
                default=0,
                help_text=(
                    "Ngày công chuẩn đã giới hạn theo ngày vào làm/nghỉ việc, trừ tiếp số ngày "
                    "nghỉ không lương trong tháng — do calculate() tự tính, dùng để quy đổi "
                    "Lương cơ bản/Phụ cấp theo tỷ lệ ngày công thực tế / ngày công chuẩn."
                ),
                max_digits=4,
                verbose_name="Ngày công thực tế được tính lương",
            ),
        ),
    ]