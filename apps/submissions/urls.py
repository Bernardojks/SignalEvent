from django.urls import path

from apps.submissions.views import (
    FormSubmissionListAPIView,
    PublicFeedbackSubmissionCreateAPIView,
    SubmissionDetailAPIView,
)

urlpatterns = [
    path(
        "public/forms/<uuid:public_id>/submit/",
        PublicFeedbackSubmissionCreateAPIView.as_view(),
        name="public-feedback-submit",
    ),
    path(
        "forms/<int:form_id>/submissions/",
        FormSubmissionListAPIView.as_view(),
        name="form-submission-list",
    ),
    path(
        "submissions/<int:pk>/",
        SubmissionDetailAPIView.as_view(),
        name="submission-detail",
    ),
]
