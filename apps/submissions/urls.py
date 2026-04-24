from django.urls import path

from apps.submissions.views import PublicFeedbackSubmissionCreateAPIView

urlpatterns = [
    path(
        "public/forms/<uuid:public_id>/submit/",
        PublicFeedbackSubmissionCreateAPIView.as_view(),
        name="public-feedback-submit",
    ),
]