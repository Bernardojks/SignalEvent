from django.urls import path

from apps.dashboard.views import DashboardOverviewAPIView

urlpatterns = [
    path(
        "dashboard/overview/",
        DashboardOverviewAPIView.as_view(),
        name="dashboard-overview",
    ),
]