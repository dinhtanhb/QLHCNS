"""Presentation contracts from bb053b2, exercised on the current dashboard."""
from datetime import date
from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from apps.portal.home_presentation import home_presentation
from apps.portal import test_home_dashboard as fixtures
from apps.portal.dashboard_phase2 import phase2_sections


class DisclosureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.inside = []
        self.outside = []

    def handle_starttag(self, tag, attrs):
        if tag == 'details':
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'details':
            self.depth -= 1

    def handle_data(self, data):
        (self.inside if self.depth else self.outside).append(data)


class DashboardReviewTests(TestCase):
    user = fixtures.HomeDashboardTests.user

    @classmethod
    def setUpTestData(cls):
        fixtures.HomeDashboardTests.setUpTestData.__func__(cls)

    def test_legacy_none_removed_zero_retained_and_empty_groups_removed(self):
        user = self.user('HR_MANAGER')
        for value, expected in ((None, []), (0, [0])):
            with self.subTest(value=value), self.assertNumQueries(0):
                result = home_presentation(user, {'is_management_view': True, 'total_employees': value})
            self.assertEqual([c['value'] for g in result['home_groups'] for c in g['cards']], expected)
            self.assertEqual(len(result['home_groups']), bool(expected))

    def render_dashboard(self, user, sections):
        context = {'user': user, 'employee': user.employee, 'dashboard_snapshot': {'sections': sections}}
        context.update(home_presentation(user, context))
        return render_to_string('portal/dashboard.html', context)

    @staticmethod
    def leave(key):
        return {'key': key, 'state': 'ready', 'global_scope': key == 'global_leave', 'rows': [
            {'type_label': key + '-private-marker', 'from_date': date(2026, 10, 1),
             'to_date': date(2026, 10, 2), 'status': 'Pending', 'employee__full_name': 'QA'}]}

    def test_both_leave_blocks_own_rows_only_inside_disclosure(self):
        user = self.user('HR_MANAGER', True)
        html = self.render_dashboard(user, {key: self.leave(key) for key in ('own_leave', 'global_leave')})
        parser = DisclosureParser(); parser.feed(html)
        self.assertIn('Đơn nghỉ gần đây của tôi', html)
        self.assertEqual(html.count('own_leave-private-marker'), 1)
        self.assertIn('own_leave-private-marker', ''.join(parser.inside))
        self.assertNotIn('own_leave-private-marker', ''.join(parser.outside))

    def test_only_own_leave_is_regular_block(self):
        html = self.render_dashboard(self.user('EMPLOYEE', True), {'own_leave': self.leave('own_leave')})
        self.assertIn('own_leave-private-marker', html)
        self.assertNotIn('class="dashboard-own-leave"', html)

    def test_only_global_leave_has_no_personal_disclosure(self):
        html = self.render_dashboard(self.user('HR_MANAGER'), {'global_leave': self.leave('global_leave')})
        self.assertIn('global_leave-private-marker', html)
        self.assertNotIn('class="dashboard-own-leave"', html)

    def test_unlinked_user_has_no_own_leave_data_or_markup(self):
        user = self.user('HR_MANAGER')
        sections = phase2_sections(user, None, date(2026, 10, 26), lambda builder: builder())
        self.assertNotIn('own_leave', sections)
        html = self.render_dashboard(user, sections)
        self.assertNotIn('own_leave-private-marker', html)
        self.assertNotIn('class="dashboard-own-leave"', html)

    def test_phase_one_and_two_errors_remain_visible_without_fake_zero(self):
        user = self.user('HR_MANAGER', True)
        for key in ('status', 'joined', 'queue', 'headcount', 'contracts', 'history',
                    'own_leave', 'global_leave', 'postings', 'candidates', 'requests'):
            with self.subTest(key=key):
                html = self.render_dashboard(user, {key: {'state': 'error'}})
                self.assertIn('Không tải được dữ liệu', html)

    def test_cta_labels_and_destinations_have_one_source(self):
        user = self.user('HR_MANAGER', True)
        sections = phase2_sections(user, user.employee, date(2026, 10, 26), lambda builder: builder())
        for key, label, route in (('postings', 'Tuyển dụng', 'recruitment_hub'),
                                  ('candidates', 'Xem ứng viên', 'hr_candidate_list'),
                                  ('requests', 'Xem đề xuất', 'recruitment_list')):
            with self.subTest(key=key):
                item = sections[key]
                self.assertEqual(item['cta_label'], label)
                self.assertEqual(item['cta'], reverse('portal:' + route))
                html = render_to_string('portal/dashboard/_phase2_metric.html', {'key': key, 'data': item})
                self.assertIn(f'href="{item["cta"]}"', html)
                self.assertIn(label, html)
                custom = render_to_string('portal/dashboard/_phase2_metric.html',
                                          {'key': key, 'data': dict(item, cta_label='QA custom CTA')})
                self.assertIn('QA custom CTA', custom)

    def test_error_metric_does_not_nest_cards(self):
        html = render_to_string('portal/dashboard/_phase2_metric.html',
                                {'key': 'postings', 'data': {'state': 'error', 'label': 'QA'}})
        self.assertNotIn('<div class="ui-card">', html)
