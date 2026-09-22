
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_031_prospective_candidate_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["candidate_count"]>0 and not s["formula_retuning_allowed"] and not s["threshold_retuning_allowed"]
s2,_=build(Path.cwd());assert s2["activation_epoch"]==s["activation_epoch"] and s2["candidate_source_hash"]==s["candidate_source_hash"]
print("[FILE]",p);print("[CANDIDATES]",s["candidate_count"]);print("[ACTIVATION_EPOCH]",s["activation_epoch"]);print("[CANDIDATE_HASH]",s["candidate_source_hash"])
print("[PASS] prospective formulas frozen immutably before future observations");print("[PASS] repeat build preserves original activation boundary");print("[PASS] OPD-031 prospective candidate freeze certified")
