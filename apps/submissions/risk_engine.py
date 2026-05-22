from apps.organizations.models import Organization


def calculate_risk(technical_data, answers_data, organization=None):
    score = 0
    reasons = []
    security_level = get_security_level(organization)
    suspicious_threshold, reject_threshold = get_risk_thresholds(security_level)

    if not technical_data.get("captcha_passed"):
        score += 50
        reasons.append("captcha_failed")

        if organization and organization.require_captcha:
            score += 25
            reasons.append("captcha_required")

    if not technical_data.get("fingerprint_hash"):
        score += 10
        reasons.append("missing_fingerprint")

    for answer in answers_data:
        text = answer.get("text_value", "")
        if text and len(text.strip()) < 3:
            score += 20
            reasons.append("very_short_text")

    score = min(score, 100)

    if score >= reject_threshold:
        risk_level = "high"
        decision = "rejected"
    elif score >= suspicious_threshold:
        risk_level = "medium"
        decision = "suspicious"
    else:
        risk_level = "low"
        decision = "accepted"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "reasons": reasons,
        "engine_version": "v1",
    }


def get_security_level(organization):
    if organization is None:
        return Organization.SecurityLevel.STANDARD

    return organization.security_level


def get_risk_thresholds(security_level):
    if security_level == Organization.SecurityLevel.RELAXED:
        return 50, 80

    if security_level == Organization.SecurityLevel.STRICT:
        return 30, 60

    return 40, 70
