import re
import os
import json
import logging
import requests
from dotenv import load_dotenv
from .models import TicketPredictionLog

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORIES = ["billing", "technical", "authentication", "network", "account"]

# ─── THRESHOLDS ───────────────────────────────────────────────────────────────
CATEGORY_THRESHOLDS = {
    "billing":        0.82,
    "technical":      0.78,
    "authentication": 0.84,
    "network":        0.78,
    "account":        0.78,
}

# ─── NAMED CONSTANTS (replaces fragile index access) ─────────────────────────
PAYMENT_FAILED    = "payment failed"
CHARGED_TWICE     = "charged twice"
MONEY_DEDUCTED    = "money deducted"
SERVER_ERROR      = "server error"
ERROR_500         = "500 error"
ACCESS_DENIED     = "access denied"
VERIFICATION_LINK = "verification link"
CANNOT_CONNECT    = "cannot connect"
DELETE_ACCOUNT    = "delete account"
NOT_WORKING       = "not working"

# ─── KEYWORD LISTS ────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "billing": [
        PAYMENT_FAILED, CHARGED_TWICE, MONEY_DEDUCTED,
        "refund not received", "billing issue", "invoice not generated",
        "wrong bill", "incorrectly billed", "subscription renewal",
        "payment deducted", "transaction failed", "overcharged",
        "refund", "invoice", "billing", "charged", "deducted",
        "subscription", "upi", "payment",
    ],
    "technical": [
        SERVER_ERROR, ERROR_500,
        "app crash", "app crashed", "website crash", "dashboard not loading",
        "upload failed", "file upload failed", "dashboard", "upload",
        "unexpected exception", "invalid response", "wrong data shown",
        "page broken", "feature not working", "report incorrect",
        "analytics wrong", "data mismatch", "crash", "bug", "broken", "exception",
    ],
    "authentication": [
        ACCESS_DENIED, VERIFICATION_LINK,
        "cannot login", "unable to login", "login failed", "invalid credentials",
        "account locked", "otp not received", "password reset link",
        "session expired", "verification failed", "verify email",
        "email verification", "sign in", "locked",
        "login", "password", "otp", "signin", "verify", "credentials",
    ],
    "network": [
        CANNOT_CONNECT,
        "unable to connect", "server unreachable", "connection timeout",
        "request timed out", "network error", "internet issue", "wifi issue",
        "slow internet", "high latency", "frequent disconnect", "connection lost",
        "timeout", "latency", "disconnect", "network", "wifi", "internet", "connection",
    ],
    "account": [
        DELETE_ACCOUNT,
        "change email", "change phone", "update profile", "remove account",
        "account settings", "profile update", "registered number",
        "email address change", "phone number change",
        "registered phone number", "registered mobile number",
        "update phone number", "profile", "display name",
    ],
}

AUTH_DEBOOST_PHRASES = [
    "login works", "able to login", "logged in successfully", "can login",
]

URGENT_PHRASES = [
    "production down", "system down", "site down", "all users affected",
    "cannot process payments", "critical issue", "urgent", "asap",
]

GENERIC_WEAK_WORDS = {"help", "update", "issue", "problem"}

SUPPORT_HINTS = [
    "login", "password", "otp", "payment", "refund", "charged", "deducted",
    "invoice", "subscription", "dashboard", "upload", "server", "connection",
    "timeout", "network", "wifi", "profile", "account", "email", "phone",
    ACCESS_DENIED, "error", "crash", NOT_WORKING, "failed", "bug", "delete",
]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

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


# ─── PRIORITY HELPERS ─────────────────────────────────────────────────────────

def bill_category(text: str) -> str:
    if contains_any(text, [
        PAYMENT_FAILED, CHARGED_TWICE, MONEY_DEDUCTED, "deducted twice",
        "refund", "transaction failed", "wrong amount", "overcharged",
        "charged", "deducted",
    ]):
        return "high"
    if contains_any(text, [
        "invoice not", "invoice page", "invoice not visible", "invoice not loading",
    ]):
        return "high"
    if contains_any(text, ["gst", "details", "information", "how to"]):
        return "low"
    if contains_any(text, ["invoice", "billing page", "payment history", "payment record"]):
        return "medium"
    return "medium"


