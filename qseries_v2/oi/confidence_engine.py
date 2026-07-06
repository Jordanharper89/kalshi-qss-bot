"""
OI-002 Confidence Engine
"""

class ConfidenceEngine:

    def __init__(self):
        self.weights = {
            "market": 1.00,
            "news": 0.90,
            "historical": 0.85,
            "social": 0.60,
        }

    def score(self, evidence_list):
        if not evidence_list:
            return 0.0

        total = 0.0

        for evidence in evidence_list:
            weight = self.weights.get(evidence.category.lower(), 0.50)
            total += weight

        confidence = (total / len(evidence_list)) * 100
        return round(min(confidence, 100.0), 2)


confidence_engine = ConfidenceEngine()
