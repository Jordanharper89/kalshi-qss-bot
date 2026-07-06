from __future__ import annotations
from typing import Any, Dict, List, Mapping, Optional
from .universal_market_adapter_replay_contracts import READ_ONLY_GUARDRAILS, ReplayResult, build_replay_result, safe_dict, safe_records

class UniversalMarketAdapterReplayQueryEngine:
    module_id = "OI-194"
    module_name = "Oracle Universal Market Adapter Replay Query Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._results: List[ReplayResult] = []

    def create_request(self, **kwargs: Any) -> Dict[str, Any]:
        return dict(kwargs)

    def query(self, records: Any, request: Optional[Mapping[str, Any]] = None) -> ReplayResult:
        source = safe_records(records)
        req = safe_dict(request)
        selected = list(source)
        where = safe_dict(req.get("where"))
        if where:
            selected = [record for record in selected if self._matches(record, where)]
        sort_by = req.get("sort_by")
        if sort_by:
            selected.sort(key=lambda item: item.get(sort_by, 0), reverse=str(req.get("sort_order", "asc")).lower() == "desc")
        if req.get("limit") is not None:
            selected = selected[: int(req["limit"])]
        columns = req.get("select") or req.get("columns")
        if columns:
            selected = [{column: record.get(column) for column in columns} for record in selected]
        result = build_replay_result(
            oracle_instance_id=self.oracle_instance_id, module_id=self.module_id, module_name=self.module_name,
            operation="query", records=selected, input_count=len(source), metadata={"request": req},
            explainability={"purpose": "Project, sort, and limit replay artifacts without mutation.", "read_only_reason": "Queries return derived views only.", "execution_boundary": "Q Series remains the only execution engine.", "canonical_contract": "Returns ReplayResult."},
        )
        self._results.append(result)
        return result

    def query_registered(self, records: Any) -> ReplayResult:
        return self.query(records, {"where": {"status": "registered"}})

    def results(self) -> List[ReplayResult]:
        return list(self._results)

    def latest_result(self) -> Optional[ReplayResult]:
        return self._results[-1] if self._results else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "query_count": len(self._results), "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

    def _matches(self, record: Dict[str, Any], where: Dict[str, Any]) -> bool:
        for key, expected in where.items():
            actual = record.get(key)
            if isinstance(expected, str):
                if str(actual).lower() != expected.lower():
                    return False
            elif actual != expected:
                return False
        return True

def create_replay_query_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayQueryEngine:
    return UniversalMarketAdapterReplayQueryEngine(oracle_instance_id)

__all__ = ["READ_ONLY_GUARDRAILS", "UniversalMarketAdapterReplayQueryEngine", "create_replay_query_engine"]
