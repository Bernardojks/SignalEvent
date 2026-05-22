from django.urls import path

from apps.dashboard.views import DashboardOverviewAPIView, FormAnalyticsAPIView

urlpatterns = [
    path(
        "dashboard/overview/",
        DashboardOverviewAPIView.as_view(),
        name="dashboard-overview",
    ),
    path(
        "forms/<int:form_id>/analytics/",
        FormAnalyticsAPIView.as_view(),
        name="form-analytics",
    ),
]
