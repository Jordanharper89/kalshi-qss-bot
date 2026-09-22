from pathlib import Path
import json
from dataclasses import asdict
from qseries_v2.kalshi_sports_evidence_mapping.pre_activation_readiness import evaluate

root=Path.cwd()
r=evaluate(root)
print("[READINESS]",r)
state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
(state/"ksem065_pre_activation_24x7_readiness.json").write_text(json.dumps(asdict(r),indent=2),encoding="utf-8")
assert r.exact_live_retrieval
assert r.proposition_context
assert r.explicit_osn_binding_status
assert r.durable_cycle
if r.exact_bound_count==0:
    raise RuntimeError("NO_PHYSICAL_EXACT_OSN_BINDING_YET__DO_NOT_PATCH_PRODUCTION_LAUNCHER")
assert r.ready_for_24x7_activation
assert r.production_launcher_change_allowed
assert r.execution_authority is False
print("[PASS] KSEM has physical exact evidence binding and is ready for native 24x7 activation")
print("[PASS] KSEM-065 certified")
