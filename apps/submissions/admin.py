from django.contrib import admin

from apps.submissions.models import FeedbackSubmission, SubmissionAnswer


@admin.register(FeedbackSubmission)
class FeedbackSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "form",
        "organization",
        "status",
        "analysis_eligible",
        "dashboard_eligible",
        "submitted_at",
    )
    list_filter = (
        "status",
        "analysis_eligible",
        "dashboard_eligible",
        "organization",
    )
    search_fields = (
        "form__name",
        "organization__name",
    )
    readonly_fields = (
        "public_id",
        "submitted_at",
        "created_at",
        "updated_at",
    )


@admin.register(SubmissionAnswer)
class SubmissionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "question",
        "rating_value",
    )
    search_fields = (
        "question__title",
        "submission__form__name",
    )