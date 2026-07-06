"""
OI-013 Research Report Engine

Produces a clean Oracle research report from a decision pipeline result.
Oracle researches, scores, explains, and learns.
Oracle does not execute trades.
"""

class ResearchReportEngine:

    def generate(self, decision):
        rec = decision.get("recommendation", {})
        calibration = decision.get("calibration", {})

        lines = []
        lines.append("ORACLE RESEARCH REPORT")
        lines.append("=" * 40)
        lines.append(f"Ticker: {decision.get('ticker')}")
        lines.append(f"Action: {rec.get('action')}")
        lines.append(f"Confidence: {rec.get('confidence')}%")
        lines.append(f"Market YES Price: {rec.get('market_yes_price')}")
        lines.append(f"Oracle Fair YES Price: {rec.get('fair_yes_price')}")
        lines.append(f"Edge: {rec.get('edge')}")
        lines.append("")
        lines.append("Reason")
        lines.append("-" * 40)
        lines.append(str(rec.get("reason")))
        lines.append("")
        lines.append("Calibration")
        lines.append("-" * 40)
        lines.append(f"Min Confidence: {calibration.get('active_min_confidence', 'n/a')}")
        lines.append(f"Min Edge: {calibration.get('active_min_edge', 'n/a')}")
        lines.append("")
        lines.append("Explanation")
        lines.append("-" * 40)
        lines.append(str(decision.get("explanation", "")))
        lines.append("")
        lines.append("Execution")
        lines.append("-" * 40)
        lines.append("Oracle does not execute trades. Q Series handles execution.")

        return "\n".join(lines)


research_report_engine = ResearchReportEngine()
