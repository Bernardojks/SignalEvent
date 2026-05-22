from django.urls import reverse
from django.core.cache import cache
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.forms.models import FeedbackForm, FormQuestion
from apps.organizations.models import Organization
from apps.submissions.models import (
    FeedbackSubmission,
    SubmissionAnswer,
    SubmissionRiskAssessment,
    SubmissionTechnicalData,
)
from apps.analysis.models import AnalysisJob, FeedbackAnalysis


class PublicFeedbackSubmissionCreateAPITests(APITestCase):
    def setUp(self):
        cache.clear()
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

    def test_strict_security_level_marks_submission_as_suspicious_with_lower_risk_threshold(self):
        self.organization.security_level = Organization.SecurityLevel.STRICT
        self.organization.save(update_fields=["security_level", "updated_at"])
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "ok",
                },
            ],
            "technical_data": {
                "ip_address": "127.0.0.1",
                "user_agent": "api-client",
                "captcha_passed": True,
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], FeedbackSubmission.Status.SUSPICIOUS)
        self.assertFalse(response.data["dashboard_eligible"])

    def test_accept_policy_allows_suspicious_submission(self):
        self.organization.suspicious_submission_policy = (
            Organization.SuspiciousSubmissionPolicy.ACCEPT
        )
        self.organization.save(
            update_fields=["suspicious_submission_policy", "updated_at"]
        )
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Great service.",
                },
            ],
            "technical_data": {
                "ip_address": "127.0.0.1",
                "user_agent": "api-client",
                "fingerprint_hash": "device-123",
                "captcha_passed": False,
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], FeedbackSubmission.Status.ACCEPTED)
        self.assertTrue(response.data["dashboard_eligible"])

    def test_reject_policy_rejects_suspicious_submission(self):
        self.organization.suspicious_submission_policy = (
            Organization.SuspiciousSubmissionPolicy.REJECT
        )
        self.organization.save(
            update_fields=["suspicious_submission_policy", "updated_at"]
        )
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Great service.",
                },
            ],
            "technical_data": {
                "ip_address": "127.0.0.1",
                "user_agent": "api-client",
                "fingerprint_hash": "device-123",
                "captcha_passed": False,
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], FeedbackSubmission.Status.REJECTED)
        self.assertFalse(response.data["dashboard_eligible"])

    @override_settings(
        PUBLIC_SUBMISSION_PROTECTION={
            "request_ip_limit": 2,
            "request_ip_window_seconds": 300,
            "source_limit": 10,
            "source_window_seconds": 600,
            "source_cooldown_seconds": 0,
            "duplicate_window_seconds": 0,
        }
    )
    def test_rejects_too_many_requests_from_same_ip(self):
        for index in range(2):
            response = self.client.post(
                self.url,
                {
                    "answers": [
                        {
                            "question_id": self.rating_question.id,
                            "rating_value": 5,
                        },
                        {
                            "question_id": self.text_question.id,
                            "text_value": f"Feedback {index}",
                        },
                    ],
                    "technical_data": {
                        **self.technical_data,
                        "fingerprint_hash": f"device-{index}",
                    },
                },
                format="json",
                REMOTE_ADDR="10.0.0.10",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.url,
            {
                "answers": [
                    {
                        "question_id": self.rating_question.id,
                        "rating_value": 5,
                    },
                    {
                        "question_id": self.text_question.id,
                        "text_value": "Feedback 3",
                    },
                ],
                "technical_data": {
                    **self.technical_data,
                    "fingerprint_hash": "device-3",
                },
            },
            format="json",
            REMOTE_ADDR="10.0.0.10",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["code"], "request_ip_rate_limited")
        self.assertEqual(FeedbackSubmission.objects.count(), 2)

    @override_settings(
        PUBLIC_SUBMISSION_PROTECTION={
            "request_ip_limit": 10,
            "request_ip_window_seconds": 300,
            "source_limit": 10,
            "source_window_seconds": 600,
            "source_cooldown_seconds": 30,
            "duplicate_window_seconds": 0,
        }
    )
    def test_rejects_when_submission_cooldown_is_active(self):
        first_response = self.client.post(
            self.url,
            {
                "answers": [
                    {
                        "question_id": self.rating_question.id,
                        "rating_value": 5,
                    },
                    {
                        "question_id": self.text_question.id,
                        "text_value": "First feedback",
                    },
                ],
                "technical_data": self.technical_data,
            },
            format="json",
            REMOTE_ADDR="10.0.0.20",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.url,
            {
                "answers": [
                    {
                        "question_id": self.rating_question.id,
                        "rating_value": 4,
                    },
                    {
                        "question_id": self.text_question.id,
                        "text_value": "Second feedback",
                    },
                ],
                "technical_data": self.technical_data,
            },
            format="json",
            REMOTE_ADDR="10.0.0.20",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["code"], "submission_cooldown_active")
        self.assertEqual(FeedbackSubmission.objects.count(), 1)

    @override_settings(
        PUBLIC_SUBMISSION_PROTECTION={
            "request_ip_limit": 10,
            "request_ip_window_seconds": 300,
            "source_limit": 10,
            "source_window_seconds": 600,
            "source_cooldown_seconds": 0,
            "duplicate_window_seconds": 600,
        }
    )
    def test_rejects_duplicate_submission_payload_from_same_source(self):
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Repeated feedback",
                },
            ],
            "technical_data": self.technical_data,
        }

        first_response = self.client.post(
            self.url,
            payload,
            format="json",
            REMOTE_ADDR="10.0.0.30",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.url,
            payload,
            format="json",
            REMOTE_ADDR="10.0.0.30",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["code"], "duplicate_submission_detected")
        self.assertEqual(FeedbackSubmission.objects.count(), 1)

    def test_require_captcha_rejects_submission_when_captcha_is_missing(self):
        self.organization.require_captcha = True
        self.organization.save(update_fields=["require_captcha", "updated_at"])
        payload = {
            "answers": [
                {
                    "question_id": self.rating_question.id,
                    "rating_value": 5,
                },
                {
                    "question_id": self.text_question.id,
                    "text_value": "Great service.",
                },
            ],
            "technical_data": {
                "ip_address": "127.0.0.1",
                "user_agent": "api-client",
                "fingerprint_hash": "device-123",
                "captcha_passed": False,
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], FeedbackSubmission.Status.REJECTED)
        self.assertFalse(response.data["dashboard_eligible"])


