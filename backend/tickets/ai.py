import re
import os
import json
import requests
from dotenv import load_dotenv
from .models import TicketPredictionLog

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORIES = ["billing", "technical", "authentication", "network", "account"]

CATEGORY_KEYWORDS = {
    "billing": [
        "payment", "paid", "refund", "charged", "charge", "billing",
        "invoice", "subscription", "money", "deducted", "transaction",
        "checkout", "premium", "plan", "renewal", "gateway", "unpaid","billed",
        "billing issue", "incorrectly billed", "wrong bill", "overcharged"
    ],
    "technical": [
        "error", "bug", "crash", "crashes", "crashed", "freeze", "freezes",
        "frozen", "broken", "issue", "problem", "not working", "failed",
        "fails", "failure", "exception", "dashboard", "upload", "unexpected",
        "wrong data", "invalid response", "app", "website"
    ],
    "authentication": [
        "login", "log in", "signin", "sign in", "password", "otp",
        "verify", "verification", "session", "credentials", "locked",
        "unlock", "reset link", "access denied"
    ],
    "network": [
        "network", "internet", "wifi", "wi-fi", "connection", "timeout",
        "timed out", "latency", "slow connection", "disconnect",
        "disconnected", "server unreachable", "cannot connect"
    ],
    "account": [
        "account", "profile", "settings", "email address", "phone number",
        "delete account", "remove account", "update profile", "change email",
        "change phone", "registered number", "account settings"
    ],
}

CATEGORY_THRESHOLDS = {
    "billing": 0.80,
    "technical": 0.75,
    "authentication": 0.85,
    "network": 0.78,
    "account": 0.78,
}

URGENT_KEYWORDS = [
    "urgent", "immediately", "asap", "right now", "critical", "blocked",
    "production down", "system down", "cannot access", "money deducted"
]

HIGH_KEYWORDS = [
    "cannot login", "unable to login", "login failed", "account locked",
    "payment failed", "charged twice", "refund", "crash", "crashes",
    "server error", "network error", "timeout", "transaction failed",
    "not working", "service unavailable", "unable to connect"
]

MEDIUM_KEYWORDS = [
    "slow", "delay", "issue", "problem", "not loading", "error",
    "incorrect", "wrong", "failed", "freeze", "disconnect", "bug"
]


def preprocess(text):
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def keyword_score(text, keywords):
    score = 0
    for keyword in keywords:
        if keyword in text:
            if " " in keyword:
                score += 2
            else:
                score += 1
    return score


def best_keyword_category(text):
    scores = {
        category: keyword_score(text, keywords)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score <= 0:
        return None

    confidence = min(0.72 + (best_score * 0.06), 0.92)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "source": "keyword_fallback",
        "scores": scores,
    }


def get_priority(text, category=None):
    text = text.lower()

    urgent_keywords = [
        "urgent", "immediately", "asap", "critical", "production down", "system down"
    ]
    high_keywords = [
        "cannot login", "unable to login", "account locked", "money deducted",
        "charged twice", "payment failed", "refund", "cannot connect",
        "timeout", "network error"
    ]
    medium_keywords = [
        "slow", "issue", "problem", "error", "not loading", "freeze",
        "not working", "failed", "incorrect"
    ]

    if any(k in text for k in urgent_keywords):
        return "urgent"

    if category == "authentication" and any(k in text for k in ["cannot login", "unable to login", "account locked","login", "credentials", "account locked", "password"]):
        return "high"

    if category == "billing" and any(k in text for k in ["charged", "charged twice", "money deducted", "refund", "payment failed", "billing", "billed incorrectly"]):
        return "high"

    if category == "network" and any(k in text for k in ["cannot connect", "timeout", "network error", "disconnect"]):
        return "high"

    if category == "technical" and any(k in text for k in ["crash", "crashes", "broken", "unexpected errors"]):
        return "high"
    
    
    if any(k in text for k in medium_keywords):
        return "medium"
    
    return "low"

