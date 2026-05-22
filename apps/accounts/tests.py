from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.plans.models import OrganizationSubscription, Plan, UsageBucket


class CurrentUserAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Inc",
            slug="acme-inc",
        )
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Acme Owner",
            organization=self.organization,
        )
        self.url = reverse("account-me")

    def test_returns_authenticated_user_data(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "owner@example.com")
        self.assertEqual(response.data["full_name"], "Acme Owner")
        self.assertEqual(response.data["organization"]["name"], "Acme Inc")
        self.assertEqual(response.data["organization"]["slug"], "acme-inc")

    def test_accepts_bearer_token(self):
        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "owner@example.com")

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegisterCompanyAccountAPITests(APITestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        self.url = reverse("auth-register")

    def test_registers_user_and_organization_and_logs_user_in_and_returns_tokens(self):
        payload = {
            "organization_name": "Acme Inc",
            "email": "owner@example.com",
            "password": "testpass123",
            "full_name": "Acme Owner",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Organization.objects.count(), 1)
        user = User.objects.get(email="owner@example.com")
        self.assertEqual(user.organization.name, "Acme Inc")
        self.assertEqual(response.data["user"]["organization"]["name"], "Acme Inc")
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(OrganizationSubscription.objects.count(), 1)
        self.assertEqual(UsageBucket.objects.count(), 1)

        me_response = self.client.get(reverse("account-me"))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "owner@example.com")

    def test_rejects_duplicate_email(self):
        User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        payload = {
            "organization_name": "Acme Inc",
            "email": "owner@example.com",
            "password": "testpass123",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class LoginLogoutAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Inc",
            slug="acme-inc",
        )
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Acme Owner",
            organization=self.organization,
        )
        self.login_url = reverse("auth-login")
        self.logout_url = reverse("auth-logout")
        self.refresh_url = reverse("auth-token-refresh")
        self.me_url = reverse("account-me")

    def test_login_returns_user_data_tokens_and_starts_session(self):
        response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], "owner@example.com")
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "owner@example.com")

    def test_refresh_returns_new_access_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        response = self.client.post(
            self.refresh_url,
            {
                "refresh": login_response.data["tokens"]["refresh"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_rotates_and_blacklists_previous_refresh_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        first_refresh = login_response.data["tokens"]["refresh"]

        refresh_response = self.client.post(
            self.refresh_url,
            {
                "refresh": first_refresh,
            },
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", refresh_response.data)
        self.assertNotEqual(refresh_response.data["refresh"], first_refresh)

        second_refresh_attempt = self.client.post(
            self.refresh_url,
            {
                "refresh": first_refresh,
            },
            format="json",
        )

        self.assertEqual(second_refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "wrongpass",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid email or password.")

    def test_logout_ends_session(self):
        self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_with_jwt_blacklists_refresh_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        token_client = APIClient()
        token_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}"
        )

        response = token_client.post(
            self.logout_url,
            {
                "refresh": login_response.data["tokens"]["refresh"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        refresh_response = self.client.post(
            self.refresh_url,
            {
                "refresh": login_response.data["tokens"]["refresh"],
            },
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_jwt_requires_refresh_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": "owner@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        token_client = APIClient()
        token_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}"
        )

        response = token_client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh", response.data)
