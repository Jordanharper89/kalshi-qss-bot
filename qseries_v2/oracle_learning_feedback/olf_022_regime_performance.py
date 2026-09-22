from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json,os
from .olf_021_experience_regimes import materialize_regime_segments

OLF_022_BUILD_ID="OLF-022";OLF_022_REVISION="OLF_022_REGIME_SPECIFIC_PERFORMANCE_CALIBRATION_V1";OUTPUT_NAME="oracle_regime_performance_calibration.json"

def build_regime_performance(root=None,min_samples=2):
    root=Path(root or Path.cwd()).resolve();src=materialize_regime_segments(root);g=defaultdict(list)
    for x in src["records"]:g[x["regime_id"]].append(x)
    out=[]
    for rid,rows in sorted(g.items()):
        if len(rows)<min_samples:continue
        n=len(rows);hits=sum(x["prediction_hit"] is True for x in rows);b=sum(float(x["brier_score"]) for x in rows)/n
        mp=sum(float(x["implied_yes_probability"]) for x in rows)/n;yr=sum(x["settlement_result"]=="yes" for x in rows)/n;ce=abs(mp-yr)
        support=n/(n+8.0);rel=max(0.0,min(1.0,support*(1-b)*(1-ce)))
        out.append({"regime_id":rid,"series_key":rows[0]["series_key"],"observation_type":rows[0]["observation_type"],"utc_session":rows[0]["utc_session"],"probability_band":rows[0]["probability_band"],"samples":n,"hit_rate":hits/n,"mean_brier_score":b,"calibration_error":ce,"reliability_weight":rel})
    return {"revision":OLF_022_REVISION,"learner_state_hash":src["learner_state_hash"],"min_samples":min_samples,"regimes":out,"execution_authority":False}
def materialize_regime_performance(root=None,min_samples=2):
    root=Path(root or Path.cwd()).resolve();p=build_regime_performance(root,min_samples);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path);return p
def verify_olf_022_regime_specific_performance_calibration():return OLF_022_BUILD_ID=="OLF-022" and callable(build_regime_performance)
