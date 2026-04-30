from .ai_constants import (
    ACCESS_DENIED,
    AUTH_DEBOOST_PHRASES,
    CATEGORY_KEYWORDS,
    CHARGED_TWICE,
    ERROR_500,
    MONEY_DEDUCTED,
    PAYMENT_FAILED,
    SERVER_ERROR,
    VERIFICATION_LINK,
)
from .ai_helper import contains_any


def apply_override(final: dict, category: str, source: str, confidence: float) -> None:
    final["category"] = category
    final["source"] = source
    final["confidence"] = max(final.get("confidence", 0.0), confidence)


def starts_with_refund_request(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("need refund") or stripped.startswith("refund")


def apply_billing_overrides(text: str, final: dict) -> None:
    category = final.get("category")
    has_strong_billing_signal = contains_any(
        text,
        [CHARGED_TWICE, MONEY_DEDUCTED, PAYMENT_FAILED, "money deduction", "payment deducted", "refund"],
    )

    if (
        category == "account"
        and contains_any(text, CATEGORY_KEYWORDS["billing"])
        and contains_any(text, ["payment", "refund", "charged", "invoice", "deducted"])
    ):
        apply_override(final, "billing", "billing_override", 0.88)

    if category == "authentication" and contains_any(
        text,
        [CHARGED_TWICE, "refund", "invoice", PAYMENT_FAILED, MONEY_DEDUCTED],
    ):
        apply_override(final, "billing", "billing_override", 0.90)

    if category == "technical" and contains_any(
        text,
        ["refund", CHARGED_TWICE, MONEY_DEDUCTED, "payment", "invoice"],
    ):
        has_technical_failure = contains_any(
            text,
            ["crash", "error", "not loading", "broken", "failed to load"],
        )
        if has_strong_billing_signal or not has_technical_failure or starts_with_refund_request(text):
            apply_override(final, "billing", "billing_override", 0.88)


def apply_auth_overrides(text: str, final: dict) -> None:
    category = final.get("category")

    if VERIFICATION_LINK in text:
        apply_override(final, "authentication", "auth_override", 0.88)

    if contains_any(text, ["two factor authentication", "authentication code", "invalid code"]):
        apply_override(final, "authentication", "auth_override", 0.88)

    if (
        category == "account"
        and contains_any(text, CATEGORY_KEYWORDS["authentication"])
        and contains_any(text, [ACCESS_DENIED, "login", "password", "otp", "locked"])
    ):
        apply_override(final, "authentication", "auth_override", 0.88)


def apply_technical_overrides(text: str, final: dict) -> None:
    category = final.get("category")

    if (
        category == "authentication"
        and contains_any(text, AUTH_DEBOOST_PHRASES)
        and contains_any(text, ["dashboard", SERVER_ERROR, "slow", "upload", "crash"])
    ):
        apply_override(final, "technical", "technical_override", 0.86)

    if category == "network" and contains_any(
        text,
        ["dashboard", "upload", SERVER_ERROR, ERROR_500, "exception"],
    ):
        apply_override(final, "technical", "technical_override", 0.86)

    if contains_any(text, ["analytics", "report incorrect", "data mismatch", "wrong data shown"]):
        apply_override(final, "technical", "technical_override", 0.88)


def apply_account_overrides(text: str, final: dict) -> None:
    if "delete" in text and contains_any(text, ["account", "my account", "permanently"]):
        apply_override(final, "account", "account_override", 0.90)

    if "display name" in text:
        apply_override(final, "account", "account_override", 0.88)

    if contains_any(text, ["account details", "username", "account settings"]):
        apply_override(final, "account", "account_override", 0.86)


def apply_conflict_overrides(text: str, final: dict) -> dict:
    apply_billing_overrides(text, final)
    apply_auth_overrides(text, final)
    apply_technical_overrides(text, final)
    apply_account_overrides(text, final)
    return final
