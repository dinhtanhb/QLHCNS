"""Valid native sessions survive transient activity-write contention."""
from unittest.mock import patch

from django.contrib.sessions.models import Session
from django.db import OperationalError
from django.test import TestCase, override_settings

from apps.mobile import tests as fixtures


@override_settings(MOBILE_API_ENABLED=True, AXES_ENABLED=False)
class MobileActivityWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixtures.MobileAPITests.setUpTestData.__func__(cls)

    post = fixtures.MobileAPITests.post
    login_as = fixtures.MobileAPITests.login_as

    def test_database_lock_on_activity_write_keeps_valid_session_and_warns_without_secrets(self):
        token = self.login_as()
        original = Session.save

        def locked(row, *args, **kwargs):
            if kwargs.get('force_update'):
                raise OperationalError('database is locked')
            return original(row, *args, **kwargs)

        with patch.object(Session, 'save', locked):
            with self.assertLogs('apps.mobile.middleware', level='WARNING') as logs:
                response = self.client.get('/api/mobile/v1/me/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Session.objects.filter(session_key=token).exists())
        self.assertNotIn(token, ' '.join(logs.output))
        self.assertNotIn('database is locked', ' '.join(logs.output))

    def test_revoked_session_cannot_be_recreated_by_cached_activity(self):
        from django.contrib.sessions.backends.db import SessionStore
        from apps.mobile.middleware import save_native_session
        token = self.login_as()
        cached = SessionStore(session_key=token)
        self.assertTrue(cached.get('mobile_session'))
        cached['security_last_activity'] = 123
        Session.objects.filter(session_key=token).delete()
        self.assertFalse(save_native_session(cached))
        self.assertFalse(Session.objects.filter(session_key=token).exists())
        self.assertEqual(self.client.get('/api/mobile/v1/me/').status_code, 401)

    def test_activity_write_failure_does_not_mask_business_session_changes(self):
        self.login_as()
        original = Session.save

        def locked(row, *args, **kwargs):
            if kwargs.get('force_update'):
                raise OperationalError('database is locked')
            return original(row, *args, **kwargs)

        # Workspace assistant updates history as well as the idle timestamp.
        with patch.object(Session, 'save', locked):
            response = self.post('workspace/', {'path': '/assistant/api/search/', 'method': 'POST',
                                                'json': {'question': 'công văn'}})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client.get('/api/mobile/v1/me/').status_code, 200)

    def test_real_idle_expiry_boundary_is_unchanged(self):
        from django.contrib.sessions.backends.db import SessionStore
        from django.conf import settings
        token = self.login_as()
        for age, expected in [(settings.SESSION_IDLE_TIMEOUT, 200), (settings.SESSION_IDLE_TIMEOUT + 1, 401)]:
            with self.subTest(age=age):
                session = SessionStore(session_key=token)
                session['security_last_activity'] = 2000000000 - age
                session.save()
                with patch('apps.security.middleware.time.time', return_value=2000000000):
                    response = self.client.get('/api/mobile/v1/me/')
                self.assertEqual(response.status_code, expected)