def rule_engine(text):
    if len(text.split()) < 2:
        return {
            "category": "other",
            "confidence": 0.45,
            "source": "rule_short_input",
        }

    if any(k in text for k in ["login", "log in", "signin", "sign in", "password", "otp",
                                "verify", "verification", "session", "credentials",
                                "correct credentials", "invalid credentials", "account locked",
                                "unlock", "reset link", "access denied", "login not working"]):
        return {
            "category": "authentication",
            "confidence": 0.95,
            "source": "rule",
        }
    
    if any(k in text for k in ["payment", "refund", "charged", "deducted", "subscription", "invoice", "billing"]):
        return {
            "category": "billing",
            "confidence": 0.93,
            "source": "rule",
        }

    if any(k in text for k in ["network", "internet", "wifi", "connection", "timeout", "cannot connect", "server unreachable"]):
        return {
            "category": "network",
            "confidence": 0.90,
            "source": "rule",
        }
    
    
    
    if any(k in text for k in ["profile", "account settings", "change email", "change phone", "delete account", "registered number"]):
        if not any(k in text for k in ["payment", "billing", "charged", "refund"]):
            return {
                "category": "account",
                "confidence": 0.89,
                "source": "rule",
            }
            
    if any(k in text for k in ["crash", "error", "bug", "not working", "freeze", "broken", "upload", "dashboard", "unexpected"]):
        if not any(k in text for k in["login","log","account"]):
            return {
                "category": "technical",
                "confidence": 0.84,
                "source": "rule",
            }
    

    if any(k in text for k in ["billed incorrectly", "incorrectly billed", "wrong bill", "overcharged"]):
        return {"category": "billing", "confidence": 0.95, "source": "rule"}
    
    if "slow" in text:
        return {
            "category": "network",
            "confidence": 0.75,
            "source": "rule",
        }

    return None


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
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You classify support tickets. "
                            "Return only valid JSON. "
                            "Never explain. "
                            "Choose one category from: billing, technical, authentication, network, account. "
                            "Prefer the closest category instead of rejecting."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
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
Classify this support ticket into exactly one of:
billing, technical, authentication, network, account

Return only JSON in this format:
{{
  "category": "billing|technical|authentication|network|account",
  "confidence": 0.00
}}

Ticket:
{text}
"""
    result = call_groq(prompt)
    if not result:
        return None

    try:
        parsed = json.loads(result)
        category = str(parsed.get("category", "")).lower().strip()
        confidence = float(parsed.get("confidence", 0.70))

        if category in CATEGORIES:
            return {
                "category": category,
                "confidence": round(max(0.0, min(confidence, 0.99)), 2),
                "source": "AI",
            }
    except Exception:
        pass

    return None


def choose_final(rule_result, ai_result, keyword_result):
    candidates = [r for r in [rule_result, ai_result, keyword_result] if r]

    if not candidates:
        return {
            "category": "other",
            "confidence": 0.40,
            "source": "fallback",
        }

    candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    top = candidates[0]

    # If rule and AI agree, boost confidence
    if rule_result and ai_result and rule_result["category"] == ai_result["category"]:
        return {
            "category": rule_result["category"],
            "confidence": round(min(max(rule_result["confidence"], ai_result["confidence"]) + 0.03, 0.99), 2),
            "source": "rule+AI",
        }

    return top


def log_prediction(text, result, ticket=None):
    TicketPredictionLog.objects.create(
        ticket=ticket,
        text=text,
        predicted_category=result["category"],
        predicted_priority=result["priority"],
        source=result["source"],
        confidence=result["confidence"],
    )


def predict_ticket(text):
    clean = preprocess(text)

    rule_result = rule_engine(clean)
    ai_result = ai_classification(text)
    keyword_result = best_keyword_category(clean)

    final = choose_final(rule_result, ai_result, keyword_result)

    if any(k in clean for k in ["payment", "charged", "refund", "billed", "billing", "subscription", "invoice", "deducted"]):
        if final["category"] == "account":
            final["category"] = "billing"
            final["source"] = "billing_override"
            final["confidence"] = max(final["confidence"], 0.9)

    category = final.get("category", "other")
    confidence = final.get("confidence", 0.40)

    if category not in CATEGORIES:
        category = "other"
        confidence = 0.40
        final["source"] = "fallback"

    threshold = CATEGORY_THRESHOLDS.get(category, 0.75)
    if category != "other" and confidence < threshold:
        fallback = keyword_result or rule_result
        if fallback and fallback.get("category") in CATEGORIES:
            category = fallback["category"]
            confidence = max(fallback.get("confidence", 0.72), 0.72)
            final["source"] = "soft_fallback"
        else:
            category = "other"
            confidence = 0.50
            final["source"] = "threshold_reject"

    priority = get_priority(text, category)

    needs_manual_review = (
        confidence < 0.85
        or category == "other"
        or final["source"] in ["fallback", "threshold_reject", "soft_fallback"]
    )

    return {
        "category": category,
        "confidence": round(confidence, 2),
        "source": final["source"],
        "priority": priority,
        "needs_manual_review": needs_manual_review,
    }