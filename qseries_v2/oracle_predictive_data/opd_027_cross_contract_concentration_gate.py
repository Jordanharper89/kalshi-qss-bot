
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json
MIN_TICKERS=10;MAX_TOP1_SHARE=0.25;MAX_TOP3_SHARE=0.50;MIN_ALIGNED_TICKER_RATE=0.60;MIN_OBS_PER_TICKER=3
TARGETS=("UP_5C","DOWN_5C","UP_10C","DOWN_10C","RETURN_POS","RETURN_NEG")
def _target(y,name):
    return bool(y.get("hit_plus_05")) if name=="UP_5C" else bool(y.get("hit_minus_05")) if name=="DOWN_5C" else bool(y.get("hit_plus_10")) if name=="UP_10C" else bool(y.get("hit_minus_10")) if name=="DOWN_10C" else float(y.get("future_return",0))>0 if name=="RETURN_POS" else float(y.get("future_return",0))<0
def _load_rows(rt):
    rows=[];inv=defaultdict(set)
    with (rt/"opd_021_holdout_feature_primitives.jsonl").open(encoding="utf-8") as f:
        for i,line in enumerate(f):
            x=json.loads(line);rows.append(x)
            for t in x["tokens"]:inv[(int(x["horizon_seconds"]),t)].add(i)
    return rows,inv
def _matches(inv,h,formula):
    sets=[inv.get((int(h),t),set()) for t in formula]
    if not sets:return set()
    sets=sorted(sets,key=len);z=set(sets[0])
    for s in sets[1:]:
        z.intersection_update(s)
        if not z:break
    return z
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";prev=json.loads((rt/"opd_026_temporal_replication_registry.json").read_text());rows,inv=_load_rows(rt)
    base=defaultdict(lambda:[0,0])
    for x in rows:
        h=int(x["horizon_seconds"]);t=x["ticker"]
        for target in TARGETS:base[(h,t,target)][0]+=int(_target(x["future_target"],target));base[(h,t,target)][1]+=1
    outrows=[]
    for f in prev:
        ids=_matches(inv,f["horizon_seconds"],f["formula"]);tc=Counter(rows[i]["ticker"] for i in ids);total=sum(tc.values());shares=sorted((v/total for v in tc.values()),reverse=True) if total else []
        by=defaultdict(list)
        for i in ids:by[rows[i]["ticker"]].append(i)
        aligned=eligible=0
        for t,mids in by.items():
            if len(mids)<MIN_OBS_PER_TICKER:continue
            eligible+=1;k=sum(int(_target(rows[i]["future_target"],f["target"])) for i in mids);bk,bn=base[(int(f["horizon_seconds"]),t,f["target"])]
            lift=(k/len(mids)-bk/bn) if bn else 0.0;aligned+=int(lift*f["discovery_lift"]>0)
        ar=aligned/eligible if eligible else 0.0
        checks={"min_tickers":len(tc)>=MIN_TICKERS,"top1_share":(shares[0] if shares else 1)<=MAX_TOP1_SHARE,"top3_share":sum(shares[:3])<=MAX_TOP3_SHARE,"aligned_ticker_rate":ar>=MIN_ALIGNED_TICKER_RATE}
        z=dict(f);z["match_count"]=total;z["ticker_count"]=len(tc);z["top1_share"]=shares[0] if shares else None;z["top3_share"]=sum(shares[:3]) if shares else None;z["eligible_tickers_for_sign"]=eligible;z["aligned_ticker_rate"]=ar;z["contract_concentration_checks"]=checks;z["cross_contract_pass"]=bool(f.get("temporal_replication_pass")) and all(checks.values());outrows.append(z)
    rf=rt/"opd_027_cross_contract_concentration_registry.json";rf.write_text(json.dumps(outrows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-027","evaluated":len(outrows),"cross_contract_pass":sum(x["cross_contract_pass"] for x in outrows),"fixed_thresholds":{"min_tickers":MIN_TICKERS,"max_top1_share":MAX_TOP1_SHARE,"max_top3_share":MAX_TOP3_SHARE,"min_aligned_ticker_rate":MIN_ALIGNED_TICKER_RATE,"min_obs_per_ticker":MIN_OBS_PER_TICKER},"thresholds_tuned_on_validation":False,"registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0}
    out=rt/"opd_027_cross_contract_concentration_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
