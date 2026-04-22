from django.contrib import admin

from apps.submissions.models import (
    FeedbackSubmission,
    SubmissionAnswer,
    SubmissionRiskAssessment,
    SubmissionTechnicalData,
)


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


@admin.register(SubmissionTechnicalData)
class SubmissionTechnicalDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "ip_address",
        "captcha_passed",
        "created_at",
    )
    search_fields = (
        "submission__form__name",
        "ip_address",
        "fingerprint_hash",
    )


@admin.register(SubmissionRiskAssessment)
class SubmissionRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "risk_score",
        "risk_level",
        "decision",
        "evaluated_at",
    )
    list_filter = ("risk_level", "decision")
    search_fields = (
        "submission__form__name",
        "submission__organization__name",
    )