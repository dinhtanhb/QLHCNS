"""Grouped Dashboard presentation must preserve the existing permission DTO."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.portal.home_presentation import grouped_dashboard


class GroupedDashboardTests(SimpleTestCase):
    def build(self, sections, *, permissions=(), **context):
        snapshot = {"sections": sections, "metrics": [], "plan_year": 2026}
        original = deepcopy(snapshot)
        with patch("apps.portal.home_presentation.has_permission",
                   side_effect=lambda user, permission: permission in permissions):
            result = grouped_dashboard(SimpleNamespace(), dict(context, dashboard_snapshot=snapshot),
                {"home_actions": [], "home_queue": [], "home_groups": []})
        self.assertEqual(snapshot, original)
        return result

    def test_bounded_rows_compact_permissions_and_group_order(self):
        rows = [{"pk": i} for i in range(8)]
        sections = {"headcount": {"rows": rows}, "history": {"rows": rows},
                    "global_leave": {"rows": rows, "global_scope": True},
                    "contracts": {"upcoming_count": 8, "upcoming_rows": rows,
                                  "overdue_rows": rows, "types": rows},
                    "requests": {"value": 1, "rows": []}}
        result = self.build(sections, permissions=("approve_personnel_decision",))
        self.assertEqual(result["limit"], 3)
        for key in ("history", "leave"):
            self.assertEqual(len(result[key]["rows"]), 3)
        self.assertEqual(len(result["headcount"]["rows"]), 4)
        self.assertEqual(len(result["contracts"]["upcoming_rows"]), 3)
        self.assertEqual([group["key"] for group in result["groups"]],
                         ["hr", "admin", "recruitment"])
        self.assertEqual(self.build(sections, permissions=("manage_hr",))["limit"], 5)

    def test_employee_has_only_my_work_and_no_own_leave_history(self):
        result = self.build({"own_leave": {"rows": [{"pk": 1}]}}, employee=object())
        self.assertTrue(result["my_work"])
        self.assertFalse(result["groups"])
        self.assertIsNone(result["leave"])
        self.assertFalse(result["project_allowed"])

    def test_zero_sections_hide_and_positive_project_is_retained(self):
        result = self.build({"postings": {"value": 0}, "queue": {"rows": []}},
                            show_project_activity_summary=True, activity_overdue=2,
                            activity_total=0)
        self.assertEqual(result["recruitment"][0]["value"], 0)
        self.assertFalse(result["queue"])
        self.assertEqual(len(result["projects"]), 5)
        self.assertEqual(result["projects"][2]["value"], 2)
        self.assertTrue(result["projects"][2]["warning"])

    def test_project_scope_keeps_all_zero_values_and_precedes_hr(self):
        result = self.build({"headcount": {"rows": [{"actual": 1}]},
                             "requests": {"value": 0}}, show_project_activity_summary=True)
        self.assertEqual([group["key"] for group in result["groups"]],
                         ["projects", "hr", "recruitment"])
        self.assertEqual([row["value"] for row in result["projects"]], [0] * 5)
        self.assertFalse(any(row["warning"] for row in result["projects"]))
        self.assertFalse(self.build({}, show_project_activity_summary=False)["projects"])

    def test_fallback_metric_does_not_mutate_snapshot(self):
        snapshot = {"sections": {"joined": {"value": 2, "label": "Nhân sự vào làm trong tháng"}},
                    "metrics": [{"key": "managed", "label": "Nhân sự đang quản lý", "value": 5}]}
        before = deepcopy(snapshot)
        with patch("apps.portal.home_presentation.has_permission", return_value=False):
            grouped_dashboard(SimpleNamespace(), {"dashboard_snapshot": snapshot},
                              {"home_actions": [], "home_queue": [], "home_groups": []})
        self.assertEqual(snapshot, before)
