
from pathlib import Path
from bisect import bisect_right
from datetime import datetime,timezone
from collections import Counter
import hashlib,json

def _epoch(v):
    if v is None:return None
    try:return float(v)
    except Exception:pass
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except Exception:return None

def _hfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def build(root=None):
    root=Path(root or Path.cwd())
    rt=root/"runtime"/"predictive_data"

    grouped={}
    rowsfile=rt/"opd_009_crypto_condition_raw_state_rows.jsonl"
    with rowsfile.open(encoding="utf-8") as f:
        for line in f:
            r=json.loads(line)
            asset=str(r.get("asset") or "").upper()
            metric=str(r.get("metric_name") or r.get("source_id") or "")
            t=_epoch(r.get("state_time"))
            if not asset or not metric or t is None:continue
            grouped.setdefault(asset,{}).setdefault(metric,[]).append((t,r))

    index={}
    for asset,metrics in grouped.items():
        index[asset]={}
        for metric,series in metrics.items():
            series.sort(key=lambda x:x[0])
            index[asset][metric]={
                "times":[x[0] for x in series],
                "rows":[x[1] for x in series],
            }

    asset_by_anchor={}
    with (rt/"opd_012_coinbase_hf_strict_asof_join.jsonl").open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line)
            asset_by_anchor[x["anchor_id"]]=x.get("asset")

    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    outrows=rt/"opd_013_crypto_condition_strict_asof_join.jsonl"

    total=0
    crypto=0
    covered=0
    leakage=0
    metric_hits=Counter()
    asset_hits=Counter()

    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line)
            total+=1
            aid=a["anchor_id"]
            asset=asset_by_anchor.get(aid)
            anchor_t=float(a["anchor_epoch"])
            states={}

            if asset:
                crypto+=1
                for metric,bucket in index.get(asset,{}).items():
                    times=bucket["times"]
                    j=bisect_right(times,anchor_t)-1
                    if j<0:continue
                    t=times[j]
                    if t>anchor_t:
                        leakage+=1
                        continue
                    r=bucket["rows"][j]
                    states[metric]={
                        "sequence_number":r.get("sequence_number"),
                        "state_epoch":t,
                        "age_seconds":anchor_t-t,
                        "source_id":r.get("source_id"),
                        "value":r.get("value"),
                        "unit":r.get("unit"),
                        "direction":r.get("direction"),
                        "basis":r.get("basis"),
                    }
                    metric_hits[metric]+=1

            if states:
                covered+=1
                asset_hits[asset]+=1

            dst.write(json.dumps({
                "anchor_id":aid,
                "asset":asset,
                "crypto_conditions":states
            },sort_keys=True,separators=(",",":"))+"\n")

    s={
        "schema_version":"OPD-013",
        "revision":"PREINDEXED_REPAIR",
        "anchor_rows":total,
        "crypto_anchor_rows":crypto,
        "covered_anchor_rows":covered,
        "coverage_fraction":covered/total if total else 0.0,
        "crypto_coverage_fraction":covered/crypto if crypto else 0.0,
        "asset_covered_counts":dict(asset_hits),
        "metric_coverage_counts":dict(metric_hits),
        "indexed_assets":sorted(index),
        "indexed_metric_count":sum(len(x) for x in index.values()),
        "post_t_feature_rows":leakage,
        "strict_asof_rule":"CRYPTO_CONDITION_STATE_TIME_LE_ANCHOR_EPOCH",
        "join_algorithm":"PREINDEXED_TIMELINES_PLUS_BINARY_SEARCH",
        "join_hash":_hfile(outrows),
        "model_fit_allowed":False,
        "formula_mining_allowed":False,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }

    out=rt/"opd_013_crypto_condition_strict_asof_join.json"
    out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
