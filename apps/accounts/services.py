from datetime import timedelta

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.plans.models import OrganizationSubscription, Plan, UsageBucket


def get_default_plan():
    return Plan.objects.order_by("monthly_analysis_limit", "name").first()


@transaction.atomic
def register_company_account(
    organization_name,
    email,
    password,
    full_name="",
):
    organization = Organization.objects.create(name=organization_name)
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        organization=organization,
    )

    default_plan = get_default_plan()
    if default_plan:
        period_start = timezone.now()
        period_end = period_start + timedelta(days=30)
        OrganizationSubscription.objects.create(
            organization=organization,
            plan=default_plan,
            active=True,
            current_period_start=period_start,
            current_period_end=period_end,
        )
        UsageBucket.objects.create(
            organization=organization,
            period_start=period_start,
            period_end=period_end,
            analysis_used=0,
        )

    return user


def authenticate_company_user(email, password):
    return authenticate(email=email, password=password)


def generate_auth_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def blacklist_refresh_token(refresh_token):
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        return False

    return True
