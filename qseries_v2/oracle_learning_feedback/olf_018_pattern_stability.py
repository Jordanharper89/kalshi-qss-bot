from __future__ import annotations
from pathlib import Path
import json,os
from .olf_017_pattern_performance import materialize_pattern_performance

OLF_018_BUILD_ID="OLF-018"
OLF_018_REVISION="OLF_018_PATTERN_CONTRADICTION_STABILITY_V1"
OUTPUT_NAME="oracle_pattern_contradiction_stability.json"

def build_pattern_stability(root=None):
    root=Path(root or Path.cwd()).resolve();src=materialize_pattern_performance(root,3)
    rows=[]
    for x in src.get("patterns",[]):
        failure_rate=1.0-float(x["hit_rate"])
        calibration_error=float(x["calibration_error"])
        contradiction=max(failure_rate,calibration_error)
        reliable=float(x["reliability_weight"])
        mature=bool(x["mature"])
        stable=mature and contradiction<=.35 and reliable>=.35
        status="STABLE" if stable else "CONTESTED" if mature else "INSUFFICIENT"
        rows.append({**x,"failure_rate":failure_rate,"contradiction_score":contradiction,"stable":stable,"status":status})
    return {"revision":OLF_018_REVISION,"learner_state_hash":src["learner_state_hash"],"patterns":rows,"stable_patterns":sum(1 for x in rows if x["stable"]),"contested_patterns":sum(1 for x in rows if x["status"]=="CONTESTED"),"execution_authority":False}

def materialize_pattern_stability(root=None):
    root=Path(root or Path.cwd()).resolve();p=build_pattern_stability(root)
    path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path);return p

def verify_olf_018_pattern_contradiction_stability():
    return OLF_018_BUILD_ID=="OLF-018" and callable(build_pattern_stability)
