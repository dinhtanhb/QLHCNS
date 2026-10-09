"""Regression coverage for navigation between Django Admin and the portal."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.security.models import User


class AdminPortalNavigationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin-navigation",
            password="test-password",
            email="admin-navigation@example.test",
        )
        self.client.force_login(self.admin)

    def test_admin_header_has_visible_portal_return_link(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/portal/"')
        self.assertContains(response, "Về giao diện sử dụng")

    def test_admin_loads_custom_navigation_stylesheet(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(settings.JAZZMIN_SETTINGS["custom_css"], "css/admin.css")
        self.assertContains(response, "css/admin.css")
