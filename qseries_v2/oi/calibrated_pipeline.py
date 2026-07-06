"""
OI-012 Calibrated Decision Pipeline

Uses Calibration Engine to adjust confidence and edge thresholds before
Oracle produces a recommendation.
"""

from .confidence_engine import confidence_engine
from .probability_engine import probability_engine
from .recommendation_engine import recommendation_engine
from .explanation_engine import explanation_engine
from .calibration_engine import calibration_engine


class CalibratedDecisionPipeline:

    def run(self, ticker, market_yes_price, evidence):
        raw_confidence = confidence_engine.score(evidence)
        adjusted_confidence = calibration_engine.adjusted_confidence(raw_confidence)
        fair_yes = probability_engine.fair_yes_price(adjusted_confidence)

        recommendation = recommendation_engine.recommend(
            ticker=ticker,
            market_yes_price=market_yes_price,
            fair_yes_price=fair_yes,
            confidence=adjusted_confidence,
        )

        calibration = calibration_engine.settings()

        if adjusted_confidence < calibration["active_min_confidence"]:
            recommendation["action"] = "PASS"
            recommendation["reason"] = "Adjusted confidence below calibrated minimum."

        if abs(recommendation["edge"]) < calibration["active_min_edge"]:
            recommendation["action"] = "PASS"
            recommendation["reason"] = "Edge below calibrated minimum."

        explanation = explanation_engine.explain(recommendation, evidence)

        return {
            "ticker": ticker,
            "raw_confidence": raw_confidence,
            "adjusted_confidence": adjusted_confidence,
            "fair_yes_price": fair_yes,
            "calibration": calibration,
            "recommendation": recommendation,
            "explanation": explanation,
            "oracle_executes": False,
        }


calibrated_decision_pipeline = CalibratedDecisionPipeline()
