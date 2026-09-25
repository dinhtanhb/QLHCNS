from django.db import migrations


def seed_project_roles(apps, schema_editor):
    Role = apps.get_model("security", "Role")
    roles = (
        ("PROJECT_MANAGER", "Quản lý dự án"),
        ("PROJECT_COORDINATOR", "Điều phối hoạt động dự án"),
        ("CBDA", "Cán bộ dự án"),
    )
    for role_code, role_name in roles:
        Role.objects.using(schema_editor.connection.alias).get_or_create(
            role_code=role_code,
            defaults={"role_name": role_name},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0001_initial"),
        ("security", "0002_user_employee_alter_user_external_object_id"),
        ("task", "0002_activity_report_fields"),
    ]

    operations = [migrations.RunPython(seed_project_roles, migrations.RunPython.noop)]
