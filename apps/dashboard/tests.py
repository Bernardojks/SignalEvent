from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.analysis.models import FeedbackAnalysis
from apps.forms.models import FeedbackForm, FormQuestion
from apps.organizations.models import Organization
from apps.plans.models import OrganizationSubscription, Plan, UsageBucket
from apps.submissions.models import FeedbackSubmission, SubmissionAnswer


class DashboardOverviewAPITests(APITestCase):
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
        now = timezone.now()
        self.plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        self.subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            active=True,
            current_period_start=now - timedelta(days=5),
            current_period_end=now + timedelta(days=25),
        )
        UsageBucket.objects.create(
            organization=self.organization,
            period_start=self.subscription.current_period_start,
            period_end=self.subscription.current_period_end,
            analysis_used=7,
        )
        self.form_one = FeedbackForm.objects.create(
            organization=self.organization,
            name="Main Form",
            description="Customer feedback form",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.form_two = FeedbackForm.objects.create(
            organization=self.organization,
            name="Support Form",
            description="Support follow-up",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.other_form = FeedbackForm.objects.create(
            organization=self.other_organization,
            name="Other Form",
            description="Other feedback form",
            status=FeedbackForm.Status.ACTIVE,
        )
        self.rating_question_one = FormQuestion.objects.create(
            form=self.form_one,
            title="How do you rate us?",
            question_type=FormQuestion.QuestionType.RATING,
            is_required=True,
            order=1,
            min_value=1,
            max_value=5,
        )
        self.rating_question_two = FormQuestion.objects.create(
            form=self.form_two,
            title="How was support?",
            question_type=FormQuestion.QuestionType.RATING,
            is_required=True,
            order=1,
            min_value=1,
            max_value=5,
        )
        self.text_question_one = FormQuestion.objects.create(
            form=self.form_one,
            title="Tell us more",
            question_type=FormQuestion.QuestionType.TEXT,
            is_required=False,
            order=2,
        )
        self.accepted_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form_one,
            status=FeedbackSubmission.Status.ANALYZED,
            analysis_eligible=True,
            dashboard_eligible=True,
        )
        self.suspicious_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form_one,
            status=FeedbackSubmission.Status.SUSPICIOUS,
            analysis_eligible=False,
            dashboard_eligible=False,
        )
        self.rejected_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form_two,
            status=FeedbackSubmission.Status.REJECTED,
            analysis_eligible=False,
            dashboard_eligible=False,
        )
        FeedbackSubmission.objects.create(
            organization=self.other_organization,
            form=self.other_form,
            status=FeedbackSubmission.Status.ACCEPTED,
            dashboard_eligible=True,
        )
        SubmissionAnswer.objects.create(
            submission=self.accepted_submission,
            question=self.rating_question_one,
            rating_value=5,
        )
        SubmissionAnswer.objects.create(
            submission=self.accepted_submission,
            question=self.text_question_one,
            text_value="Great support.",
        )
        SubmissionAnswer.objects.create(
            submission=self.suspicious_submission,
            question=self.rating_question_one,
            rating_value=3,
        )
        SubmissionAnswer.objects.create(
            submission=self.rejected_submission,
            question=self.rating_question_two,
            rating_value=1,
        )
        FeedbackAnalysis.objects.create(
            submission=self.accepted_submission,
            sentiment="positive",
            urgency="low",
            topics=["support"],
            summary="Customers are happy.",
            raw_response={"provider": "fake"},
        )
        self.rejected_submission.submitted_at = now - timedelta(days=10)
        self.rejected_submission.save(update_fields=["submitted_at"])
        self.url = reverse("dashboard-overview")

    def test_returns_richer_dashboard_overview(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_submissions"], 3)
        self.assertEqual(response.data["accepted_submissions"], 1)
        self.assertEqual(response.data["suspicious_submissions"], 1)
        self.assertEqual(response.data["rejected_submissions"], 1)
        self.assertEqual(response.data["average_rating"], 3.0)
        self.assertEqual(response.data["usage_summary"]["analysis_used"], 7)
        self.assertEqual(response.data["usage_summary"]["analysis_remaining"], 93)
        self.assertEqual(len(response.data["top_forms"]), 2)
        self.assertEqual(response.data["top_forms"][0]["name"], "Main Form")
        self.assertEqual(response.data["recent_analyses"][0]["summary"], "Customers are happy.")
        self.assertEqual(len(response.data["recent_submissions"]), 3)

    def test_can_filter_overview_by_form_and_period(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.url,
            {
                "form_id": self.form_one.id,
                "submitted_after": (timezone.now() - timedelta(days=2)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scope"]["form_id"], self.form_one.id)
        self.assertEqual(response.data["total_submissions"], 2)
        self.assertEqual(len(response.data["top_forms"]), 1)
        self.assertEqual(response.data["top_forms"][0]["name"], "Main Form")

    def test_cannot_filter_overview_with_form_from_another_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, {"form_id": self.other_form.id})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FormAnalyticsAPITests(APITestCase):
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
        self.accepted_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form,
            status=FeedbackSubmission.Status.ANALYZED,
            analysis_eligible=True,
            dashboard_eligible=True,
        )
        self.suspicious_submission = FeedbackSubmission.objects.create(
            organization=self.organization,
            form=self.form,
            status=FeedbackSubmission.Status.SUSPICIOUS,
            analysis_eligible=False,
            dashboard_eligible=False,
        )
        SubmissionAnswer.objects.create(
            submission=self.accepted_submission,
            question=self.rating_question,
            rating_value=5,
        )
        SubmissionAnswer.objects.create(
            submission=self.accepted_submission,
            question=self.text_question,
            text_value="Great support.",
        )
        SubmissionAnswer.objects.create(
            submission=self.suspicious_submission,
            question=self.rating_question,
            rating_value=3,
        )
        FeedbackAnalysis.objects.create(
            submission=self.accepted_submission,
            sentiment="positive",
            urgency="low",
            topics=["support"],
            summary="Customers are happy.",
            raw_response={"provider": "fake"},
        )
        self.url = reverse(
            "form-analytics",
            kwargs={"form_id": self.form.id},
        )
        self.other_form_url = reverse(
            "form-analytics",
            kwargs={"form_id": self.other_form.id},
        )

    def test_returns_analytics_for_authenticated_user_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["form"]["name"], "Main Form")
        self.assertEqual(response.data["total_submissions"], 2)
        self.assertEqual(response.data["accepted_submissions"], 1)
        self.assertEqual(response.data["suspicious_submissions"], 1)
        self.assertEqual(response.data["rejected_submissions"], 0)
        self.assertEqual(response.data["analyzed_submissions"], 1)
        self.assertEqual(response.data["average_rating"], 4.0)
        self.assertEqual(len(response.data["rating_questions"]), 1)
        self.assertEqual(response.data["rating_questions"][0]["responses_count"], 2)
        self.assertEqual(response.data["sentiment_breakdown"][0]["sentiment"], "positive")
        self.assertEqual(response.data["recent_analyses"][0]["summary"], "Customers are happy.")

    def test_cannot_access_analytics_from_another_organization_form(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.other_form_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
