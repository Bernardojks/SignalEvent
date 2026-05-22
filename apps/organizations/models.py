from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel


class Organization(BaseModel):
    class SecurityLevel(models.TextChoices):
        RELAXED = "relaxed", "Relaxed"
        STANDARD = "standard", "Standard"
        STRICT = "strict", "Strict"

    class SuspiciousSubmissionPolicy(models.TextChoices):
        FLAG = "flag", "Flag"
        ACCEPT = "accept", "Accept"
        REJECT = "reject", "Reject"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    security_level = models.CharField(
        max_length=20,
        choices=SecurityLevel.choices,
        default=SecurityLevel.STANDARD,
    )
    suspicious_submission_policy = models.CharField(
        max_length=20,
        choices=SuspiciousSubmissionPolicy.choices,
        default=SuspiciousSubmissionPolicy.FLAG,
    )
    require_captcha = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 1

            while Organization.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"

            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
