from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.forms.models import FeedbackForm
from apps.forms.serializers import PublicFeedbackFormSerializer


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