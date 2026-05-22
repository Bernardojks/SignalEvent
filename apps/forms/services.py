from django.db import transaction
from django.utils import timezone

from apps.forms.models import FeedbackForm


def activate_form(form):
    if form.status == FeedbackForm.Status.ARCHIVED:
        raise ValueError("Archived forms cannot be activated.")

    if not form.questions.exists():
        raise ValueError("A form must have at least one question before activation.")

    form.status = FeedbackForm.Status.ACTIVE
    form.save(update_fields=["status", "updated_at"])
    return form


def deactivate_form(form):
    if form.status == FeedbackForm.Status.ARCHIVED:
        raise ValueError("Archived forms cannot be deactivated.")

    form.status = FeedbackForm.Status.INACTIVE
    form.save(update_fields=["status", "updated_at"])
    return form


@transaction.atomic
def reorder_form_questions(form, question_ids):
    questions = list(form.questions.order_by("order", "id"))
    existing_ids = [question.id for question in questions]

    if len(question_ids) != len(existing_ids):
        raise ValueError("All form questions must be included in the reorder payload.")

    if len(set(question_ids)) != len(question_ids):
        raise ValueError("Question IDs must be unique in the reorder payload.")

    if set(question_ids) != set(existing_ids):
        raise ValueError("The reorder payload must match the form questions exactly.")

    questions_by_id = {question.id: question for question in questions}
    now = timezone.now()
    total_questions = len(questions)

    temporary_ordered_questions = []
    for index, question_id in enumerate(question_ids, start=1):
        question = questions_by_id[question_id]
        question.order = total_questions + index
        question.updated_at = now
        temporary_ordered_questions.append(question)

    form.questions.model.objects.bulk_update(
        temporary_ordered_questions,
        ["order", "updated_at"],
    )

    reordered_questions = []
    for index, question_id in enumerate(question_ids, start=1):
        question = questions_by_id[question_id]
        question.order = index
        question.updated_at = now
        reordered_questions.append(question)

    form.questions.model.objects.bulk_update(
        reordered_questions,
        ["order", "updated_at"],
    )

    return sorted(reordered_questions, key=lambda question: question.order)
