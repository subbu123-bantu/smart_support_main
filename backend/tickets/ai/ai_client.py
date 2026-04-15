import json
import logging
import os
import re

import requests
from dotenv import load_dotenv
from requests import RequestException

from .ai_constants import CATEGORIES

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = os.environ.get(
    "GROQ_URL",
    "https://api.groq.com/openai/v1/chat/completions",
)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def build_groq_payload(prompt: str) -> dict:
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
                    "return other with low confidence."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }


def call_groq(prompt: str):
    if not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=build_groq_payload(prompt),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except RequestException as error:
        logger.warning("Groq request failed: %s", error)
        return None
    except (KeyError, IndexError, TypeError, ValueError) as error:
        logger.warning("Unexpected Groq response structure: %s", error)
        return None


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
    prompt = f"""Classify this support ticket into exactly one of:
billing, technical, authentication, network, account, other

Return only JSON:
{{
  "category": "billing|technical|authentication|network|account|other",
  "confidence": 0.00
}}

Ticket:
{text}"""

    result = call_groq(prompt)
    if not result:
        return None

    return parse_ai_result(result)