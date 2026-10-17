"""CSRF rotation regressions; isolated clients with real CSRF enforcement."""
import re

from django.test import Client, TestCase
from django.urls import reverse

from apps.security.models import User


class LoginCsrfTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="csrf-synthetic", password="Synthetic-test-only-123")

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("portal:login")

    def credentials(self, token):
        return dict(username="csrf-synthetic", password="Synthetic-test-only-123", csrfmiddlewaretoken=token)

    def test_login_loads_scoped_sync_and_still_has_server_token(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-login-csrf')
        from apps.common.asset_version import get_asset_hash
        self.assertContains(response, 'js/login_csrf.js?v='+get_asset_hash('js/login_csrf.js'))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_old_form_rejected_current_cookie_accepted_after_rotation(self):
        response = self.client.get(self.url)
        old = re.search(r'name="csrfmiddlewaretoken" value="([A-Za-z0-9]+)"', response.content.decode())[1]
        first = self.client.post(self.url, self.credentials(old))
        self.assertEqual(first.status_code, 302)
        self.assertEqual(self.client.post(self.url, self.credentials(old)).status_code, 403)
        current = self.client.cookies["csrftoken"].value
        self.assertEqual(self.client.post(self.url, self.credentials(current)).status_code, 302)

    def test_missing_and_forged_tokens_remain_rejected(self):
        self.client.get(self.url)
        for token in ("", "a" * 32, "invalid"):
            with self.subTest(token_length=len(token)):
                self.assertEqual(self.client.post(self.url, self.credentials(token)).status_code, 403)
