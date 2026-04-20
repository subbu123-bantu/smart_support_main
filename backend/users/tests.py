from django.test import TestCase
from django.utils.crypto import get_random_string
from types import SimpleNamespace
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Category
from users.permissions import IsAdmin, IsAdminOrReadOnly, IsAgent, IsCustomer
from users.models import AgentProfile, User
from users.serializers import RegisterSerializer


PASSWORD_FIELD = "password"


def build_test_password():
    return f"test-{get_random_string(16)}-Aa1!"


class RegisterSerializerTests(TestCase):
    def test_create_sets_customer_defaults_and_hashes_password(self):
        password = build_test_password()
        serializer = RegisterSerializer(
            data={
                "username": "newcustomer",
                "email": "newcustomer@example.com",
                PASSWORD_FIELD: password,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, "customer")
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))


class UserApiTests(APITestCase):
    def setUp(self):
        self.register_url = "/api/register/"
        self.login_url = "/api/login/"
        self.logout_url = "/api/logout/"
        self.agents_url = "/api/agents/"
        self.agent_profile_url = None
        self.admin_password = build_test_password()
        self.agent_password = build_test_password()
        self.customer_password = build_test_password()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            **{PASSWORD_FIELD: self.admin_password},
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentuser",
            email="agent@example.com",
            **{PASSWORD_FIELD: self.agent_password},
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            **{PASSWORD_FIELD: self.customer_password},
            role="customer",
        )

        self.agent_profile = AgentProfile.objects.create(user=self.agent_user, is_available=True)
        self.billing_category = Category.objects.create(name="Billing")
        self.technical_category = Category.objects.create(name="Technical")
        self.account_category = Category.objects.create(name="Account")
        self.agent_profile.categories.add(self.billing_category)
        self.agent_profile_url = f"/api/agents/{self.agent_user.id}/"

    def test_register_view_creates_customer_user(self):
        password = build_test_password()
        response = self.client.post(
            self.register_url,
            {
                "username": "freshuser",
                "email": "fresh@example.com",
                PASSWORD_FIELD: password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(username="freshuser")
        self.assertEqual(created_user.role, "customer")
        self.assertTrue(created_user.check_password(password))
        self.assertNotIn(PASSWORD_FIELD, response.data)

    def test_register_view_rejects_invalid_payload(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "",
                "email": "invalid@example.com",
                PASSWORD_FIELD: build_test_password(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_login_view_returns_access_token_for_valid_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "username": self.admin_user.username,
                PASSWORD_FIELD: self.admin_password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertEqual(response.data["user"]["username"], self.admin_user.username)
        self.assertEqual(response.data["user"]["role"], "admin")
        self.assertIn("access", response.data["user"])

    def test_login_view_rejects_invalid_credentials(self):
        invalid_password = build_test_password()
        response = self.client.post(
            self.login_url,
            {
                "username": self.admin_user.username,
                PASSWORD_FIELD: invalid_password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Invalid credentials")

    def test_logout_view_returns_success_message(self):
        response = self.client.post(self.logout_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out successfully")

    def test_get_agents_returns_profiles_for_admin(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.agents_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], self.agent_user.username)
        self.assertTrue(response.data[0]["is_available"])
        self.assertEqual(response.data[0]["categories"], [self.billing_category.id])
        self.assertEqual(response.data[0]["category_names"], [self.billing_category.name])

    def test_get_agents_requires_authenticated_user(self):
        response = self.client.get(self.agents_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_agents_forbids_non_admin_users(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get(self.agents_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can view agents.", str(response.data))

    def test_update_agent_profile_updates_multiple_categories_for_admin(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            self.agent_profile_url,
            {
                "is_available": False,
                "categories": [self.billing_category.id, self.technical_category.id, self.account_category.id],
            },
            format="json",
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
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            self.agent_profile_url,
            {"categories": [99999]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categories", response.data)

    def test_update_agent_profile_requires_admin_user(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.patch(
            self.agent_profile_url,
            {"categories": [self.technical_category.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can update agents.", str(response.data))


class PermissionClassTests(TestCase):
    def test_role_permissions_require_authenticated_matching_role(self):
        admin_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="admin"))
        agent_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="agent"))
        customer_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="customer"))
        anonymous_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False, role="admin"))

        self.assertTrue(IsAdmin().has_permission(admin_request, None))
        self.assertFalse(IsAdmin().has_permission(anonymous_request, None))
        self.assertTrue(IsAgent().has_permission(agent_request, None))
        self.assertTrue(IsCustomer().has_permission(customer_request, None))

    def test_is_admin_or_read_only_allows_safe_methods_for_authenticated_users(self):
        request = SimpleNamespace(method="GET", user=SimpleNamespace(is_authenticated=True, role="customer"))

        self.assertTrue(IsAdminOrReadOnly().has_permission(request, None))

    def test_is_admin_or_read_only_requires_admin_for_write_methods(self):
        customer_request = SimpleNamespace(method="POST", user=SimpleNamespace(is_authenticated=True, role="customer"))
        admin_request = SimpleNamespace(method="POST", user=SimpleNamespace(is_authenticated=True, role="admin"))

        self.assertFalse(IsAdminOrReadOnly().has_permission(customer_request, None))
        self.assertTrue(IsAdminOrReadOnly().has_permission(admin_request, None))
