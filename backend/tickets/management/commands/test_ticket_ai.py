import csv
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from django.core.management.base import BaseCommand, CommandError

from tickets.ai import predict_ticket
from tickets.ai.ai_dataset import DATASET_PATH


def load_test_cases(csv_path: Path):
    test_cases = []

    with csv_path.open(newline="", encoding="utf-8") as dataset_file:
        reader = csv.DictReader(dataset_file)

        for row in reader:
            text = (row.get("text") or "").strip()
            expected_category = (row.get("category") or "").strip().lower()
            expected_priority = (row.get("priority") or "").strip().lower()

            if not text or not expected_category:
                continue

            test_cases.append(
                {
                    "text": text,
                    "expected_category": expected_category,
                    "expected_priority": expected_priority or None,
                }
            )

    return test_cases


class Command(BaseCommand):
    help = "Run ticket AI evaluation directly against the dataset CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--failures-only",
            action="store_true",
            help="Only print rows where category or priority does not match.",
        )
        parser.add_argument(
            "--no-ai",
            action="store_true",
            help="Disable AI classification and benchmark only local rule-based logic.",
        )
        parser.add_argument(
            "--dataset",
            default=str(DATASET_PATH),
            help="Path to the CSV dataset file.",
        )

    def _validate_dataset(self, dataset_path: Path):
        if not dataset_path.exists():
            raise CommandError(f"Dataset CSV not found: {dataset_path}")

        test_cases = load_test_cases(dataset_path)
        if not test_cases:
            raise CommandError(f"No usable rows found in dataset CSV: {dataset_path}")

        return test_cases

    def _runner(self, no_ai: bool):
        if no_ai:
            return patch("tickets.ai.ai.ai_classification", return_value=None)
        return nullcontext()

    def _evaluate_case(self, case: dict):
        result = predict_ticket(case["text"])
        got_category = result.get("category")
        got_priority = result.get("priority")
        expected_priority = case["expected_priority"]
        category_ok = got_category == case["expected_category"]
        priority_ok = expected_priority is None or got_priority == expected_priority

        return {
            "result": result,
            "got_category": got_category,
            "got_priority": got_priority,
            "category_ok": category_ok,
            "priority_ok": priority_ok,
        }

    def _update_totals(self, totals: dict, case: dict, evaluation: dict):
        if evaluation["category_ok"]:
            totals["category_correct"] += 1

        if case["expected_priority"] is None:
            return

        totals["priority_total"] += 1
        if evaluation["priority_ok"]:
            totals["priority_correct"] += 1

    def _should_print_case(self, failures_only: bool, evaluation: dict) -> bool:
        return not (failures_only and evaluation["category_ok"] and evaluation["priority_ok"])

    def _print_case(self, case: dict, evaluation: dict):
        result = evaluation["result"]

        self.stdout.write("")
        self.stdout.write(f"TEXT: {case['text']!r}")
        self.stdout.write(f"EXPECTED CATEGORY: {case['expected_category']}")
        self.stdout.write(f"GOT CATEGORY     : {evaluation['got_category']}")
        if case["expected_priority"] is not None:
            self.stdout.write(f"EXPECTED PRIORITY: {case['expected_priority']}")
        self.stdout.write(f"GOT PRIORITY     : {evaluation['got_priority']}")
        self.stdout.write(f"SOURCE           : {result.get('source')}")
        self.stdout.write(f"CONF             : {result.get('confidence')}")
        self.stdout.write(f"REVIEW           : {result.get('needs_manual_review')}")
        self.stdout.write(
            f"PASS             : {'OK' if evaluation['category_ok'] and evaluation['priority_ok'] else 'FAIL'}"
        )

    def _print_summary(self, *, no_ai: bool, dataset_path: Path, test_cases: list, totals: dict):
        total = len(test_cases)
        category_accuracy = round((totals["category_correct"] / total) * 100, 2) if total else 0
        priority_total = totals["priority_total"]
        priority_accuracy = (
            round((totals["priority_correct"] / priority_total) * 100, 2)
            if priority_total
            else None
        )

        self.stdout.write("")
        self.stdout.write(f"MODE: {'local-rules-only' if no_ai else 'hybrid'}")
        self.stdout.write(f"DATASET: {dataset_path}")
        self.stdout.write("==============================")
        self.stdout.write(f"TOTAL ROWS TESTED: {total}")
        self.stdout.write(f"CATEGORY ACCURACY: {category_accuracy} %")
        if priority_accuracy is None:
            self.stdout.write("PRIORITY ACCURACY: skipped (no priority column in dataset)")
        else:
            self.stdout.write(f"PRIORITY ACCURACY: {priority_accuracy} %")
        self.stdout.write("==============================")

    def handle(self, *args, **options):
        failures_only = options["failures_only"]
        no_ai = options["no_ai"]
        dataset_path = Path(options["dataset"]).resolve()
        test_cases = self._validate_dataset(dataset_path)
        totals = {
            "category_correct": 0,
            "priority_correct": 0,
            "priority_total": 0,
        }

        with self._runner(no_ai):
            for case in test_cases:
                evaluation = self._evaluate_case(case)
                self._update_totals(totals, case, evaluation)
                if self._should_print_case(failures_only, evaluation):
                    self._print_case(case, evaluation)

        self._print_summary(
            no_ai=no_ai,
            dataset_path=dataset_path,
            test_cases=test_cases,
            totals=totals,
        )
