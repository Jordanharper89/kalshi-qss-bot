"""
OI-005 Explanation Engine

Turns Oracle recommendations into clear, auditable explanations.
Every recommendation must be explainable.
"""

class ExplanationEngine:

    def explain(self, recommendation, evidence=None):
        evidence = evidence or []

        lines = []
        lines.append(f"Ticker: {recommendation.get('ticker')}")
        lines.append(f"Action: {recommendation.get('action')}")
        lines.append(f"Confidence: {recommendation.get('confidence')}%")
        lines.append(f"Market YES Price: {recommendation.get('market_yes_price')}")
        lines.append(f"Oracle Fair YES Price: {recommendation.get('fair_yes_price')}")
        lines.append(f"Edge: {recommendation.get('edge')}")
        lines.append(f"Reason: {recommendation.get('reason')}")
        lines.append("Oracle Execution: Disabled — Q Series handles execution.")

        if evidence:
            lines.append("")
            lines.append("Evidence:")
            for item in evidence:
                source = getattr(item, "source", "unknown")
                category = getattr(item, "category", "unknown")
                value = getattr(item, "value", {})
                lines.append(f"- {category} evidence from {source}: {value}")

        return "\n".join(lines)


explanation_engine = ExplanationEngine()
