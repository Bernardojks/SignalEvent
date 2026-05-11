from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.models import FeedbackForm
from apps.submissions.serializers import PublicFeedbackSubmissionCreateSerializer
from apps.submissions.services import submit_feedback


class PublicFeedbackSubmissionCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, public_id):
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

        serializer = PublicFeedbackSubmissionCreateSerializer(
            data=request.data,
            context={"form": form},
        )
        serializer.is_valid(raise_exception=True)

        submission = submit_feedback(
            form=form,
            answers_data=serializer.validated_data["validated_answers"],
            technical_data=serializer.validated_data["technical_data"],
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
