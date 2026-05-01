import csv
import tempfile
from importlib import import_module
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

dataset_generator = import_module("scripts.dataset_generator")
ai_dataset = import_module("tickets.ai.ai_dataset")


class SequenceRng:
    def __init__(self, *, random_values=None, choice_values=None, uniform_values=None):
        self.random_values = list(random_values or [])
        self.choice_values = list(choice_values or [])
        self.uniform_values = list(uniform_values or [])

    def random(self):
        return self.random_values.pop(0)

    def choice(self, _options):
        return self.choice_values.pop(0)

    def uniform(self, _start, _end):
        return self.uniform_values.pop(0)


class DatasetGeneratorTests(SimpleTestCase):
    def test_add_noise_replaces_matching_words_when_threshold_is_met(self):
        rng = SequenceRng(random_values=[0.1, 0.9], choice_values=["paymnt"])

        with patch.object(dataset_generator, "RNG", rng):
            result = dataset_generator.add_noise("payment failed")

        self.assertEqual(result, "paymnt failed")

    def test_generate_ticket_can_switch_to_hinglish_and_append_extra(self):
        rng = SequenceRng(
            random_values=[0.5, 0.1, 0.2],
            choice_values=[
                "Payment failed but money deducted",
                "refund abhi tak nahi mila",
                "Charged twice for same order",
            ],
        )

        with patch.object(dataset_generator, "RNG", rng):
            result = dataset_generator.generate_ticket("billing")

        self.assertEqual(result, "refund abhi tak nahi mila and also Charged twice for same order")

    def test_generate_confidence_uses_category_ranges(self):
        rng = SequenceRng(uniform_values=[0.33, 0.88])

        with patch.object(dataset_generator, "RNG", rng):
            other_confidence = dataset_generator.generate_confidence("other")
            billing_confidence = dataset_generator.generate_confidence("billing")

        self.assertEqual(other_confidence, 0.33)
        self.assertEqual(billing_confidence, 0.88)

    def test_generate_priority_uses_preprocess_before_priority_lookup(self):
        with (
            patch.object(dataset_generator, "preprocess", return_value="normalized text") as mock_preprocess,
            patch.object(dataset_generator, "get_priority", return_value="high") as mock_get_priority,
        ):
            result = dataset_generator.generate_priority("billing", "Raw TEXT")

        self.assertEqual(result, "high")
        mock_preprocess.assert_called_once_with("Raw TEXT")
        mock_get_priority.assert_called_once_with("normalized text", "billing")

    def test_generate_dataset_writes_expected_csv_rows(self):
        output_path = Path("tests") / "tmp_dataset_generator.csv"
        self.addCleanup(output_path.unlink, missing_ok=True)

        with (
            patch.object(dataset_generator, "RNG", SequenceRng(choice_values=["billing", "other"])),
            patch.object(dataset_generator, "generate_ticket", side_effect=["Payment failed", "Hello"]) as mock_ticket,
            patch.object(dataset_generator, "generate_confidence", side_effect=[0.91, 0.25]) as mock_confidence,
            patch.object(dataset_generator, "generate_priority", side_effect=["high", "low"]) as mock_priority,
        ):
            dataset_generator.generate_dataset(n=2, filename=output_path)

        with output_path.open(newline="", encoding="utf-8") as created_file:
            rows = list(csv.reader(created_file))

        self.assertEqual(
            rows,
            [
                ["text", "category", "confidence", "priority"],
                ["Payment failed", "billing", "0.91", "high"],
                ["Hello", "other", "0.25", "low"],
            ],
        )
        self.assertEqual(mock_ticket.call_count, 2)
        self.assertEqual(mock_confidence.call_count, 2)
        self.assertEqual(mock_priority.call_count, 2)


class AiDatasetTests(SimpleTestCase):
    def setUp(self):
        ai_dataset.load_examples_from_csv.cache_clear()
        self.addCleanup(ai_dataset.load_examples_from_csv.cache_clear)

    def test_load_examples_returns_empty_list_when_csv_is_missing(self):
        missing_path = Path(tempfile.gettempdir()) / "missing-ai-dataset.csv"

        with (
            patch.object(ai_dataset, "DATASET_PATH", missing_path),
            patch.object(ai_dataset, "logger") as mock_logger,
        ):
            examples = ai_dataset.load_examples_from_csv()

        self.assertEqual(examples, [])
        mock_logger.warning.assert_called_once()

    def test_load_examples_skips_invalid_rows_and_normalizes_confidence(self):
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".csv", delete=False) as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(["text", "category", "confidence"])
            writer.writerow(["Payment failed", "billing", "1.7"])
            writer.writerow(["", "billing", "0.3"])
            writer.writerow(["Hello", "invalid", "0.4"])
            writer.writerow(["Need help", "other", "not-a-number"])
            dataset_path = Path(temp_file.name)

        with (
            patch.object(ai_dataset, "DATASET_PATH", dataset_path),
            patch.object(ai_dataset, "logger") as mock_logger,
        ):
            examples = ai_dataset.load_examples_from_csv()

        self.assertEqual(
            examples,
            [
                {"text": "Payment failed", "category": "billing", "confidence": 1.0},
                {"text": "Need help", "category": "other", "confidence": 0.5},
            ],
        )
        self.assertEqual(mock_logger.warning.call_count, 2)

    def test_format_examples_for_prompt_renders_loaded_examples(self):
        examples = [
            {"text": "Payment failed", "category": "billing", "confidence": 0.91},
            {"text": "Router timeout", "category": "network", "confidence": 0.75},
        ]

        with patch.object(ai_dataset, "load_examples_from_csv", return_value=examples):
            rendered = ai_dataset.format_examples_for_prompt()

        self.assertIn('Ticket: Payment failed', rendered)
        self.assertIn('"category": "billing"', rendered)
        self.assertIn('"confidence": 0.91', rendered)
        self.assertIn('Ticket: Router timeout', rendered)
