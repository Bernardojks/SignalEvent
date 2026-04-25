def calculate_risk(technical_data, answers_data):
    score = 0
    reasons = []

    if not technical_data.get("captcha_passed"):
        score += 50
        reasons.append("captcha_failed")

    if not technical_data.get("fingerprint_hash"):
        score += 10
        reasons.append("missing_fingerprint")

    for answer in answers_data:
        text = answer.get("text_value", "")
        if text and len(text.strip()) < 3:
            score += 20
            reasons.append("very_short_text")

    score = min(score, 100)

    if score >= 70:
        risk_level = "high"
        decision = "rejected"
    elif score >= 40:
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