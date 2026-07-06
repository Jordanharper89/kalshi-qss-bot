from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_review_result_engine.py"
TEST = ROOT / "test_oi_109_oracle_review_result_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-109 Oracle Review Result Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle review plan items into structured read-only review result packets.
- Summarize review depth, checklist completion, signal quality, and review conclusion.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleReviewResultEngine:
    module = "oi_109_oracle_review_result_engine"

    def __init__(self):
        self.last_results = {}

    def build_review_results(self, review_plan_report=None, evidence_snapshot=None):
        review_plan_report = review_plan_report or {}
        evidence_snapshot = evidence_snapshot or {}

        plan_items = [
            x for x in review_plan_report.get("review_plan", [])
            if isinstance(x, dict)
        ]

        evidence_by_market = self._evidence_by_market(evidence_snapshot)

        results = []
        for item in plan_items:
            market = str(item.get("market") or "UNKNOWN")
            evidence = evidence_by_market.get(market, {})

            checklist = item.get("checklist", [])
            if not isinstance(checklist, list):
                checklist = []

            completed = self._completed_checklist(checklist, evidence)
            completion_rate = len(completed) / max(1, len(checklist))

            signal_quality = self._signal_quality(item, evidence, completion_rate)
            conclusion = self._conclusion(signal_quality, item)

            results.append({
                "market": market,
                "review_order": int(self._float(item.get("review_order"), 0)),
                "review_depth": str(item.get("review_depth") or "light"),
                "assigned_lane": str(item.get("assigned_lane") or "standard_monitoring"),
                "review_cadence": str(item.get("review_cadence") or "normal"),
                "checklist_count": len(checklist),
                "completed_checklist_count": len(completed),
                "checklist_completion_rate": round(completion_rate, 4),
                "completed_checklist": completed,
                "signal_quality_score": round(signal_quality, 4),
                "review_conclusion": conclusion,
                "review_note": self._note(market, conclusion, signal_quality, completion_rate),
                "evidence_summary": self._evidence_summary(evidence),
                "read_only": True,
            })

        results.sort(
            key=lambda x: (
                self._conclusion_rank(x["review_conclusion"]),
                x["signal_quality_score"],
                x["checklist_completion_rate"],
            ),
            reverse=True,
        )

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_108_oracle_review_plan_engine",
            "result_count": len(results),
            "review_results": results,
            "highest_quality_results": results[:10],
            "needs_more_evidence": [x for x in results if x["review_conclusion"] == "needs_more_evidence"],
            "summary": self._summary(results),
        }

        self.last_results = report
        return report

    def _evidence_by_market(self, evidence_snapshot):
        out = {}

        if isinstance(evidence_snapshot.get("markets"), dict):
            for market, data in evidence_snapshot.get("markets", {}).items():
                out[str(market)] = data if isinstance(data, dict) else {}

        for key in ("items", "evidence", "snapshots"):
            rows = evidence_snapshot.get(key, [])
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict):
                    market = str(row.get("market") or row.get("ticker") or "").strip()
                    if market:
                        out.setdefault(market, {}).update(row)

        return out

    def _completed_checklist(self, checklist, evidence):
        completed = []
        evidence_keys = set(str(k) for k in evidence.keys())

        for item in checklist:
            name = str(item)

            if name == "confirm_read_only_context":
                completed.append(name)
            elif name == "review_latest_oracle_snapshot" and evidence:
                completed.append(name)
            elif name == "review_priority_queue_context" and "priority_score" in evidence_keys:
                completed.append(name)
            elif name == "review_risk_posture_synthesis" and "risk_posture_score" in evidence_keys:
                completed.append(name)
            elif name == "review_systemic_risk_contagion" and "contagion_score" in evidence_keys:
                completed.append(name)
            elif name == "review_global_market_stability" and "stability_score" in evidence_keys:
                completed.append(name)
            elif name == "review_active_alerts" and self._float(evidence.get("alert_count")) > 0:
                completed.append(name)
            elif name == "review_alert_evidence" and "top_alert_priority" in evidence_keys:
                completed.append(name)
            elif name == "review_cross_market_anomalies" and self._float(evidence.get("anomaly_count")) > 0:
                completed.append(name)
            elif name == "compare_previous_snapshot" and "previous_score" in evidence_keys:
                completed.append(name)
            elif name == "review_market_health_dashboard" and "health_score" in evidence_keys:
                completed.append(name)
            elif name == "review_recovery_forecast" and "recovery_score" in evidence_keys:
                completed.append(name)
            elif name == "produce_oracle_read_only_note":
                completed.append(name)

        return completed

    def _signal_quality(self, item, evidence, completion_rate):
        priority_score = self._float(item.get("priority_score"))
        alert_count = self._float(evidence.get("alert_count", item.get("alert_count", 0)))
        anomaly_count = self._float(evidence.get("anomaly_count", item.get("anomaly_count", 0)))
        health = self._float(evidence.get("health_score"), 50)
        recovery = self._float(evidence.get("recovery_score"), 50)
        stability = self._float(evidence.get("stability_score"), 50)

        quality = (
            completion_rate * 35
            + min(priority_score, 100) * 0.22
            + min(alert_count * 12, 20)
            + min(anomaly_count * 12, 20)
            + max(0, 100 - abs(health - stability)) * 0.12
            + max(0, 100 - abs(recovery - stability)) * 0.11
        )

        return max(0.0, min(100.0, quality))

    def _conclusion(self, quality, item):
        depth = str(item.get("review_depth") or "light")
        if quality >= 80 and depth == "deep":
            return "high_confidence_review"
        if quality >= 65:
            return "confirmed_review"
        if quality >= 45:
            return "partial_review"
        return "needs_more_evidence"

    def _conclusion_rank(self, conclusion):
        return {
            "high_confidence_review": 4,
            "confirmed_review": 3,
            "partial_review": 2,
            "needs_more_evidence": 1,
        }.get(conclusion, 0)

    def _note(self, market, conclusion, quality, completion_rate):
        return (
            f"{market} review result is {conclusion} with signal quality "
            f"{round(quality, 2)} and checklist completion {round(completion_rate * 100, 1)}%."
        )

    def _evidence_summary(self, evidence):
        return {
            "has_evidence": bool(evidence),
            "evidence_fields": sorted([str(k) for k in evidence.keys()])[:20],
            "alert_count": self._float(evidence.get("alert_count", 0)),
            "anomaly_count": self._float(evidence.get("anomaly_count", 0)),
        }

    def _summary(self, results):
        counts = {}
        for item in results:
            conclusion = item["review_conclusion"]
            counts[conclusion] = counts.get(conclusion, 0) + 1

        return {
            "conclusion_counts": counts,
            "top_market": results[0]["market"] if results else None,
            "top_conclusion": results[0]["review_conclusion"] if results else None,
            "needs_more_evidence_count": counts.get("needs_more_evidence", 0),
            "result_count": len(results),
        }

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
            "has_results": bool(self.last_results),
            "result_count": self.last_results.get("result_count", 0),
            "read_only": True,
        }


