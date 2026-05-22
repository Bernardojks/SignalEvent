from django.db.models import Q

from apps.forms.models import FeedbackForm


def get_feedback_forms_for_organization(organization, filters):
    queryset = FeedbackForm.objects.filter(
        organization=organization,
    ).prefetch_related("questions")

    status = filters.get("status")
    search = filters.get("search")
    ordering = filters.get("ordering", "-created_at")

    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    if ordering not in {
        "created_at",
        "-created_at",
        "name",
        "-name",
        "status",
        "-status",
    }:
        ordering = "-created_at"

    return queryset.order_by(ordering)
