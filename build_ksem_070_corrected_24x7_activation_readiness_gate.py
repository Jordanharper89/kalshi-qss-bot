from pathlib import Path
ROOT = Path.cwd()
PKG = ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE = PKG/"state"
MOD = PKG/"activation_readiness_gate.py"
TEST = ROOT/"test_ksem_070_corrected_24x7_activation_readiness_gate.py"

MODULE = r"""
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
"""

TEST_BODY = r"""
from pathlib import Path
from dataclasses import asdict
import json
from qseries_v2.kalshi_sports_evidence_mapping.activation_readiness_gate import evaluate

root = Path.cwd()
r = evaluate(root)
print("[READINESS]", r)
state = root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem070_24x7_activation_readiness.json").write_text(
    json.dumps(asdict(r), indent=2), encoding="utf-8"
)
assert r.latest_state_present
assert r.total_rows > 0
assert r.full_accounting
assert r.durable_content_hash_present
assert r.physical_exact_binding
assert r.exact_bound_count > 0
assert r.probability_enabled is False
assert r.execution_authority is False
assert r.production_launcher_change_allowed
assert r.ready_for_24x7_activation
print("[PASS] readiness derived only from latest KSEM-069 durable physical state")
print("[PASS] production launcher activation now permitted")
print("[PASS] KSEM-070 certified")
"""

def main():
    print("="*120)
    print(" KSEM-070 CORRECTED 24x7 ACTIVATION READINESS GATE INSTALLER")
    print("="*120)
    dep = STATE/"ksem_live_mapping_state.json"
    if not dep.is_file():
        raise RuntimeError("KSEM-069 latest durable mapping state required")
    MOD.write_text(MODULE.lstrip(), encoding="utf-8")
    TEST.write_text(TEST_BODY.lstrip(), encoding="utf-8")
    print("[PASS] wrote", MOD.relative_to(ROOT))
    print("[PASS] wrote", TEST.name)
    print("[PASS] stale KSEM-063 state is not consulted")
    print("[PASS] exact physical bind + full accounting required")
    print("[PASS] launcher remains untouched by this installer")
    print("[PASS] KSEM-070 installer complete")
if __name__ == "__main__":
    main()
