from rest_framework import serializers

from apps.organizations.models import Organization


class OrganizationSecuritySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "security_level",
            "suspicious_submission_policy",
            "require_captcha",
        ]
        read_only_fields = [
            "id",
            "name",
            "slug",
        ]
