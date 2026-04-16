from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import AgentProfile, User
from users.serializers import RegisterSerializer


class RegisterSerializerTests(TestCase):
    def test_create_sets_customer_defaults_and_hashes_password(self):
        serializer = RegisterSerializer(
            data={
                "username": "newcustomer",
                "email": "newcustomer@example.com",
                "password": "StrongPass123!",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, "customer")
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(user.check_password("StrongPass123!"))


class UserApiTests(APITestCase):
    def setUp(self):
        self.register_url = "/api/register/"
        self.login_url = "/api/login/"
        self.logout_url = "/api/logout/"
        self.agents_url = "/api/agents/"

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="AdminPass123!",
            role="admin",
        )
        self.agent_user = User.objects.create_user(
            username="agentuser",
            email="agent@example.com",
            password="AgentPass123!",
            role="agent",
        )
        self.customer_user = User.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            password="CustomerPass123!",
            role="customer",
        )

        AgentProfile.objects.create(user=self.agent_user, is_available=True)

    def test_register_view_creates_customer_user(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "freshuser",
                "email": "fresh@example.com",
                "password": "FreshPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(username="freshuser")
        self.assertEqual(created_user.role, "customer")
        self.assertTrue(created_user.check_password("FreshPass123!"))
        self.assertNotIn("password", response.data)

    def test_register_view_rejects_invalid_payload(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "",
                "email": "invalid@example.com",
                "password": "short",
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
                "password": "AdminPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertEqual(response.data["user"]["username"], self.admin_user.username)
        self.assertEqual(response.data["user"]["role"], "admin")
        self.assertIn("access", response.data["user"])

    def test_login_view_rejects_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "username": self.admin_user.username,
                "password": "WrongPass123!",
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

    def test_get_agents_requires_authenticated_user(self):
        response = self.client.get(self.agents_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_agents_forbids_non_admin_users(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get(self.agents_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Only admins can view agents.", str(response.data))
