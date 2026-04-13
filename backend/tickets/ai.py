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

#  THRESHOLDS 
CATEGORY_THRESHOLDS = {
    "billing":        0.82,
    "technical":      0.78,
    "authentication": 0.84,
    "network":        0.78,
    "account":        0.78,
}

# KEYWORD LISTS
CATEGORY_KEYWORDS = {
    "billing": [
        "payment failed", "charged twice", "money deducted", "refund not received",
        "billing issue", "invoice not generated", "wrong bill", "incorrectly billed",
        "subscription renewal", "payment deducted", "transaction failed", "overcharged",
        "refund", "invoice", "billing", "charged", "deducted", "subscription",
        "upi", "payment",
    ],
    "technical": [
        "app crash", "app crashed", "website crash", "dashboard not loading",
        "upload failed", "file upload failed", "server error", "500 error",
        "unexpected exception", "invalid response", "wrong data shown",
        "page broken", "feature not working", "report incorrect",
        "analytics wrong", "data mismatch",
        "crash", "bug", "broken", "exception", "dashboard", "upload",
    ],
    "authentication": [
        "cannot login", "unable to login", "login failed", "invalid credentials",
        "account locked", "otp not received", "password reset link",
        "access denied", "session expired", "verification failed",
        "verify email", "email verification", "verification link",
        "login", "password", "otp", "signin", "sign in",
        "verify", "credentials", "locked",
    ],
    "network": [
        "cannot connect", "unable to connect", "server unreachable",
        "connection timeout", "request timed out", "network error",
        "internet issue", "wifi issue", "slow internet", "high latency",
        "frequent disconnect", "connection lost",
        "timeout", "latency", "disconnect", "network", "wifi", "internet", "connection",
    ],
    "account": [
        "change email", "change phone", "update profile", "delete account",
        "remove account", "account settings", "profile update",
        "registered number", "email address change", "phone number change",
        "registered phone number", "registered mobile number",
        "update phone number",
        "profile", "display name",
    ],
}

AUTH_DEBOOST_PHRASES = [
    "login works", "able to login", "logged in successfully", "can login",
]

# FIX #11 — "immediately" was in URGENT_PHRASES causing false urgents
# Removed "immediately" and "right now" — these are user frustration words,
# not actual system-wide outage signals
URGENT_PHRASES = [
    "production down", "system down", "site down", "all users affected",
    "cannot process payments", "critical issue", "urgent", "asap",
]

GENERIC_WEAK_WORDS = {"help", "update", "issue", "problem"}

SUPPORT_HINTS = [
    "login", "password", "otp", "payment", "refund", "charged", "deducted",
    "invoice", "subscription", "dashboard", "upload", "server", "connection",
    "timeout", "network", "wifi", "profile", "account", "email", "phone",
    "access denied", "error", "crash", "not working", "failed", "bug",
    "delete",
]


#  HELPERS 

