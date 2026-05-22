from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.plans.models import OrganizationSubscription, Plan, UsageBucket


class PlanListAPITests(APITestCase):
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
        self.starter_plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        self.pro_plan = Plan.objects.create(
            name="Pro",
            code="pro",
            monthly_analysis_limit=500,
        )
        self.url = reverse("plan-list")

    def test_returns_available_plans_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["code"], "starter")
        self.assertEqual(response.data[1]["code"], "pro")

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CurrentSubscriptionAPITests(APITestCase):
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
        self.plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        now = timezone.now()
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
            analysis_used=12,
        )
        self.url = reverse("current-subscription")

    def test_returns_subscription_and_usage_summary(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subscription"]["plan"]["code"], "starter")
        self.assertEqual(response.data["subscription"]["plan"]["monthly_analysis_limit"], 100)
        self.assertEqual(response.data["usage"]["analysis_used"], 12)
        self.assertEqual(response.data["usage"]["analysis_remaining"], 88)

    def test_returns_null_when_user_has_no_organization(self):
        user_without_org = User.objects.create_user(
            email="no-org@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=user_without_org)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["subscription"])
        self.assertIsNone(response.data["usage"])

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChangeCurrentPlanAPITests(APITestCase):
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
        self.starter_plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        self.pro_plan = Plan.objects.create(
            name="Pro",
            code="pro",
            monthly_analysis_limit=500,
        )
        now = timezone.now()
        self.subscription = OrganizationSubscription.objects.create(
            organization=self.organization,
            plan=self.starter_plan,
            active=True,
            current_period_start=now - timedelta(days=5),
            current_period_end=now + timedelta(days=25),
        )
        self.url = reverse("change-current-plan")

    def test_changes_current_plan(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"plan_code": "pro"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.plan.code, "pro")
        self.assertTrue(self.subscription.active)
        self.assertEqual(response.data["subscription"]["plan"]["code"], "pro")

    def test_rejects_switching_to_same_plan(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"plan_code": "starter"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Organization is already on this plan.")

    def test_requires_authentication(self):
        response = self.client.post(
            self.url,
            {"plan_code": "pro"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CancelCurrentPlanAPITests(APITestCase):
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
        self.plan = Plan.objects.create(
            name="Starter",
            code="starter",
            monthly_analysis_limit=100,
        )
        now = timezone.now()
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
            analysis_used=12,
        )
        self.url = reverse("cancel-current-plan")
        self.current_url = reverse("current-subscription")

    def test_cancels_current_subscription(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.active)
        self.assertFalse(response.data["subscription"]["active"])

    def test_current_subscription_returns_latest_inactive_subscription_after_cancel(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)

        response = self.client.get(self.current_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["subscription"]["active"])
        self.assertEqual(response.data["subscription"]["plan"]["code"], "starter")

    def test_requires_authentication(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
