"""Create or serve a persistent synthetic portal, never the configured database.

python ops/dashboard_demo.py create --directory <new directory outside source>
python ops/dashboard_demo.py serve --directory <same directory> --port 8766
Credentials and runtime secrets stay in that demo directory, outside Git.
"""
import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import secrets
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("create", "serve"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error("Demo directory must be outside the source repository.")
    marker = folder / "synthetic-demo.json"
    if args.command == "create":
        if folder.exists() and any(folder.iterdir()):
            parser.error("Refusing to overwrite a nonempty directory.")
        folder.mkdir(parents=True, exist_ok=True)
        runtime = {"synthetic_only": True, "secret_key": secrets.token_urlsafe(64)}
        marker.write_text(json.dumps(runtime), encoding="utf-8")
    else:
        runtime = json.loads(marker.read_text(encoding="utf-8"))
        if runtime.get("synthetic_only") is not True or not (folder / "synthetic.sqlite3").is_file():
            parser.error("Not an initialized synthetic demo.")
    os.environ.update(DJANGO_SETTINGS_MODULE="config.settings", APP_ENV="test",
                      DB_ENGINE="django.db.backends.sqlite3", SECRET_KEY=runtime["secret_key"],
                      DEBUG="True", M365_STORAGE_ENABLED="False", ENABLE_HTTPS_ENFORCEMENT="False")
    sys.path.insert(0, str(root / "src"))
    import config.settings as cfg
    cfg.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(folder / "synthetic.sqlite3")}}
    cfg.MEDIA_ROOT = folder / "media"
    cfg.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    cfg.M365_STORAGE_ENABLED = False
    cfg.SYNTHETIC_DEMO = True
    cfg.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    for handler in cfg.LOGGING["handlers"].values():
        if "filename" in handler:
            handler["filename"] = str(folder / Path(handler["filename"]).name)
    import django
    django.setup()
    from django.core.management import call_command
    if args.command == "serve":
        call_command("runserver", f"127.0.0.1:{args.port}", use_reloader=False)
        return
    call_command("migrate", interactive=False, verbosity=0)
    seed(folder)
    print("Synthetic demo created. Credentials: " + str(folder / "DEMO_ACCOUNTS.txt"))


