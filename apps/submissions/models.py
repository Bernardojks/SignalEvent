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
    
class SubmissionTechnicalData(BaseModel):
    submission = models.OneToOneField(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name="technical_data",
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    fingerprint_hash = models.CharField(max_length=255, blank=True)

    accept_language = models.CharField(max_length=255, blank=True)
    referer = models.URLField(blank=True)

    captcha_provider = models.CharField(max_length=100, blank=True)
    captcha_passed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["fingerprint_hash"]),
            models.Index(fields=["ip_address", "created_at"]),
            models.Index(fields=["fingerprint_hash", "created_at"]),
        ]

    def __str__(self):
        return f"Technical data for {self.submission.public_id}"


class SubmissionRiskAssessment(BaseModel):
    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Decision(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        SUSPICIOUS = "suspicious", "Suspicious"
        REJECTED = "rejected", "Rejected"

    submission = models.OneToOneField(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name="risk_assessment",
    )

    risk_score = models.PositiveSmallIntegerField()
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
    )

    reasons = models.JSONField(default=list, blank=True)
    engine_version = models.CharField(max_length=50, default="v1")

    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["decision"]),
            models.Index(fields=["risk_level"]),
            models.Index(fields=["evaluated_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(risk_score__gte=0) & models.Q(risk_score__lte=100),
                name="submission_risk_score_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"Risk assessment for {self.submission.public_id}"
    
