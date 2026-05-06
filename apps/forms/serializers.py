from rest_framework import serializers

from apps.forms.models import FeedbackForm, FormQuestion


class FormQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = [
            "id",
            "title",
            "description",
            "question_type",
            "is_required",
            "order",
            "min_value",
            "max_value",
        ]


class FormQuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = [
            "title",
            "description",
            "question_type",
            "is_required",
            "order",
            "min_value",
            "max_value",
        ]


class PublicFeedbackFormSerializer(serializers.ModelSerializer):
    questions = FormQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackForm
        fields = [
            "public_id",
            "name",
            "description",
            "status",
            "questions",
        ]


class FeedbackFormSerializer(serializers.ModelSerializer):
    questions = FormQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackForm
        fields = [
            "id",
            "public_id",
            "name",
            "description",
            "status",
            "questions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "updated_at"]


class FeedbackFormCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackForm
        fields = [
            "name",
            "description",
            "status",
        ]