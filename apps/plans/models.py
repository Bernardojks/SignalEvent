from django.db import models

from apps.common.models import BaseModel


class Plan(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    monthly_analysis_limit = models.IntegerField()

    def __str__(self):
        return self.name
    
class OrganizationSubscription(BaseModel):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    active = models.BooleanField(default=True)

    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()

    def __str__(self):
        return f"{self.organization} - {self.plan}"
    
class UsageBucket(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="usage_buckets",
    )

    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    analysis_used = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["period_start", "period_end"]),
        ]

    def __str__(self):
        return f"Usage for {self.organization.name}"
    
class UsageEvent(BaseModel):
    class EventType(models.TextChoices):
        ANALYSIS = "analysis", "Analysis"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="usage_events",
    )

    submission = models.ForeignKey(
        "submissions.FeedbackSubmission",
        on_delete=models.CASCADE,
        related_name="usage_events",
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )

    amount = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.organization.name}"