def tech_category(text: str) -> str:
    if contains_any(text, ["all users", "everyone", "for all admins", "production down"]):
        return "urgent"
    if contains_any(text, [SERVER_ERROR, ERROR_500, "crash", "exception"]):
        return "high"
    if contains_any(text, ["dashboard not loading", "upload failed", "file upload", "page freezes"]):
        return "high"
    if contains_any(text, [NOT_WORKING, "failed", "broken", "bug", "wrong data", "slow"]):
        return "medium"
    return "medium"


def network_category(text: str) -> str:
    # FIX: nested correctly — "dashboard"/"repeatedly"/"after" downgrades
    # from high to medium only when the high condition was triggered
    if contains_any(text, [
        CANNOT_CONNECT, "server unreachable",
        "connection timeout", "request timed out", "connection lost",
    ]):
        if contains_any(text, ["dashboard", "repeatedly", "after"]):
            return "medium"
        return "high"
    if "fails on" in text and contains_any(text, ["wifi", "network"]):
        return "high"
    if contains_any(text, ["timeout", "disconnect", "latency", "slow internet", "wifi"]):
        return "medium"
    return "medium"


def auth_category(text: str) -> str:
    if contains_any(text, [
        "cannot login", "unable to login", "account locked",
        "otp not received", "invalid credentials", "two factor", "2fa",
        ACCESS_DENIED, "cannot sign in", "otp not working",
        "otp verification", "otp isnt working",
    ]):
        return "high"
    if contains_any(text, [
        VERIFICATION_LINK, "password reset", "verification", "session expired",
    ]):
        return "medium"
    return "medium"


# ─── PRIORITY ─────────────────────────────────────────────────────────────────

def get_priority(text: str, category: str = None) -> str:
    if contains_any(text, URGENT_PHRASES):
        return "urgent"

    priority_map = {
        "billing":        bill_category,
        "technical":      tech_category,
        "network":        network_category,
        "authentication": auth_category,
    }

    handler = priority_map.get(category)
    if handler:
        return handler(text)

    if category == "account":
        if DELETE_ACCOUNT in text:
            return "medium"
        return "low"

    # "other" — only medium if truly blocking
    if contains_any(text, ["error", "failed", NOT_WORKING, "crash"]):
        if contains_any(text, ["cannot", "unable", "blocked", "not access"]):
            return "medium"
        return "low"
    return "low"


# ─── RULE ENGINE ──────────────────────────────────────────────────────────────

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

    if contains_any(text, ["dashboard", SERVER_ERROR, "upload", "crash", "500"]):
        scores["technical"] += 2

    if contains_any(text, [CANNOT_CONNECT, "timeout", "latency", "disconnect"]):
        scores["network"] += 2

    if contains_any(text, ["change email", "change phone", "update profile", DELETE_ACCOUNT]):
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


# ─── AI CLASSIFICATION ────────────────────────────────────────────────────────

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
        cleaned = re.sub(r"```(?:json)?```", "", result).strip()
        parsed = json.loads(cleaned)
        category = str(parsed.get("category", "")).lower().strip()
        confidence = float(parsed.get("confidence", 0.65))
        confidence = round(max(0.25, min(confidence, 0.88)), 2)

        if category in CATEGORIES or category == "other":
            return {"category": category, "confidence": confidence, "source": "AI"}

    except (json.JSONDecodeError, TypeError) as e :
        logger.warning("Failed to parse Groq response: %s | raw=%r", e, result)

    return None


# ─── DECISION LOGIC ───────────────────────────────────────────────────────────

