"""Phase-two read contracts, privacy, scopes and whole-page query budgets."""
import json
import math
import time
from datetime import datetime, time as midnight, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import connection, DatabaseError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.portal import test_home_dashboard as fixtures
from apps.portal import dashboard_data as data
from apps.hrm.models import Employee
from apps.leave.models import LeaveRequest, LeaveType
from apps.recruitment.models import Candidate, Interview, Offer, JobPosting, RecruitmentRequest
from apps.document.models import PersonnelDecision, PersonnelDecisionHistory
from apps.organization.models import Department
from apps.security.permissions import has_permission


class DashboardPhase2Tests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_approved_blocks_present(self):
        user = self.user('HR_MANAGER', True)
        self.client.force_login(user)
        response = self.client.get(reverse('portal:dashboard'))
        for key in ('own_leave', 'global_leave', 'postings', 'candidates', 'joined', 'history', 'requests'):
            self.assertIn(key, response.context['dashboard_snapshot']['sections'])
            self.assertContains(response, 'id="phase2-' + key + '"')

    def stamp(self, obj, day, hour=0):
        stamp = timezone.make_aware(datetime.combine(day, midnight(hour)), timezone.get_current_timezone())
        type(obj).all_objects.filter(pk=obj.pk).update(created_date=stamp)
        return obj

    def leave(self, employee, day, kind, **extra):
        today = timezone.localdate()
        obj = LeaveRequest.objects.create(employee=employee, leave_type=kind, from_date=today,
            to_date=today, total_days=Decimal('2.5'), reason='SECRET_REASON', attachment='SECRET_ATTACHMENT', **extra)
        return self.stamp(obj, day)

    def test_leave_window_privacy_parents_and_stored_days(self):
        hr = self.user('HR_MANAGER', True)
        director = self.user('DIRECTOR', True)
        employee = self.user('EMPLOYEE', True)
        today = timezone.localdate()
        kind = LeaveType.objects.create(leave_type_code='SENSITIVE', leave_type_name='Thai sản')
        expected = []
        for offset in (-29, -30, 0, 1):
            row = self.leave(employee.employee, today + timedelta(days=offset), kind)
            if offset in (-29, 0): expected.append(row.pk)
        self.leave(director.employee, today, kind, status='Rejected')
        deleted_kind = LeaveType.objects.create(leave_type_code='DELETED', leave_type_name='DELETED_TYPE', is_deleted=True)
        self.leave(employee.employee, today, deleted_kind)
        deleted = self.user('DELETED', True)
        self.leave(deleted.employee, today, kind)
        deleted.employee.delete()
        for user in (hr, director, employee):
            self.client.force_login(user)
            response = self.client.get(reverse('portal:dashboard'))
            sections = response.context['dashboard_snapshot']['sections']
            block = sections['global_leave'] if user != employee else sections['own_leave']
            ids = [row['pk'] for row in block['rows']]
            for pk in expected: self.assertIn(pk, ids)
            self.assertEqual(all(row['total_days'] == Decimal('2.5') for row in block['rows']), True)
            text = response.content.decode() + str(sections)
            for secret in ('SECRET_REASON', 'SECRET_ATTACHMENT', 'DELETED_TYPE'):
                self.assertNotIn(secret, text)
            self.assertEqual('Thai sản' in text, has_permission(user, 'manage_hr'))
        self.assertEqual(len(sections['own_leave']['rows']), 2)

    def request(self, status='Pending', department=None):
        return RecruitmentRequest.objects.create(request_code='REQ-' + str(RecruitmentRequest.all_objects.count()),
            department=department or self.department, position=self.position, required_date=timezone.localdate(),
            status=status, request_reason='SECRET_REQUEST', required_quantity=99)

    def test_recruitment_aggregates_and_request_scope(self):
        hr = self.user('HR_MANAGER', True)
        manager = self.user('DEPT_MANAGER', True)
        outside = Department.objects.create(organization=self.department.organization, department_code='OUT', department_name='Outside')
        for status in ('Pending', 'Approved', 'Rejected', 'Closed'): self.request(status)
        self.request(department=outside)
        parent = self.request()
        for status in ('Open', 'Closed'):
            JobPosting.objects.create(recruitment_request=parent, posting_title='SECRET_POSTING',
                open_date=timezone.localdate()+timedelta(days=30), close_date=timezone.localdate()-timedelta(days=1), status=status)
        deleted_parent = self.request(); deleted_parent.delete()
        JobPosting.objects.create(recruitment_request=deleted_parent, posting_title='SECRET_POSTING', open_date=timezone.localdate())
        for status, _ in Candidate.STATUS_CHOICES:
            candidate = Candidate.objects.create(candidate_code=status, full_name='SECRET_CANDIDATE',
                phone_number='SECRET_PHONE', email='secret@example.test', status=status)
            for _ in range(2):
                Interview.objects.create(candidate=candidate, interviewer=hr.employee, interview_date=timezone.now(), interview_type='Fake')
                Offer.objects.create(candidate=candidate, offer_date=timezone.localdate(), expected_join_date=timezone.localdate(), salary_offer=999)
        for user in (hr, manager):
            snap = data.dashboard_snapshot(user, user.employee)
            self.client.force_login(user)
            target = self.client.get(reverse('portal:recruitment_list')).context['requests']
            self.assertEqual(snap['sections']['requests']['value'], target.count())
            self.assertIsNone(snap['sections']['requests']['href'])
        snap = data.dashboard_snapshot(hr, hr.employee)
        self.assertEqual(snap['sections']['postings']['value'], 1)
        self.assertEqual(snap['sections']['candidates']['value'], 4)
        self.assertEqual([r['value'] for r in snap['sections']['candidates']['rows']], [1]*6)
        self.assertNotIn('SECRET_', str(snap))

    def test_joined_same_selector_and_boundaries(self):
        hr = self.user('HR_MANAGER', True)
        manager = self.user('DEPT_MANAGER', True)
        today = timezone.localdate()
        first = today.replace(day=1)
        for index, (day, status) in enumerate(((first,'Active'), (today,'Probation'), (today,'OnLeave'),
                (today+timedelta(days=1),'Active'), (first-timedelta(days=1),'Active'), (today,'Resigned'))):
            user = self.user('CASE' + str(index), True)
            Employee.objects.filter(pk=user.employee_id).update(join_date=day, employment_status=status)
        for user in (hr, manager):
            snapshot = data.dashboard_snapshot(user, user.employee)
            item = snapshot['sections']['joined']
            self.assertEqual(item['value'], 3)
            self.client.force_login(user)
            response = self.client.get(item['href'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].paginator.count, item['value'])
        manager.employee.managed_departments.clear()
        self.assertEqual(data.dashboard_snapshot(manager, manager.employee)['sections']['joined']['value'], 0)

    def test_history_scope_window_order_and_privacy(self):
        hr = self.user('HR_MANAGER', True)
        director = self.user('DIRECTOR', True)
        employee = self.user('EMPLOYEE', True)
        today = timezone.localdate()
        rows = []
        for status in ('PendingApproval', 'Issued', 'Draft'):
            decision = PersonnelDecision.objects.create(employee=employee.employee, template_slug='fake',
                decision_no='FAKE-' + status, status=status, content_snapshot={'private': 'SECRET_SNAPSHOT'})
            for offset in (-30, -29, 0, 1):
                event = PersonnelDecisionHistory.objects.create(decision=decision, action='Approved',
                    status_to=status, comment='SECRET_COMMENT', created_by=director if status=='Issued' else hr)
                self.stamp(event, today+timedelta(days=offset)); rows.append(event)
        for user, expected in ((hr,6), (director,4)):
            snapshot = data.dashboard_snapshot(user,user.employee)
            events = snapshot['sections']['history']['rows']
            self.assertEqual(len(events), expected)
            self.assertEqual([(r['created_date'],r['pk']) for r in events], sorted([(r['created_date'],r['pk']) for r in events], reverse=True))
            self.assertNotIn('SECRET_', str(snapshot))
            self.client.force_login(user)
            for row in events: self.assertEqual(self.client.get(row['href']).status_code, 200)
        self.assertNotIn('history', data.dashboard_snapshot(employee, employee.employee)['sections'])

    def test_role_matrix_denied_sources_and_get_writes(self):
        roles = ('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN','SUPER_ADMIN')
        for role in roles:
            for linked in (False, True):
                user = self.user(role,linked)
                with CaptureQueriesContext(connection) as captured:
                    snapshot = data.dashboard_snapshot(user, user.employee)
                sections = snapshot['sections']
                expected = {'own_leave':linked, 'global_leave':has_permission(user,'approve_leave_all_departments'),
                    'postings':has_permission(user,'view_reports'), 'candidates':has_permission(user,'manage_hr'),
                    'joined':has_permission(user,'view_all_employees') or role=='DEPT_MANAGER' and linked,
                    'history':has_permission(user,'manage_hr') or has_permission(user,'approve_personnel_decision'),
                    'requests':has_permission(user,'request_recruitment') and (role=='HR_MANAGER' or linked)}
                for key, allowed in expected.items(): self.assertEqual(key in sections, bool(allowed), (role,linked,key))
                sql = ' '.join(q['sql'] for q in captured)
                for key, table in (('postings','tblJobPosting'),('candidates','tblCandidate'),('history','tblPersonnelDecisionHistory'),('requests','tblRecruitmentRequest')):
                    if not expected[key]: self.assertNotRegex(sql, r'FROM\s+["\[]' + table + r'["\]]')
                self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in captured))
                self.client.force_login(user)
                response = self.client.get(reverse('portal:dashboard'))
                for key,allowed in expected.items(): self.assertEqual('id="phase2-'+key+'"' in response.content.decode(), bool(allowed))

    def test_query_matrix_p95_and_size_independence(self):
        matrix = {}
        url = reverse('portal:dashboard')
        for role in ('EMPLOYEE','DEPT_MANAGER','HR_OFFICER','HR_MANAGER','DIRECTOR','FINANCE_OFFICER','SYS_ADMIN','SUPER_ADMIN','SUPERUSER'):
            for linked in (False,True):
                user = self.user(role,linked)
                if role == 'SUPERUSER':
                    user.is_superuser = True; user.save(update_fields=['is_superuser'])
                self.client.force_login(user)
                start=time.perf_counter(); self.client.get(url); cold=time.perf_counter()-start
                times=[]
                for _ in range(20):
                    start=time.perf_counter()
                    with CaptureQueriesContext(connection) as captured: response=self.client.get(url)
                    times.append(time.perf_counter()-start)
                selects=sum(q['sql'].lstrip().upper().startswith('SELECT') for q in captured)
                self.assertLessEqual(selects,24,(role,linked))
                matrix[f'{role}-{linked}']={'selects':selects,'cold_seconds':round(cold,4),
                    'p95_seconds':round(sorted(times)[math.ceil(len(times)*.95)-1],4)}
        print('PHASE2_QUERY_MATRIX='+json.dumps(matrix))
        hr = self.user('GROWTH',False); hr.role = self.user_role('HR_MANAGER'); hr.save(update_fields=['role'])
        self.client.force_login(hr); self.client.get(url)
        with CaptureQueriesContext(connection) as before: self.client.get(url)
        for index in range(100):
            Department.objects.create(organization=self.department.organization,department_code='GROW'+str(index),department_name='Fake '+str(index))
        Candidate.objects.bulk_create([Candidate(candidate_code='GROW'+str(i), full_name='Synthetic',phone_number='000',email='fake@example.test') for i in range(1000)])
        Employee.objects.bulk_create([Employee(employee_code='GROW'+str(i), first_name='Fake',last_name='Fake',full_name='Synthetic',date_of_birth='1990-01-01',gender='Other',national_id='GROW'+str(i),company_email=f'grow{i}@example.test',mobile_phone='000',join_date=timezone.localdate(),department=self.department,position=self.position) for i in range(1000)])
        decision=PersonnelDecision.objects.create(employee=self.user('HISTORY',True).employee,template_slug='fake',decision_no='GROW')
        PersonnelDecisionHistory.objects.bulk_create([PersonnelDecisionHistory(decision=decision,action='DraftCreated',status_to='Draft') for _ in range(1000)])
        with CaptureQueriesContext(connection) as after: self.client.get(url)
        count=lambda queries:sum(q['sql'].lstrip().upper().startswith('SELECT') for q in queries)
        self.assertEqual(count(before),count(after))
        print('PHASE2_GROWTH='+json.dumps({'before':count(before),'after':count(after)}))

    def test_superuser_staff_errors_limits_and_deleted_parents(self):
        from apps.security.models import User
        superuser = User.objects.create(username='phase2-super',is_superuser=True)
        staff = User.objects.create(username='phase2-staff',is_staff=True)
        self.assertNotIn('candidates',data.dashboard_snapshot(staff)['sections'])
        self.assertIn('candidates',data.dashboard_snapshot(superuser)['sections'])
        hr = self.user('HR_MANAGER',True)
        today = timezone.localdate()
        kind = LeaveType.objects.create(leave_type_code='LIMIT',leave_type_name='Fake')
        for _ in range(9): self.leave(hr.employee,today,kind)
        snapshot = data.dashboard_snapshot(hr,hr.employee)
        self.assertEqual(len(snapshot['sections']['own_leave']['rows']),6)
        decision = PersonnelDecision.objects.create(employee=hr.employee,template_slug='fake',decision_no='LIMIT')
        for _ in range(10): PersonnelDecisionHistory.objects.create(decision=decision,action='DraftCreated',status_to='Draft')
        self.assertEqual(len(data.dashboard_snapshot(hr,hr.employee)['sections']['history']['rows']),8)
        self.department.delete()
        snapshot = data.dashboard_snapshot(hr,hr.employee)
        self.assertFalse(snapshot['sections']['history']['rows'])
        self.assertFalse(snapshot['sections']['own_leave']['rows'])
        from apps.portal import dashboard_phase2
        with patch.object(dashboard_phase2,'postings',side_effect=DatabaseError('SECRET_SQL')):
            snapshot = data.dashboard_snapshot(superuser)
        self.assertEqual(snapshot['sections']['postings']['state'],'error')
        self.assertNotIn('SECRET_SQL',str(snapshot))

    def test_deleted_events_decisions_and_posting_parents(self):
        hr=self.user('HR_MANAGER',True)
        decision=PersonnelDecision.objects.create(employee=hr.employee,template_slug='fake',decision_no='DELETED')
        event=PersonnelDecisionHistory.objects.create(decision=decision,action='Submitted',status_to='PendingApproval')
        event.delete()
        self.assertFalse(data.dashboard_snapshot(hr,hr.employee)['sections']['history']['rows'])
        PersonnelDecisionHistory.objects.create(decision=decision,action='Submitted',status_to='PendingApproval')
        decision.delete()
        self.assertFalse(data.dashboard_snapshot(hr,hr.employee)['sections']['history']['rows'])
        parent=self.request()
        posting=JobPosting.objects.create(recruitment_request=parent,posting_title='Fake',open_date=timezone.localdate())
        posting.delete()
        self.assertEqual(data.dashboard_snapshot(hr,hr.employee)['sections']['postings']['value'],0)
        JobPosting.objects.create(recruitment_request=parent,posting_title='Fake',open_date=timezone.localdate())
        self.position.delete()
        snapshot=data.dashboard_snapshot(hr,hr.employee)
        self.assertEqual(snapshot['sections']['postings']['value'],0)
        # RecruitmentRequest must retain the exact broader destination scope.
        self.client.force_login(hr)
        self.assertEqual(snapshot['sections']['requests']['value'],self.client.get(reverse('portal:recruitment_list')).context['requests'].count())

    def test_midnight_exclusive_end_and_leave_soft_delete(self):
        hr=self.user('HR_OFFICER',True)
        today=timezone.localdate()
        kind=LeaveType.objects.create(leave_type_code='MIDNIGHT',leave_type_name='Fake')
        first=self.leave(hr.employee,today-timedelta(days=29),kind)
        prior=self.leave(hr.employee,today-timedelta(days=30),kind)
        end=self.leave(hr.employee,today+timedelta(days=1),kind)
        deleted=self.leave(hr.employee,today,kind); deleted.delete()
        rows=data.dashboard_snapshot(hr,hr.employee)['sections']['own_leave']['rows']
        self.assertEqual([row['pk'] for row in rows],[first.pk])
        from apps.portal.dashboard_phase2 import created_window
        start,stop=created_window(today)
        self.assertEqual(timezone.localtime(start).hour,0)
        self.assertEqual(timezone.localtime(stop).date(),today+timedelta(days=1))

    def test_combined_leaves_independently_limit_own_and_global(self):
        hr=self.user('HR_MANAGER',True)
        other=self.user('EMPLOYEE',True)
        today=timezone.localdate()
        kind=LeaveType.objects.create(leave_type_code='RANK',leave_type_name='Fake')
        own=[self.leave(hr.employee,today-timedelta(days=10),kind).pk for _ in range(8)]
        global_ids=[self.leave(other.employee,today,kind).pk for _ in range(9)]
        from apps.portal.dashboard_phase2 import recent_leave_pair
        with CaptureQueriesContext(connection) as captured:
            pair=recent_leave_pair(hr,hr.employee,today)
        self.assertEqual([r['pk'] for r in pair['own']['rows']],list(reversed(own[-6:])))
        self.assertEqual([r['pk'] for r in pair['global_leave']['rows']],list(reversed(global_ids[-6:])))
        self.assertEqual(sum(q['sql'].lstrip().upper().startswith('SELECT') for q in captured),1)
        self.assertTrue(all('employee__full_name' not in row for row in pair['own']['rows']))

    def test_history_list_scope_with_deleted_actor_event_has_no_dead_detail_link(self):
        hr=self.user('HR_MANAGER',True)
        director=self.user('DIRECTOR',True)
        decision=PersonnelDecision.objects.create(employee=hr.employee,template_slug='fake',decision_no='LEGACY',status='Issued')
        own=PersonnelDecisionHistory.objects.create(decision=decision,action='Approved',status_to='Approved',created_by=director)
        own.delete()
        event=PersonnelDecisionHistory.objects.create(decision=decision,action='Issued',status_to='Issued',created_by=hr)
        self.client.force_login(director)
        self.assertEqual(self.client.get(reverse('portal:personnel_decision_detail',args=[decision.pk])).status_code,403)
        rows=data.dashboard_snapshot(director,director.employee)['sections']['history']['rows']
        self.assertEqual([r['pk'] for r in rows],[event.pk])
        self.assertIsNone(rows[0]['href'])

    def user_role(self, code):
        from apps.security.models import Role
        return Role.objects.get(role_code=code)
