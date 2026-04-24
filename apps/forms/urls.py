from django.urls import path

from apps.forms.views import PublicFeedbackFormDetailAPIView

urlpatterns = [
    path(
        "public/forms/<uuid:public_id>/",
        PublicFeedbackFormDetailAPIView.as_view(),
        name="public-feedback-form-detail",
    ),
]