from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from tickets.management.commands.test_ticket_ai import TEST_CASES


class TicketAiCommandTests(SimpleTestCase):
    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_prints_summary(self, mock_predict_ticket):
        mock_predict_ticket.return_value = {
            "category": "billing",
            "priority": "high",
            "source": "rule",
            "confidence": 0.91,
            "needs_manual_review": False,
        }

        output = StringIO()
        call_command("test_ticket_ai", stdout=output)
        rendered = output.getvalue()

        self.assertIn("MODE: hybrid", rendered)
        self.assertIn("TOTAL TESTS: 43", rendered)
        self.assertIn("CATEGORY ACCURACY:", rendered)
        self.assertIn("PRIORITY ACCURACY:", rendered)

    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_failures_only_filters_passing_cases(self, mock_predict_ticket):
        mock_predict_ticket.side_effect = [
            {
                "category": expected_category,
                "priority": expected_priority,
                "source": "rule",
                "confidence": 0.91,
                "needs_manual_review": False,
            }
            for _, expected_category, expected_priority in TEST_CASES
        ]

        output = StringIO()
        call_command("test_ticket_ai", "--failures-only", stdout=output)
        rendered = output.getvalue()

        self.assertNotIn("TEXT:", rendered)
        self.assertIn("TOTAL TESTS: 43", rendered)

    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_no_ai_prints_local_mode(self, mock_predict_ticket):
        mock_predict_ticket.return_value = {
            "category": "billing",
            "priority": "high",
            "source": "rule",
            "confidence": 0.91,
            "needs_manual_review": False,
        }

        output = StringIO()
        call_command("test_ticket_ai", "--no-ai", stdout=output)
        rendered = output.getvalue()

        self.assertIn("MODE: local-rules-only", rendered)
