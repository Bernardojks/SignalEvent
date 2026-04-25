from rest_framework import serializers

from apps.forms.models import FormQuestion


class SubmissionAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    rating_value = serializers.IntegerField(required=False)
    text_value = serializers.CharField(required=False, allow_blank=True)

    def validate_question_id(self, value):
        if not FormQuestion.objects.filter(id=value).exists():
            raise serializers.ValidationError("Question does not exist.")
        return value


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
        answers = attrs["answers"]
        question_ids = [item["question_id"] for item in answers]

        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Duplicate questions are not allowed.")

        return attrs