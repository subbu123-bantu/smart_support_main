from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from types import SimpleNamespace

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from users.permissions import IsAdminOrReadOnly
from users.models import User
from users.serializers import (
    AgentProfileSerializer,
    ChangeEmailSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
)

from .test_utils import PASSWORD_FIELD, build_test_password, make_agent_profile, make_category, make_user


class RegisterSerializerTests(TestCase):
    def test_create_sets_customer_defaults_and_hashes_password(self):
        password = build_test_password()
        serializer = RegisterSerializer(
            data={"username": "newcustomer", "email": "newcustomer@example.com", PASSWORD_FIELD: password}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.role, "customer")
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))

    def test_reset_password_serializer_rejects_mismatch(self):
        serializer = ResetPasswordSerializer(
            data={
                "uid": "abc",
                "token": "token",
                PASSWORD_FIELD: build_test_password(),
                "confirm_password": build_test_password(),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)

    def test_reset_password_serializer_runs_password_validation(self):
        weak_password = "password"
        serializer = ResetPasswordSerializer(
            data={
                "uid": "abc",
                "token": "token",
                PASSWORD_FIELD: weak_password,
                "confirm_password": weak_password,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_change_email_serializer_rejects_duplicate_email_and_wrong_password(self):
        user = make_user(role="customer", username="email-owner")
        other_user = make_user(role="customer", username="email-other")

        duplicate_serializer = ChangeEmailSerializer(
            data={"email": other_user.email, "current_password": user.raw_password},
            context={"request": SimpleNamespace(user=user)},
        )
        self.assertFalse(duplicate_serializer.is_valid())
        self.assertIn("email", duplicate_serializer.errors)

        password_serializer = ChangeEmailSerializer(
            data={"email": "unique@example.com", "current_password": build_test_password()},
            context={"request": SimpleNamespace(user=user)},
        )
        self.assertFalse(password_serializer.is_valid())
        self.assertIn("current_password", password_serializer.errors)

    def test_change_email_serializer_accepts_unique_email_and_valid_password(self):
        user = make_user(role="customer", username="email-valid")
        serializer = ChangeEmailSerializer(
            data={"email": "unique@example.com", "current_password": user.raw_password},
            context={"request": SimpleNamespace(user=user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_agent_profile_serializer_updates_fields_without_touching_categories_when_missing(self):
        agent = make_user(role="agent", username="agent-serializer")
        billing = make_category("BillingSerializer")
        technical = make_category("TechnicalSerializer")
        profile = make_agent_profile(agent, categories=[billing, technical])

        serializer = AgentProfileSerializer(profile, data={"is_available": False}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertFalse(updated.is_available)
        self.assertCountEqual(updated.categories.values_list("id", flat=True), [billing.id, technical.id])

    def test_forgot_password_serializer_accepts_valid_email(self):
        serializer = ForgotPasswordSerializer(data={"email": "valid@example.com"})
        self.assertTrue(serializer.is_valid(), serializer.errors)


class UserApiTests(APITestCase):
    def setUp(self):
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.logout_url = "/api/auth/logout/"
        self.agents_url = "/api/auth/agents/"
        self.forgot_password_url = "/api/auth/forgot-password/"
        self.reset_password_url = "/api/auth/reset-password/"
        self.change_email_url = "/api/auth/change-email/"
        self.admin_user = make_user(role="admin", username="adminuser")
        self.agent_user = make_user(role="agent", username="agentuser")
        self.customer_user = make_user(role="customer", username="customeruser")
        self.admin_password = self.admin_user.raw_password
        self.agent_password = self.agent_user.raw_password
        self.customer_password = self.customer_user.raw_password
        self.billing_category = make_category("Billing")
        self.technical_category = make_category("Technical")
        self.account_category = make_category("Account")
        self.agent_profile = make_agent_profile(self.agent_user, categories=[self.billing_category])
        self.agent_profile_url = f"/api/auth/agents/{self.agent_user.id}/"

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def post_json(self, url, data=None):
        return self.client.post(url, data or {}, format="json")

    def patch_json(self, url, data):
        return self.client.patch(url, data, format="json")

    def get_json(self, url):
        return self.client.get(url, format="json")

    @patch("users.views.send_email_task.delay")
    def test_forgot_password_view_queues_email_for_existing_user(self, mock_delay):
        response = self.post_json(self.forgot_password_url, {"email": self.customer_user.email.upper()})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reset link has been sent", response.data["message"].lower())
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        self.assertEqual(args[:2], (self.customer_user.email, "Reset your Smart Support password"))
        self.assertIn("/reset-password?uid=", kwargs["context"]["reset_url"])

    @patch("users.views.logger")
    @patch("users.views.send_email_task.delay", side_effect=Exception("queue down"))
    def test_forgot_password_view_logs_when_email_queue_fails(self, _mock_delay, mock_logger):
        response = self.post_json(self.forgot_password_url, {"email": self.customer_user.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_logger.exception.assert_called_once()

    @patch("users.views.send_email_task.delay")
    def test_forgot_password_view_skips_email_for_unknown_user(self, mock_delay):
        response = self.post_json(self.forgot_password_url, {"email": "missing@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_delay.assert_not_called()

    def test_forgot_password_view_rejects_invalid_email_payload(self):
        response = self.post_json(self.forgot_password_url, {"email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_reset_password_view_rejects_invalid_uid(self):
        password = build_test_password()
        response = self.post_json(
            self.reset_password_url,
            {"uid": "bad-uid", "token": "token", PASSWORD_FIELD: password, "confirm_password": password},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid reset link.")

    def test_reset_password_view_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.customer_user.pk))
        password = build_test_password()
        response = self.post_json(
            self.reset_password_url,
            {"uid": uid, "token": "invalid-token", PASSWORD_FIELD: password, "confirm_password": password},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Reset link is invalid or expired.")

    def test_reset_password_view_updates_password_for_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.customer_user.pk))
        token = default_token_generator.make_token(self.customer_user)
        new_password = build_test_password()
        response = self.post_json(
            self.reset_password_url,
            {"uid": uid, "token": token, PASSWORD_FIELD: new_password, "confirm_password": new_password},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer_user.refresh_from_db()
        self.assertTrue(self.customer_user.check_password(new_password))

    def test_change_email_view_updates_authenticated_user_email(self):
        self.authenticate(self.customer_user)
        response = self.patch_json(
            self.change_email_url,
            {"email": "updated@example.com", "current_password": self.customer_password},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.email, "updated@example.com")

    def test_change_email_view_requires_authentication(self):
        response = self.patch_json(
            self.change_email_url,
            {"email": "updated@example.com", "current_password": self.customer_password},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_email_view_returns_serializer_errors(self):
        self.authenticate(self.customer_user)
        response = self.patch_json(
            self.change_email_url,
            {"email": self.admin_user.email, "current_password": build_test_password()},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email" in response.data or "current_password" in response.data)

    def test_register_view_creates_customer_user(self):
        password = build_test_password()
        response = self.post_json(self.register_url, {"username": "freshuser", "email": "fresh@example.com", PASSWORD_FIELD: password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(username="freshuser")
        self.assertEqual(created_user.role, "customer")
        self.assertTrue(created_user.check_password(password))
        self.assertNotIn(PASSWORD_FIELD, response.data)

    def test_register_view_rejects_invalid_payload(self):
        response = self.post_json(self.register_url, {"username": "", "email": "invalid@example.com", PASSWORD_FIELD: build_test_password()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_login_view_returns_access_token_for_valid_credentials(self):
        response = self.post_json(self.login_url, {"username": self.admin_user.username, PASSWORD_FIELD: self.admin_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertEqual(response.data["user"]["username"], self.admin_user.username)
        self.assertEqual(response.data["user"]["role"], "admin")
        self.assertIn("access", response.data["user"])

    def test_login_view_rejects_invalid_credentials(self):
        response = self.post_json(self.login_url, {"username": self.admin_user.username, PASSWORD_FIELD: build_test_password()})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Invalid credentials")

    def test_logout_view_returns_success_message(self):
        response = self.post_json(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out successfully")

    def test_get_agents_returns_profiles_for_admin(self):
        self.authenticate(self.admin_user)
        response = self.get_json(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], self.agent_user.username)
        self.assertTrue(response.data[0]["is_available"])
        self.assertEqual(response.data[0]["categories"], [self.billing_category.id])
        self.assertEqual(response.data[0]["category_names"], [self.billing_category.name])

    def test_get_agents_requires_authenticated_user(self):
        response = self.get_json(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_agents_forbids_non_admin_users(self):
        self.authenticate(self.customer_user)
        response = self.get_json(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can view agents.", str(response.data))

    def test_update_agent_profile_updates_multiple_categories_for_admin(self):
        self.authenticate(self.admin_user)
        response = self.patch_json(
            self.agent_profile_url,
            {"is_available": False, "categories": [self.billing_category.id, self.technical_category.id, self.account_category.id]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent_profile.refresh_from_db()
        self.assertFalse(self.agent_profile.is_available)
        self.assertCountEqual(
            self.agent_profile.categories.values_list("id", flat=True),
            [self.billing_category.id, self.technical_category.id, self.account_category.id],
        )
        self.assertCountEqual(
            response.data["category_names"],
            [self.billing_category.name, self.technical_category.name, self.account_category.name],
        )

    def test_update_agent_profile_rejects_invalid_category_ids(self):
        self.authenticate(self.admin_user)
        response = self.patch_json(self.agent_profile_url, {"categories": [99999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categories", response.data)

    def test_update_agent_profile_returns_404_for_missing_agent_profile(self):
        self.authenticate(self.admin_user)
        response = self.patch_json("/api/auth/agents/999999/", {"is_available": False})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No AgentProfile found", response.data["error"])

    def test_update_agent_profile_requires_admin_user(self):
        self.authenticate(self.customer_user)
        response = self.patch_json(self.agent_profile_url, {"categories": [self.technical_category.id]})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can update agents.", str(response.data))


class PermissionClassTests(TestCase):
    def build_request(self, role, method="GET", authenticated=True):
        return SimpleNamespace(method=method, user=SimpleNamespace(is_authenticated=authenticated, role=role))

    def test_is_admin_or_read_only_allows_safe_methods_for_authenticated_users(self):
        self.assertTrue(IsAdminOrReadOnly().has_permission(self.build_request("customer"), None))

    def test_is_admin_or_read_only_requires_admin_for_write_methods(self):
        self.assertFalse(IsAdminOrReadOnly().has_permission(self.build_request("customer", method="POST"), None))
        self.assertTrue(IsAdminOrReadOnly().has_permission(self.build_request("admin", method="POST"), None))