def choose_final(rule_result, ai_result, keyword_result) -> dict:
    candidates = [r for r in [rule_result, ai_result, keyword_result] if r]

    if not candidates:
        return {"category": "other", "confidence": 0.35, "source": "fallback"}

    if rule_result and ai_result and rule_result["category"] == ai_result["category"]:
        boosted = round(min(
            max(rule_result["confidence"], ai_result["confidence"]) + 0.04, 0.97
        ), 2)
        return {"category": rule_result["category"], "confidence": boosted, "source": "rule+AI"}

    if rule_result and keyword_result and rule_result["category"] == keyword_result["category"]:
        boosted = round(min(
            max(rule_result["confidence"], keyword_result["confidence"]) + 0.03, 0.95
        ), 2)
        return {"category": rule_result["category"], "confidence": boosted, "source": "rule+keyword"}

    candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return candidates[0]


def apply_override(final: dict, category: str, source: str, confidence: float) -> None:
    final["category"] = category
    final["source"] = source
    final["confidence"] = max(final.get("confidence", 0.0), confidence)


def starts_with_refund_request(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("need refund") or stripped.startswith("refund")


def apply_billing_overrides(text: str, final: dict) -> None:
    cat = final.get("category")

    if (
        cat == "account"
        and contains_any(text, CATEGORY_KEYWORDS["billing"])
        and contains_any(text, ["payment", "refund", "charged", "invoice", "deducted"])
    ):
        apply_override(final, "billing", "billing_override", 0.88)

    if cat == "authentication" and contains_any(
        text, [CHARGED_TWICE, "refund", "invoice", PAYMENT_FAILED, MONEY_DEDUCTED]
    ):
        apply_override(final, "billing", "billing_override", 0.90)

    if cat == "technical" and contains_any(text, ["refund", CHARGED_TWICE, MONEY_DEDUCTED]):
        has_technical_failure = contains_any(
            text, ["crash", "error", "not loading", "broken", "failed to load"]
        )
        if not has_technical_failure or starts_with_refund_request(text):
            apply_override(final, "billing", "billing_override", 0.88)


def apply_auth_overrides(text: str, final: dict) -> None:
    cat = final.get("category")

    if VERIFICATION_LINK in text:
        apply_override(final, "authentication", "auth_override", 0.88)

    if (
        cat == "account"
        and contains_any(text, CATEGORY_KEYWORDS["authentication"])
        and contains_any(text, [ACCESS_DENIED, "login", "password", "otp", "locked"])
    ):
        apply_override(final, "authentication", "auth_override", 0.88)


def apply_technical_overrides(text: str, final: dict) -> None:
    cat = final.get("category")

    if (
        cat == "authentication"
        and contains_any(text, AUTH_DEBOOST_PHRASES)
        and contains_any(text, ["dashboard", SERVER_ERROR, "slow", "upload", "crash"])
    ):
        apply_override(final, "technical", "technical_override", 0.86)

    if cat == "network" and contains_any(
        text, ["dashboard", "upload", SERVER_ERROR, ERROR_500, "exception"]
    ):
        apply_override(final, "technical", "technical_override", 0.86)

    if contains_any(text, ["analytics", "report incorrect", "data mismatch", "wrong data shown"]):
        apply_override(final, "technical", "technical_override", 0.88)


def apply_account_overrides(text: str, final: dict) -> None:
    if "delete" in text and contains_any(text, ["account", "my account", "permanently"]):
        apply_override(final, "account", "account_override", 0.90)

    if "display name" in text:
        apply_override(final, "account", "account_override", 0.88)


def apply_conflict_overrides(text: str, final: dict) -> dict:
    apply_billing_overrides(text, final)
    apply_auth_overrides(text, final)
    apply_technical_overrides(text, final)
    apply_account_overrides(text, final)
    return final

# ─── LOGGING ──────────────────────────────────────────────────────────────────

def log_prediction(text: str, result: dict, ticket=None) -> None:
    TicketPredictionLog.objects.create(
        ticket=ticket,
        text=text,
        predicted_category=result["category"],
        predicted_priority=result["priority"],
        source=result["source"],
        confidence=result["confidence"],
    )


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────

def predict_ticket(text: str) -> dict:
    clean = preprocess(text)
    words = clean.split()

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

    final = choose_final(rule_result, ai_result, keyword_result)
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