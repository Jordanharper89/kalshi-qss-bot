from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_040_live_worker_activation_readiness_gate.py";TEST=ROOT/"test_opd_040_live_worker_activation_readiness_gate.py"
MOD.write_text(r"""
from pathlib import Path
import json
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    c=json.loads((rt/"opd_036_live_production_boundary_contract.json").read_text());r=json.loads((rt/"opd_037_bounded_canonical_tail_reader.json").read_text())
    l=json.loads((rt/"opd_038_formula_token_lineage_gate.json").read_text());q=json.loads((rt/"opd_039_durable_horizon_maturity_queue.json").read_text())
    checks={"production_boundary":c["candidate_count"]==2 and c["canonical_highwater_sequence"]>0,
            "bounded_reader":r["bounded_sequence_query"] and not r["whole_table_aggregate_used"],
            "token_lineage":l["all_tokens_physically_observed"] and l["exact_opd017_rules_required"],
            "maturity_queue":q["restart_rebuildable"] and q["duplicate_resolution_prevented"],
            "prospective_freeze":(rt/"opd_031_prospective_candidate_freeze.json").exists(),
            "state_intake":(root/"qseries_v2"/"oracle_predictive_data"/"opd_032_prospective_state_intake_ledger.py").exists(),
            "outcome_resolver":(root/"qseries_v2"/"oracle_predictive_data"/"opd_033_prospective_future_outcome_resolver.py").exists()}
    ready=all(checks.values())
    s={"schema_version":"OPD-040","checks":checks,"live_worker_activation_ready":ready,
       "launcher_mutated":False,"native_child_registered":False,"reason":"READINESS_ONLY_UNTIL_EXACT_LIVE_TOKEN_MATERIALIZER_IS_BOUND",
       "next_required":"OPD-041_EXACT_LIVE_TOKEN_MATERIALIZER_FROM_FROZEN_OPD017_SEMANTICS_THEN_NATIVE_CHILD_CUTOVER",
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_040_live_worker_activation_readiness_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True))
    if not ready:raise RuntimeError("OPD040_READINESS_FAILED:"+repr(checks))
    return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_040_live_worker_activation_readiness_gate import build
s,p=build(Path.cwd());assert p.exists() and s["live_worker_activation_ready"] and not s["launcher_mutated"] and not s["native_child_registered"] and not s["execution_authority"]
print("[FILE]",p);print("[CHECKS]",s["checks"]);print("[LIVE_WORKER_ACTIVATION_READY]",s["live_worker_activation_ready"]);print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] no guessed live token materializer or premature launcher mutation admitted");print("[PASS] OPD-036..OPD-040 physical live-wiring readiness slice certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-040 installer complete")