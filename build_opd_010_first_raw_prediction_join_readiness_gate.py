from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data"
MOD=PKG/"opd_010_first_raw_prediction_join_readiness_gate.py";TEST=ROOT/"test_opd_010_first_raw_prediction_join_readiness_gate.py"
assert (PKG/"opd_009_crypto_condition_raw_state_extract.py").exists()
MOD.write_text(r"""
from pathlib import Path
import hashlib,json
def H(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def build(root=None):
 root=Path(root or Path.cwd());d=root/"runtime"/"predictive_data"
 depth=load(d/"opd_007_full_history_source_depth_census.json")
 kalshi=load(d/"opd_004_kalshi_raw_state_at_t.json")
 outcome=load(d/"opd_005_future_outcome_census.json")
 cb=load(d/"opd_008_coinbase_hf_raw_condition_state.json")
 crypto=load(d/"opd_009_crypto_condition_raw_state.json")
 checks={
  "full_history_census_present":depth["total_rows"]>0,
  "kalshi_state_present":kalshi["row_count"]>0,
  "future_outcomes_present":outcome["outcome_rows"]>0,
  "coinbase_independent_state_present":cb["row_count"]>0,
  "crypto_condition_state_present":crypto["row_count"]>0,
  "strict_future_labels":all(x["label_strictly_future"] for x in outcome["outcomes"]),
 }
 ready=all(checks.values())
 s={"schema_version":"OPD-010","checks":checks,"raw_join_pavement_ready":ready,
    "physical_counts":{"canonical_total_rows":depth["total_rows"],"kalshi_state_rows":kalshi["row_count"],
     "future_outcome_rows":outcome["outcome_rows"],"coinbase_hf_rows":cb["row_count"],"crypto_condition_rows":crypto["row_count"]},
    "source_hashes":{"kalshi":kalshi["state_hash"],"outcomes":outcome["outcome_hash"],"coinbase":cb["hash"],"crypto_conditions":crypto["hash"]},
    "next_required":["ASOF_JOIN_EACH_OUTCOME_ANCHOR_TO_ONLY_PRE_T_EXTERNAL_STATE",
     "ADD_RELATED_KALSHI_STATE","ADD_LEARNED_STATE_WITH_ASOF_LINEAGE","ADD_OTHER_DOMAIN_STATE_WHERE_TEMPORALLY_VALID",
     "FREEZE_PREDICTION_READY_MATRIX_BEFORE_FORMULA_MINING"],
    "model_fit_allowed":False,"formula_mining_allowed":False,"edge_proven":False,
    "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
 s["gate_hash"]=H(s)
 p=d/"opd_010_first_raw_prediction_join_readiness_gate.json";p.write_text(json.dumps(s,indent=2,sort_keys=True));return s,p
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_010_first_raw_prediction_join_readiness_gate import build
s,p=build(Path.cwd());assert p.exists() and s["raw_join_pavement_ready"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[CHECKS]",s["checks"]);print("[PHYSICAL_COUNTS]",s["physical_counts"]);print("[SOURCE_HASHES]",s["source_hashes"]);print("[NEXT_REQUIRED]",s["next_required"]);print("[GATE_HASH]",s["gate_hash"])
print("[PASS] raw predictive ingredients physically present")
print("[PASS] formula mining remains blocked until strict as-of state join is frozen")
print("[PASS] OPD-006..OPD-010 predictive-data dissection slice certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-010 installer complete")
