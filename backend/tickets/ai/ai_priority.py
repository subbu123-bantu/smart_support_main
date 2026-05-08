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


BILLING_REFUND_DELAY_PHRASES = (
    "refund not received",
    "refund pending",
    "refund delayed",
)

BILLING_HIGH_PAYMENT_PHRASES = (
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
)

BILLING_HIGH_INVOICE_PHRASES = (
    "invoice not",
    "invoice page",
    "invoice not visible",
    "invoice not loading",
)

BILLING_LOW_INFO_PHRASES = (
    "gst",
    "details",
    "information",
    "how to",
)

BILLING_MEDIUM_HISTORY_PHRASES = (
    "invoice",
    "billing page",
    "payment history",
    "payment record",
)

TECH_URGENT_PHRASES = (
    "all users",
    "everyone",
    "for all admins",
    "production down",
    "critical",
    "immediate",
)

TECH_HIGH_ERROR_PHRASES = (
    SERVER_ERROR,
    ERROR_500,
    "crash",
    "exception",
)

TECH_HIGH_DASHBOARD_PHRASES = (
    "dashboard not loading",
    "upload failed",
    "file upload",
    "page freezes",
)

TECH_MEDIUM_GENERAL_PHRASES = (
    NOT_WORKING,
    "failed",
    "broken",
    "bug",
    "wrong data",
    "slow",
    "button",
    "mobile view",
)

NETWORK_URGENT_PHRASES = (
    "all users",
    "completely down",
    "network down",
)

NETWORK_CONNECTION_PHRASES = (
    CANNOT_CONNECT,
    "server unreachable",
    "connection timeout",
    "request timed out",
    "connection lost",
    "unable to connect",
)

NETWORK_MEDIUM_CONTEXT_PHRASES = (
    "dashboard",
    "repeatedly",
    "after",
)

NETWORK_HIGH_DISCONNECT_PHRASES = (
    "disconnect",
    "disconnecting",
    "timeout",
    "request failed due to network timeout",
)

NETWORK_MEDIUM_SPEED_PHRASES = (
    "latency",
    "slow internet",
    "wifi",
)

AUTH_HIGH_PHRASES = (
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
)

AUTH_MEDIUM_PHRASES = (
    VERIFICATION_LINK,
    "password reset",
    "verification",
    "session expired",
)

ACCOUNT_MEDIUM_DELETE_PHRASES = (
    "delete account",
    "remove account",
    "permanently delete",
    "close account",
    "delete my account",
)

ACCOUNT_LOW_CONTACT_CHANGE_PHRASES = (
    "change email",
    "change phone",
    "update phone number",
    "registered mobile number",
    "registered mobile",
    "registered phone number",
    "email address change",
)

ACCOUNT_MEDIUM_SETTINGS_PHRASES = (
    "account details",
    "details are incorrect",
    "cannot see my account settings",
    "account settings",
)

ACCOUNT_LOW_PROFILE_PHRASES = (
    "update profile",
    "profile update",
    "display name",
    "profile",
    "username",
)


def bill_category(text: str) -> str:
    if contains_any(text, BILLING_REFUND_DELAY_PHRASES):
        return "medium"

    if contains_any(text, BILLING_HIGH_PAYMENT_PHRASES):
        return "high"

    if contains_any(text, BILLING_HIGH_INVOICE_PHRASES):
        return "high"

    if contains_any(text, BILLING_LOW_INFO_PHRASES):
        return "low"

    if contains_any(text, BILLING_MEDIUM_HISTORY_PHRASES):
        return "medium"

    return "medium"


def tech_category(text: str) -> str:
    if contains_any(text, TECH_URGENT_PHRASES):
        return "urgent"

    if contains_any(text, TECH_HIGH_ERROR_PHRASES):
        return "high"

    if contains_any(text, TECH_HIGH_DASHBOARD_PHRASES):
        return "high"

    if contains_any(text, TECH_MEDIUM_GENERAL_PHRASES):
        return "medium"

    return "medium"


def network_category(text: str) -> str:
    if contains_any(text, NETWORK_URGENT_PHRASES):
        return "urgent"

    if contains_any(text, NETWORK_CONNECTION_PHRASES):
        if contains_any(text, NETWORK_MEDIUM_CONTEXT_PHRASES):
            return "medium"
        return "high"

    if "fails on" in text and contains_any(text, ["wifi", "network"]):
        return "high"

    if contains_any(text, NETWORK_HIGH_DISCONNECT_PHRASES):
        return "high"

    if contains_any(text, NETWORK_MEDIUM_SPEED_PHRASES):
        return "medium"

    return "medium"


def auth_category(text: str) -> str:
    if contains_any(text, AUTH_HIGH_PHRASES):
        return "high"

    if contains_any(text, AUTH_MEDIUM_PHRASES):
        return "medium"

    return "medium"


def acc_category(text: str) -> str:
    if contains_any(text, ACCOUNT_MEDIUM_DELETE_PHRASES):
        return "medium"

    if contains_any(text, ACCOUNT_LOW_CONTACT_CHANGE_PHRASES):
        return "low"

    if contains_any(text, ACCOUNT_MEDIUM_SETTINGS_PHRASES):
        return "medium"

    if contains_any(text, ACCOUNT_LOW_PROFILE_PHRASES):
        return "low"

    return "low"


def get_priority(text: str, category: str | None = None) -> str:
    if contains_any(text, URGENT_PHRASES):
        return "urgent"

    match category:
        case "billing":
            return bill_category(text)
        case "technical":
            return tech_category(text)
        case "network":
            return network_category(text)
        case "authentication":
            return auth_category(text)
        case "account":
            return acc_category(text)

    if contains_any(text, ["error", "failed", NOT_WORKING, "crash"]):
        if contains_any(text, ["cannot", "unable", "blocked", "not access"]):
            return "medium"
        return "low"

    return "low"
