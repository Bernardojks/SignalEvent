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