from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Mapping
import json

READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

def stable_hash(value: Any) -> str:
    return sha256(stable_json(value).encode("utf-8")).hexdigest()

def safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}

def safe_records(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if hasattr(value, "records"):
        records = value.records
        if callable(records):
            records = records()
        return [safe_dict(item) for item in records]
    data = safe_dict(value)
    for key in ("records", "results", "items"):
        if isinstance(data.get(key), list):
            return [safe_dict(item) for item in data[key]]
    if isinstance(value, list):
        return [safe_dict(item) for item in value]
    return []

@dataclass(frozen=True)
class ReplayResult:
    result_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    operation: str
    passed: bool
    status: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    record_count: int = 0
    input_count: int = 0
    output_count: int = 0
    result_hash: str = ""
    read_only_guardrails: Dict[str, Any] = field(default_factory=lambda: dict(READ_ONLY_GUARDRAILS))
    telemetry: Dict[str, Any] = field(default_factory=dict)
    explainability: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __len__(self) -> int:
        return len(self.records)

def build_replay_result(
    *,
    oracle_instance_id: str,
    module_id: str,
    module_name: str,
    operation: str,
    records: List[Dict[str, Any]],
    input_count: int = 0,
    passed: bool = True,
    status: str = "ok",
    telemetry: Dict[str, Any] | None = None,
    explainability: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> ReplayResult:
    clean_records = [safe_dict(item) for item in records]
    payload = {
        "oracle_instance_id": oracle_instance_id,
        "module_id": module_id,
        "operation": operation,
        "records": clean_records,
        "input_count": input_count,
        "passed": passed,
        "status": status,
        "metadata": metadata or {},
    }
    result_hash = stable_hash(payload)
    base_telemetry = {
        "oracle_instance_id": oracle_instance_id,
        "module_id": module_id,
        "module_name": module_name,
        "operation": operation,
        "input_count": input_count,
        "output_count": len(clean_records),
        "record_count": len(clean_records),
        "result_hash": result_hash,
    }
    if telemetry:
        base_telemetry.update(telemetry)

    return ReplayResult(
        result_id=f"{module_id.lower()}.result.{result_hash[:24]}",
        created_at=utc_now(),
        oracle_instance_id=oracle_instance_id,
        module_id=module_id,
        module_name=module_name,
        operation=operation,
        passed=passed,
        status=status,
        records=clean_records,
        record_count=len(clean_records),
        input_count=input_count,
        output_count=len(clean_records),
        result_hash=result_hash,
        read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        telemetry=base_telemetry,
        explainability=explainability or {},
        metadata=metadata or {},
    )

__all__ = [
    "READ_ONLY_GUARDRAILS", "ReplayResult", "build_replay_result",
    "safe_dict", "safe_records", "stable_hash", "stable_json", "utc_now",
]
