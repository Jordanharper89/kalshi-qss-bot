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
