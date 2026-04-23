from apps.analysis.models import AnalysisJob, FeedbackAnalysis


def create_analysis_job(submission):
    return AnalysisJob.objects.create(
        submission=submission,
        status=AnalysisJob.Status.PENDING,
    )


def save_feedback_analysis(
    submission,
    sentiment,
    urgency,
    topics,
    summary,
    raw_response,
):
    return FeedbackAnalysis.objects.create(
        submission=submission,
        sentiment=sentiment,
        urgency=urgency,
        topics=topics,
        summary=summary,
        raw_response=raw_response,
    )