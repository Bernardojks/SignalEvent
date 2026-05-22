from django.urls import path

from apps.plans.views import (
    CancelCurrentPlanAPIView,
    ChangeCurrentPlanAPIView,
    CurrentSubscriptionAPIView,
    PlanListAPIView,
)

urlpatterns = [
    path(
        "plans/",
        PlanListAPIView.as_view(),
        name="plan-list",
    ),
    path(
        "plans/current/",
        CurrentSubscriptionAPIView.as_view(),
        name="current-subscription",
    ),
    path(
        "plans/current/change/",
        ChangeCurrentPlanAPIView.as_view(),
        name="change-current-plan",
    ),
    path(
        "plans/current/cancel/",
        CancelCurrentPlanAPIView.as_view(),
        name="cancel-current-plan",
    ),
]
