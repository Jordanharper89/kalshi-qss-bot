"""
OI-003 Probability Engine
"""

class ProbabilityEngine:

    def probability(self, confidence):
        confidence = max(0.0, min(100.0, float(confidence)))
        return round(confidence / 100.0, 4)

    def fair_yes_price(self, confidence):
        return round(self.probability(confidence) * 100, 2)

    def fair_no_price(self, confidence):
        return round(100 - self.fair_yes_price(confidence), 2)

    def expected_edge(self, market_price, fair_price):
        return round(fair_price - market_price, 2)


probability_engine = ProbabilityEngine()
