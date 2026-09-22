from __future__ import annotations
from pathlib import Path
import json,os
from .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience

OLF_021_BUILD_ID="OLF-021"
OLF_021_REVISION="OLF_021_EXPERIENCE_REGIME_SEGMENTATION_V1"
OUTPUT_NAME="oracle_experience_regime_segments.json"

def probability_band(p):
    if p is None:return "PRICE_UNKNOWN"
    p=float(p)
    if p<.20:return "YES_00_19"
    if p<.40:return "YES_20_39"
    if p<.60:return "YES_40_59"
    if p<.80:return "YES_60_79"
    return "YES_80_100"

def regime_id(row):
    return "|".join((str(row.get("series_key") or "UNKNOWN"),
                     str(row.get("observation_type") or "UNKNOWN"),
                     str(row.get("utc_session") or "UNKNOWN"),
                     probability_band(row.get("implied_yes_probability"))))

def build_regime_segments(root=None):
    root=Path(root or Path.cwd()).resolve();src=materialize_outcome_attributed_experience(root)
    rows=[]
    for x in src.get("records",[]):
        if not x.get("scored"):continue
        rows.append({**x,"probability_band":probability_band(x.get("implied_yes_probability")),"regime_id":regime_id(x)})
    return {"revision":OLF_021_REVISION,"learner_state_hash":src["learner_state_hash"],
            "scored_records":len(rows),"distinct_regimes":len({x["regime_id"] for x in rows}),
            "records":rows,"execution_authority":False}

def materialize_regime_segments(root=None):
    root=Path(root or Path.cwd()).resolve();p=build_regime_segments(root);path=root/"runtime_state"/OUTPUT_NAME
    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(p,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path);return p

def verify_olf_021_experience_regime_segmentation():
    return OLF_021_BUILD_ID=="OLF-021" and probability_band(.10)=="YES_00_19" and probability_band(.90)=="YES_80_100"
