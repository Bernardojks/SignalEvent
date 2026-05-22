from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import Organization


class OrganizationSecuritySettingsAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Inc",
            slug="acme-inc",
        )
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            organization=self.organization,
        )
        self.url = reverse("organization-security-settings")

    def test_returns_current_organization_security_settings(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["security_level"], Organization.SecurityLevel.STANDARD)
        self.assertEqual(
            response.data["suspicious_submission_policy"],
            Organization.SuspiciousSubmissionPolicy.FLAG,
        )
        self.assertFalse(response.data["require_captcha"])

    def test_updates_security_settings_for_current_organization(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "security_level": Organization.SecurityLevel.STRICT,
            "suspicious_submission_policy": Organization.SuspiciousSubmissionPolicy.REJECT,
            "require_captcha": True,
        }

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.security_level, Organization.SecurityLevel.STRICT)
        self.assertEqual(
            self.organization.suspicious_submission_policy,
            Organization.SuspiciousSubmissionPolicy.REJECT,
        )
        self.assertTrue(self.organization.require_captcha)

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
