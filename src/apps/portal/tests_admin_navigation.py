"""Regression coverage for navigation between Django Admin and the portal."""

import re

from django.conf import settings
from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse

from apps.common.asset_version import get_asset_hash
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

    def test_admin_loads_navigation_stylesheet_once_with_content_hash(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(settings.JAZZMIN_SETTINGS.get("custom_css"))
        self.assertContains(response, f'{static("css/admin.css")}?v={get_asset_hash("css/admin.css")}')
        links = re.findall(r'<link[^>]+href="[^"]*/css/admin\.css(?:\?[^"]*)?"', response.content.decode())
        self.assertEqual(len(links), 1)
