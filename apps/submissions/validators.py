from rest_framework import serializers

from apps.forms.models import FormQuestion


def validate_public_submission_answers(form, answers):
    questions = list(form.questions.all())
    questions_by_id = {question.id: question for question in questions}
    seen_question_ids = set()
    validated_answers = []

    for item in answers:
        question_id = item["question_id"]

        if question_id in seen_question_ids:
            raise serializers.ValidationError(
                {"answers": f"Question {question_id} was submitted more than once."}
            )

        seen_question_ids.add(question_id)

        question = questions_by_id.get(question_id)
        if not question:
            raise serializers.ValidationError(
                {"answers": f"Question {question_id} does not belong to this form."}
            )

        if question.question_type == FormQuestion.QuestionType.RATING:
            validated_answers.append(
                validate_rating_answer(question=question, payload=item)
            )
            continue

        if question.question_type == FormQuestion.QuestionType.TEXT:
            validated_answers.append(
                validate_text_answer(question=question, payload=item)
            )
            continue

        raise serializers.ValidationError(
            {"answers": f"Question {question.id} has an unsupported type."}
        )

    missing_required_ids = [
        question.id
        for question in questions
        if question.is_required and question.id not in seen_question_ids
    ]

    if missing_required_ids:
        raise serializers.ValidationError(
            {
                "answers": (
                    "Required questions are missing: "
                    + ", ".join(str(question_id) for question_id in missing_required_ids)
                )
            }
        )

    return validated_answers


def validate_rating_answer(question, payload):
    if "rating_value" not in payload:
        raise serializers.ValidationError(
            {"answers": f"Question {question.id} requires rating_value."}
        )

    if "text_value" in payload:
        raise serializers.ValidationError(
            {"answers": f"Question {question.id} does not accept text_value."}
        )

    rating_value = payload["rating_value"]

    if question.min_value is not None and rating_value < question.min_value:
        raise serializers.ValidationError(
            {
                "answers": (
                    f"Question {question.id} rating_value must be at least "
                    f"{question.min_value}."
                )
            }
        )

    if question.max_value is not None and rating_value > question.max_value:
        raise serializers.ValidationError(
            {
                "answers": (
                    f"Question {question.id} rating_value must be at most "
                    f"{question.max_value}."
                )
            }
        )

    return {
        "question": question,
        "rating_value": rating_value,
    }


def validate_text_answer(question, payload):
    if "rating_value" in payload:
        raise serializers.ValidationError(
            {"answers": f"Question {question.id} does not accept rating_value."}
        )

    text_value = payload.get("text_value", "")

    if question.is_required and not text_value.strip():
        raise serializers.ValidationError(
            {"answers": f"Question {question.id} requires a non-empty text_value."}
        )

    return {
        "question": question,
        "text_value": text_value,
    }