class FormSubmissionListAPITests(APITestCase):
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
            name="Main Form",
            description="Customer feedback form",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Form",
            description="Other feedback form",
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
            is_required=False,
            order=2,
        )
        self.submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form,
            status=FeedbackSubmission.Status.ACCEPTED,
            dashboard_eligible=True,
        )
        SubmissionAnswer.objects.create(
            submission=self.submission,
            question=self.rating_question,
            rating_value=5,
        )
        SubmissionAnswer.objects.create(
            submission=self.submission,
            question=self.text_question,
            text_value="Great support.",
        )
        SubmissionRiskAssessment.objects.create(
            submission=self.submission,
            risk_score=10,
            risk_level=SubmissionRiskAssessment.RiskLevel.LOW,
            decision=SubmissionRiskAssessment.Decision.ACCEPTED,
            reasons=[],
        )
        self.suspicious_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form,
            status=FeedbackSubmission.Status.SUSPICIOUS,
            analysis_eligible=False,
            dashboard_eligible=False,
        )
        SubmissionAnswer.objects.create(
            submission=self.suspicious_submission,
            question=self.rating_question,
            rating_value=2,
        )
        SubmissionRiskAssessment.objects.create(
            submission=self.suspicious_submission,
            risk_score=45,
            risk_level=SubmissionRiskAssessment.RiskLevel.MEDIUM,
            decision=SubmissionRiskAssessment.Decision.SUSPICIOUS,
            reasons=["captcha_failed"],
        )
        self.other_submission = FeedbackSubmission.objects.create(
            organization=self.other_organization,
            form=self.other_form,
            status=FeedbackSubmission.Status.REJECTED,
            dashboard_eligible=False,
        )
        self.url = reverse(
            "form-submission-list",
            kwargs={"form_id": self.form.id},
        )
        self.other_form_url = reverse(
            "form-submission-list",
            kwargs={"form_id": self.other_form.id},
        )

    def test_list_returns_only_submissions_from_authenticated_user_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        returned_ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(returned_ids, {self.submission.id, self.suspicious_submission.id})

    def test_list_cannot_access_submissions_from_another_organization_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.other_form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_list_filters_submissions_by_status_and_dashboard_eligibility(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {
                "status": FeedbackSubmission.Status.SUSPICIOUS,
                "dashboard_eligible": "false",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.suspicious_submission.id)

    def test_list_supports_pagination(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {
                "page_size": 1,
                "page": 2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubmissionDetailAPITests(APITestCase):
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
            name="Main Form",
            description="Customer feedback form",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.question = FormQuestion.objects.create(
            form=self.form,
            title="How do you rate us?",
            question_type=FormQuestion.QuestionType.RATING,
            is_required=True,
            order=1,
            min_value=1,
            max_value=5,
        )
        self.submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form,
            status=FeedbackSubmission.Status.ANALYZED,
            analysis_eligible=True,
            dashboard_eligible=True,
        )
        SubmissionAnswer.objects.create(
            submission=self.submission,
            question=self.question,
            rating_value=5,
        )
        SubmissionTechnicalData.objects.create(
            submission=self.submission,
            ip_address="127.0.0.1",
            user_agent="api-client",
            fingerprint_hash="device-123",
            captcha_passed=True,
        )
        SubmissionRiskAssessment.objects.create(
            submission=self.submission,
            risk_score=12,
            risk_level=SubmissionRiskAssessment.RiskLevel.LOW,
            decision=SubmissionRiskAssessment.Decision.ACCEPTED,
            reasons=[],
        )
        AnalysisJob.objects.create(
            submission=self.submission,
            status=AnalysisJob.Status.COMPLETED,
            attempts=1,
        )
        FeedbackAnalysis.objects.create(
            submission=self.submission,
            sentiment="positive",
            urgency="low",
            topics=["support"],
            summary="Customers are happy.",
            raw_response={"provider": "fake"},
        )
        self.other_submission = FeedbackSubmission.objects.create(
            organization=self.other_organization,
            form=FeedbackForm.objects.create(
                organization=self.other_organization,
                name="Other Form",
                description="Other feedback form",
                status=FeedbackForm.Status.ACTIVE,
            ),
            status=FeedbackSubmission.Status.REJECTED,
        )
        self.url = reverse(
            "submission-detail",
            kwargs={"pk": self.submission.id},
        )
        self.other_url = reverse(
            "submission-detail",
            kwargs={"pk": self.other_submission.id},
        )

    def test_detail_returns_submission_with_nested_data(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.submission.id)
        self.assertEqual(response.data["form_name"], "Main Form")
        self.assertEqual(response.data["technical_data"]["ip_address"], "127.0.0.1")
        self.assertEqual(response.data["risk_assessment"]["risk_score"], 12)
        self.assertEqual(response.data["analysis_job"]["status"], AnalysisJob.Status.COMPLETED)
        self.assertEqual(response.data["analysis"]["sentiment"], "positive")
        self.assertEqual(len(response.data["answers"]), 1)

    def test_detail_cannot_access_submission_from_another_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.other_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
