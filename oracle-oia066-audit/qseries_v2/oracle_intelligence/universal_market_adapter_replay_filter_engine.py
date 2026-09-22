from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from .universal_market_adapter_replay_contracts import READ_ONLY_GUARDRAILS, ReplayResult, build_replay_result, safe_records

@dataclass(frozen=True)
class ReplayFilterCriteria:
    criteria: Dict[str, Any] = field(default_factory=dict)

class UniversalMarketAdapterReplayFilterEngine:
    module_id = "OI-193"
    module_name = "Oracle Universal Market Adapter Replay Filter Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._history: List[ReplayResult] = []

    def filter_records(self, records: Any, criteria: Optional[Mapping[str, Any]] = None) -> ReplayResult:
        source = safe_records(records)
        criteria_dict = dict(criteria or {})
        selected = [record for record in source if self._matches(record, criteria_dict)]
        result = build_replay_result(
            oracle_instance_id=self.oracle_instance_id, module_id=self.module_id, module_name=self.module_name,
            operation="filter_records", records=selected, input_count=len(source),
            metadata={"criteria": criteria_dict, "rejected_count": len(source) - len(selected)},
            explainability={"purpose": "Filter replay artifacts using canonical deterministic criteria.", "read_only_reason": "Filtering returns a derived view only.", "execution_boundary": "Q Series remains the only execution engine.", "canonical_contract": "Returns ReplayResult."},
        )
        self._history.append(result)
        return result

    def chain_filter(self, records: Any, criteria_chain: List[Mapping[str, Any]]) -> ReplayResult:
        current = safe_records(records)
        for criteria in criteria_chain:
            current = self.filter_records(current, criteria).records
        return self.filter_records(current, {})

    def history(self) -> List[ReplayResult]:
        return list(self._history)

    def latest_result(self) -> Optional[ReplayResult]:
        return self._history[-1] if self._history else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "filter_count": len(self._history), "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

    def _matches(self, record: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        for key, expected in criteria.items():
            if expected is None:
                continue
            if key == "min_confidence":
                if float(record.get("confidence", 0.0)) < float(expected):
                    return False
                continue
            if key == "max_confidence":
                if float(record.get("confidence", 0.0)) > float(expected):
                    return False
                continue
            actual = record.get(key)
            if isinstance(expected, str):
                if str(actual).lower() != expected.lower():
                    return False
            elif actual != expected:
                return False
        return True

def create_replay_filter_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayFilterEngine:
    return UniversalMarketAdapterReplayFilterEngine(oracle_instance_id)

def create_universal_market_adapter_replay_filter_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayFilterEngine:
    return create_replay_filter_engine(oracle_instance_id)

__all__ = ["READ_ONLY_GUARDRAILS", "ReplayFilterCriteria", "UniversalMarketAdapterReplayFilterEngine", "create_replay_filter_engine", "create_universal_market_adapter_replay_filter_engine"]
