from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.models import FeedbackForm, FormQuestion
from apps.submissions.serializers import PublicFeedbackSubmissionCreateSerializer
from apps.submissions.services import submit_feedback


class PublicFeedbackSubmissionCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, public_id):
        serializer = PublicFeedbackSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            form = (
                FeedbackForm.objects
                .prefetch_related("questions")
                .get(public_id=public_id, status=FeedbackForm.Status.ACTIVE)
            )
        except FeedbackForm.DoesNotExist:
            return Response(
                {"detail": "Form not found or not active."},
                status=status.HTTP_404_NOT_FOUND,
            )

        questions_by_id = {question.id: question for question in form.questions.all()}
        answers_data = []

        for item in serializer.validated_data["answers"]:
            question = questions_by_id.get(item["question_id"])
            if not question:
                return Response(
                    {"detail": f"Question {item['question_id']} does not belong to this form."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            answer_payload = {"question": question}

            if question.question_type == FormQuestion.QuestionType.RATING:
                if "rating_value" not in item:
                    return Response(
                        {"detail": f"Question {question.id} requires rating_value."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                answer_payload["rating_value"] = item["rating_value"]

            elif question.question_type == FormQuestion.QuestionType.TEXT:
                answer_payload["text_value"] = item.get("text_value", "")

            answers_data.append(answer_payload)

        submission = submit_feedback(
            form=form,
            answers_data=answers_data,
            technical_data=serializer.validated_data["technical_data"],
            risk_data=serializer.validated_data["risk_data"],
        )

        return Response(
            {
                "public_id": str(submission.public_id),
                "status": submission.status,
                "analysis_eligible": submission.analysis_eligible,
                "dashboard_eligible": submission.dashboard_eligible,
            },
            status=status.HTTP_201_CREATED,
        )