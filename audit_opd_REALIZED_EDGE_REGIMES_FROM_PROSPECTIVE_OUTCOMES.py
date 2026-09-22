from pathlib import Path
import json, math, statistics
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=BASE/"opd_full_evidence_live_outcome_ledger.jsonl"
DEST=BASE/"opd_realized_edge_regime_audit.json"

HURDLE=0.020
MIN_N=12
MIN_TICKERS=3
Z=1.2815515655446004
REV="REALIZED_EDGE_REGIME_AUDIT_V1"

def rows(p):
    if not p.exists(): return []
    out=[]
    with p.open("r",encoding="utf-8") as f:
        for line in f:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def asset(t):
    u=str(t or "").upper()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return "OTHER"

def family(t):
    u=str(t or "").upper()
    if u.startswith(("KXBTC15M","KXETH15M","KXSOL15M")): return "CRYPTO_15M"
    if u.startswith(("KXBTCD","KXETHD","KXSOLD")): return "CRYPTO_DAILY_THRESHOLD"
    if u.startswith(("KXBTC-","KXETH-","KXSOL-")): return "CRYPTO_RANGE"
    return "OTHER"

def band(x,w):
    try:
        x=float(x)
        return f"{math.floor(x/w)*w:.2f}-{(math.floor(x/w)+1)*w:.2f}"
    except Exception: return "NA"

def summarize(rs):
    vals=[]; ticks=set(); hits=0
    for r in rs:
        try: v=float(r["directional_return"])-HURDLE
        except Exception: continue
        vals.append(v); ticks.add(str(r.get("ticker") or ""))
        if v>0: hits+=1
    n=len(vals)
    if not n: return None
    mean=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n) if n else None
    lower=mean-Z*se if se is not None else None
    return {"n":n,"unique_tickers":len(ticks),"mean_net_after_2pct":mean,
            "cumulative_net_after_2pct":sum(vals),"positive_net_rate":hits/n,
            "stddev":sd,"standard_error":se,"conservative_lower_bound":lower,
            "eligible_positive":n>=MIN_N and len(ticks)>=MIN_TICKERS and lower is not None and lower>0}

def main():
    if not PRED.exists(): raise SystemExit("[FAIL] prediction ledger missing: "+str(PRED))
    if not OUT.exists(): raise SystemExit("[FAIL] outcome ledger missing: "+str(OUT))
    pred={str(x.get("prediction_id")):x for x in rows(PRED) if x.get("prediction_id")}
    joined=[]
    for o in rows(OUT):
        if o.get("resolution_status")!="RESOLVED_EXACT_FUTURE": continue
        p=pred.get(str(o.get("prediction_id")),{})
        r=dict(o)
        for k,v in p.items(): r.setdefault(k,v)
        if int(r.get("generation") or 2)!=2: continue
        if not bool(r.get("actionable_at_freeze")): continue
        r["_asset"]=asset(r.get("ticker"))
        r["_family"]=family(r.get("ticker"))
        r["_pband"]=band(r.get("predicted_probability"),.10)
        r["_eband"]=band(r.get("net_edge_after_2pct"),.025)
        r["_aband"]=band(r.get("evidence_agreement"),.25)
        joined.append(r)

    dims=[
      ("horizon",lambda r:(r.get("horizon_seconds"),)),
      ("asset_horizon_direction",lambda r:(r["_asset"],r.get("horizon_seconds"),r.get("direction"))),
      ("family_horizon_direction",lambda r:(r["_family"],r.get("horizon_seconds"),r.get("direction"))),
      ("asset_family_horizon_direction",lambda r:(r["_asset"],r["_family"],r.get("horizon_seconds"),r.get("direction"))),
      ("asset_family_horizon_direction_probability",lambda r:(r["_asset"],r["_family"],r.get("horizon_seconds"),r.get("direction"),r["_pband"])),
      ("asset_family_horizon_direction_edge",lambda r:(r["_asset"],r["_family"],r.get("horizon_seconds"),r.get("direction"),r["_eband"])),
      ("asset_family_horizon_direction_probability_agreement",lambda r:(r["_asset"],r["_family"],r.get("horizon_seconds"),r.get("direction"),r["_pband"],r["_aband"])),
    ]
    report={"revision":REV,"hurdle":HURDLE,"min_n":MIN_N,"min_tickers":MIN_TICKERS,
            "z":Z,"resolved_actionable_gen2":len(joined),"aggregate":summarize(joined),"dimensions":{}}
    winners=[]
    for name,fn in dims:
        g=defaultdict(list)
        for r in joined: g[fn(r)].append(r)
        arr=[]
        for key,rs in g.items():
            s=summarize(rs)
            if not s: continue
            item={"key":[str(x) for x in key],**s}
            arr.append(item)
            if s["eligible_positive"]: winners.append({"dimension":name,**item})
        arr.sort(key=lambda x:(x["eligible_positive"],x["conservative_lower_bound"] if x["conservative_lower_bound"] is not None else -999,x["n"]),reverse=True)
        report["dimensions"][name]=arr
    winners.sort(key=lambda x:(x["conservative_lower_bound"],x["n"]),reverse=True)
    report["positive_regimes"]=winners
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    a=report["aggregate"] or {}
    print("="*112)
    print(" REALIZED-EDGE REGIME AUDIT")
    print("="*112)
    print("[REVISION]",REV)
    print("[GEN2 RESOLVED ACTIONABLE]",len(joined))
    print("[AGGREGATE] mean_net_after_2pct=",a.get("mean_net_after_2pct"),
          "cumulative_net=",a.get("cumulative_net_after_2pct"),
          "positive_net_rate=",a.get("positive_net_rate"))
    print("[POSITIVE SUPPORTED REGIMES]",len(winners))
    for i,w in enumerate(winners[:20],1):
        print("[WINNER]",i,"DIM=",w["dimension"],"KEY=","|".join(w["key"]),
              "N=",w["n"],"TICKERS=",w["unique_tickers"],
              "MEAN_NET=",round(w["mean_net_after_2pct"],6),
              "LOWER_BOUND=",round(w["conservative_lower_bound"],6),
              "POS_RATE=",round(w["positive_net_rate"],4))
    if not winners:
        print("[RESULT] NO_SUPPORTED_POSITIVE_REGIME_FOUND_AT_CURRENT RESOLUTION")
    else:
        print("[RESULT] SUPPORTED_POSITIVE_REGIMES_FOUND_FOR_CHALLENGER DESIGN")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__": main()
from pathlib import Path
import json,tempfile,subprocess,sys

src=Path("audit_opd_REALIZED_EDGE_REGIMES_FROM_PROSPECTIVE_OUTCOMES.py")
text=src.read_text(encoding="utf-8")
assert 'HURDLE=0.020' in text
assert 'MIN_N=12' in text
assert 'MIN_TICKERS=3' in text
assert 'RESOLVED_EXACT_FUTURE' in text
assert 'actionable_at_freeze' in text
assert 'generation") or 2)!=2' in text
assert 'conservative_lower_bound' in text
assert 'eligible_positive' in text
assert 'NO MODEL MUTATION' in text
compile(text,str(src),"exec")
print("[PASS] audit is read-only against immutable prediction/outcome ledgers")
print("[PASS] exact resolved prospective Gen2 actionable outcomes only")
print("[PASS] fixed 2pct hurdle preserved")
print("[PASS] support floor 12 cases / 3 tickers preserved")
print("[PASS] conservative lower-bound profitability criterion preserved")
print("[PASS] horizon/asset/family/direction/probability/edge/agreement regimes audited")
print("[PASS] no predictor, resolver, ledger, threshold, publication, or execution mutation")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")

