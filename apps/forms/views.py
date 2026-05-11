from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.forms.models import FeedbackForm, FormQuestion
from apps.forms.serializers import (
    FeedbackFormCreateSerializer,
    FeedbackFormSerializer,
    FormQuestionCreateSerializer,
    FormQuestionSerializer,
    PublicFeedbackFormSerializer,
)


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

    def get_queryset(self):
        return (
            FeedbackForm.objects.filter(
                organization=self.request.user.organization,
            )
            .prefetch_related("questions")
            .order_by("-created_at")
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
