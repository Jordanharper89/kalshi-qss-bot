"""
OI-008 Performance Review Engine

Reviews Oracle's historical recommendations and summarizes performance.
Every engine is a measurable scientific experiment.
"""

class PerformanceReviewEngine:

    def review(self, records):
        total = len(records)
        wins = sum(1 for r in records if getattr(r, "result", "") == "win")
        losses = sum(1 for r in records if getattr(r, "result", "") == "loss")
        passes = sum(1 for r in records if getattr(r, "result", "") == "pass")
        pending = sum(1 for r in records if getattr(r, "result", "") == "pending")

        resolved = wins + losses
        win_rate = round((wins / resolved) * 100, 2) if resolved else 0.0

        avg_confidence = round(
            sum(float(getattr(r, "confidence", 0)) for r in records) / total,
            2
        ) if total else 0.0

        avg_edge = round(
            sum(float(getattr(r, "edge", 0)) for r in records) / total,
            2
        ) if total else 0.0

        return {
            "total_records": total,
            "wins": wins,
            "losses": losses,
            "passes": passes,
            "pending": pending,
            "resolved": resolved,
            "win_rate": win_rate,
            "avg_confidence": avg_confidence,
            "avg_edge": avg_edge,
        }


performance_review_engine = PerformanceReviewEngine()
