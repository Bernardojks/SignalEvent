from django.urls import path

from apps.forms.views import (
    FeedbackFormActivateAPIView,
    FeedbackFormDeactivateAPIView,
    FeedbackFormDetailAPIView,
    FeedbackFormListCreateAPIView,
    FormQuestionReorderAPIView,
    FormQuestionDetailAPIView,
    FormQuestionListCreateAPIView,
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
    path(
        "forms/<int:form_id>/activate/",
        FeedbackFormActivateAPIView.as_view(),
        name="feedback-form-activate",
    ),
    path(
        "forms/<int:form_id>/deactivate/",
        FeedbackFormDeactivateAPIView.as_view(),
        name="feedback-form-deactivate",
    ),
    path(
        "forms/<int:form_id>/questions/",
        FormQuestionListCreateAPIView.as_view(),
        name="form-question-list-create",
    ),
    path(
        "forms/<int:form_id>/questions/reorder/",
        FormQuestionReorderAPIView.as_view(),
        name="form-question-reorder",
    ),
    path(
        "forms/<int:form_id>/questions/<int:pk>/",
        FormQuestionDetailAPIView.as_view(),
        name="form-question-detail",
    ),
]
