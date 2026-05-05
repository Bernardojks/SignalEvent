from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.forms.models import FeedbackForm
from apps.forms.serializers import (
    FeedbackFormCreateSerializer,
    FeedbackFormSerializer,
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
            FeedbackForm.objects.filter(organization=self.request.user.organization)
            .prefetch_related("questions")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FeedbackFormCreateSerializer
        return FeedbackFormSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class FeedbackFormDetailAPIView(generics.RetrieveAPIView):
    serializer_class = FeedbackFormSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            FeedbackForm.objects.filter(organization=self.request.user.organization)
            .prefetch_related("questions")
        )