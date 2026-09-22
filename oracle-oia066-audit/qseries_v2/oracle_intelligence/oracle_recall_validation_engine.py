
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