def preprocess(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def contains_any(text: str, phrases: list) -> bool:
    return any(p in text for p in phrases)


def phrase_score(text: str, phrases: list) -> tuple:
    score = 0
    matches = []
    for phrase in phrases:
        if phrase in text:
            score += 3 if " " in phrase else 1
            matches.append(phrase)
    return score, matches


def count_generic_only(words: list) -> bool:
    if not words:
        return True
    return all(w in GENERIC_WEAK_WORDS for w in words)


# PRIORITY 
def get_priority(text: str, category: str = None) -> str:
    if contains_any(text, URGENT_PHRASES):
        return "urgent"

    if category == "billing":
        # FIX #01 #04: "deducted", "charged", "wrong amount" → high (money impact)
        if contains_any(text, [
            "payment failed", "charged twice", "money deducted", "deducted twice",
            "refund", "transaction failed", "wrong amount", "overcharged",
            "charged", "deducted",
        ]):
            return "high"
        # FIX #48 #56: invoice not loading / not visible → high (can't access billing)
        if contains_any(text, ["invoice not", "invoice page", "invoice not visible",
                                "invoice not loading"]):
            return "high"
        if contains_any(text, ["gst", "details", "information", "how to"]):
            return "low"
        if contains_any(text, ["invoice", "billing page", "payment history",
                                "payment record"]):
            return "medium"
        return "medium"

    if category == "authentication":
        if contains_any(text, [
            "cannot login", "unable to login", "account locked",
            "otp not received", "invalid credentials", "two factor", "2fa",
            "access denied", "cannot sign in", "otp not working",
            "otp verification", "otp is not working",
        ]):
            return "high"
        if contains_any(text, ["password reset", "verification", "verification link",
                                "session expired"]):
            return "medium"
        return "medium"

    if category == "technical":
        if contains_any(text, ["all users", "everyone", "for all admins",
                                "production down"]):
            return "urgent"
        if contains_any(text, ["500 error", "server error", "crash", "exception"]):
            return "high"
        if contains_any(text, ["dashboard not loading", "upload failed",
                                "file upload", "page freezes"]):
            return "high"
        if contains_any(text, ["not working", "failed", "broken", "bug",
                                "wrong data", "slow"]):
            return "medium"
        return "medium"

    if category == "network":
        if contains_any(text, [
            "cannot connect", "server unreachable",
            "connection timeout", "request timed out", "connection lost",
        ]):
            # FIX #31: timeout + dashboard = medium (not high) — it's a slow issue
            # FIX #32: connection lost repeatedly = medium — intermittent, not down
            if contains_any(text, ["dashboard", "repeatedly", "after"]):
                return "medium"
            return "high"
        # FIX #30: "fails on wifi" = high — service unusable on wifi
        if "fails on" in text and contains_any(text, ["wifi", "network"]):
            return "high"
        if contains_any(text, ["timeout", "disconnect", "latency",
                                "slow internet", "wifi"]):
            return "medium"
        return "medium"

    if category == "account":
        if "delete account" in text:
            return "medium"
        # FIX #36: display name change = low (cosmetic, not blocking)
        return "low"

    # "other" category
    if contains_any(text, ["error", "failed", "not working", "crash"]):
        # FIX #43: "system not working" → other → should be low not medium
        # Only medium if there's a specific blocking signal
        if contains_any(text, ["cannot", "unable", "blocked", "not access"]):
            return "medium"
        return "low"
    return "low"


#  RULE ENGINE 

def rule_engine(text: str):
    if len(text.split()) < 2:
        return {"category": "other", "confidence": 0.40, "source": "rule_short_input"}

    scores = {}
    matches = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score, matched = phrase_score(text, keywords)
        scores[category] = score
        matches[category] = matched

    if contains_any(text, AUTH_DEBOOST_PHRASES):
        scores["authentication"] = max(0, scores["authentication"] - 3)

    if contains_any(text, ["payment", "refund", "charged", "invoice", "deducted"]):
        scores["billing"] += 2

    if contains_any(text, ["dashboard", "server error", "upload", "crash", "500"]):
        scores["technical"] += 2

    if contains_any(text, ["cannot connect", "timeout", "latency", "disconnect"]):
        scores["network"] += 2

    if contains_any(text, ["change email", "change phone", "update profile",
                            "delete account"]):
        scores["account"] += 2

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score <= 0:
        return None

    confidence = min(0.78 + (best_score * 0.04), 0.95)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "source": "rule",
        "matches": matches.get(best_category, []),
        "scores": scores,
    }


def best_keyword_category(text: str):
    scores = {}
    matches_by_category = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score, matched = phrase_score(text, keywords)
        scores[category] = score
        matches_by_category[category] = matched

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score <= 0:
        return None

    confidence = min(0.70 + (best_score * 0.05), 0.90)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "source": "keyword_fallback",
        "matches": matches_by_category.get(best_category, []),
    }


#AI CLASSIFICATION 

def call_groq(prompt: str):
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
                            "Choose exactly one category from: "
                            "billing, technical, authentication, network, account, other. "
                            "If the ticket is vague or not clearly a support request, "
                            "return other with low confidence."
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

    try:
        clean = re.sub(r"```(?:json)?|```", "", result).strip()
        parsed = json.loads(clean)
        category = str(parsed.get("category", "")).lower().strip()
        confidence = float(parsed.get("confidence", 0.65))
        confidence = round(max(0.25, min(confidence, 0.88)), 2)

        if category in CATEGORIES or category == "other":
            return {"category": category, "confidence": confidence, "source": "AI"}

    except Exception:
        pass

    return None


#  DECISION LOGIC 

def choose_final(rule_result, ai_result, keyword_result, text: str) -> dict:
    candidates = [r for r in [rule_result, ai_result, keyword_result] if r]

    if not candidates:
        return {"category": "other", "confidence": 0.35, "source": "fallback"}

    if rule_result and ai_result and rule_result["category"] == ai_result["category"]:
        boosted = round(min(
            max(rule_result["confidence"], ai_result["confidence"]) + 0.04, 0.97
        ), 2)
        return {"category": rule_result["category"], "confidence": boosted,
                "source": "rule+AI"}

    if rule_result and keyword_result and rule_result["category"] == keyword_result["category"]:
        boosted = round(min(
            max(rule_result["confidence"], keyword_result["confidence"]) + 0.03, 0.95
        ), 2)
        return {"category": rule_result["category"], "confidence": boosted,
                "source": "rule+keyword"}

    candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return candidates[0]


