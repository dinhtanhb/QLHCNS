from django.core.management.base import BaseCommand
from apps.organization.models import Organization, Department, Position, JobTitle


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu Tổ chức/Phòng ban/Vị trí để test nhanh"

    from apps.security.models import Role
    roles = [
        ("SUPER_ADMIN", "Quản trị viên hệ thống"),
        ("SYS_ADMIN", "Quản trị viên kỹ thuật"),
        ("HR_MANAGER", "Trưởng phòng Nhân sự"),
        ("HR_OFFICER", "Chuyên viên Nhân sự"),
        ("FINANCE_OFFICER", "Kế toán"),
        ("DEPT_MANAGER", "Trưởng phòng ban"),
        ("EMPLOYEE", "Nhân viên"),
        ("DIRECTOR", "Ban Giám đốc"),
    ]
    for code, name in roles:
        Role.objects.get_or_create(role_code=code, defaults={"role_name": name})

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            organization_code="HQ", defaults={"organization_name": "Trung tâm demo"}
        )
        for code, name in [("NV", "Nhân viên"), ("TP", "Trưởng phòng"), ("GD", "Giám đốc")]:
            Position.objects.get_or_create(position_code=code, defaults={"position_name": name})
        for code, name in [("HCNS", "Hành chính Nhân sự"), ("KT", "Kế toán"), ("IT", "Công nghệ thông tin")]:
            Department.objects.get_or_create(
                department_code=code, defaults={"department_name": name, "organization": org}
            )
        for code, name in [("CV", "Chuyên viên"), ("QL", "Quản lý")]:
            JobTitle.objects.get_or_create(job_title_code=code, defaults={"job_title_name": name})

        from apps.contract.models import ContractType
        for code, name in [
            ("THUVIEC", "Hợp đồng thử việc"),
            ("XDTH", "Hợp đồng xác định thời hạn"),
            ("KXDTH", "Hợp đồng không xác định thời hạn"),
        ]:
            ContractType.objects.get_or_create(contract_type_code=code, defaults={"contract_type_name": name})

        from datetime import date
        from apps.payroll.models import InsuranceRateConfig, PersonalIncomeTaxBracket, TaxDeductionConfig

        InsuranceRateConfig.objects.get_or_create(
            effective_from=date(2026, 1, 1),
            defaults=dict(
                employee_social_insurance_rate=8,
                employee_health_insurance_rate=1.5,
                employee_unemployment_insurance_rate=1,
                employer_social_insurance_rate=17.5,
                employer_health_insurance_rate=3,
                employer_unemployment_insurance_rate=1,
                legal_reference="Luật BHXH 2024, Luật Việc làm 2025, NĐ 188/2025/NĐ-CP, NĐ 158/2025/NĐ-CP",
            ),
        )

        TaxDeductionConfig.objects.get_or_create(
            effective_from=date(2026, 1, 1),
            defaults=dict(self_deduction_monthly=15_500_000, dependent_deduction_monthly=6_200_000),
        )

        brackets_2026 = [
            (1, 0, 10_000_000, 5),
            (2, 10_000_000, 30_000_000, 10),
            (3, 30_000_000, 60_000_000, 20),
            (4, 60_000_000, 100_000_000, 30),
            (5, 100_000_000, None, 35),
        ]
        for no, low, high, rate in brackets_2026:
            PersonalIncomeTaxBracket.objects.get_or_create(
                effective_from=date(2026, 1, 1), bracket_no=no,
                defaults=dict(income_from_monthly=low, income_to_monthly=high, tax_rate=rate),
            )

        from apps.leave.models import LeaveType
        for code, name, paid in [
            ("AL", "Nghỉ phép năm", True),
            ("SL", "Nghỉ ốm", True),
            ("UL", "Nghỉ không lương", False),
            ("ML", "Nghỉ thai sản", True),
            ("PL", "Nghỉ bù", False),
        ]:
            LeaveType.objects.get_or_create(leave_type_code=code, defaults={"leave_type_name": name, "is_paid": paid})

        from apps.attendance.models import Holiday, WorkingCalendar
        for code, name, hdate in [
            ("TET2027", "Tết Dương lịch 2027", date(2027, 1, 1)),
            ("QK2026", "Quốc khánh 2/9", date(2026, 9, 2)),
        ]:
            Holiday.objects.get_or_create(holiday_code=code, defaults={"holiday_name": name, "holiday_date": hdate})
        WorkingCalendar.objects.get_or_create(
            calendar_year=2026, defaults={"working_days_per_month": 26, "working_hours_per_day": 8, "is_default": True}
        )

        from apps.project.models import Project
        for code, name in [("INC3b", "Dự án Hòa nhập 3b"), ("LDSC", "Dự án LDSC")]:
            Project.objects.get_or_create(project_code=code, defaults={"project_name": name})

        # Bổ sung loại nghỉ "Nghỉ bù" mà file Excel BCC yêu cầu, chưa có trong seed trước đó
        LeaveType.objects.get_or_create(leave_type_code="CL", defaults={"leave_type_name": "Nghỉ bù", "is_paid": True})

        from apps.office.models import MeetingRoom, Vehicle, SupplyItem
        for code, name, cap in [("PH1", "Phòng họp lớn", 20), ("PH2", "Phòng họp nhỏ", 6)]:
            MeetingRoom.objects.get_or_create(room_code=code, defaults={"room_name": name, "capacity": cap})
        Vehicle.objects.get_or_create(vehicle_code="XE01", defaults={"vehicle_name": "Innova", "plate_number": "51A-123.45", "capacity": 7})
        for code, name, unit, stock in [("BUT01", "Bút bi", "Cây", 100), ("GIAY01", "Giấy A4", "Ram", 50)]:
            SupplyItem.objects.get_or_create(item_code=code, defaults={"item_name": name, "unit": unit, "quantity_in_stock": stock})

        self.stdout.write(self.style.SUCCESS("Đã tạo xong dữ liệu mẫu."))



