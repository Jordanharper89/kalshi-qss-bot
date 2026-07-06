from __future__ import annotations
from typing import Any, Dict, List, Optional
from .universal_market_adapter_replay_contracts import READ_ONLY_GUARDRAILS, ReplayResult, build_replay_result, safe_records

class UniversalMarketAdapterReplayAnalyticsEngine:
    module_id = "OI-195"
    module_name = "Oracle Universal Market Adapter Replay Analytics Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reports: List[ReplayResult] = []

    def analyze(self, records: Any) -> ReplayResult:
        source = safe_records(records)
        certified_count = sum(1 for record in source if bool(record.get("certified")))
        uncertified_count = len(source) - certified_count
        confidences = [float(record.get("confidence", 0.0)) for record in source if record.get("confidence") is not None]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        adapters = sorted({str(record.get("adapter_id")) for record in source if record.get("adapter_id")})
        levels: Dict[str, int] = {}
        for record in source:
            level = str(record.get("certification_level") or "unknown")
            levels[level] = levels.get(level, 0) + 1
        analytics_record = {"analytics_id": f"oi195.analytics.{len(self._reports) + 1}", "record_count": len(source), "certified_count": certified_count, "uncertified_count": uncertified_count, "average_confidence": round(average_confidence, 6), "adapter_count": len(adapters), "adapters": adapters, "certification_levels": levels}
        result = build_replay_result(
            oracle_instance_id=self.oracle_instance_id, module_id=self.module_id, module_name=self.module_name,
            operation="analyze", records=[analytics_record], input_count=len(source),
            metadata=analytics_record, telemetry=analytics_record,
            explainability={"purpose": "Summarize replay artifacts into institutional analytics.", "read_only_reason": "Analytics derive measurements only.", "execution_boundary": "Q Series remains the only execution engine.", "canonical_contract": "Returns ReplayResult."},
        )
        self._reports.append(result)
        return result

    def summarize(self, records: Any) -> ReplayResult:
        return self.analyze(records)

    def reports(self) -> List[ReplayResult]:
        return list(self._reports)

    def latest_report(self) -> Optional[ReplayResult]:
        return self._reports[-1] if self._reports else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "report_count": len(self._reports), "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

def create_replay_analytics_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayAnalyticsEngine:
    return UniversalMarketAdapterReplayAnalyticsEngine(oracle_instance_id)

__all__ = ["READ_ONLY_GUARDRAILS", "UniversalMarketAdapterReplayAnalyticsEngine", "create_replay_analytics_engine"]
