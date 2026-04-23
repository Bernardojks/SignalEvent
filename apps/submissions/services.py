from django.db import transaction
from django.utils import timezone

from apps.analysis.services import create_analysis_job
from apps.plans.services import has_available_analysis_quota, consume_analysis_quota
from apps.submissions.models import (
    FeedbackSubmission,
    SubmissionAnswer,
    SubmissionRiskAssessment,
    SubmissionTechnicalData,
)

def create_submission(form):
    return FeedbackSubmission.objects.create(
        organization=form.organization,
        form=form,
        status=FeedbackSubmission.Status.RECEIVED,
    )


def create_submission_answers(submission, answers_data):
    created_answers = []

    for item in answers_data:
        answer = SubmissionAnswer.objects.create(
            submission=submission,
            question=item["question"],
            rating_value=item.get("rating_value"),
            text_value=item.get("text_value", ""),
        )
        created_answers.append(answer)

    return created_answers


def create_submission_technical_data(submission, technical_data):
    return SubmissionTechnicalData.objects.create(
        submission=submission,
        ip_address=technical_data["ip_address"],
        user_agent=technical_data.get("user_agent", ""),
        fingerprint_hash=technical_data.get("fingerprint_hash", ""),
        accept_language=technical_data.get("accept_language", ""),
        referer=technical_data.get("referer", ""),
        captcha_provider=technical_data.get("captcha_provider", ""),
        captcha_passed=technical_data.get("captcha_passed", False),
    )


def create_submission_risk_assessment(submission, risk_data):
    assessment = SubmissionRiskAssessment.objects.create(
        submission=submission,
        risk_score=risk_data["risk_score"],
        risk_level=risk_data["risk_level"],
        decision=risk_data["decision"],
        reasons=risk_data.get("reasons", []),
        engine_version=risk_data.get("engine_version", "v1"),
    )

    if assessment.decision == SubmissionRiskAssessment.Decision.ACCEPTED:
        submission.status = FeedbackSubmission.Status.ACCEPTED
        submission.dashboard_eligible = True
        submission.accepted_at = timezone.now()

    elif assessment.decision == SubmissionRiskAssessment.Decision.SUSPICIOUS:
        submission.status = FeedbackSubmission.Status.SUSPICIOUS
        submission.dashboard_eligible = False
        submission.suspicious_at = timezone.now()

    elif assessment.decision == SubmissionRiskAssessment.Decision.REJECTED:
        submission.status = FeedbackSubmission.Status.REJECTED
        submission.dashboard_eligible = False
        submission.rejected_at = timezone.now()

    submission.save()

    return assessment

@transaction.atomic
def submit_feedback(form, answers_data, technical_data, risk_data):
    submission = create_submission(form=form)

    create_submission_answers(
        submission=submission,
        answers_data=answers_data,
    )

    create_submission_technical_data(
        submission=submission,
        technical_data=technical_data,
    )

    assessment = create_submission_risk_assessment(
        submission=submission,
        risk_data=risk_data,
    )

    if assessment.decision != SubmissionRiskAssessment.Decision.ACCEPTED:
        return submission

    has_text_answers = submission.answers.filter(
        question__question_type="text",
        text_value__gt="",
    ).exists()

    if has_text_answers and has_available_analysis_quota(submission.organization):
        consume_analysis_quota(
            organization=submission.organization,
            submission=submission,
        )

        create_analysis_job(submission=submission)

        submission.analysis_eligible = True
        submission.status = FeedbackSubmission.Status.QUEUED_FOR_ANALYSIS
        submission.save(update_fields=["analysis_eligible", "status", "updated_at"])

    return submission