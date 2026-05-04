import json
import logging
import os
import re
import time

import requests
from dotenv import load_dotenv
from requests import RequestException

from .ai_constants import CATEGORIES
from .ai_dataset import format_examples_for_prompt

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = os.environ.get(
    "GROQ_URL",
    "https://api.groq.com/openai/v1/chat/completions",
)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_RATE_LIMIT_COOLDOWN = int(os.environ.get("GROQ_RATE_LIMIT_COOLDOWN", "60"))
GROQ_FAILURE_COOLDOWN = int(os.environ.get("GROQ_FAILURE_COOLDOWN", "30"))
GROQ_REQUEST_FAILED_LOG = "Groq request failed: %s"
_groq_cooldown_until = 0.0


def _retry_after_seconds(response) -> int:
    if response is None:
        return GROQ_RATE_LIMIT_COOLDOWN

    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return GROQ_RATE_LIMIT_COOLDOWN

    try:
        return max(int(retry_after), 1)
    except (TypeError, ValueError):
        return GROQ_RATE_LIMIT_COOLDOWN


def _start_cooldown(seconds: int) -> None:
    global _groq_cooldown_until
    _groq_cooldown_until = time.monotonic() + max(seconds, 1)


def _in_cooldown() -> bool:
    return time.monotonic() < _groq_cooldown_until


class GroqTicketClassifier:
    def __init__(self, api_key=None, url=None, model=None):
        self.api_key = api_key
        self.url = url
        self.model = model

    @property
    def resolved_api_key(self):
        return GROQ_API_KEY if self.api_key is None else self.api_key

    @property
    def resolved_url(self):
        return GROQ_URL if self.url is None else self.url

    @property
    def resolved_model(self):
        return GROQ_MODEL if self.model is None else self.model

    def build_payload(self, prompt: str) -> dict:
        return {
            "model": self.resolved_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You classify support tickets. "
                        "Return only valid JSON. "
                        "Choose exactly one category from: "
                        "billing, technical, authentication, network, account, other. "
                        "If the ticket is vague or not clearly a support request, "
                        "return other with low confidence. "
                        "Use the examples provided by the user as reference patterns."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }

    def build_prompt(self, text: str) -> str:
        return f"""Classify this support ticket into exactly one of:
billing, technical, authentication, network, account, other

Reference examples:
{format_examples_for_prompt()}

Return only JSON:
{{
  "category": "billing|technical|authentication|network|account|other",
  "confidence": 0.00
}}

Ticket:
{text}"""

    def call(self, prompt: str):
        api_key = self.resolved_api_key
        if not api_key:
            return None

        if _in_cooldown():
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.resolved_url,
                headers=headers,
                json=self.build_payload(prompt),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except RequestException as error:
            response = getattr(error, "response", None)
            if response is not None and response.status_code == 429:
                cooldown_seconds = _retry_after_seconds(response)
                _start_cooldown(cooldown_seconds)
                logger.warning(
                    "Groq rate limited; skipping AI calls for %ss",
                    cooldown_seconds,
                )
                return None
            _start_cooldown(GROQ_FAILURE_COOLDOWN)
            logger.warning(GROQ_REQUEST_FAILED_LOG, error)
            return None
        except (KeyError, IndexError, TypeError, ValueError) as error:
            logger.warning("Unexpected Groq response structure: %s", error)
            return None

CLASSIFIER = GroqTicketClassifier()


def build_groq_payload(prompt: str) -> dict:
    return CLASSIFIER.build_payload(prompt)


def build_groq_prompt(text: str) -> str:
    return CLASSIFIER.build_prompt(text)


def call_groq(prompt: str):
    return CLASSIFIER.call(prompt)


def parse_ai_result(result: str):
    try:
        cleaned = re.sub(r"```(?:json)?```", "", result).strip()
        parsed = json.loads(cleaned)

        category = str(parsed.get("category", "")).lower().strip()
        confidence = float(parsed.get("confidence", 0.65))
        confidence = round(max(0.25, min(confidence, 0.88)), 2)

        if category in CATEGORIES or category == "other":
            return {
                "category": category,
                "confidence": confidence,
                "source": "AI",
            }
    except (TypeError, ValueError) as error:
        logger.warning("Failed to parse Groq response: %s | raw=%r", error, result)

    return None


def ai_classification(text: str):
    prompt = build_groq_prompt(text)
    result = call_groq(prompt)
    if not result:
        return None

    return parse_ai_result(result)
