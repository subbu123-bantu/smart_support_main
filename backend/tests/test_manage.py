from importlib import import_module, reload
from unittest.mock import patch

from django.test import SimpleTestCase


class ManagePyTests(SimpleTestCase):
    def test_main_sets_default_settings_module_and_executes_command(self):
        manage = import_module("manage")

        with patch("manage.os.environ.setdefault") as mock_setdefault, patch(
            "django.core.management.execute_from_command_line"
        ) as mock_execute:
            manage.main()

        mock_setdefault.assert_called_once_with("DJANGO_SETTINGS_MODULE", "core.settings")
        mock_execute.assert_called_once()

    def test_main_raises_helpful_import_error_when_django_is_missing(self):
        manage = reload(import_module("manage"))
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "django.core.management":
                raise ImportError("django missing")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(ImportError) as context:
                manage.main()

        self.assertIn("Couldn't import Django", str(context.exception))
