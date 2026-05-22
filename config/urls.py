from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.organizations.urls")),
    path("api/", include("apps.forms.urls")),
    path("api/", include("apps.dashboard.urls")),
    path("api/", include("apps.plans.urls")),
    path("api/", include("apps.submissions.urls")),
]
