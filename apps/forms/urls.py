from django.urls import path

from apps.forms.views import (
    FeedbackFormDetailAPIView,
    FeedbackFormListCreateAPIView,
    PublicFeedbackFormDetailAPIView,
)

urlpatterns = [
    path(
        "public/forms/<uuid:public_id>/",
        PublicFeedbackFormDetailAPIView.as_view(),
        name="public-feedback-form-detail",
    ),
    path(
        "forms/",
        FeedbackFormListCreateAPIView.as_view(),
        name="feedback-form-list-create",
    ),
    path(
        "forms/<int:pk>/",
        FeedbackFormDetailAPIView.as_view(),
        name="feedback-form-detail",
    ),
]