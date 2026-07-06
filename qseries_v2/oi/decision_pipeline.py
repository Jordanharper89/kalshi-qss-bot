"""
OI-006 Oracle Decision Pipeline

Connects:
Evidence -> Confidence -> Probability -> Recommendation -> Explanation
"""

from .confidence_engine import confidence_engine
from .probability_engine import probability_engine
from .recommendation_engine import recommendation_engine
from .explanation_engine import explanation_engine


class OracleDecisionPipeline:

    def run(self, ticker, market_yes_price, evidence):
        confidence = confidence_engine.score(evidence)
        fair_yes = probability_engine.fair_yes_price(confidence)

        recommendation = recommendation_engine.recommend(
            ticker=ticker,
            market_yes_price=market_yes_price,
            fair_yes_price=fair_yes,
            confidence=confidence,
        )

        explanation = explanation_engine.explain(
            recommendation=recommendation,
            evidence=evidence,
        )

        return {
            "ticker": ticker,
            "confidence": confidence,
            "fair_yes_price": fair_yes,
            "recommendation": recommendation,
            "explanation": explanation,
            "oracle_executes": False,
        }


oracle_decision_pipeline = OracleDecisionPipeline()
