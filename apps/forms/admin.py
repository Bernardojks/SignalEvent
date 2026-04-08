from django.contrib import admin

from apps.forms.models import FeedbackForm, FormQuestion


@admin.register(FeedbackForm)
class FeedbackFormAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "status",
        "created_at",
    )
    list_filter = ("status", "organization")
    search_fields = ("name", "description", "organization__name")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "form",
        "title",
        "question_type",
        "is_required",
        "order",
    )
    list_filter = ("question_type", "is_required", "form__organization")
    search_fields = ("title", "description", "form__name", "form__organization__name")