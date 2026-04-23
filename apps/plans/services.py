from django.db import transaction
from django.utils import timezone

from apps.plans.models import OrganizationSubscription, UsageBucket, UsageEvent


def get_active_subscription(organization):
    return OrganizationSubscription.objects.filter(
        organization=organization,
        active=True,
    ).select_related("plan").first()


def get_or_create_current_usage_bucket(organization):
    now = timezone.now()

    bucket = UsageBucket.objects.filter(
        organization=organization,
        period_start__lte=now,
        period_end__gte=now,
    ).first()

    if bucket:
        return bucket

    subscription = get_active_subscription(organization)
    if not subscription:
        return None

    bucket = UsageBucket.objects.create(
        organization=organization,
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
        analysis_used=0,
    )
    return bucket


def has_available_analysis_quota(organization):
    subscription = get_active_subscription(organization)
    if not subscription:
        return False

    bucket = get_or_create_current_usage_bucket(organization)
    if not bucket:
        return False

    return bucket.analysis_used < subscription.plan.monthly_analysis_limit


@transaction.atomic
def consume_analysis_quota(organization, submission):
    subscription = get_active_subscription(organization)
    if not subscription:
        raise ValueError("Organization has no active subscription.")

    bucket = get_or_create_current_usage_bucket(organization)
    if not bucket:
        raise ValueError("No usage bucket available.")

    if bucket.analysis_used >= subscription.plan.monthly_analysis_limit:
        raise ValueError("Analysis quota exceeded.")

    bucket.analysis_used += 1
    bucket.save(update_fields=["analysis_used", "updated_at"])

    UsageEvent.objects.create(
        organization=organization,
        submission=submission,
        event_type=UsageEvent.EventType.ANALYSIS,
        amount=1,
    )

    return bucket