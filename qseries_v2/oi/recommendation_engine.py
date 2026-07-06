"""
OI-004 Recommendation Engine

Oracle researches, scores, explains, and learns.
Oracle does NOT execute trades.
"""

class RecommendationEngine:

    def recommend(self, ticker, market_yes_price, fair_yes_price, confidence):
        edge = round(float(fair_yes_price) - float(market_yes_price), 2)
        confidence = float(confidence)

        if confidence < 55:
            action = "PASS"
            reason = "Confidence below minimum threshold."
        elif edge >= 7:
            action = "BUY_YES"
            reason = "Fair value is meaningfully above market price."
        elif edge <= -7:
            action = "BUY_NO"
            reason = "Market YES price is meaningfully above fair value."
        else:
            action = "PASS"
            reason = "No strong edge after confidence and price comparison."

        return {
            "ticker": ticker,
            "action": action,
            "market_yes_price": round(float(market_yes_price), 2),
            "fair_yes_price": round(float(fair_yes_price), 2),
            "edge": edge,
            "confidence": round(confidence, 2),
            "reason": reason,
            "oracle_executes": False,
        }


recommendation_engine = RecommendationEngine()
