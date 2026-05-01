import csv
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


def write_dataset(rows):
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="utf-8",
        suffix=".csv",
        delete=False,
    )

    with temp_file:
        writer = csv.writer(temp_file)
        writer.writerow(["text", "category", "priority"])
        writer.writerows(rows)

    return Path(temp_file.name)


class TicketAiCommandTests(SimpleTestCase):
    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_prints_summary(self, mock_predict_ticket):
        dataset_path = write_dataset(
            [
                ["Payment failed", "billing", "high"],
                ["OTP not received", "authentication", "high"],
            ]
        )
        self.addCleanup(dataset_path.unlink)

        mock_predict_ticket.return_value = {
            "category": "billing",
            "priority": "high",
            "source": "rule",
            "confidence": 0.91,
            "needs_manual_review": False,
        }

        output = StringIO()
        call_command("test_ticket_ai", "--dataset", str(dataset_path), stdout=output)
        rendered = output.getvalue()

        self.assertIn("MODE: hybrid", rendered)
        self.assertIn("TOTAL ROWS TESTED: 2", rendered)
        self.assertIn("CATEGORY ACCURACY:", rendered)
        self.assertIn("PRIORITY ACCURACY:", rendered)

    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_failures_only_filters_passing_cases(self, mock_predict_ticket):
        dataset_path = write_dataset(
            [
                ["Payment failed", "billing", "high"],
                ["OTP not received", "authentication", "high"],
            ]
        )
        self.addCleanup(dataset_path.unlink)

        mock_predict_ticket.side_effect = [
            {
                "category": "billing",
                "priority": "high",
                "source": "rule",
                "confidence": 0.91,
                "needs_manual_review": False,
            },
            {
                "category": "authentication",
                "priority": "high",
                "source": "rule",
                "confidence": 0.91,
                "needs_manual_review": False,
            },
        ]

        output = StringIO()
        call_command(
            "test_ticket_ai",
            "--dataset",
            str(dataset_path),
            "--failures-only",
            stdout=output,
        )
        rendered = output.getvalue()

        self.assertNotIn("TEXT:", rendered)
        self.assertIn("TOTAL ROWS TESTED: 2", rendered)

    @patch("tickets.management.commands.test_ticket_ai.predict_ticket")
    def test_command_no_ai_prints_local_mode(self, mock_predict_ticket):
        dataset_path = write_dataset([["Payment failed", "billing", "high"]])
        self.addCleanup(dataset_path.unlink)

        mock_predict_ticket.return_value = {
            "category": "billing",
            "priority": "high",
            "source": "rule",
            "confidence": 0.91,
            "needs_manual_review": False,
        }

        output = StringIO()
        call_command(
            "test_ticket_ai",
            "--dataset",
            str(dataset_path),
            "--no-ai",
            stdout=output,
        )
        rendered = output.getvalue()

        self.assertIn("MODE: local-rules-only", rendered)
