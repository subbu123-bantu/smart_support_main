import json
import logging
import os
import re

import httpx
from dotenv import load_dotenv

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
GROQ_REQUEST_FAILED_LOG = "Groq request failed: %s"


class GroqTicketClassifier:
    def build_payload(self, prompt: str) -> dict:
        return {
            "model": GROQ_MODEL,
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

    async def call(self, prompt: str):
        if not GROQ_API_KEY:
            return None

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    GROQ_URL,
                    headers=headers,
                    json=self.build_payload(prompt),
                )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as error:
            response = error.response
            if response is not None and response.status_code == 429:
                logger.warning(
                    "Groq rate limited; request skipped",
                )
                return None
            logger.warning(GROQ_REQUEST_FAILED_LOG, error)
            return None
        except httpx.RequestError as error:
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


async def call_groq_async(prompt: str):
    return await CLASSIFIER.call(prompt)


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


async def ai_classification_async(text: str):
    prompt = build_groq_prompt(text)
    result = await call_groq_async(prompt)
    if not result:
        return None

    return parse_ai_result(result)
