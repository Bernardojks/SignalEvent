from django.db import models

from apps.common.models import BaseModel


class AnalysisJob(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    submission = models.OneToOneField(
        "submissions.FeedbackSubmission",
        on_delete=models.CASCADE,
        related_name="analysis_job",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    scheduled_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self):
        return f"Job for {self.submission.public_id}"
    

class FeedbackAnalysis(BaseModel):
    submission = models.OneToOneField(
        "submissions.FeedbackSubmission",
        on_delete=models.CASCADE,
        related_name="analysis",
    )

    sentiment = models.CharField(max_length=20)
    urgency = models.CharField(max_length=20)

    topics = models.JSONField(default=list)
    summary = models.TextField()

    raw_response = models.JSONField()

    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.submission.public_id}"