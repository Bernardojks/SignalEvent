from rest_framework import serializers

from apps.analysis.models import AnalysisJob, FeedbackAnalysis
from apps.submissions.models import (
    FeedbackSubmission,
    SubmissionAnswer,
    SubmissionRiskAssessment,
    SubmissionTechnicalData,
)
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


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source="question.id", read_only=True)
    question_title = serializers.CharField(source="question.title", read_only=True)
    question_type = serializers.CharField(source="question.question_type", read_only=True)

    class Meta:
        model = SubmissionAnswer
        fields = [
            "question_id",
            "question_title",
            "question_type",
            "rating_value",
            "text_value",
        ]


class FeedbackSubmissionListSerializer(serializers.ModelSerializer):
    answers = SubmissionAnswerSerializer(many=True, read_only=True)
    risk_score = serializers.IntegerField(
        source="risk_assessment.risk_score",
        read_only=True,
    )
    risk_level = serializers.CharField(
        source="risk_assessment.risk_level",
        read_only=True,
    )
    risk_decision = serializers.CharField(
        source="risk_assessment.decision",
        read_only=True,
    )

    class Meta:
        model = FeedbackSubmission
        fields = [
            "id",
            "public_id",
            "status",
            "analysis_eligible",
            "dashboard_eligible",
            "submitted_at",
            "accepted_at",
            "rejected_at",
            "suspicious_at",
            "risk_score",
            "risk_level",
            "risk_decision",
            "answers",
        ]


class SubmissionTechnicalDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionTechnicalData
        fields = [
            "ip_address",
            "user_agent",
            "fingerprint_hash",
            "accept_language",
            "referer",
            "captcha_provider",
            "captcha_passed",
        ]


class SubmissionRiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionRiskAssessment
        fields = [
            "risk_score",
            "risk_level",
            "decision",
            "reasons",
            "engine_version",
            "evaluated_at",
        ]


class AnalysisJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisJob
        fields = [
            "status",
            "attempts",
            "last_error",
            "scheduled_at",
            "processed_at",
        ]


class FeedbackAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackAnalysis
        fields = [
            "sentiment",
            "urgency",
            "topics",
            "summary",
            "raw_response",
            "processed_at",
        ]


class FeedbackSubmissionDetailSerializer(serializers.ModelSerializer):
    form_id = serializers.IntegerField(source="form.id", read_only=True)
    form_public_id = serializers.UUIDField(source="form.public_id", read_only=True)
    form_name = serializers.CharField(source="form.name", read_only=True)
    answers = SubmissionAnswerSerializer(many=True, read_only=True)
    technical_data = SubmissionTechnicalDataSerializer(read_only=True)
    risk_assessment = SubmissionRiskAssessmentSerializer(read_only=True)
    analysis_job = AnalysisJobSerializer(read_only=True)
    analysis = FeedbackAnalysisSerializer(read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = [
            "id",
            "public_id",
            "form_id",
            "form_public_id",
            "form_name",
            "status",
            "analysis_eligible",
            "dashboard_eligible",
            "submitted_at",
            "accepted_at",
            "rejected_at",
            "suspicious_at",
            "technical_data",
            "risk_assessment",
            "analysis_job",
            "analysis",
            "answers",
        ]


class SubmissionListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=FeedbackSubmission.Status.choices,
        required=False,
    )
    dashboard_eligible = serializers.BooleanField(required=False)
    analysis_eligible = serializers.BooleanField(required=False)
    submitted_after = serializers.DateTimeField(required=False)
    submitted_before = serializers.DateTimeField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            "submitted_at",
            "-submitted_at",
            "status",
            "-status",
        ],
        required=False,
    )
