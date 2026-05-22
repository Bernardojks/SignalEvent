from django.db.models import Avg, Count, Q

from apps.analysis.models import FeedbackAnalysis
from apps.plans.selectors import get_current_subscription_data
from apps.submissions.models import FeedbackSubmission, SubmissionAnswer


def apply_submission_filters(queryset, filters):
    submitted_after = filters.get("submitted_after")
    submitted_before = filters.get("submitted_before")
    form = filters.get("form")

    if form is not None:
        queryset = queryset.filter(form=form)

    if submitted_after is not None:
        queryset = queryset.filter(submitted_at__gte=submitted_after)

    if submitted_before is not None:
        queryset = queryset.filter(submitted_at__lte=submitted_before)

    return queryset


def get_dashboard_overview(organization, filters=None):
    filters = filters or {}
    submissions_qs = apply_submission_filters(
        FeedbackSubmission.objects.filter(organization=organization),
        filters,
    )
    analyses_qs = FeedbackAnalysis.objects.filter(
        submission__in=submissions_qs,
    )

    total_submissions = submissions_qs.count()

    accepted_submissions = submissions_qs.filter(
        status__in=[
            FeedbackSubmission.Status.ACCEPTED,
            FeedbackSubmission.Status.QUEUED_FOR_ANALYSIS,
            FeedbackSubmission.Status.ANALYZED,
        ]
    ).count()

    suspicious_submissions = submissions_qs.filter(
        status=FeedbackSubmission.Status.SUSPICIOUS
    ).count()

    rejected_submissions = submissions_qs.filter(
        status=FeedbackSubmission.Status.REJECTED
    ).count()

    average_rating = SubmissionAnswer.objects.filter(
        submission__in=submissions_qs,
        question__question_type="rating",
        rating_value__isnull=False,
    ).aggregate(avg=Avg("rating_value"))["avg"]

    sentiment_breakdown = (
        analyses_qs
        .values("sentiment")
        .annotate(total=Count("id"))
        .order_by("sentiment")
    )

    urgency_breakdown = (
        analyses_qs
        .values("urgency")
        .annotate(total=Count("id"))
        .order_by("urgency")
    )

    recent_submissions = (
        submissions_qs.select_related("form")
        .order_by("-submitted_at")[:5]
    )

    top_forms = list(
        submissions_qs.values(
            "form_id",
            "form__name",
            "form__public_id",
            "form__status",
        )
        .annotate(
            total_submissions=Count("id"),
            average_rating=Avg(
                "answers__rating_value",
                filter=Q(
                    answers__question__question_type="rating",
                    answers__rating_value__isnull=False,
                ),
            ),
        )
        .order_by("-total_submissions", "form__name")[:5]
    )

    for item in top_forms:
        item["id"] = item.pop("form_id")
        item["name"] = item.pop("form__name")
        item["public_id"] = str(item.pop("form__public_id"))
        item["status"] = item.pop("form__status")
        if item["average_rating"] is not None:
            item["average_rating"] = float(item["average_rating"])

    recent_analyses = [
        {
            "submission_id": analysis.submission_id,
            "submission_public_id": str(analysis.submission.public_id),
            "form_id": analysis.submission.form_id,
            "form_name": analysis.submission.form.name,
            "sentiment": analysis.sentiment,
            "urgency": analysis.urgency,
            "topics": analysis.topics,
            "summary": analysis.summary,
            "processed_at": analysis.processed_at,
        }
        for analysis in analyses_qs.select_related("submission__form").order_by("-processed_at")[:5]
    ]

    subscription_data = get_current_subscription_data(organization)
    usage_summary = subscription_data["usage"]

    return {
        "scope": {
            "form_id": filters.get("form").id if filters.get("form") else None,
            "submitted_after": filters.get("submitted_after"),
            "submitted_before": filters.get("submitted_before"),
        },
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions,
        "suspicious_submissions": suspicious_submissions,
        "rejected_submissions": rejected_submissions,
        "average_rating": float(average_rating) if average_rating is not None else None,
        "usage_summary": usage_summary,
        "sentiment_breakdown": list(sentiment_breakdown),
        "urgency_breakdown": list(urgency_breakdown),
        "top_forms": top_forms,
        "recent_analyses": recent_analyses,
        "recent_submissions": [
            {
                "public_id": str(submission.public_id),
                "form_id": submission.form_id,
                "form": submission.form.name,
                "status": submission.status,
                "submitted_at": submission.submitted_at,
                "analysis_eligible": submission.analysis_eligible,
                "dashboard_eligible": submission.dashboard_eligible,
            }
            for submission in recent_submissions
        ],
    }


def get_form_analytics(form):
    submissions_qs = FeedbackSubmission.objects.filter(form=form)
    analyses_qs = FeedbackAnalysis.objects.filter(submission__form=form)

    total_submissions = submissions_qs.count()
    accepted_submissions = submissions_qs.filter(
        status__in=[
            FeedbackSubmission.Status.ACCEPTED,
            FeedbackSubmission.Status.QUEUED_FOR_ANALYSIS,
            FeedbackSubmission.Status.ANALYZED,
        ]
    ).count()
    suspicious_submissions = submissions_qs.filter(
        status=FeedbackSubmission.Status.SUSPICIOUS
    ).count()
    rejected_submissions = submissions_qs.filter(
        status=FeedbackSubmission.Status.REJECTED
    ).count()
    analyzed_submissions = analyses_qs.count()

    average_rating = SubmissionAnswer.objects.filter(
        submission__form=form,
        question__question_type="rating",
        rating_value__isnull=False,
    ).aggregate(avg=Avg("rating_value"))["avg"]

    rating_questions = list(
        SubmissionAnswer.objects.filter(
            submission__form=form,
            question__question_type="rating",
            rating_value__isnull=False,
        )
        .values("question_id", "question__title")
        .annotate(
            average_rating=Avg("rating_value"),
            responses_count=Count("id"),
        )
        .order_by("question__title")
    )

    for item in rating_questions:
        item["question_title"] = item.pop("question__title")
        if item["average_rating"] is not None:
            item["average_rating"] = float(item["average_rating"])

    sentiment_breakdown = list(
        analyses_qs.values("sentiment")
        .annotate(total=Count("id"))
        .order_by("sentiment")
    )
    urgency_breakdown = list(
        analyses_qs.values("urgency")
        .annotate(total=Count("id"))
        .order_by("urgency")
    )
    recent_analyses = [
        {
            "submission_id": analysis.submission_id,
            "submission_public_id": str(analysis.submission.public_id),
            "sentiment": analysis.sentiment,
            "urgency": analysis.urgency,
            "topics": analysis.topics,
            "summary": analysis.summary,
            "processed_at": analysis.processed_at,
        }
        for analysis in analyses_qs.select_related("submission").order_by("-processed_at")[:5]
    ]

    return {
        "form": {
            "id": form.id,
            "public_id": str(form.public_id),
            "name": form.name,
            "status": form.status,
        },
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions,
        "suspicious_submissions": suspicious_submissions,
        "rejected_submissions": rejected_submissions,
        "analyzed_submissions": analyzed_submissions,
        "average_rating": float(average_rating) if average_rating is not None else None,
        "rating_questions": rating_questions,
        "sentiment_breakdown": sentiment_breakdown,
        "urgency_breakdown": urgency_breakdown,
        "recent_analyses": recent_analyses,
    }