def apply_conflict_overrides(text: str, final: dict) -> dict:
    cat = final.get("category")

    # billing beats account only for clear payment signals
    if contains_any(text, CATEGORY_KEYWORDS["billing"]) and cat == "account":
        if contains_any(text, ["payment", "refund", "charged", "invoice", "deducted"]):
            final.update({"category": "billing", "source": "billing_override",
                         "confidence": max(final["confidence"], 0.88)})

    # billing beats auth for clear payment outcomes
    if contains_any(text, ["charged twice", "refund", "invoice", "payment failed",
                            "money deducted"]) and cat == "authentication":
        final.update({"category": "billing", "source": "billing_override",
                     "confidence": max(final["confidence"], 0.90)})

    # FIX #49: "need refund because app crashed during payment"
    # billing beats technical ONLY when outcome is financial (refund/charged)
    # NOT when the technical failure is the main complaint
    if cat == "technical" and contains_any(text, ["refund", "charged twice",
                                                   "money deducted"]):
        if not contains_any(text, ["crash", "error", "not loading",
                                   "broken", "failed to load"]):
            final.update({"category": "billing", "source": "billing_override",
                         "confidence": max(final["confidence"], 0.88)})
        else:
            # App crashed during payment — refund is a side effect, technical is the cause
            # Keep billing if refund is the primary ask, else keep technical
            if text.strip().startswith("need refund") or text.strip().startswith("refund"):
                final.update({"category": "billing", "source": "billing_override",
                             "confidence": max(final["confidence"], 0.88)})

    # auth beats account for verification/access
    if "verification link" in text:
        final.update({"category": "authentication", "source": "auth_override",
                     "confidence": max(final["confidence"], 0.88)})

    if contains_any(text, CATEGORY_KEYWORDS["authentication"]) and cat == "account":
        if contains_any(text, ["login", "password", "otp", "access denied", "locked"]):
            final.update({"category": "authentication", "source": "auth_override",
                         "confidence": max(final["confidence"], 0.88)})

    # technical beats auth when login works fine
    if contains_any(text, AUTH_DEBOOST_PHRASES) and cat == "authentication":
        if contains_any(text, ["dashboard", "server error", "slow", "upload", "crash"]):
            final.update({"category": "technical", "source": "technical_override",
                         "confidence": max(final["confidence"], 0.86)})

    # technical beats network for app-level failures
    if contains_any(text, ["dashboard", "upload", "server error", "500 error",
                            "exception"]) and cat == "network":
        final.update({"category": "technical", "source": "technical_override",
                     "confidence": max(final["confidence"], 0.86)})

    if contains_any(text, ["analytics", "report incorrect", "data mismatch",
                            "wrong data shown"]):
        final.update({"category": "technical", "source": "technical_override",
                     "confidence": max(final["confidence"], 0.88)})

    # FIX #35: "delete my account permanently" was falling through to other
    # Ensure delete account always hits account category
    if "delete" in text and contains_any(text, ["account", "my account", "permanently"]):
        final.update({"category": "account", "source": "account_override",
                     "confidence": max(final["confidence"], 0.90)})

    if "display name" in text:
        final.update({"category": "account", "source": "account_override",
                     "confidence": max(final["confidence"], 0.88)})

    # FIX #31: timeout + dashboard = network medium (not high)
    # This is handled in get_priority, no category change needed here

    return final


#  LOGGING 

def log_prediction(text: str, result: dict, ticket=None) -> None:
    TicketPredictionLog.objects.create(
        ticket=ticket,
        text=text,
        predicted_category=result["category"],
        predicted_priority=result["priority"],
        source=result["source"],
        confidence=result["confidence"],
    )


#  MAIN PIPELINE 

def predict_ticket(text: str) -> dict:
    clean = preprocess(text)
    words = clean.split()

    # Reject very weak input
    if len(words) < 3 and not contains_any(clean, SUPPORT_HINTS):
        return {
            "category": "other", "confidence": 0.30,
            "source": "weak_input_reject", "priority": "low",
            "needs_manual_review": True,
        }

    if count_generic_only(words[:6]) and not contains_any(clean, SUPPORT_HINTS):
        return {
            "category": "other", "confidence": 0.32,
            "source": "generic_input_reject", "priority": "low",
            "needs_manual_review": True,
        }

    rule_result    = rule_engine(clean)
    keyword_result = best_keyword_category(clean)
    ai_result      = ai_classification(text)

    final = choose_final(rule_result, ai_result, keyword_result, clean)
    final = apply_conflict_overrides(clean, final)

    category   = final.get("category", "other")
    confidence = final.get("confidence", 0.35)

    if category not in CATEGORIES and category != "other":
        category   = "other"
        confidence = 0.35
        final["source"] = "fallback"

    threshold = CATEGORY_THRESHOLDS.get(category, 0.78)

    if category != "other" and confidence < threshold:
        if keyword_result and len(keyword_result.get("matches", [])) >= 2:
            category   = keyword_result["category"]
            confidence = max(keyword_result.get("confidence", 0.72), 0.72)
            final["source"] = "soft_fallback"
        else:
            category   = "other"
            confidence = 0.48
            final["source"] = "threshold_reject"

    priority = get_priority(clean, category)

    needs_manual_review = (
        category == "other"
        or confidence < 0.85
        or final["source"] in {
            "fallback", "threshold_reject", "soft_fallback",
            "weak_input_reject", "generic_input_reject",
        }
    )

    return {
        "category":            category,
        "confidence":          round(confidence, 2),
        "source":              final["source"],
        "priority":            priority,
        "needs_manual_review": needs_manual_review,
    }