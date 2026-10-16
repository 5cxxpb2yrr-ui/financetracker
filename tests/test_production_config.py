"""Production configuration safety checks for FinanceTracker."""

import os
import subprocess
import sys
import unittest


class ProductionSecretConfigurationTests(unittest.TestCase):
    def run_import(self, secret_key):
        env = os.environ.copy()
        env["FLASK_ENV"] = "production"
        if secret_key is None:
            env.pop("SECRET_KEY", None)
        else:
            env["SECRET_KEY"] = secret_key
        # Keep tests independent of any locally configured database path.
        env.pop("DATABASE", None)
        return subprocess.run(
            [sys.executable, "-c", "import app"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_missing_secret_fails_closed_in_production(self):
        result = self.run_import(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY must be explicitly configured", result.stderr)

    def test_known_development_secret_fails_closed_in_production(self):
        result = self.run_import("dev-secret-key-change-in-production")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY must be explicitly configured", result.stderr)

    def test_explicit_secret_allows_production_import(self):
        result = self.run_import(
            "test-only-secret-for-configuration-check-"
            "not-a-real-production-secret-32-bytes"
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
