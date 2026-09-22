"""
OI-161 — Oracle Institutional Readiness Engine

Read-only readiness engine for Oracle Intelligence after alpha integration.

Purpose:
- Convert alpha integration output into an institutional readiness report.
- Confirm Oracle remains read-only and execution ownership remains Q Series.
- Score readiness across integration, replayability, explainability, memory,
  universal market model compatibility, and operational safety.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class InstitutionalReadinessDimension:
    dimension_id: str
    dimension: str
    score: float
    status: str
    note: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleInstitutionalReadinessEngine:
    name: str = "oracle_institutional_readiness_engine"
    version: str = "OI-161"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    readiness_schema_version: str = "institutional_readiness_v1"
    supported_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    def classify_status(self, score: float) -> str:
        if score >= 95:
            return "institutional_ready"
        if score >= 85:
            return "alpha_ready"
        if score >= 75:
            return "ready_with_review"
        if score >= 60:
            return "limited_readiness"
        return "not_ready"

    def _dimension(self, name: str, score: float, note: str) -> InstitutionalReadinessDimension:
        payload = {"dimension": name, "score": score, "note": note}
        return InstitutionalReadinessDimension(
            dimension_id=_hash(payload),
            dimension=name,
            score=round(score, 2),
            status=self.classify_status(score),
            note=note,
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def evaluate(self, alpha_report: Dict[str, Any]) -> Dict[str, Any]:
        alpha_report = _safe_dict(alpha_report)

        alpha_status = str(alpha_report.get("alpha_status") or "unknown")
        issue_count = int(_num(alpha_report.get("issue_count"), 0))
        critical_count = int(_num(alpha_report.get("critical_count"), 0))
        warning_count = int(_num(alpha_report.get("warning_count"), 0))
        packet_count = int(_num(alpha_report.get("packet_count"), 0))
        universal_market_model_ready = alpha_report.get("universal_market_model_ready") is True

        contract_score = 100.0
        if alpha_report.get("read_only") is not True:
            contract_score -= 40
        if alpha_report.get("execution_allowed") is not False:
            contract_score -= 40
        if alpha_report.get("execution_owner") != "Q Series":
            contract_score -= 20

        integration_score = 100.0
        if alpha_status == "alpha_integration_failed":
            integration_score -= 50
        elif alpha_status == "alpha_integration_ready_with_warnings":
            integration_score -= 15
        elif alpha_status != "alpha_integration_ready":
            integration_score -= 30
        integration_score -= min(critical_count * 15, 45)
        integration_score -= min(warning_count * 5, 20)

        packet_score = min(packet_count / 5.0, 1.0) * 100.0
        if packet_count < 5:
            packet_score -= 20

        replayability_score = 100.0 if packet_count >= 5 and critical_count == 0 else max(0.0, 80.0 - critical_count * 20)
        explainability_score = 95.0 if critical_count == 0 else 70.0
        memory_score = 95.0 if packet_count >= 5 else 65.0
        umm_score = 100.0 if universal_market_model_ready else 70.0
        safety_score = max(0.0, contract_score - critical_count * 10)

        dimensions = [
            self._dimension("read_only_contract", contract_score, "Oracle must remain read-only with Q Series as execution owner."),
            self._dimension("alpha_integration", integration_score, f"Alpha integration status: {alpha_status}."),
            self._dimension("packet_completeness", packet_score, f"{packet_count}/5 required packets present."),
            self._dimension("replayability", replayability_score, "Historical replay path is required for institutional auditability."),
            self._dimension("explainability", explainability_score, "Explainability must remain available for summaries and integration packets."),
            self._dimension("historical_memory", memory_score, "Historical memory continuity supports permanent institutional intelligence."),
            self._dimension("universal_market_model", umm_score, "Universal Market Model compatibility supports future adapter expansion."),
            self._dimension("operational_safety", safety_score, "Oracle safety requires zero execution capability."),
        ]

        readiness_score = round(sum(d.score for d in dimensions) / len(dimensions), 2)
        readiness_status = self.classify_status(readiness_score)

        if critical_count > 0 or contract_score < 100:
            readiness_status = "not_ready"
        elif warning_count > 0 and readiness_status == "institutional_ready":
            readiness_status = "alpha_ready"

        readiness_id = _hash({
            "alpha_integration_id": alpha_report.get("alpha_integration_id"),
            "readiness_score": readiness_score,
            "readiness_status": readiness_status,
            "dimensions": [d.__dict__ for d in dimensions],
        })

        return {
            "module": self.name,
            "version": self.version,
            "readiness_schema_version": self.readiness_schema_version,
            "institutional_readiness_id": readiness_id,
            "readiness_status": readiness_status,
            "readiness_score": readiness_score,
            "evaluated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": universal_market_model_ready,
            "supported_domains": list(self.supported_domains),
            "source_alpha_integration_id": alpha_report.get("alpha_integration_id"),
            "source_alpha_status": alpha_status,
            "source_issue_count": issue_count,
            "source_critical_count": critical_count,
            "source_warning_count": warning_count,
            "dimension_count": len(dimensions),
            "executive_summary": {
                "headline": (
                    "Oracle Intelligence is institutionally ready."
                    if readiness_status == "institutional_ready"
                    else f"Oracle institutional readiness status: {readiness_status}."
                ),
                "institutional_readiness_id": readiness_id,
                "readiness_status": readiness_status,
                "readiness_score": readiness_score,
                "source_alpha_status": alpha_status,
                "operator_note": "Oracle remains intelligence-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "dimensions": [d.__dict__ for d in dimensions],
        }

    def explain_dimension(self, readiness_report: Dict[str, Any], dimension: str) -> Dict[str, Any]:
        readiness_report = _safe_dict(readiness_report)
        dimensions = _safe_list(readiness_report.get("dimensions"))

        requested = str(dimension or "").strip().lower()
        for item in dimensions:
            item = _safe_dict(item)
            if str(item.get("dimension") or "").strip().lower() == requested:
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "dimension": item.get("dimension"),
                    "explanation": item.get("note"),
                    "dimension_record": item,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "dimension": dimension,
            "explanation": "No institutional readiness dimension found for requested name.",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_institutional_readiness_engine = OracleInstitutionalReadinessEngine()
