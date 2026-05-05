import csv
import os
import secrets
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from tickets.ai.ai_helper import preprocess
from tickets.ai.ai_priority import get_priority

categories = ["billing", "technical", "authentication", "network", "account", "other"]

billing_templates = [
    "Payment failed but money deducted",
    "Charged twice for same order",
    "Refund not received after cancellation",
    "Invoice amount incorrect",
    "Subscription charged after cancellation",
    "Auto debit happened unexpectedly",
]

technical_templates = [
    "App crashes on upload",
    "White screen after login",
    "Button not working",
    "Page keeps reloading",
    "Unexpected server error",
    "Feature not responding",
]

auth_templates = [
    "Cannot login with correct password",
    "OTP not received",
    "Password reset link expired",
    "Account locked unexpectedly",
    "Session expired quickly",
]

network_templates = [
    "Connection timeout error",
    "App disconnects frequently",
    "High latency issue",
    "Works on mobile data but not wifi",
    "Network unstable",
]

account_templates = [
    "Change email address",
    "Update phone number",
    "Delete my account",
    "Modify profile details",
    "Update username",
]

other_templates = [
    "Hello",
    "Good morning",
    "I need help",
    "This is not working",
    "Please check",
    "Thanks for support",
]

typos = {
    "payment": ["paymnt", "pymnt", "paymet"],
    "login": ["logn", "lgin"],
    "account": ["accnt", "acount"],
    "network": ["netwrk", "ntwrk"],
}

hinglish_templates = {
    "billing": [
        "payment cut ho gaya but service nahi mila",
        "refund abhi tak nahi mila",
    ],
    "technical": [
        "app bar bar crash ho raha hai",
        "feature response nahi de raha",
    ],
    "authentication": [
        "login nahi ho raha",
        "otp nahi aa raha",
    ],
    "network": [
        "network issue aa raha hai",
        "wifi se connect nahi ho raha",
    ],
    "account": [
        "mera email address update karna hai",
        "account details change karni hai",
    ],
    "other": [
        "hello bhai",
        "thoda help chahiye",
    ],
}

mixable_extras = {
    "billing": billing_templates,
    "technical": technical_templates,
    "authentication": auth_templates,
    "network": network_templates,
    "account": account_templates,
    "other": other_templates,
}

DEFAULT_DATASET_PATH = BACKEND_ROOT / "tickets" / "ai" / "ticket_ai_dataset.csv"
RNG = secrets.SystemRandom()


def add_noise(text):
    # Randomly inject a typo to make examples less uniform.
    words = text.split()
    for i in range(len(words)):
        if words[i].lower() in typos and RNG.random() < 0.3:
            words[i] = RNG.choice(typos[words[i].lower()])
    return " ".join(words)


def generate_ticket(category):
        
    match category:
        case "billing":
            base = RNG.choice(billing_templates)
        case "technical":
            base = RNG.choice(technical_templates)
        case "authentication":
            base = RNG.choice(auth_templates)
        case "network":
            base = RNG.choice(network_templates)
        case "account":
            base = RNG.choice(account_templates)
        case "other":
            base = RNG.choice(other_templates)

    if RNG.random() < 0.4:
        base = add_noise(base)

    if RNG.random() < 0.2:
        base = RNG.choice(hinglish_templates[category])

    if RNG.random() < 0.25:
        extra = RNG.choice(mixable_extras[category])
        base = base + " and also " + extra

    return base


def generate_confidence(category):
    match category:
        case "other":
            return round(RNG.uniform(0.2, 0.4), 2)
    return round(RNG.uniform(0.75, 0.95), 2)


def generate_priority(category, text):
    return get_priority(preprocess(text), category)


def generate_dataset(n=1000, filename=None):
    output_path = Path(filename) if filename else DEFAULT_DATASET_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["text", "category", "confidence", "priority"])

        for _ in range(n):
            category = RNG.choice(categories)
            text = generate_ticket(category)
            confidence = generate_confidence(category)
            priority = generate_priority(category, text)
            writer.writerow([text, category, confidence, priority])

    print(f"Dataset with {n} rows generated -> {output_path}")


if __name__ == "__main__":
    generate_dataset(1000)
