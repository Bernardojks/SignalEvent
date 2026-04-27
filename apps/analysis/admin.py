from django.contrib import admin

from apps.analysis.models import AnalysisJob, FeedbackAnalysis


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "status", "attempts", "scheduled_at", "processed_at")
    list_filter = ("status",)
    search_fields = ("submission__public_id",)


@admin.register(FeedbackAnalysis)
class FeedbackAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "sentiment", "urgency", "processed_at")
    list_filter = ("sentiment", "urgency")
    search_fields = ("submission__public_id", "summary")