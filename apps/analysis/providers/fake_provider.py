class FakeAnalysisProvider:
    def analyze(self, text: str) -> dict:
        normalized_text = (text or "").strip().lower()

        if not normalized_text:
            return {
                "sentiment": "neutral",
                "urgency": "low",
                "topics": [],
                "summary": "No textual feedback provided.",
                "raw_response": {
                    "provider": "fake",
                    "note": "empty text",
                },
            }

        negative_keywords = [
            "bad", "terrible", "awful", "horrible", "slow", "delay", "poor"
        ]

        urgent_keywords = [
            "urgent", "immediate", "asap", "critical", "important"
        ]

        sentiment = "positive"
        urgency = "low"
        topics = []

        if any(word in normalized_text for word in negative_keywords):
            sentiment = "negative"
            topics.append("service_quality")

        if any(word in normalized_text for word in urgent_keywords):
            urgency = "high"
            topics.append("urgent_issue")

        if "service" in normalized_text or "support" in normalized_text:
            topics.append("customer_service")

        if "wait" in normalized_text or "delay" in normalized_text:
            topics.append("waiting_time")

        if sentiment == "positive" and not topics:
            topics.append("general_feedback")

        summary = normalized_text[:180]

        return {
            "sentiment": sentiment,
            "urgency": urgency,
            "topics": list(dict.fromkeys(topics)),
            "summary": summary,
            "raw_response": {
                "provider": "fake",
                "text_length": len(normalized_text),
            },
        }