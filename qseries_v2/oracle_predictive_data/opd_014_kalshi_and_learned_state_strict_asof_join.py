
from pathlib import Path
from bisect import bisect_right
from collections import Counter
from datetime import datetime,timezone
import hashlib,json

def _asset(t):
    u=str(t).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
    return None

def _epoch(v):
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
    ks=json.loads((rt/"opd_004_kalshi_raw_state_at_t.json").read_text(encoding="utf-8"))
    byseq={int(x["sequence_number"]):x for x in ks.get("rows") or []}

    from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
    learned=read_crypto_learned_case_history(root,per_asset_limit=10000,include_legacy=True)
    lidx={}
    for x in learned:
        t=_epoch(x.outcome_observed_at)
        if t is None:continue
        lidx.setdefault(str(x.asset).upper(),[]).append((t,x))
    for k in lidx:lidx[k].sort(key=lambda z:z[0])

    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    outrows=rt/"opd_014_kalshi_and_learned_state_strict_asof_join.jsonl"
    total=kcover=lcover=leakage=0;assets=Counter()
    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line);total+=1;seq=int(a["anchor_sequence_number"]);k=byseq.get(seq);asset=_asset(a["ticker"])
            if k:kcover+=1
            learned_state=None
            if asset:
                assets[asset]+=1;series=lidx.get(asset,[]);times=[z[0] for z in series]
                j=bisect_right(times,float(a["anchor_epoch"]))-1
                if j>=0:
                    t,x=series[j]
                    if t>float(a["anchor_epoch"]):leakage+=1
                    else:
                        lcover+=1
                        learned_state={
                            "sequence_number":x.sequence_number,"available_epoch":t,
                            "age_seconds":float(a["anchor_epoch"])-t,
                            "experience_id":x.experience_id,"snapshot_at":x.snapshot_at,
                            "condition_vector":list(x.condition_vector),"temporal_vector":list(x.temporal_vector),
                            "condition_hash":x.condition_hash,"experience_hash":x.experience_hash,
                            "lineage_hash":x.lineage_hash,"horizon_seconds":x.horizon_seconds,
                            "return_fraction":x.return_fraction,"outcome_hash":x.outcome_hash,
                            "timing_certified":x.timing_certified,"legacy_timing":x.legacy_timing,
                        }
            kstate=None if not k else {
                "sequence_number":k.get("sequence_number"),"event_epoch":k.get("event_epoch"),
                "trade_price":k.get("trade_price"),"yes_bid":k.get("yes_bid"),"yes_ask":k.get("yes_ask"),
                "spread":k.get("spread"),"yes_bid_size":k.get("yes_bid_size"),"yes_ask_size":k.get("yes_ask_size"),
                "last_trade_size":k.get("last_trade_size"),"volume":k.get("volume"),"open_interest":k.get("open_interest"),
                "observation_type":k.get("observation_type"),"event_time_path":k.get("event_time_path"),
            }
            if kstate and float(kstate["event_epoch"])>float(a["anchor_epoch"]):leakage+=1
            dst.write(json.dumps({"anchor_id":a["anchor_id"],"asset":asset,"kalshi_anchor_state":kstate,"learned_state":learned_state},sort_keys=True,separators=(",",":"))+"\n")

    s={"schema_version":"OPD-014","anchor_rows":total,"kalshi_anchor_state_covered":kcover,
       "learned_state_covered":lcover,"asset_anchor_counts":dict(assets),"learned_cases_loaded":len(learned),
       "post_t_feature_rows":leakage,
       "learned_availability_rule":"LEARNED_CASE_OUTCOME_OBSERVED_AT_LE_ANCHOR_EPOCH",
       "join_hash":_hfile(outrows),"model_fit_allowed":False,"formula_mining_allowed":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_014_kalshi_and_learned_state_strict_asof_join.json";out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
