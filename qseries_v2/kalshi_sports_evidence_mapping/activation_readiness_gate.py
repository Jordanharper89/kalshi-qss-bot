from pathlib import Path
from dataclasses import dataclass, asdict
import json

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False
STATUSES = ("EXACT_BOUND","PARTIAL","AMBIGUOUS","SOURCE_GAP","UNSUPPORTED")

@dataclass(frozen=True)
class KSEMActivationReadiness:
    schema_version: str
    latest_state_present: bool
    total_rows: int
    accounted_rows: int
    exact_bound_count: int
    partial_count: int
    ambiguous_count: int
    source_gap_count: int
    unsupported_count: int
    full_accounting: bool
    physical_exact_binding: bool
    durable_content_hash_present: bool
    probability_enabled: bool
    production_launcher_change_allowed: bool
    ready_for_24x7_activation: bool
    execution_authority: bool = False

def evaluate(root=None):
    root = Path(root or Path.cwd()).resolve()
    path = root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json"
    if not path.is_file():
        raise RuntimeError("LATEST_KSEM_DURABLE_STATE_MISSING")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "KSEM-069":
        raise RuntimeError("LATEST_KSEM_DURABLE_STATE_NOT_KSEM_069")
    rows = data.get("rows") or []
    counts = data.get("counts") or {}
    total = int(data.get("total_rows", len(rows)))
    accounted = sum(int(counts.get(s,0)) for s in STATUSES)
    exact = int(counts.get("EXACT_BOUND",0))
    full = bool(total > 0 and accounted == total and int(data.get("accounted_rows",accounted)) == total)
    durable = bool(str(data.get("content_hash") or "").strip())
    safe = (
        data.get("execution_authority") is False
        and data.get("probability_enabled") is False
        and all(r.get("execution_authority") is False for r in rows)
    )
    ready = bool(full and durable and exact > 0 and safe)
    return KSEMActivationReadiness(
        "KSEM-070",
        True,
        total,
        accounted,
        exact,
        int(counts.get("PARTIAL",0)),
        int(counts.get("AMBIGUOUS",0)),
        int(counts.get("SOURCE_GAP",0)),
        int(counts.get("UNSUPPORTED",0)),
        full,
        exact > 0,
        durable,
        False,
        ready,
        ready,
        False,
    )
