from apps.submissions.models import FeedbackSubmission


def get_form_submissions_for_organization(form_id, organization, filters):
    queryset = (
        FeedbackSubmission.objects.filter(
            form_id=form_id,
            organization=organization,
        )
        .prefetch_related("risk_assessment", "answers__question")
    )

    status = filters.get("status")
    dashboard_eligible = filters.get("dashboard_eligible")
    analysis_eligible = filters.get("analysis_eligible")
    submitted_after = filters.get("submitted_after")
    submitted_before = filters.get("submitted_before")
    ordering = filters.get("ordering", "-submitted_at")

    if status:
        queryset = queryset.filter(status=status)

    if dashboard_eligible is not None:
        queryset = queryset.filter(dashboard_eligible=dashboard_eligible)

    if analysis_eligible is not None:
        queryset = queryset.filter(analysis_eligible=analysis_eligible)

    if submitted_after is not None:
        queryset = queryset.filter(submitted_at__gte=submitted_after)

    if submitted_before is not None:
        queryset = queryset.filter(submitted_at__lte=submitted_before)

    if ordering not in {
        "submitted_at",
        "-submitted_at",
        "status",
        "-status",
    }:
        ordering = "-submitted_at"

    return queryset.order_by(ordering)
