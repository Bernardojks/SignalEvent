import uuid

from django.db import models

from apps.common.models import BaseModel


class FeedbackSubmission(BaseModel):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        VALIDATED = "validated", "Validated"
        ACCEPTED = "accepted", "Accepted"
        SUSPICIOUS = "suspicious", "Suspicious"
        REJECTED = "rejected", "Rejected"
        QUEUED_FOR_ANALYSIS = "queued_for_analysis", "Queued for analysis"
        ANALYZED = "analyzed", "Analyzed"
        ANALYSIS_FAILED = "analysis_failed", "Analysis failed"
        ANALYSIS_SKIPPED_LIMIT = "analysis_skipped_limit", "Analysis skipped limit"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    form = models.ForeignKey(
        "forms.FeedbackForm",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.RECEIVED,
    )

    analysis_eligible = models.BooleanField(default=False)
    dashboard_eligible = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    suspicious_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["form"]),
            models.Index(fields=["status"]),
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["organization", "submitted_at"]),
            models.Index(fields=["organization", "status", "submitted_at"]),
            models.Index(fields=["form", "submitted_at"]),
        ]

    def __str__(self):
        return f"Submission {self.public_id} - {self.form.name}"
    

class SubmissionAnswer(BaseModel):
    submission = models.ForeignKey(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "forms.FormQuestion",
        on_delete=models.CASCADE,
        related_name="answers",
    )

    rating_value = models.PositiveSmallIntegerField(null=True, blank=True)
    text_value = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission"]),
            models.Index(fields=["question"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_question_in_submission",
            ),
        ]

    def __str__(self):
        return f"Answer for {self.question.title}"