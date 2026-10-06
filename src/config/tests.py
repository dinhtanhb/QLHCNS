from django.test import SimpleTestCase

from config.env import env_flag


class EnvironmentFlagTests(SimpleTestCase):
    def test_true_values_are_case_and_whitespace_insensitive(self):
        for value in ("True", "true", "TRUE", "1", "t", " T "):
            with self.subTest(value=value):
                self.assertTrue(env_flag("FEATURE_ENABLED", environ={"FEATURE_ENABLED": value}))

    def test_false_empty_and_unknown_values_are_disabled(self):
        for value in ("False", "false", "0", "", "yes", "enabled"):
            with self.subTest(value=value):
                self.assertFalse(env_flag("FEATURE_ENABLED", environ={"FEATURE_ENABLED": value}))

    def test_missing_flag_uses_default(self):
        self.assertFalse(env_flag("FEATURE_ENABLED", environ={}))
        self.assertTrue(env_flag("FEATURE_ENABLED", default="1", environ={}))
