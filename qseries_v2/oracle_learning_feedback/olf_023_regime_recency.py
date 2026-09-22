from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import json,math,os
from .olf_021_experience_regimes import materialize_regime_segments

OLF_023_BUILD_ID="OLF-023";OLF_023_REVISION="OLF_023_REGIME_RECENCY_DECAY_V1";OUTPUT_NAME="oracle_regime_recency_decay.json"
def _dt(v):
    try:
        x=datetime.fromisoformat(str(v).replace("Z","+00:00"));return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except Exception:return None
def build_recency_weighted_regimes(root=None,half_life_days=30.0,min_samples=2):
    root=Path(root or Path.cwd()).resolve();src=materialize_regime_segments(root);valid=[x for x in src["records"] if _dt(x.get("settlement_ts"))]
    anchor=max((_dt(x["settlement_ts"]) for x in valid),default=datetime.now(timezone.utc));g=defaultdict(list)
    for x in valid:g[x["regime_id"]].append(x)
    out=[]
    for rid,rows in sorted(g.items()):
        if len(rows)<min_samples:continue
        weighted=[]
        for x in rows:
            age=max(0.0,(anchor-_dt(x["settlement_ts"])).total_seconds()/86400.0);w=2**(-age/half_life_days);weighted.append((x,w,age))
        sw=sum(w for _,w,_ in weighted)
        if sw<=0:continue
        hit=sum((1.0 if x["prediction_hit"] else 0.0)*w for x,w,_ in weighted)/sw;b=sum(float(x["brier_score"])*w for x,w,_ in weighted)/sw
        mp=sum(float(x["implied_yes_probability"])*w for x,w,_ in weighted)/sw;yr=sum((1.0 if x["settlement_result"]=="yes" else 0.0)*w for x,w,_ in weighted)/sw;ce=abs(mp-yr)
        eff=min(float(len(rows)),sw);support=eff/(eff+8.0);rel=max(0.0,min(1.0,support*(1-b)*(1-ce)))
        out.append({"regime_id":rid,"samples":len(rows),"effective_samples":eff,"recency_weighted_hit_rate":hit,"recency_weighted_brier":b,"recency_weighted_calibration_error":ce,"recency_reliability_weight":rel,"newest_age_days":min(a for _,_,a in weighted),"oldest_age_days":max(a for _,_,a in weighted)})
    return {"revision":OLF_023_REVISION,"learner_state_hash":src["learner_state_hash"],"anchor_settlement_ts":anchor.isoformat(),"half_life_days":half_life_days,"regimes":out,"execution_authority":False}
def materialize_recency_weighted_regimes(root=None,half_life_days=30.0,min_samples=2):
    root=Path(root or Path.cwd()).resolve();p=build_recency_weighted_regimes(root,half_life_days,min_samples);path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path);return p
def verify_olf_023_regime_recency_decay():return OLF_023_BUILD_ID=="OLF-023" and callable(build_recency_weighted_regimes)
