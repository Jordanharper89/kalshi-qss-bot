
"""
OI-110 Oracle Decision Support Packet Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle review results into read-only decision support packets.
- Summarize market state, review conclusion, confidence, risk, and next Oracle-only observation.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleDecisionSupportPacketEngine:
    module = "oi_110_oracle_decision_support_packet_engine"

    def __init__(self):
        self.last_packets = {}

    def build_support_packets(self, review_results_report=None, priority_queue_report=None, risk_posture_report=None):
        review_results_report = review_results_report or {}
        priority_queue_report = priority_queue_report or {}
        risk_posture_report = risk_posture_report or {}

        results = [x for x in review_results_report.get("review_results", []) if isinstance(x, dict)]
        queue = self._index(priority_queue_report.get("priority_queue", []), "market")
        postures = self._index(risk_posture_report.get("postures", []), "market")

        packets = []
        for result in results:
            market = str(result.get("market") or "UNKNOWN")
            q = queue.get(market, {})
            p = postures.get(market, {})

            signal_quality = self._float(result.get("signal_quality_score"))
            completion = self._float(result.get("checklist_completion_rate"))
            priority_score = self._float(q.get("priority_score"))
            posture_score = self._float(p.get("risk_posture_score"))

            support_score = self._support_score(
                signal_quality=signal_quality,
                completion=completion,
                priority_score=priority_score,
                posture_score=posture_score,
            )

            packets.append({
                "market": market,
                "support_packet_score": round(support_score, 4),
                "support_tier": self._tier(support_score),
                "review_conclusion": str(result.get("review_conclusion") or "unknown"),
                "signal_quality_score": round(signal_quality, 4),
                "checklist_completion_rate": round(completion, 4),
                "priority_score": round(priority_score, 4),
                "risk_posture_score": round(posture_score, 4),
                "queue_action": q.get("queue_action"),
                "posture": p.get("posture"),
                "decision_support_summary": self._summary_text(market, support_score, result, q, p),
                "oracle_observation": self._observation(result, q, p),
                "execution_allowed": False,
                "read_only": True,
            })

        packets.sort(key=lambda x: x["support_packet_score"], reverse=True)

        for idx, packet in enumerate(packets, start=1):
            packet["support_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_109_oracle_review_result_engine",
                "oi_103_market_priority_queue_engine",
                "oi_102_risk_posture_synthesis_engine",
            ],
            "packet_count": len(packets),
            "support_packets": packets,
            "top_support_packets": packets[:10],
            "high_support_packets": [x for x in packets if x["support_tier"] in {"critical", "high"}],
            "summary": self._summary(packets),
        }

        self.last_packets = report
        return report

    def _support_score(self, signal_quality, completion, priority_score, posture_score):
        score = (
            signal_quality * 0.34
            + completion * 100 * 0.22
            + priority_score * 0.24
            + posture_score * 0.20
        )
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "low"

    def _summary_text(self, market, score, result, queue, posture):
        return (
            f"{market} support packet is {self._tier(score)} with review conclusion "
            f"{result.get('review_conclusion')}, queue action {queue.get('queue_action')}, "
            f"and posture {posture.get('posture')}."
        )

    def _observation(self, result, queue, posture):
        conclusion = str(result.get("review_conclusion") or "")
        queue_action = str(queue.get("queue_action") or "")
        posture_state = str(posture.get("posture") or "")

        if conclusion == "needs_more_evidence":
            return "Collect more Oracle evidence before downstream use."
        if "immediate" in queue_action or posture_state in {"systemic_alert", "defensive"}:
            return "Keep market in elevated Oracle observation rotation."
        if conclusion in {"high_confidence_review", "confirmed_review"}:
            return "Oracle review packet is ready for read-only downstream visibility."
        return "Continue standard Oracle observation."

    def _summary(self, packets):
        counts = {}
        for packet in packets:
            tier = packet["support_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        return {
            "tier_counts": counts,
            "top_market": packets[0]["market"] if packets else None,
            "top_tier": packets[0]["support_tier"] if packets else None,
            "packet_count": len(packets),
            "execution_allowed": False,
        }

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = str(row.get(key) or "").strip()
                if value:
                    out[value] = row
        return out

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_packets": bool(self.last_packets),
            "packet_count": self.last_packets.get("packet_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_decision_support_packet_engine = OracleDecisionSupportPacketEngine()
