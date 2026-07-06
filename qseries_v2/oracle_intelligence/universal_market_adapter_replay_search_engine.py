from __future__ import annotations
from typing import Any, Dict, List, Mapping, Optional
from .universal_market_adapter_replay_contracts import READ_ONLY_GUARDRAILS, ReplayResult, build_replay_result, safe_dict

class UniversalMarketAdapterReplaySearchEngine:
    module_id = "OI-192"
    module_name = "Oracle Universal Market Adapter Replay Search Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._records: List[Dict[str, Any]] = []
        self._results: List[ReplayResult] = []

    def load_registry_records(self, records: Any) -> ReplayResult:
        self._records = [safe_dict(item) for item in list(records or [])]
        return self._make_result("load_registry_records", self._records, len(self._records), {"loaded": len(self._records)})

    def search(self, criteria: Optional[Mapping[str, Any]] = None) -> ReplayResult:
        criteria_dict = safe_dict(criteria)
        selected = [record for record in self._records if self._matches(record, criteria_dict)]
        return self._make_result("search", selected, len(self._records), {"criteria": criteria_dict})

    def search_by_adapter(self, adapter_id: str) -> ReplayResult:
        return self.search({"adapter_id": adapter_id})

    def search_by_registration_id(self, registration_id: str) -> ReplayResult:
        return self.search({"registration_id": registration_id})

    def search_by_manifest_id(self, manifest_id: str) -> ReplayResult:
        return self.search({"manifest_id": manifest_id})

    def search_by_certification_id(self, certification_id: str) -> ReplayResult:
        return self.search({"certification_id": certification_id})

    def search_by_symbol(self, symbol: str) -> ReplayResult:
        return self.search({"symbol": symbol})

    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def results(self) -> List[ReplayResult]:
        return list(self._results)

    def latest_result(self) -> Optional[ReplayResult]:
        return self._results[-1] if self._results else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        return {"module_id": self.module_id, "module_name": self.module_name, "oracle_instance_id": self.oracle_instance_id, "stored_records": len(self._records), "result_count": len(self._results), "read_only_guardrails": dict(READ_ONLY_GUARDRAILS)}

    def _matches(self, record: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        for key, expected in criteria.items():
            if expected is None:
                continue
            actual = record.get(key)
            if isinstance(expected, str):
                if str(actual).lower() != expected.lower():
                    return False
            elif actual != expected:
                return False
        return True

    def _make_result(self, operation: str, records: List[Dict[str, Any]], input_count: int, metadata: Dict[str, Any]) -> ReplayResult:
        result = build_replay_result(
            oracle_instance_id=self.oracle_instance_id, module_id=self.module_id, module_name=self.module_name,
            operation=operation, records=records, input_count=input_count, metadata=metadata,
            explainability={"purpose": "Search replay registry artifacts using deterministic read-only criteria.", "read_only_reason": "Search returns a derived view only.", "execution_boundary": "Q Series remains the only execution engine.", "canonical_contract": "Returns ReplayResult."},
        )
        self._results.append(result)
        return result

def create_replay_search_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplaySearchEngine:
    return UniversalMarketAdapterReplaySearchEngine(oracle_instance_id)

__all__ = ["READ_ONLY_GUARDRAILS", "UniversalMarketAdapterReplaySearchEngine", "create_replay_search_engine"]
