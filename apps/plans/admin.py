from django.contrib import admin

from apps.plans.models import Plan, OrganizationSubscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "monthly_analysis_limit", "created_at")
    search_fields = ("name", "code")


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "plan",
        "active",
        "current_period_start",
        "current_period_end",
    )
    list_filter = ("active", "plan")
    search_fields = ("organization__name", "plan__name")