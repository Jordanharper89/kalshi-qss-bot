from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json,os
from .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience

OLF_017_BUILD_ID="OLF-017"
OLF_017_REVISION="OLF_017_PATTERN_PERFORMANCE_CALIBRATION_V1"
OUTPUT_NAME="oracle_pattern_performance_calibration.json"

def build_pattern_performance(root=None,min_samples=3):
    root=Path(root or Path.cwd()).resolve();src=materialize_outcome_attributed_experience(root)
    groups=defaultdict(list)
    for x in src.get("records",[]):
        if not x.get("scored"):continue
        pid=str(x.get("series_key") or "")+"|"+str(x.get("observation_type") or "UNKNOWN")
        groups[pid].append(x)
    patterns=[]
    for pid,rows in sorted(groups.items()):
        if len(rows)<int(min_samples):continue
        n=len(rows);hits=sum(1 for x in rows if x.get("prediction_hit") is True)
        mean_prob=sum(float(x["implied_yes_probability"]) for x in rows)/n
        yes_rate=sum(1 for x in rows if x.get("settlement_result")=="yes")/n
        mean_brier=sum(float(x["brier_score"]) for x in rows)/n
        calibration_error=abs(mean_prob-yes_rate)
        sample_weight=n/(n+10.0)
        reliability=max(0.0,min(1.0,sample_weight*(1.0-mean_brier)*(1.0-calibration_error)))
        patterns.append({
            "pattern_id":pid,"series_key":rows[0]["series_key"],
            "observation_type":rows[0]["observation_type"],"samples":n,
            "hits":hits,"misses":n-hits,"hit_rate":hits/n,
            "mean_implied_yes_probability":mean_prob,"yes_outcome_rate":yes_rate,
            "mean_brier_score":mean_brier,"calibration_error":calibration_error,
            "reliability_weight":reliability,"mature":n>=5,
        })
    return {"revision":OLF_017_REVISION,"learner_state_hash":src["learner_state_hash"],"min_samples":int(min_samples),"patterns":patterns,"execution_authority":False}

def materialize_pattern_performance(root=None,min_samples=3):
    root=Path(root or Path.cwd()).resolve();p=build_pattern_performance(root,min_samples)
    path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path);return p

def verify_olf_017_pattern_performance_calibration():
    return OLF_017_BUILD_ID=="OLF-017" and callable(build_pattern_performance)
