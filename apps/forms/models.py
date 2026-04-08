import uuid

from django.db import models

from apps.common.models import BaseModel


class FeedbackForm(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="forms",
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    

class FormQuestion(BaseModel):
    class QuestionType(models.TextChoices):
        RATING = "rating", "Rating"
        TEXT = "text", "Text"

    form = models.ForeignKey(
        FeedbackForm,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
    )

    is_required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()

    min_value = models.PositiveSmallIntegerField(null=True, blank=True)
    max_value = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        indexes = [
            models.Index(fields=["form"]),
            models.Index(fields=["form", "order"]),
            models.Index(fields=["question_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["form", "order"],
                name="unique_question_order_per_form",
            ),
        ]

    def __str__(self):
        return f"{self.form.name} - {self.title}"