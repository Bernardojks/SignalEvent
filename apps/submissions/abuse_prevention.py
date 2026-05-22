import hashlib
import json
import math
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


DEFAULT_PUBLIC_SUBMISSION_PROTECTION = {
    "request_ip_limit": 15,
    "request_ip_window_seconds": 300,
    "source_limit": 5,
    "source_window_seconds": 600,
    "source_cooldown_seconds": 30,
    "duplicate_window_seconds": 600,
}


@dataclass
class SubmissionAbuseError(Exception):
    detail: str
    code: str
    retry_after_seconds: int


def get_public_submission_protection_settings():
    configured = getattr(settings, "PUBLIC_SUBMISSION_PROTECTION", {})
    return {
        **DEFAULT_PUBLIC_SUBMISSION_PROTECTION,
        **configured,
    }


def get_request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "").strip() or "unknown"


def enforce_public_submission_request_limit(form, request):
    protection = get_public_submission_protection_settings()
    request_ip = get_request_ip(request)

    enforce_window_limit(
        namespace="request-ip",
        form_id=form.id,
        subject=request_ip,
        limit=protection["request_ip_limit"],
        window_seconds=protection["request_ip_window_seconds"],
        detail="Too many submission attempts from this IP. Try again later.",
        code="request_ip_rate_limited",
    )

    return request_ip


def enforce_public_submission_source_protection(
    form,
    request_ip,
    technical_data,
    answers_data,
):
    protection = get_public_submission_protection_settings()
    source_key = build_source_key(request_ip, technical_data)

    enforce_window_limit(
        namespace="source",
        form_id=form.id,
        subject=source_key,
        limit=protection["source_limit"],
        window_seconds=protection["source_window_seconds"],
        detail="Too many submissions from the same source. Try again later.",
        code="submission_source_rate_limited",
    )

    duplicate_window_seconds = protection["duplicate_window_seconds"]
    if duplicate_window_seconds > 0:
        duplicate_key = build_cache_key(
            namespace="duplicate",
            form_id=form.id,
            subject=f"{source_key}:{build_duplicate_signature(form.id, answers_data)}",
        )
        duplicate_added = cache.add(
            duplicate_key,
            timezone.now().timestamp() + duplicate_window_seconds,
            timeout=duplicate_window_seconds,
        )
        if not duplicate_added:
            raise SubmissionAbuseError(
                detail="Duplicate submission detected. Please wait before resending the same feedback.",
                code="duplicate_submission_detected",
                retry_after_seconds=duplicate_window_seconds,
            )

    cooldown_seconds = protection["source_cooldown_seconds"]
    if cooldown_seconds > 0:
        cooldown_key = build_cache_key(
            namespace="cooldown",
            form_id=form.id,
            subject=source_key,
        )
        cooldown_added = cache.add(
            cooldown_key,
            timezone.now().timestamp() + cooldown_seconds,
            timeout=cooldown_seconds,
        )
        if not cooldown_added:
            raise SubmissionAbuseError(
                detail="Please wait before submitting this form again.",
                code="submission_cooldown_active",
                retry_after_seconds=cooldown_seconds,
            )


def enforce_window_limit(
    namespace,
    form_id,
    subject,
    limit,
    window_seconds,
    detail,
    code,
):
    if limit <= 0 or window_seconds <= 0:
        return

    block_key = build_cache_key(
        namespace=f"{namespace}-block",
        form_id=form_id,
        subject=subject,
    )
    blocked_until = cache.get(block_key)

    if blocked_until:
        remaining_seconds = max(
            1,
            math.ceil(blocked_until - timezone.now().timestamp()),
        )
        raise SubmissionAbuseError(
            detail=detail,
            code=code,
            retry_after_seconds=remaining_seconds,
        )

    counter_key = build_cache_key(
        namespace=f"{namespace}-counter",
        form_id=form_id,
        subject=subject,
    )
    current_count = increment_counter(counter_key, window_seconds)

    if current_count <= limit:
        return

    blocked_until = timezone.now().timestamp() + window_seconds
    cache.set(block_key, blocked_until, timeout=window_seconds)

    raise SubmissionAbuseError(
        detail=detail,
        code=code,
        retry_after_seconds=window_seconds,
    )


def increment_counter(counter_key, window_seconds):
    counter_created = cache.add(counter_key, 1, timeout=window_seconds)
    if counter_created:
        return 1

    try:
        return cache.incr(counter_key)
    except ValueError:
        cache.set(counter_key, 1, timeout=window_seconds)
        return 1


def build_source_key(request_ip, technical_data):
    fingerprint_hash = technical_data.get("fingerprint_hash", "").strip()
    if fingerprint_hash:
        return f"fingerprint:{fingerprint_hash}"

    return f"ip:{request_ip}"


def build_duplicate_signature(form_id, answers_data):
    normalized_answers = []

    for answer in answers_data:
        normalized_answer = {
            "question_id": answer["question"].id,
        }
        if answer.get("rating_value") is not None:
            normalized_answer["rating_value"] = answer["rating_value"]

        text_value = answer.get("text_value", "").strip()
        if text_value:
            normalized_answer["text_value"] = text_value

        normalized_answers.append(normalized_answer)

    normalized_answers.sort(key=lambda item: item["question_id"])

    payload = json.dumps(
        {
            "form_id": form_id,
            "answers": normalized_answers,
        },
        sort_keys=True,
        ensure_ascii=True,
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_cache_key(namespace, form_id, subject):
    subject_hash = hashlib.sha256(subject.encode("utf-8")).hexdigest()
    return f"public-submission:{namespace}:form:{form_id}:subject:{subject_hash}"
