from django.utils.crypto import get_random_string


PASSWORD_FIELD = "password"


def build_test_password():
    return f"test-{get_random_string(16)}-Aa1!"
