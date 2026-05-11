from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.forms.models import FeedbackForm
from apps.organizations.models import Organization


class FeedbackFormDetailAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Inc",
            slug="acme-inc",
        )
        self.other_organization = Organization.objects.create(
            name="Other Inc",
            slug="other-inc",
        )
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            organization=self.organization,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            organization=self.other_organization,
        )
        self.form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Customer Satisfaction",
            description="Initial description",
            status=FeedbackForm.Status.DRAFT,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Form",
            description="Other description",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.url = reverse("feedback-form-detail", kwargs={"pk": self.form.id})
        self.other_form_url = reverse(
            "feedback-form-detail",
            kwargs={"pk": self.other_form.id},
        )

    def test_patch_updates_only_the_current_organization_form(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "name": "Updated Customer Satisfaction",
            "status": FeedbackForm.Status.ACTIVE,
        }

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.form.refresh_from_db()
        self.assertEqual(self.form.name, "Updated Customer Satisfaction")
        self.assertEqual(self.form.status, FeedbackForm.Status.ACTIVE)
        self.assertEqual(self.form.description, "Initial description")

    def test_patch_cannot_access_form_from_another_organization(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "name": "Trying to invade another tenant",
        }

        response = self.client.patch(self.other_form_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.other_form.refresh_from_db()
        self.assertEqual(self.other_form.name, "Other Form")

    def test_delete_removes_only_the_current_organization_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FeedbackForm.objects.filter(id=self.form.id).exists())

    def test_delete_cannot_remove_form_from_another_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.other_form_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(FeedbackForm.objects.filter(id=self.other_form.id).exists())
