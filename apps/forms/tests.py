from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.forms.models import FeedbackForm, FormQuestion
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


class FeedbackFormListAPITests(APITestCase):
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
        self.draft_form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Draft Form",
            description="Internal testing",
            status=FeedbackForm.Status.DRAFT,
        )
        self.active_form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Customer Satisfaction",
            description="Customer feedback",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.inactive_form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Archived Journey",
            description="Journey form",
            status=FeedbackForm.Status.INACTIVE,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Tenant Form",
            description="Should never appear",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.url = reverse("feedback-form-list-create")

    def test_returns_paginated_forms_for_current_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, {"page_size": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filters_forms_by_status_and_search(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {
                "status": FeedbackForm.Status.ACTIVE,
                "search": "Customer",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.active_form.id)

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FeedbackFormActivationAPITests(APITestCase):
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
        self.form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Customer Satisfaction",
            description="Initial description",
            status=FeedbackForm.Status.DRAFT,
        )
        self.form_with_question = FeedbackForm.objects.create(
            organization=self.organization,
            name="Questioned Form",
            description="Has one question",
            status=FeedbackForm.Status.DRAFT,
        )
        self.active_form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Active Form",
            description="Can be deactivated",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Form",
            description="Other tenant form",
            status=FeedbackForm.Status.DRAFT,
        )
        FormQuestion.objects.create(
            form=self.form_with_question,
            title="How do you rate us?",
            question_type=FormQuestion.QuestionType.RATING,
            is_required=True,
            order=1,
            min_value=1,
            max_value=5,
        )
        self.activate_url = reverse(
            "feedback-form-activate",
            kwargs={"form_id": self.form_with_question.id},
        )
        self.activate_without_questions_url = reverse(
            "feedback-form-activate",
            kwargs={"form_id": self.form.id},
        )
        self.deactivate_url = reverse(
            "feedback-form-deactivate",
            kwargs={"form_id": self.active_form.id},
        )
        self.other_activate_url = reverse(
            "feedback-form-activate",
            kwargs={"form_id": self.other_form.id},
        )

    def test_activate_form_with_questions(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.activate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.form_with_question.refresh_from_db()
        self.assertEqual(self.form_with_question.status, FeedbackForm.Status.ACTIVE)

    def test_activate_form_without_questions_returns_error(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.activate_without_questions_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "A form must have at least one question before activation.",
        )
        self.form.refresh_from_db()
        self.assertEqual(self.form.status, FeedbackForm.Status.DRAFT)

    def test_deactivate_active_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.deactivate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_form.refresh_from_db()
        self.assertEqual(self.active_form.status, FeedbackForm.Status.INACTIVE)

    def test_activate_cannot_access_form_from_another_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.other_activate_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FormQuestionReorderAPITests(APITestCase):
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
        self.form = FeedbackForm.objects.create(
            organization=self.organization,
            name="Customer Satisfaction",
            description="Initial description",
            status=FeedbackForm.Status.DRAFT,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Form",
            description="Other tenant form",
            status=FeedbackForm.Status.DRAFT,
        )
        self.question_one = FormQuestion.objects.create(
            form=self.form,
            title="Question 1",
            question_type=FormQuestion.QuestionType.TEXT,
            is_required=True,
            order=1,
        )
        self.question_two = FormQuestion.objects.create(
            form=self.form,
            title="Question 2",
            question_type=FormQuestion.QuestionType.TEXT,
            is_required=True,
            order=2,
        )
        self.question_three = FormQuestion.objects.create(
            form=self.form,
            title="Question 3",
            question_type=FormQuestion.QuestionType.TEXT,
            is_required=True,
            order=3,
        )
        self.reorder_url = reverse(
            "form-question-reorder",
            kwargs={"form_id": self.form.id},
        )
        self.other_reorder_url = reverse(
            "form-question-reorder",
            kwargs={"form_id": self.other_form.id},
        )

    def test_reorders_questions_sequentially(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "question_ids": [
                self.question_three.id,
                self.question_one.id,
                self.question_two.id,
            ]
        }

        response = self.client.post(self.reorder_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.question_one.refresh_from_db()
        self.question_two.refresh_from_db()
        self.question_three.refresh_from_db()

        self.assertEqual(self.question_three.order, 1)
        self.assertEqual(self.question_one.order, 2)
        self.assertEqual(self.question_two.order, 3)
        self.assertEqual(response.data[0]["id"], self.question_three.id)

    def test_rejects_incomplete_reorder_payload(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "question_ids": [
                self.question_one.id,
                self.question_two.id,
            ]
        }

        response = self.client.post(self.reorder_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "All form questions must be included in the reorder payload.",
        )

    def test_reorder_cannot_access_form_from_another_organization(self):
        self.client.force_authenticate(user=self.user)
        payload = {"question_ids": []}

        response = self.client.post(self.other_reorder_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
