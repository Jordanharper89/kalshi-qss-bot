
from pathlib import Path
from bisect import bisect_right
from collections import Counter
import hashlib,json

WINDOWS=(5,15,30,60)

def _asset(t):
    u=str(t).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
    return None

def _hfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    cb=json.loads((rt/"opd_008_coinbase_hf_raw_condition_state.json").read_text(encoding="utf-8"))
    idx={}
    for r in cb.get("rows") or []:
        product=str(r.get("product_id") or "");asset=product.split("-")[0].upper()
        try:w=int(r.get("window_seconds"));t=float(r.get("anchor_epoch"))
        except:continue
        if w not in WINDOWS:continue
        idx.setdefault((asset,w),[]).append((t,r))
    for k in idx:idx[k].sort(key=lambda x:x[0])

    outrows=rt/"opd_012_coinbase_hf_strict_asof_join.jsonl"
    total=crypto=covered=0; per_asset=Counter(); leakage=0
    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line);total+=1;asset=_asset(a["ticker"])
            states={}
            if asset:
                crypto+=1;per_asset[asset]+=1
                for w in WINDOWS:
                    series=idx.get((asset,w),[]);times=[x[0] for x in series]
                    j=bisect_right(times,float(a["anchor_epoch"]))-1
                    if j>=0:
                        t,r=series[j]
                        if t>float(a["anchor_epoch"]):leakage+=1;continue
                        states[str(w)]={
                            "sequence_number":r.get("sequence_number"),"state_epoch":t,
                            "age_seconds":float(a["anchor_epoch"])-t,
                            "open_price":r.get("open_price"),"close_price":r.get("close_price"),
                            "return":r.get("return"),"event_count":r.get("event_count"),
                            "max_event_gap_seconds":r.get("max_event_gap_seconds"),
                            "boundary_age_seconds":r.get("boundary_age_seconds"),
                        }
            if states:covered+=1
            dst.write(json.dumps({"anchor_id":a["anchor_id"],"asset":asset,"coinbase_hf":states},sort_keys=True,separators=(",",":"))+"\n")

    s={"schema_version":"OPD-012","anchor_rows":total,"crypto_anchor_rows":crypto,
       "covered_anchor_rows":covered,"coverage_fraction":covered/total if total else 0.0,
       "crypto_coverage_fraction":covered/crypto if crypto else 0.0,
       "asset_anchor_counts":dict(per_asset),"post_t_feature_rows":leakage,
       "strict_asof_rule":"COINBASE_STATE_EPOCH_LE_ANCHOR_EPOCH",
       "join_hash":_hfile(outrows),"model_fit_allowed":False,"formula_mining_allowed":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_012_coinbase_hf_strict_asof_join.json";out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
