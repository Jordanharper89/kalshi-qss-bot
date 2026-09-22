from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_031_prospective_candidate_freeze.py";TEST=ROOT/"test_opd_031_prospective_candidate_freeze.py"
MOD.write_text(r"""
from pathlib import Path
import hashlib,json,time
def _canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def build(root=None,now=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";rt.mkdir(parents=True,exist_ok=True)
    src=json.loads((rt/"opd_030_edge_candidate_registry.json").read_text())
    frozen=[{"family_id":x["family_id"],"representative_formula_id":x["representative_formula_id"],"degree":x["degree"],
             "horizon_seconds":x["horizon_seconds"],"target":x["target"],"formula":x["formula"],
             "historical_discovery_lift":x["discovery_lift"],"historical_holdout_lift":x["holdout_lift"],
             "historical_holdout_q":x["holdout_q_value"],"historical_net_after_hurdle":x["net_expected_after_hurdle"]}
            for x in src]
    source_hash=hashlib.sha256(_canon(frozen).encode()).hexdigest();out=rt/"opd_031_prospective_candidate_freeze.json"
    if out.exists():
        old=json.loads(out.read_text())
        if old["candidate_source_hash"]!=source_hash:raise RuntimeError("FROZEN_CANDIDATE_DRIFT")
        return old,out
    s={"schema_version":"OPD-031","activation_epoch":float(now if now is not None else time.time()),"candidate_count":len(frozen),
       "candidate_source_hash":source_hash,"candidates":frozen,"formula_retuning_allowed":False,"threshold_retuning_allowed":False,
       "historical_data_allowed_for_prospective_scoring":False,"edge_certified_count":0,"execution_authority":False}
    out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_031_prospective_candidate_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["candidate_count"]>0 and not s["formula_retuning_allowed"] and not s["threshold_retuning_allowed"]
s2,_=build(Path.cwd());assert s2["activation_epoch"]==s["activation_epoch"] and s2["candidate_source_hash"]==s["candidate_source_hash"]
print("[FILE]",p);print("[CANDIDATES]",s["candidate_count"]);print("[ACTIVATION_EPOCH]",s["activation_epoch"]);print("[CANDIDATE_HASH]",s["candidate_source_hash"])
print("[PASS] prospective formulas frozen immutably before future observations");print("[PASS] repeat build preserves original activation boundary");print("[PASS] OPD-031 prospective candidate freeze certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-031 installer complete")