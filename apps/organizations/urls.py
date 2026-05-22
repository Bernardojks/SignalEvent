from django.urls import path

from apps.organizations.views import OrganizationSecuritySettingsAPIView

urlpatterns = [
    path(
        "organization/security/",
        OrganizationSecuritySettingsAPIView.as_view(),
        name="organization-security-settings",
    ),
]
