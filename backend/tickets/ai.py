import re
import os
import json
import requests
from dotenv import load_dotenv
from .models import TicketPredictionLog

#  CONFIG  #

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORIES = ["billing", "technical", "authentication", "network", "account"]

#  THRESHOLDS (NOW MEANINGFUL)  #

def get_threshold_for_category(category):
    thresholds = {
        "billing": 0.85,
        "technical": 0.80,
        "authentication": 0.90,
        "network": 0.80,
        "account": 0.80
    }
    return thresholds.get(category, 0.75)

#  PATTERNS  #

PATTERNS = {
    "billing": ["payment", "transaction", "refund", "charged", "money", "pricing", "upi", "deducted"],
    "technical": ["error", "bug", "crash", "not working", "freeze", "broken", "fails"],
    "authentication": ["login", "otp", "password", "verify", "session"],
    "network": ["internet", "wifi", "connection", "slow", "network"],
    "account": ["profile", "account", "settings", "delete"]
}

# PREPROCESS  #

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

#  PRIORITY  #

def get_priority(text):
    text = text.lower()

    score = 0

    #HIGH severity signals
    high_words = ["crash", "failed", "error", "not working", "server error", "network request failed"]
    for w in high_words:
        if w in text:
            score += 3

    # MEDIUM signals
    medium_words = ["slow", "delay", "issue", "problem", "not loading"]
    for w in medium_words:
        if w in text:
            score += 2

    # BUSINESS IMPACT signals
    critical_words = ["payment", "deducted", "refund", "charged", "order not confirmed"]
    for w in critical_words:
        if w in text:
            score += 3

    # FINAL DECISION
    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"
#  RULE ENGINE  #

def rule_engine(text):
    text = text.lower()

    if len(text.split()) < 3:
        return {"category": "other", "confidence": 0.6, "source": "rule"}

    if "password" in text:
        return {"category": "authentication", "confidence": 0.95, "source": "rule"}

    if any(w in text for w in ["login", "otp", "password", "verify", "session"]):
        if not any(w in text for w in ["error", "fail", "crash", "bug"]):
            return {"category": "authentication", "confidence": 0.90, "source": "rule"}

    if any(w in text for w in ["network", "internet", "wifi", "connection"]):
        return {"category": "network", "confidence": 0.88, "source": "rule"}

    if any(w in text for w in ["payment", "refund", "money", "upi", "charged"]):
        return {"category": "billing", "confidence": 0.88, "source": "rule"}

    if any(w in text for w in ["profile", "account", "settings"]):
        return {"category": "account", "confidence": 0.85, "source": "rule"}

    if any(w in text for w in ["error", "bug", "crash", "not working"]):
        return {"category": "technical", "confidence": 0.80, "source": "rule"}

    return None

#  AI #

def call_groq(prompt):
    if not GROQ_API_KEY:
        return None

    try:
        res = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Return ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

    except Exception:
        return None

    return None


def ai_classification(text):
    prompt = f"""
Classify into: billing, technical, authentication, network, account

Return ONLY JSON:
{{
  "category": "...",
  "confidence": 0.xx
}}

Ticket: "{text}"
"""

    result = call_groq(prompt)

    try:
        parsed = json.loads(result)
        if parsed.get("category") in CATEGORIES:
            parsed["source"] = "AI"
            parsed.setdefault("confidence", 0.7)
            return parsed
    except:
        pass

    return None

#  LOGGING  #

def log_prediction(text, result):
    TicketPredictionLog.objects.create(
        text=text,
        predicted_category=result["category"],
        predicted_priority=result["priority"],
        source=result["source"],
        confidence=result["confidence"]
    )

# MAIN PIPELINE  #

def predict_ticket(text):
    clean = preprocess(text)

    rule = rule_engine(clean)
    ai = ai_classification(text)

    # DECISION #

    if rule and ai:
        final = rule if rule["confidence"] >= ai.get("confidence", 0) else ai

    elif rule:
        final = rule

    elif ai:
        final = {
            "category": ai.get("category", "other"),
            "confidence": ai.get("confidence", 0.7),
            "source": "AI"
        }

    else:
        final = {
            "category": "other",
            "confidence": 0.5,
            "source": "fallback"
        }

    # VALIDATION  #

    if final["category"] not in CATEGORIES:
        final["category"] = "other"
        final["confidence"] = 0.5
        final["source"] = "fallback"

    #THRESHOLD ENFORCEMENT #

    threshold = get_threshold_for_category(final["category"])

    if final["confidence"] < threshold:
        final["category"] = "other"
        final["source"] = "threshold_reject"
        final["confidence"] = threshold

    # PRIORITY #

    final["priority"] = get_priority(text)

    #LOGGING  #

    log_prediction(text, final)

    return final