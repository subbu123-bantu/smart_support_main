from contextlib import nullcontext
from unittest.mock import patch

from django.core.management.base import BaseCommand

from tickets.ai import predict_ticket


TEST_CASES = [
    ("My payment failed but money was deducted from my bank account", "billing", "high"),
    ("I was charged twice for the same order", "billing", "high"),
    ("Refund not received after cancellation", "billing", "medium"),
    ("Invoice amount is incorrect", "billing", "medium"),
    ("Subscription renewal payment is not showing", "billing", "medium"),
    ("App keeps crashing when I open dashboard", "technical", "high"),
    ("Server error 500 while submitting ticket", "technical", "high"),
    ("The page is loading very slowly", "technical", "medium"),
    ("Button is not working on mobile view", "technical", "medium"),
    ("Unable to upload file, it shows an error", "technical", "medium"),
    ("I cannot login with my correct password", "authentication", "high"),
    ("OTP is not coming to my mobile number", "authentication", "high"),
    ("Password reset link expired", "authentication", "medium"),
    ("Account locked after multiple login attempts", "authentication", "high"),
    ("Two factor authentication code is invalid", "authentication", "high"),
    ("Internet connection keeps disconnecting", "network", "high"),
    ("Network is very slow in my area", "network", "medium"),
    ("Unable to connect to server due to timeout", "network", "high"),
    ("VPN connection is not working", "network", "medium"),
    ("API request failed due to network timeout", "network", "high"),
    ("I want to update my profile email address", "account", "low"),
    ("My account details are incorrect", "account", "medium"),
    ("Please change my registered mobile number", "account", "low"),
    ("I cannot see my account settings", "account", "medium"),
    ("My username is showing wrong", "account", "low"),
    ("Hello", "other", "low"),
    ("Good morning", "other", "low"),
    ("What is the weather today", "other", "low"),
    ("asdfghjkl random words", "other", "low"),
    ("I need help", "other", "low"),
    ("I changed my password but now payment history is missing", "billing", "medium"),
    ("Cannot view payment record after password reset", "billing", "medium"),
    ("Login works but dashboard crashes after opening", "technical", "high"),
    ("Payment page shows server error after money deduction", "billing", "high"),
    ("OTP not received and account is locked", "authentication", "high"),
    ("Urgent! Payment failed and money deducted, please fix asap", "billing", "urgent"),
    ("Critical server crash, users cannot access dashboard", "technical", "urgent"),
    ("Need immediate help, account locked before exam registration", "authentication", "urgent"),
    ("Network completely down for all users", "network", "urgent"),
    ("", "other", "low"),
    ("   ", "other", "low"),
    ("1234567890", "other", "low"),
    ("!!!!!?????", "other", "low"),
]


class Command(BaseCommand):
    help = "Run a canned evaluation suite against tickets.ai.predict_ticket."

    def add_arguments(self, parser):
        parser.add_argument(
            "--failures-only",
            action="store_true",
            help="Only print cases where category or priority does not match.",
        )
        parser.add_argument(
            "--no-ai",
            action="store_true",
            help="Disable AI classification and benchmark only local rule-based logic.",
        )

    def handle(self, *args, **options):
        failures_only = options["failures_only"]
        no_ai = options["no_ai"]
        category_correct = 0
        priority_correct = 0
        runner = patch("tickets.ai.ai.ai_classification", return_value=None) if no_ai else nullcontext()

        with runner:
            for text, expected_category, expected_priority in TEST_CASES:
                result = predict_ticket(text)
                got_category = result.get("category")
                got_priority = result.get("priority")

                category_ok = got_category == expected_category
                priority_ok = got_priority == expected_priority

                if category_ok:
                    category_correct += 1
                if priority_ok:
                    priority_correct += 1

                if failures_only and category_ok and priority_ok:
                    continue

                self.stdout.write("")
                self.stdout.write(f"TEXT: {text!r}")
                self.stdout.write(f"EXPECTED: {expected_category} | {expected_priority}")
                self.stdout.write(f"GOT     : {got_category} | {got_priority}")
                self.stdout.write(f"SOURCE  : {result.get('source')}")
                self.stdout.write(f"CONF    : {result.get('confidence')}")
                self.stdout.write(f"REVIEW  : {result.get('needs_manual_review')}")
                self.stdout.write(f"PASS    : {'OK' if category_ok and priority_ok else 'FAIL'}")

        total = len(TEST_CASES)
        category_accuracy = round((category_correct / total) * 100, 2) if total else 0
        priority_accuracy = round((priority_correct / total) * 100, 2) if total else 0

        self.stdout.write("")
        self.stdout.write(f"MODE: {'local-rules-only' if no_ai else 'hybrid'}")
        self.stdout.write("==============================")
        self.stdout.write(f"TOTAL TESTS: {total}")
        self.stdout.write(f"CATEGORY ACCURACY: {category_accuracy} %")
        self.stdout.write(f"PRIORITY ACCURACY: {priority_accuracy} %")
        self.stdout.write("==============================")

