from __future__ import annotations
from typing import Any, Dict, List, Optional
from .universal_market_adapter_replay_contracts import READ_ONLY_GUARDRAILS, ReplayResult, build_replay_result, safe_dict, safe_records

class UniversalMarketAdapterReplayIntelligenceEngine:
    module_id = "OI-196"
    module_name = "Oracle Universal Market Adapter Replay Intelligence Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reports: List[ReplayResult] = []

    def generate_intelligence(self, records: Any, analytics: Any = None, context: Any = None) -> ReplayResult:
        source = safe_records(records)
        analytics_dict = safe_dict(analytics)
        context_dict = safe_dict(context)
        certified = sum(1 for record in source if bool(record.get("certified")))
        high_confidence = sum(1 for record in source if float(record.get("confidence", 0.0)) >= 0.80)
        insight = {"intelligence_id": f"oi196.intelligence.{len(self._reports) + 1}", "record_count": len(source), "certified_count": certified, "high_confidence_count": high_confidence, "quality_score": round((certified / len(source)) if source else 0.0, 6), "summary": "Replay artifacts show usable certified replay intelligence." if certified else "No certified replay intelligence detected.", "context": context_dict, "analytics_result_id": analytics_dict.get("result_id")}
        result = build_replay_result(
            oracle_instance_id=self.oracle_instance_id, module_id=self.module_id, module_name=self.module_name,
            operation="generate_intelligence", records=[insight], input_count=len(source),
            metadata=insight, telemetry=insight,
            explainability={"purpose": "Convert replay analytics and artifacts into higher-level replay intelligence.", "read_only_reason": "Replay intelligence derives insights only.", "execution_boundary": "Q Series remains the only execution engine.", "canonical_contract": "Returns ReplayResult."},
        )
        self._reports.append(result)
        return result

    def generate_from_engines(self, search_result: Any = None, filter_result: Any = None, query_result: Any = None, analytics: Any = None) -> ReplayResult:
        records = safe_records(query_result) or safe_records(filter_result) or safe_records(search_result)
        return self.generate_intelligence(records, analytics=analytics, context={"source": "generate_from_engines"})

    def intelligence_manifest(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "report_count": len(self._reports), "reports": [report.to_dict() for report in self._reports], "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

    def reports(self) -> List[ReplayResult]:
        return list(self._reports)

    def latest_report(self) -> Optional[ReplayResult]:
        return self._reports[-1] if self._reports else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "report_count": len(self._reports), "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

def create_replay_intelligence_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayIntelligenceEngine:
    return UniversalMarketAdapterReplayIntelligenceEngine(oracle_instance_id)

__all__ = ["READ_ONLY_GUARDRAILS", "UniversalMarketAdapterReplayIntelligenceEngine", "create_replay_intelligence_engine"]
