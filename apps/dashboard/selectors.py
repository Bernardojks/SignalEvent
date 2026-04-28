from django.db.models import Avg, Count, Q

from apps.analysis.models import FeedbackAnalysis
from apps.submissions.models import FeedbackSubmission, SubmissionAnswer


def get_dashboard_overview(organization):
    submissions_qs = FeedbackSubmission.objects.filter(organization=organization)

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
        submission__organization=organization,
        question__question_type="rating",
        rating_value__isnull=False,
    ).aggregate(avg=Avg("rating_value"))["avg"]

    sentiment_breakdown = (
        FeedbackAnalysis.objects.filter(submission__organization=organization)
        .values("sentiment")
        .annotate(total=Count("id"))
        .order_by("sentiment")
    )

    urgency_breakdown = (
        FeedbackAnalysis.objects.filter(submission__organization=organization)
        .values("urgency")
        .annotate(total=Count("id"))
        .order_by("urgency")
    )

    recent_submissions = submissions_qs.order_by("-submitted_at")[:5]

    return {
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions,
        "suspicious_submissions": suspicious_submissions,
        "rejected_submissions": rejected_submissions,
        "average_rating": average_rating,
        "sentiment_breakdown": list(sentiment_breakdown),
        "urgency_breakdown": list(urgency_breakdown),
        "recent_submissions": [
            {
                "public_id": str(submission.public_id),
                "form": submission.form.name,
                "status": submission.status,
                "submitted_at": submission.submitted_at,
                "analysis_eligible": submission.analysis_eligible,
                "dashboard_eligible": submission.dashboard_eligible,
            }
            for submission in recent_submissions
        ],
    }