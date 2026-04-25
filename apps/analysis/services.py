from django.db import transaction
from django.utils import timezone

from apps.analysis.models import AnalysisJob, FeedbackAnalysis
from apps.analysis.providers.fake_provider import FakeAnalysisProvider


def create_analysis_job(submission):
    return AnalysisJob.objects.create(
        submission=submission,
        status=AnalysisJob.Status.PENDING,
    )

def build_submission_text(submission):
    text_answers = (
        submission.answers.filter(question__question_type="text")
        .exclude(text_value="")
        .select_related("question")
    )

    parts = [
        f"{answer.question.title}: {answer.text_value}"
        for answer in text_answers
    ]

    return "\n".join(parts).strip()


@transaction.atomic
def process_analysis_job(job: AnalysisJob):
    if job.status == AnalysisJob.Status.COMPLETED:
        return job

    if hasattr(job.submission, "analysis"):
        job.status = AnalysisJob.Status.COMPLETED
        job.processed_at = timezone.now()
        job.save(update_fields=["status", "processed_at", "updated_at"])
        return job

    job.status = AnalysisJob.Status.PROCESSING
    job.attempts += 1
    job.last_error = ""
    job.save(update_fields=["status", "attempts", "last_error", "updated_at"])

    try:
        text = build_submission_text(job.submission)

        provider = FakeAnalysisProvider()
        result = provider.analyze(text)

        FeedbackAnalysis.objects.create(
            submission=job.submission,
            sentiment=result["sentiment"],
            urgency=result["urgency"],
            topics=result["topics"],
            summary=result["summary"],
            raw_response=result["raw_response"],
        )

        job.status = AnalysisJob.Status.COMPLETED
        job.processed_at = timezone.now()
        job.save(update_fields=["status", "processed_at", "updated_at"])

        submission = job.submission
        submission.status = submission.Status.ANALYZED
        submission.save(update_fields=["status", "updated_at"])

        return job

    except Exception as exc:
        job.status = AnalysisJob.Status.FAILED
        job.last_error = str(exc)
        job.save(update_fields=["status", "last_error", "updated_at"])

        submission = job.submission
        submission.status = submission.Status.ANALYSIS_FAILED
        submission.save(update_fields=["status", "updated_at"])

        raise

