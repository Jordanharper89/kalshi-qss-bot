
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_040_live_worker_activation_readiness_gate import build
s,p=build(Path.cwd());assert p.exists() and s["live_worker_activation_ready"] and not s["launcher_mutated"] and not s["native_child_registered"] and not s["execution_authority"]
print("[FILE]",p);print("[CHECKS]",s["checks"]);print("[LIVE_WORKER_ACTIVATION_READY]",s["live_worker_activation_ready"]);print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] no guessed live token materializer or premature launcher mutation admitted");print("[PASS] OPD-036..OPD-040 physical live-wiring readiness slice certified")
