
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
