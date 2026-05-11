from rest_framework import serializers

from apps.submissions.validators import validate_public_submission_answers


class SubmissionAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    rating_value = serializers.IntegerField(required=False)
    text_value = serializers.CharField(required=False, allow_blank=True)


class SubmissionTechnicalDataInputSerializer(serializers.Serializer):
    ip_address = serializers.IPAddressField()
    user_agent = serializers.CharField(required=False, allow_blank=True)
    fingerprint_hash = serializers.CharField(required=False, allow_blank=True)
    accept_language = serializers.CharField(required=False, allow_blank=True)
    referer = serializers.CharField(required=False, allow_blank=True)
    captcha_provider = serializers.CharField(required=False, allow_blank=True)
    captcha_passed = serializers.BooleanField(default=False)


class PublicFeedbackSubmissionCreateSerializer(serializers.Serializer):
    answers = SubmissionAnswerInputSerializer(many=True)
    technical_data = SubmissionTechnicalDataInputSerializer()

    def validate(self, attrs):
        form = self.context.get("form")
        if form is None:
            raise serializers.ValidationError("Form context is required.")

        attrs["validated_answers"] = validate_public_submission_answers(
            form=form,
            answers=attrs["answers"],
        )
        return attrs
