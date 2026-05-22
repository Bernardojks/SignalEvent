from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardResultsSetPagination
from apps.forms.models import FeedbackForm
from apps.submissions.abuse_prevention import (
    SubmissionAbuseError,
    enforce_public_submission_request_limit,
    enforce_public_submission_source_protection,
)
from apps.submissions.selectors import get_form_submissions_for_organization
from apps.submissions.serializers import (
    FeedbackSubmissionDetailSerializer,
    FeedbackSubmissionListSerializer,
    PublicFeedbackSubmissionCreateSerializer,
    SubmissionListQuerySerializer,
)
from apps.submissions.services import submit_feedback
from apps.submissions.models import FeedbackSubmission


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

        try:
            request_ip = enforce_public_submission_request_limit(
                form=form,
                request=request,
            )
            serializer = PublicFeedbackSubmissionCreateSerializer(
                data=request.data,
                context={"form": form},
            )
            serializer.is_valid(raise_exception=True)
            enforce_public_submission_source_protection(
                form=form,
                request_ip=request_ip,
                technical_data=serializer.validated_data["technical_data"],
                answers_data=serializer.validated_data["validated_answers"],
            )
            submission = submit_feedback(
                form=form,
                answers_data=serializer.validated_data["validated_answers"],
                technical_data=serializer.validated_data["technical_data"],
            )
        except SubmissionAbuseError as exc:
            return Response(
                {
                    "detail": exc.detail,
                    "code": exc.code,
                    "retry_after_seconds": exc.retry_after_seconds,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
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


class FormSubmissionListAPIView(generics.ListAPIView):
    serializer_class = FeedbackSubmissionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_filter_data(self):
        if not hasattr(self, "_filter_data"):
            serializer = SubmissionListQuerySerializer(
                data=self.request.query_params.dict()
            )
            serializer.is_valid(raise_exception=True)
            self._filter_data = serializer.validated_data
        return self._filter_data

    def get_queryset(self):
        return get_form_submissions_for_organization(
            form_id=self.kwargs["form_id"],
            organization=self.request.user.organization,
            filters=self.get_filter_data(),
        )


class SubmissionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = FeedbackSubmissionDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            FeedbackSubmission.objects.filter(
                organization=self.request.user.organization,
            )
            .select_related("form")
            .prefetch_related(
                "technical_data",
                "risk_assessment",
                "analysis_job",
                "analysis",
                "answers__question",
            )
        )
