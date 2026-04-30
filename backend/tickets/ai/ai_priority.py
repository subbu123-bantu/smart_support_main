from .ai_constants import (
    ACCESS_DENIED,
    CANNOT_CONNECT,
    ERROR_500,
    NOT_WORKING,
    SERVER_ERROR,
    URGENT_PHRASES,
    VERIFICATION_LINK,
)
from .ai_helper import contains_any


def bill_category(text: str) -> str:
    if contains_any(text, ["refund not received", "refund pending", "refund delayed"]):
        return "medium"

    if contains_any(
        text,
        [
            "payment failed",
            "charged twice",
            "money deducted",
            "money deduction",
            "deducted twice",
            "refund",
            "transaction failed",
            "wrong amount",
            "overcharged",
            "charged",
            "deducted",
        ],
    ):
        return "high"

    if contains_any(
        text,
        [
            "invoice not",
            "invoice page",
            "invoice not visible",
            "invoice not loading",
        ],
    ):
        return "high"

    if contains_any(text, ["gst", "details", "information", "how to"]):
        return "low"

    if contains_any(text, ["invoice", "billing page", "payment history", "payment record"]):
        return "medium"

    return "medium"


def tech_category(text: str) -> str:
    if contains_any(text, ["all users", "everyone", "for all admins", "production down", "critical", "immediate"]):
        return "urgent"

    if contains_any(text, [SERVER_ERROR, ERROR_500, "crash", "exception"]):
        return "high"

    if contains_any(text, ["dashboard not loading", "upload failed", "file upload", "page freezes"]):
        return "high"

    if contains_any(
        text,
        [NOT_WORKING, "failed", "broken", "bug", "wrong data", "slow", "button", "mobile view"],
    ):
        return "medium"

    return "medium"


def network_category(text: str) -> str:
    if contains_any(text, ["all users", "completely down", "network down"]):
        return "urgent"

    if contains_any(
        text,
        [
            CANNOT_CONNECT,
            "server unreachable",
            "connection timeout",
            "request timed out",
            "connection lost",
            "unable to connect",
        ],
    ):
        if contains_any(text, ["dashboard", "repeatedly", "after"]):
            return "medium"
        return "high"

    if "fails on" in text and contains_any(text, ["wifi", "network"]):
        return "high"

    if contains_any(text, ["disconnect", "disconnecting", "timeout", "request failed due to network timeout"]):
        return "high"

    if contains_any(text, ["latency", "slow internet", "wifi"]):
        return "medium"

    return "medium"


def auth_category(text: str) -> str:
    if contains_any(
        text,
        [
            "cannot login",
            "unable to login",
            "account locked",
            "otp not received",
            "otp is not coming",
            "invalid credentials",
            "two factor",
            "authentication code",
            "2fa",
            ACCESS_DENIED,
            "cannot sign in",
            "otp not working",
            "otp verification",
            "otp isnt working",
        ],
    ):
        return "high"

    if contains_any(
        text,
        [
            VERIFICATION_LINK,
            "password reset",
            "verification",
            "session expired",
        ],
    ):
        return "medium"

    return "medium"


def acc_category(text: str) -> str:
    if contains_any(
        text,
        [
            "delete account",
            "remove account",
            "permanently delete",
            "close account",
            "delete my account",
        ],
    ):
        return "medium"

    if contains_any(
        text,
        [
            "change email",
            "change phone",
            "update phone number",
            "registered mobile number",
            "registered mobile",
            "registered phone number",
            "email address change",
        ],
    ):
        return "low"

    if contains_any(
        text,
        [
            "account details",
            "details are incorrect",
            "cannot see my account settings",
            "account settings",
        ],
    ):
        return "medium"

    if contains_any(
        text,
        [
            "update profile",
            "profile update",
            "display name",
            "profile",
            "username",
        ],
    ):
        return "low"

    return "low"


def get_priority(text: str, category: str | None = None) -> str:
    if contains_any(text, URGENT_PHRASES):
        return "urgent"

    priority_map = {
        "billing": bill_category,
        "technical": tech_category,
        "network": network_category,
        "authentication": auth_category,
        "account": acc_category,
    }

    handler = priority_map.get(category)
    if handler:
        return handler(text)

    if contains_any(text, ["error", "failed", NOT_WORKING, "crash"]):
        if contains_any(text, ["cannot", "unable", "blocked", "not access"]):
            return "medium"
        return "low"

    return "low"
