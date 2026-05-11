from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.models import FeedbackForm, FormQuestion
from apps.organizations.models import Organization
from apps.submissions.models import FeedbackSubmission, SubmissionAnswer


class PublicFeedbackSubmissionCreateAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Inc",
            slug="acme-inc",
        )
        self.form = FeedbackForm.objects.create(
            organization=self.organization,
            name="NPS",
            description="Customer feedback form",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.rating_question = FormQuestion.objects.create(
            form=self.form,
            title="How do you rate us?",
            question_type=FormQuestion.QuestionType.RATING,
            is_required=True,
            order=1,
            min_value=1,
            max_value=5,
        )
        self.text_question = FormQuestion.objects.create(
            form=self.form,
            title="Tell us more",
            question_type=FormQuestion.QuestionType.TEXT,
            is_required=True,
            order=2,
        )
        self.url = reverse(
            "public-feedback-submit",
            kwargs={"public_id": self.form.public_id},
        )
        self.technical_data = {
            "ip_address": "127.0.0.1",
            "user_agent": "api-client",
            "fingerprint_hash": "device-123",
            "captcha_passed": True,
        }

    def test_create_submission_with_valid_payload(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Servico muito bom.",
                },
            ],
            "technical_data": self.technical_data,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FeedbackSubmission.objects.count(), 1)
        self.assertEqual(SubmissionAnswer.objects.count(), 2)
        self.assertEqual(response.data["status"], FeedbackSubmission.Status.ACCEPTED)
        self.assertFalse(response.data["analysis_eligible"])
        self.assertTrue(response.data["dashboard_eligible"])

    def test_reject_submission_when_required_question_is_missing(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 4,
                },
            ],
            "technical_data": self.technical_data,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)
        self.assertEqual(FeedbackSubmission.objects.count(), 0)

    def test_reject_submission_when_rating_is_out_of_range(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 8,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Experiencia ok.",
                },
            ],
            "technical_data": self.technical_data,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)
        self.assertEqual(FeedbackSubmission.objects.count(), 0)

    def test_reject_submission_when_text_question_receives_rating_value(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 4,
                },
                {
                    "question_id": self.text_question.id,
                    "rating_value": 2,
                },
            ],
            "technical_data": self.technical_data,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)
        self.assertEqual(FeedbackSubmission.objects.count(), 0)

    def test_reject_submission_when_same_question_is_sent_twice(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 4,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Bom atendimento.",
                },
            ],
            "technical_data": self.technical_data,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)
        self.assertEqual(FeedbackSubmission.objects.count(), 0)
