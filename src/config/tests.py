from django.test import SimpleTestCase

from config.env import env_choice, env_flag


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


class EnvironmentChoiceTests(SimpleTestCase):
    CHOICES = ("viethealth", "chamdong", "thanam")

    def test_valid_values_are_case_and_whitespace_insensitive(self):
        for value in ("chamdong", "CHAMDONG", " ChamDong ", "thanam"):
            with self.subTest(value=value):
                chosen, invalid = env_choice("UI_PALETTE", self.CHOICES, "viethealth",
                                             environ={"UI_PALETTE": value})
                self.assertEqual(chosen, value.strip().lower())
                self.assertIsNone(invalid)

    def test_missing_value_uses_default(self):
        chosen, invalid = env_choice("UI_PALETTE", self.CHOICES, "viethealth", environ={})
        self.assertEqual(chosen, "viethealth")
        self.assertIsNone(invalid)

    def test_unknown_value_returns_default_and_raw_for_warning(self):
        chosen, invalid = env_choice("UI_PALETTE", self.CHOICES, "viethealth",
                                     environ={"UI_PALETTE": "xanh-la"})
        self.assertEqual(chosen, "viethealth")
        self.assertEqual(invalid, "xanh-la")
