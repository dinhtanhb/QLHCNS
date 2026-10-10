from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="procurementitem",
            name="quantity",
            field=models.SmallIntegerField(
                "Số lượng", default=1, db_column="Quantity", validators=[MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name="procurementitem",
            name="estimated_cost",
            field=models.DecimalField(
                "Đơn giá dự kiến", max_digits=18, decimal_places=2, null=True, blank=True,
                db_column="EstimatedCost", validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddConstraint(
            model_name="procurementitem",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="procurement_item_quantity_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="procurementitem",
            constraint=models.CheckConstraint(
                condition=models.Q(estimated_cost__gte=0) | models.Q(estimated_cost__isnull=True),
                name="procurement_item_cost_nonnegative",
            ),
        ),
    ]
