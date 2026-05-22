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

    def validate(self, attrs):
        question_type = attrs.get(
            "question_type",
            self.instance.question_type if self.instance else None,
        )
        min_value = attrs.get(
            "min_value",
            self.instance.min_value if self.instance else None,
        )
        max_value = attrs.get(
            "max_value",
            self.instance.max_value if self.instance else None,
        )
        order = attrs.get(
            "order",
            self.instance.order if self.instance else None,
        )

        form = self.context.get("form")

        if form and order is not None:
            existing_questions = FormQuestion.objects.filter(
                form=form,
                order=order,
            )

            if self.instance:
                existing_questions = existing_questions.exclude(id=self.instance.id)

            if existing_questions.exists():
                raise serializers.ValidationError(
                    {
                        "order": "This order is already used in this form."
                    }
                )

        if question_type == FormQuestion.QuestionType.RATING:
            if min_value is None:
                raise serializers.ValidationError(
                    {
                        "min_value": "Rating questions require min_value."
                    }
                )

            if max_value is None:
                raise serializers.ValidationError(
                    {
                        "max_value": "Rating questions require max_value."
                    }
                )

            if min_value > max_value:
                raise serializers.ValidationError(
                    {
                        "min_value": "min_value cannot be greater than max_value."
                    }
                )

        if question_type == FormQuestion.QuestionType.TEXT:
            if min_value is not None:
                raise serializers.ValidationError(
                    {
                        "min_value": "Text questions should not have min_value."
                    }
                )

            if max_value is not None:
                raise serializers.ValidationError(
                    {
                        "max_value": "Text questions should not have max_value."
                    }
                )

        return attrs


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


class FormQuestionReorderSerializer(serializers.Serializer):
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )


class FeedbackFormListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=FeedbackForm.Status.choices,
        required=False,
    )
    search = serializers.CharField(required=False, allow_blank=False)
    ordering = serializers.ChoiceField(
        choices=[
            "created_at",
            "-created_at",
            "name",
            "-name",
            "status",
            "-status",
        ],
        required=False,
    )
