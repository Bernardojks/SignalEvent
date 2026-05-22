from apps.plans.models import Plan
from apps.plans.services import (
    get_active_subscription,
    get_or_create_current_usage_bucket,
    get_subscription_record,
)


def list_available_plans():
    return Plan.objects.all().order_by("monthly_analysis_limit", "name")


def get_current_subscription_data(organization):
    subscription = get_subscription_record(organization)
    if not subscription:
        return {
            "subscription": None,
            "usage": None,
        }

    if subscription.active:
        bucket = get_or_create_current_usage_bucket(organization)
    else:
        bucket = organization.usage_buckets.order_by("-period_end", "-created_at").first()
    usage = None

    if bucket:
        monthly_limit = subscription.plan.monthly_analysis_limit
        usage = {
            "period_start": bucket.period_start,
            "period_end": bucket.period_end,
            "analysis_used": bucket.analysis_used,
            "analysis_remaining": max(monthly_limit - bucket.analysis_used, 0),
            "monthly_analysis_limit": monthly_limit,
        }

    return {
        "subscription": {
            "id": subscription.id,
            "active": subscription.active,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "plan": subscription.plan,
        },
        "usage": usage,
    }
