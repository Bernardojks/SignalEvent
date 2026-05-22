from rest_framework import serializers


class DashboardOverviewQuerySerializer(serializers.Serializer):
    form_id = serializers.IntegerField(required=False)
    submitted_after = serializers.DateTimeField(required=False)
    submitted_before = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        submitted_after = attrs.get("submitted_after")
        submitted_before = attrs.get("submitted_before")

        if (
            submitted_after is not None
            and submitted_before is not None
            and submitted_after > submitted_before
        ):
            raise serializers.ValidationError(
                "submitted_after cannot be greater than submitted_before."
            )

        return attrs