def seed(folder):
    from django.db import transaction
    from django.utils import timezone
    from apps.organization.models import Organization, Department, Position
    from apps.hrm.models import Employee
    from apps.security.models import User, Role
    from apps.contract.models import Contract, ContractType
    from apps.planning.models import HeadcountPlan
    from apps.leave.models import LeaveRequest, LeaveType, LeaveBalance
    from apps.portal.dashboard_data import dashboard_snapshot

    today = timezone.localdate()
    password = secrets.token_urlsafe(24)
    account_lines = ["IHRMS — DỮ LIỆU GIẢ THỬ NGHIỆM; KHÔNG PHẢI DỮ LIỆU VẬN HÀNH",
                     "URL: http://127.0.0.1:8766/portal/", "Mật khẩu chung trong bản demo: " + password, ""]
    with transaction.atomic():
        org = Organization.objects.create(organization_code="DEMO", organization_name="Trung tâm giả lập Atoms")
        names = ["Hành chính Nhân sự", "Kỹ thuật Vận hành", "Chương trình", "Kế toán", "Truyền thông", "Hỗ trợ"]
        departments = [Department.objects.create(organization=org, department_code=f"DEMO-{i}", department_name=name)
                       for i, name in enumerate(names)]
        position = Position.objects.create(position_code="DEMO", position_name="Chuyên viên giả lập")
        types = [ContractType.objects.create(contract_type_code=f"DEMO-{i}", contract_type_name=name) for i, name in enumerate(
                 ["Hợp đồng không xác định thời hạn", "Hợp đồng xác định thời hạn", "Hợp đồng thử việc", "Hợp đồng bán thời gian"])]
        people = []
        department_indices = [0]*3 + [1]*5 + [2]*5 + [3]*3 + [4]*3 + [5]*3
        for i, dep in enumerate(department_indices):
            status = "Active" if i < 17 else "Probation" if i < 20 else "OnLeave"
            person = Employee.objects.create(employee_code=f"DEMO-{i+1:03}", first_name="Giả lập", last_name=f"{i+1:02}",
                full_name=f"Nhân viên giả lập {i+1:02}", date_of_birth=date(1990,1,1), gender="Other",
                national_id=f"SYN-DEMO-{i+1:03}", company_email=f"demo{i+1:03}@example.test", mobile_phone="0000000000",
                join_date=today-timedelta(days=365), department=departments[dep], position=position, employment_status=status)
            people.append(person)
            kind = types[0 if i < 12 else 1 if i < 17 else 2 if i < 20 else 3]
            contract = Contract(employee=person, contract_type=kind, contract_no=f"DEMO-HĐ-{i+1:03}",
                start_date=today-timedelta(days=90), end_date=None if i < 12 else today+timedelta(days=[0,7,30,60,365][i%5]),
                basic_salary=5000000+i*500000, status="Active")
            contract.full_clean()
            contract.save()
            LeaveBalance.objects.create(employee=person, year=today.year, allocated_days=30)
        # Cover all contract statuses without changing effective distribution.
        for index, status in enumerate(("Draft", "Expired", "Terminated")):
            Contract.objects.create(employee=people[index], contract_type=types[1], contract_no=f"DEMO-{status}",
                start_date=today-timedelta(days=400), end_date=today-timedelta(days=90), basic_salary=5000000, status=status)
        # Active but expired and future-start boundaries are separate from the donut.
        for label, start, end in (("OVERDUE",-100,-1), ("FUTURE",1,100)):
            Contract.objects.create(employee=people[0], contract_type=types[1], contract_no="DEMO-"+label,
                start_date=today+timedelta(days=start), end_date=today+timedelta(days=end), basic_salary=5000000, status="Active")
        for dep, planned in zip(departments, (10,8,7,5,4,3)):
            HeadcountPlan.objects.create(department=dep, year=today.year, planned_headcount=planned)
        leave_type = LeaveType.objects.create(leave_type_code="DEMO", leave_type_name="Phép năm giả lập")
        for i, status in enumerate(("Approved", "Approved", "Pending", "Pending")):
            LeaveRequest.objects.create(employee=people[i+4], leave_type=leave_type, from_date=today, to_date=today, status=status)
        roles = (("hr", "HR_MANAGER", "Quản trị nhân sự", 0), ("director", "DIRECTOR", "Giám đốc", 1),
                 ("manager", "DEPT_MANAGER", "Trưởng phòng", 3), ("employee", "EMPLOYEE", "Nhân viên", 4),
                 ("finance", "FINANCE_OFFICER", "Kế toán", 13), ("hr-officer", "HR_OFFICER", "Chuyên viên nhân sự", 2))
        accounts = {}
        for name, code, label, index in roles:
            role, _ = Role.objects.get_or_create(role_code=code, defaults={"role_name":label})
            user = User.objects.create_user(username="demo-"+name, password=password, employee=people[index], role=role)
            accounts[name] = user
            if code == "DEPT_MANAGER":
                people[index].managed_departments.add(people[index].department)
            account_lines.append(f"{user.username}: {label}")
        # Phase-two synthetic boundaries and privacy sentinels. No operational copy.
        from apps.recruitment.models import RecruitmentRequest, JobPosting, Candidate
        from apps.document.models import PersonnelDecision, PersonnelDecisionHistory
        sensitive_type = LeaveType.objects.create(leave_type_code="DEMO-SENSITIVE", leave_type_name="Thai sản")
        for index, status in enumerate(("Pending", "Approved", "Rejected", "Cancelled")):
            LeaveRequest.objects.create(employee=people[index], leave_type=sensitive_type,
                from_date=today+timedelta(days=20+index), to_date=today+timedelta(days=20+index),
                total_days=1, status=status, reason="SYNTHETIC_PRIVATE_REASON", attachment="SYNTHETIC_PRIVATE_ATTACHMENT")
        Employee.objects.filter(pk__in=[people[i].pk for i in (0,3,18)]).update(join_date=today.replace(day=1))
        Employee.objects.filter(pk=people[3].pk).update(full_name="Nhân viên giả lập có họ tên dài để kiểm tra bố cục bảng và điều hướng trên màn hình hẹp")
        for index, status in enumerate(("Pending", "Approved", "Rejected", "Closed")):
            request = RecruitmentRequest.objects.create(request_code=f"DEMO-REQ-{index}",
                department=departments[index%2], position=position, required_quantity=2,
                required_date=today, status=status, request_reason="SYNTHETIC_PRIVATE_REQUEST")
            JobPosting.objects.create(recruitment_request=request, posting_title=f"Tin giả lập {index}",
                open_date=today-timedelta(days=3), status="Open" if index<3 else "Closed")
        for index, (status, _) in enumerate(Candidate.STATUS_CHOICES):
            for number in range(index+1):
                Candidate.objects.create(candidate_code=f"DEMO-C-{index}-{number}", full_name="SYNTHETIC_PRIVATE_CANDIDATE",
                    email="synthetic@example.test", phone_number="0000000000", status=status)
        for index, status in enumerate(("PendingApproval", "Issued", "Draft")):
            decision = PersonnelDecision.objects.create(employee=people[4], template_slug="qd_bo_nhiem",
                decision_no=f"DEMO-QD-{index+1:03}", status=status, content_snapshot={"private":"SYNTHETIC_PRIVATE_SNAPSHOT"})
            PersonnelDecisionHistory.objects.create(decision=decision, action="Submitted" if index==0 else "Issued" if index==1 else "DraftCreated",
                status_to=status, created_by=accounts["director"] if index==1 else accounts["hr"], comment="SYNTHETIC_PRIVATE_COMMENT")
        snapshot = dashboard_snapshot(accounts["hr"], people[0])
        manifest = {"synthetic_only": True, "date": today.isoformat(), "employees": len(people), "contracts": Contract.objects.count(),
                    "expected_kpis": {m["key"]:m["value"] for m in snapshot["metrics"]},
                    "effective_contracts": snapshot["sections"]["contracts"]["total"], "departments":6}
    (folder / "DEMO_ACCOUNTS.txt").write_text("\n".join(account_lines), encoding="utf-8")
    (folder / "DEMO_EXPECTATIONS.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
