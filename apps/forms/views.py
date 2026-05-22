from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardResultsSetPagination
from apps.forms.models import FeedbackForm, FormQuestion
from apps.forms.selectors import get_feedback_forms_for_organization
from apps.forms.serializers import (
    FeedbackFormCreateSerializer,
    FeedbackFormListQuerySerializer,
    FeedbackFormSerializer,
    FormQuestionReorderSerializer,
    FormQuestionCreateSerializer,
    FormQuestionSerializer,
    PublicFeedbackFormSerializer,
)
from apps.forms.services import activate_form, deactivate_form, reorder_form_questions


class PublicFeedbackFormDetailAPIView(generics.RetrieveAPIView):
    serializer_class = PublicFeedbackFormSerializer
    permission_classes = [AllowAny]
    lookup_field = "public_id"

    def get_queryset(self):
        return (
            FeedbackForm.objects.filter(status=FeedbackForm.Status.ACTIVE)
            .select_related("organization")
            .prefetch_related("questions")
        )


class FeedbackFormListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_filter_data(self):
        if not hasattr(self, "_filter_data"):
            serializer = FeedbackFormListQuerySerializer(
                data=self.request.query_params.dict()
            )
            serializer.is_valid(raise_exception=True)
            self._filter_data = serializer.validated_data
        return self._filter_data

    def get_queryset(self):
        return get_feedback_forms_for_organization(
            organization=self.request.user.organization,
            filters=self.get_filter_data(),
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FeedbackFormCreateSerializer
        return FeedbackFormSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class FeedbackFormDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            FeedbackForm.objects.filter(
                organization=self.request.user.organization,
            )
            .prefetch_related("questions")
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FeedbackFormCreateSerializer
        return FeedbackFormSerializer


class FormQuestionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_form(self):
        return get_object_or_404(
            FeedbackForm,
            id=self.kwargs["form_id"],
            organization=self.request.user.organization,
        )

    def get_queryset(self):
        form = self.get_form()
        return form.questions.all().order_by("order")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FormQuestionCreateSerializer
        return FormQuestionSerializer

    def perform_create(self, serializer):
        form = self.get_form()
        serializer.save(form=form)


class FormQuestionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FormQuestion.objects.filter(
            form_id=self.kwargs["form_id"],
            form__organization=self.request.user.organization,
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FormQuestionCreateSerializer
        return FormQuestionSerializer


class FeedbackFormActivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, form_id):
        form = get_object_or_404(
            FeedbackForm,
            id=form_id,
            organization=request.user.organization,
        )

        try:
            activate_form(form)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FeedbackFormSerializer(form)
        return Response(serializer.data)


class FeedbackFormDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, form_id):
        form = get_object_or_404(
            FeedbackForm,
            id=form_id,
            organization=request.user.organization,
        )

        try:
            deactivate_form(form)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FeedbackFormSerializer(form)
        return Response(serializer.data)


class FormQuestionReorderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, form_id):
        form = get_object_or_404(
            FeedbackForm,
            id=form_id,
            organization=request.user.organization,
        )

        serializer = FormQuestionReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            questions = reorder_form_questions(
                form=form,
                question_ids=serializer.validated_data["question_ids"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = FormQuestionSerializer(questions, many=True)
        return Response(response_serializer.data)
