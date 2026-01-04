import pytest
from django.core.management import call_command
from django.test import TransactionTestCase


class TestMigrations(TransactionTestCase):
    def test_migrations_complete(self):
        """Verify that all migrations can be applied without error."""
        # This will run migrations on the test database
        try:
            call_command("migrate", "--noinput")
        except Exception as e:
            pytest.fail(f"Migrations failed: {e}")
