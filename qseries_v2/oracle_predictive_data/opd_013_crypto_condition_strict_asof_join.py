
from pathlib import Path
from bisect import bisect_right
from datetime import datetime,timezone
from collections import Counter
import hashlib,json

def _epoch(v):
    if v is None:return None
    try:return float(v)
    except:pass
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except:return None

def _hfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    rowsfile=rt/"opd_009_crypto_condition_raw_state_rows.jsonl"
    idx={}
    with rowsfile.open(encoding="utf-8") as f:
        for line in f:
            r=json.loads(line);asset=str(r.get("asset") or "").upper()
            t=_epoch(r.get("state_time"));metric=str(r.get("metric_name") or r.get("source_id"))
            if not asset or t is None:continue
            idx.setdefault((asset,metric),[]).append((t,r))
    for k in idx:idx[k].sort(key=lambda x:x[0])

    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    cbjoin=rt/"opd_012_coinbase_hf_strict_asof_join.jsonl"
    amap={}
    with cbjoin.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line);amap[x["anchor_id"]]=x.get("asset")

    outrows=rt/"opd_013_crypto_condition_strict_asof_join.jsonl"
    total=covered=0;leakage=0;metric_hits=Counter()
    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line);total+=1;asset=amap.get(a["anchor_id"]);states={}
            if asset:
                for (aa,metric),series in idx.items():
                    if aa!=asset:continue
                    times=[x[0] for x in series];j=bisect_right(times,float(a["anchor_epoch"]))-1
                    if j>=0:
                        t,r=series[j]
                        if t>float(a["anchor_epoch"]):leakage+=1;continue
                        states[metric]={
                            "sequence_number":r.get("sequence_number"),"state_epoch":t,
                            "age_seconds":float(a["anchor_epoch"])-t,"source_id":r.get("source_id"),
                            "value":r.get("value"),"unit":r.get("unit"),
                            "direction":r.get("direction"),"basis":r.get("basis"),
                        };metric_hits[metric]+=1
            if states:covered+=1
            dst.write(json.dumps({"anchor_id":a["anchor_id"],"asset":asset,"crypto_conditions":states},sort_keys=True,separators=(",",":"))+"\n")

    s={"schema_version":"OPD-013","anchor_rows":total,"covered_anchor_rows":covered,
       "coverage_fraction":covered/total if total else 0.0,"post_t_feature_rows":leakage,
       "metric_coverage_counts":dict(metric_hits),
       "strict_asof_rule":"CRYPTO_CONDITION_STATE_TIME_LE_ANCHOR_EPOCH",
       "join_hash":_hfile(outrows),"model_fit_allowed":False,"formula_mining_allowed":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_013_crypto_condition_strict_asof_join.json";out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