oracle_review_result_engine = OracleReviewResultEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_review_result_engine import oracle_review_result_engine


def test_oi_109_oracle_review_result_engine():
    review_plan = {
        "review_plan": [
            {
                "market": "CRYPTO",
                "review_order": 1,
                "review_depth": "deep",
                "assigned_lane": "systemic_risk_review",
                "review_cadence": "immediate",
                "priority_score": 88,
                "alert_count": 2,
                "anomaly_count": 2,
                "checklist": [
                    "review_latest_oracle_snapshot",
                    "confirm_read_only_context",
                    "review_priority_queue_context",
                    "review_risk_posture_synthesis",
                    "review_systemic_risk_contagion",
                    "review_global_market_stability",
                    "review_active_alerts",
                    "review_alert_evidence",
                    "review_cross_market_anomalies",
                    "compare_previous_snapshot",
                    "produce_oracle_read_only_note",
                ],
            },
            {
                "market": "NASDAQ",
                "review_order": 2,
                "review_depth": "standard",
                "assigned_lane": "alert_review",
                "review_cadence": "hourly",
                "priority_score": 72.94,
                "alert_count": 1,
                "anomaly_count": 1,
                "checklist": [
                    "review_latest_oracle_snapshot",
                    "confirm_read_only_context",
                    "review_priority_queue_context",
                    "review_active_alerts",
                    "review_alert_evidence",
                    "produce_oracle_read_only_note",
                ],
            },
        ]
    }

    evidence = {
        "markets": {
            "CRYPTO": {
                "priority_score": 88,
                "risk_posture_score": 90,
                "contagion_score": 85,
                "stability_score": 30,
                "health_score": 25,
                "recovery_score": 30,
                "alert_count": 2,
                "anomaly_count": 2,
                "top_alert_priority": "critical",
                "previous_score": 48,
            },
            "NASDAQ": {
                "priority_score": 72.94,
                "health_score": 32,
                "stability_score": 50,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
        }
    }

    report = oracle_review_result_engine.build_review_results(review_plan, evidence)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["result_count"] == 2
    assert report["review_results"][0]["signal_quality_score"] >= report["review_results"][-1]["signal_quality_score"]
    assert report["summary"]["result_count"] == 2
    assert report["review_results"][0]["market"] == "CRYPTO"

    diag = oracle_review_result_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-109 Oracle Review Result Engine")
    print({
        "results": report["result_count"],
        "summary": report["summary"],
        "top": report["review_results"][0],
    })


if __name__ == "__main__":
    test_oi_109_oracle_review_result_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_review_result_engine import oracle_review_result_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-109 INSTALLER")
print(" Oracle Review Result Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-109 installed")
print()
print("Run:")
print("py test_oi_109_oracle_review_result_engine.py")