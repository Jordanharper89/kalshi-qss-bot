from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_recall_validation_engine.py"
TEST = ROOT / "test_oi_148_oracle_recall_validation_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-148 Oracle Recall Validation Engine
Read-only Oracle Intelligence module.

Purpose:
- Validate Oracle knowledge recall packets before downstream historical use.
- Confirm read-only status, execution separation, recall integrity, event recall integrity,
  tier consistency, and Q Series ownership.
- Produce validation status for institutional historical intelligence workflows.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleRecallValidationEngine:
    module = "oi_148_oracle_recall_validation_engine"

    def __init__(self):
        self.last_validation_report = {}

    def validate_recall(self, recall_report=None):
        recall_report = recall_report or {}

        packets = [
            x for x in recall_report.get("recall_packets", [])
            if isinstance(x, dict)
        ]

        checks = []
        checks.extend(self._report_checks(recall_report, packets))

        packet_validations = []
        for packet in packets:
            validation = self._packet_validation(packet)
            packet_validations.append(validation)
            checks.extend(validation["checks"])

        validation_score = self._validation_score(checks)
        failed_checks = [x for x in checks if not x["passed"]]
        critical_failures = [x for x in failed_checks if x["severity"] == "critical"]
        warnings = [x for x in checks if x["severity"] == "warning" and not x["passed"]]

        validation_status = self._status(validation_score, critical_failures, failed_checks)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_147_oracle_knowledge_recall_engine",
            ],
            "validation_status": validation_status,
            "validation_score": round(validation_score, 4),
            "validated": validation_status == "validated",
            "safe_for_historical_use": validation_status in {"validated", "validated_with_warnings"},
            "source_recall_count": len(packets),
            "packet_validation_count": len(packet_validations),
            "packet_validations": packet_validations,
            "checks": checks,
            "failed_checks": failed_checks,
            "critical_failure_count": len(critical_failures),
            "warning_count": len(warnings),
            "validation_summary": self._summary(
                validation_status,
                validation_score,
                failed_checks,
                critical_failures,
                warnings,
                packets,
            ),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "recall_validation_context_only",
            },
        }

        self.last_validation_report = report
        return report

    def _report_checks(self, recall_report, packets):
        checks = []

        checks.append(self._check(
            name="report_read_only",
            passed=recall_report.get("read_only") is True,
            severity="critical",
            message="Recall report must be read-only.",
        ))

        checks.append(self._check(
            name="report_execution_disabled",
            passed=recall_report.get("execution_allowed") is False,
            severity="critical",
            message="Recall report must not allow execution.",
        ))

        handoff = recall_report.get("qseries_handoff", {}) or {}
        checks.append(self._check(
            name="qseries_execution_owner",
            passed=handoff.get("execution_owner") == "Q Series",
            severity="critical",
            message="Q Series must remain the execution owner.",
        ))

        checks.append(self._check(
            name="oracle_permission_read_only",
            passed=handoff.get("oracle_permission") == "read_only",
            severity="critical",
            message="Oracle permission must remain read-only.",
        ))

        checks.append(self._check(
            name="recall_count_consistency",
            passed=int(self._float(recall_report.get("recall_count"), len(packets))) == len(packets),
            severity="warning",
            message="Recall count should match packet count.",
        ))

        checks.append(self._check(
            name="has_recall_packets",
            passed=len(packets) > 0,
            severity="warning",
            message="Recall validation should usually include at least one recall packet.",
        ))

        return checks

    def _packet_validation(self, packet):
        checks = []

        market = str(packet.get("market") or "UNKNOWN")
        recall_score = self._float(packet.get("recall_score"), 0)
        event_recall = [
            x for x in packet.get("event_recall", [])
            if isinstance(x, dict)
        ]

        checks.append(self._check(
            name=f"{market}_packet_read_only",
            passed=packet.get("read_only") is True,
            severity="critical",
            message=f"{market} recall packet must be read-only.",
        ))

        checks.append(self._check(
            name=f"{market}_packet_execution_disabled",
            passed=packet.get("execution_allowed") is False,
            severity="critical",
            message=f"{market} recall packet must not allow execution.",
        ))

        checks.append(self._check(
            name=f"{market}_recall_score_valid",
            passed=0 <= recall_score <= 100,
            severity="critical",
            message=f"{market} recall score must be between 0 and 100.",
        ))

        checks.append(self._check(
            name=f"{market}_recall_tier_consistent",
            passed=packet.get("recall_tier") == self._tier(recall_score),
            severity="warning",
            message=f"{market} recall tier should match recall score.",
        ))

        checks.append(self._check(
            name=f"{market}_recall_status_present",
            passed=bool(packet.get("recall_status")),
            severity="warning",
            message=f"{market} recall status should be present.",
        ))

        checks.append(self._check(
            name=f"{market}_knowledge_score_valid",
            passed=0 <= self._float(packet.get("knowledge_score"), 0) <= 100,
            severity="warning",
            message=f"{market} knowledge score should be between 0 and 100.",
        ))

        checks.append(self._check(
            name=f"{market}_search_score_valid",
            passed=0 <= self._float(packet.get("search_score"), 0) <= 100,
            severity="warning",
            message=f"{market} search score should be between 0 and 100.",
        ))

        for idx, event in enumerate(event_recall, start=1):
            checks.extend(self._event_checks(market, idx, event))

        packet_score = self._validation_score(checks)
        failed = [x for x in checks if not x["passed"]]
        critical = [x for x in failed if x["severity"] == "critical"]

        return {
            "market": market,
            "recall_score": round(recall_score, 4),
            "packet_validation_score": round(packet_score, 4),
            "packet_validation_status": self._packet_status(packet_score, critical, failed),
            "failed_check_count": len(failed),
            "critical_failure_count": len(critical),
            "event_recall_count": len(event_recall),
            "checks": checks,
            "read_only": True,
            "execution_allowed": False,
        }

    def _event_checks(self, market, idx, event):
        label = f"{market}_event_{idx}"
        weight = self._float(event.get("recall_weight"), 0)
        score = self._float(event.get("event_score"), 0)

        return [
            self._check(
                name=f"{label}_read_only",
                passed=event.get("read_only") is True,
                severity="critical",
                message=f"{label} must be read-only.",
            ),
            self._check(
                name=f"{label}_execution_disabled",
                passed=event.get("execution_allowed") is False,
                severity="critical",
                message=f"{label} must not allow execution.",
            ),
            self._check(
                name=f"{label}_event_type_present",
                passed=bool(event.get("event_type")),
                severity="warning",
                message=f"{label} should include event type.",
            ),
            self._check(
                name=f"{label}_event_score_valid",
                passed=0 <= score <= 100,
                severity="warning",
                message=f"{label} event score should be between 0 and 100.",
            ),
            self._check(
                name=f"{label}_recall_weight_valid",
                passed=0 <= weight <= 100,
                severity="warning",
                message=f"{label} recall weight should be between 0 and 100.",
            ),
        ]

    def _validation_score(self, checks):
        if not checks:
            return 100.0

        penalty = 0.0
        for check in checks:
            if check["passed"]:
                continue
            if check["severity"] == "critical":
                penalty += 18
            elif check["severity"] == "warning":
                penalty += 6
            else:
                penalty += 3

        return max(0.0, min(100.0, 100.0 - penalty))

    def _status(self, score, critical_failures, failed_checks):
        if critical_failures:
            return "failed"
        if score >= 90:
            return "validated"
        if score >= 75:
            return "validated_with_warnings"
        if failed_checks:
            return "needs_review"
        return "validated"

    def _packet_status(self, score, critical_failures, failed_checks):
        if critical_failures:
            return "failed"
        if score >= 90:
            return "validated"
        if score >= 75:
            return "validated_with_warnings"
        if failed_checks:
            return "needs_review"
        return "validated"

    def _tier(self, score):
        if score >= 85:
            return "institutional_recall"
        if score >= 70:
            return "strong_recall"
        if score >= 50:
            return "developing_recall"
        if score >= 30:
            return "thin_recall"
        return "recall_trace"

    def _check(self, name, passed, severity, message):
        return {
            "name": name,
            "passed": bool(passed),
            "severity": severity,
            "message": message,
            "read_only": True,
            "execution_allowed": False,
        }

    def _summary(self, status, score, failed, critical, warnings, packets):
        top = packets[0] if packets else {}

        if status == "validated":
            headline = "Oracle recall validation passed; recall packets are safe for historical use."
        elif status == "validated_with_warnings":
            headline = "Oracle recall validation passed with warnings."
        else:
            headline = "Oracle recall validation requires review."

        return {
            "headline": headline,
            "validation_status": status,
            "validation_score": round(score, 4),
            "source_recall_count": len(packets),
            "failed_checks": len(failed),
            "critical_failure_count": len(critical),
            "warning_count": len(warnings),
            "top_market": top.get("market"),
            "top_recall_tier": top.get("recall_tier"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
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
            "has_validation_report": bool(self.last_validation_report),
            "validation_status": self.last_validation_report.get("validation_status"),
            "validation_score": self.last_validation_report.get("validation_score"),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_recall_validation_engine = OracleRecallValidationEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_recall_validation_engine import (
    oracle_recall_validation_engine,
)


def test_oi_148_oracle_recall_validation_engine():
    recall_report = {
        "read_only": True,
        "execution_allowed": False,
        "recall_count": 1,
        "qseries_handoff": {
            "execution_owner": "Q Series",
            "oracle_permission": "read_only",
            "execution_allowed": False,
        },
        "recall_packets": [
            {
                "market": "CRYPTO",
                "recall_score": 100.0,
                "recall_tier": "institutional_recall",
                "recall_status": "executive_recall_ready",
                "knowledge_score": 100.0,
                "search_score": 100.0,
                "knowledge_tier": "institutional_knowledge",
                "knowledge_status": "executive_ready_knowledge",
                "timeline_phase": "executive_timeline_active",
                "timeline_tier": "institutional_timeline",
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "confidence_tier": "institutional_confidence",
                "memory_tier": "institutional_memory",
                "event_recall": [
                    {
                        "event_recall_id": "recall-event-002",
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "timeline_position": 2,
                        "recall_weight": 82.614,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 1,
                    },
                    {
                        "event_recall_id": "recall-event-001",
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "timeline_position": 1,
                        "recall_weight": 80.4225,
                        "read_only": True,
                        "execution_allowed": False,
                        "event_recall_rank": 2,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            }
        ],
    }

    report = oracle_recall_validation_engine.validate_recall(recall_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["validation_status"] == "validated"
    assert report["validated"] is True
    assert report["safe_for_historical_use"] is True
    assert report["validation_score"] == 100.0
    assert report["source_recall_count"] == 1
    assert report["packet_validation_count"] == 1
    assert report["packet_validations"][0]["packet_validation_status"] == "validated"
    assert report["packet_validations"][0]["execution_allowed"] is False
    assert report["packet_validations"][0]["read_only"] is True
    assert report["critical_failure_count"] == 0
    assert report["warning_count"] == 0
    assert report["validation_summary"]["execution_allowed"] is False
    assert report["validation_summary"]["execution_owner"] == "Q Series"

    diag = oracle_recall_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["validation_status"] == "validated"

    print("[PASS] OI-148 Oracle Recall Validation Engine")
    print({
        "validation_status": report["validation_status"],
        "validation_score": report["validation_score"],
        "validated": report["validated"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_148_oracle_recall_validation_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_recall_validation_engine import oracle_recall_validation_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-148 INSTALLER")
print(" Oracle Recall Validation Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-148 installed")
print()
print("Run:")
print("py test_oi_148_oracle_recall_validation_engine.py")