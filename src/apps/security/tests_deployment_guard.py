"""Deployment settings must fail closed for a network-facing UAT instance."""

import os
from pathlib import Path
import secrets
import subprocess
import sys

from django.test import SimpleTestCase


class DeploymentGuardTests(SimpleTestCase):
    def test_uat_requires_secure_settings(self):
        root = Path(__file__).resolve().parents[2]
        secure_key = secrets.token_urlsafe(64)
        baseline = {
            **os.environ,
            "APP_ENV": "uat",
            "DEBUG": "False",
            "ENABLE_HTTPS_ENFORCEMENT": "True",
            "SECRET_KEY": secure_key,
            "ALLOWED_HOSTS": "uat.example.test",
        }
        cases = (
            ({"DEBUG": "True"}, False),
            ({"ENABLE_HTTPS_ENFORCEMENT": "False"}, False),
            ({"SECRET_KEY": "django-insecure-weak"}, False),
            ({"ALLOWED_HOSTS": "*"}, False),
            ({}, True),
        )
        for overrides, expected_success in cases:
            with self.subTest(overrides=overrides):
                result = subprocess.run(
                    [sys.executable, "-c", "import config.settings"],
                    cwd=root, env={**baseline, **overrides},
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode == 0, expected_success)

    def test_qa_reset_refuses_generic_application_database_name(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                sys.executable, str(root.parent / "ops" / "reset_qa_data.py"),
                "--database", "qlhcns",
                "--backup-file", str(root.parent / "missing.bak"),
                "--credentials", str(root.parent / "missing.csv"),
                "--apply",
            ],
            cwd=root.parent,
            env={**os.environ, "APP_ENV": "test", "DB_ENGINE": "mssql", "DB_NAME": "qlhcns"},
            capture_output=True, text=True, timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Database name must explicitly identify a disposable QA/UAT copy", result.stderr)
