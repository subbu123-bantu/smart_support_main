import csv
import logging
import os
from functools import lru_cache
from pathlib import Path

from .ai_constants import CATEGORIES

logger = logging.getLogger(__name__)

DATASET_FILE = Path(__file__).with_name("ticket_ai_dataset.csv")
DATASET_PATH = Path(os.environ.get("AI_DATASET_CSV", DATASET_FILE))
VALID_CATEGORIES = set(CATEGORIES) | {"other"}


def _normalize_confidence(raw_confidence: str) -> float:
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        return 0.5

    return round(max(0.0, min(confidence, 1.0)), 2)


@lru_cache(maxsize=1)
def load_examples_from_csv():
    examples = []

    if not DATASET_PATH.exists():
        logger.warning("AI dataset CSV not found: %s", DATASET_PATH)
        return examples

    with DATASET_PATH.open(newline="", encoding="utf-8") as dataset_file:
        reader = csv.DictReader(dataset_file)

        for row_number, row in enumerate(reader, start=2):
            text = (row.get("text") or "").strip()
            category = (row.get("category") or "").strip().lower()

            if not text:
                logger.warning("Skipping empty dataset text at row %s", row_number)
                continue

            if category not in VALID_CATEGORIES:
                logger.warning(
                    "Skipping dataset row %s with invalid category: %s",
                    row_number,
                    category,
                )
                continue

            examples.append(
                {
                    "text": text,
                    "category": category,
                    "confidence": _normalize_confidence(row.get("confidence")),
                }
            )

    return examples


def format_examples_for_prompt() -> str:
    rendered = []

    for example in load_examples_from_csv():
        rendered.append(
            "\n".join(
                [
                    f'Ticket: {example["text"]}',
                    "{",
                    f'  "category": "{example["category"]}",',
                    f'  "confidence": {example["confidence"]:.2f}',
                    "}",
                ]
            )
        )

    return "\n\n".join(rendered)
