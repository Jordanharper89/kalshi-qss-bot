from pathlib import Path
import textwrap
R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=R/"test_opd_LIVE_FULL_EVIDENCE_FUSION_PREDICTOR.py"

MODULE=r"""
from pathlib import Path
import json,time,math

EXECUTION_AUTHORITY=False
PUBLICATION_ALLOWED=False
HURDLE=0.020
MIN_NET_EDGE=0.005
MIN_CASES=20
MIN_TICKERS=3
MIN_DIRECTION_PROB=0.58
MIN_MEAN_SIMILARITY=0.20
MAX_STATE_AGE_SECONDS=900.0
MAX_NEIGHBORS=100
CATEGORIES=("K","CB","CC","L")

def _rows(p):
    out=[]
    if not p.exists(): return out
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def _asset(ticker):
    t=str(ticker).upper()
    if "BTC" in t:return "BTC"
    if "ETH" in t:return "ETH"
    if "SOL" in t:return "SOL"
    return None

def _cats(tokens):
    d={k:set() for k in CATEGORIES}
    for x in tokens or []:
        s=str(x)
        if ":" not in s: continue
        p=s.split(":",1)[0]
        if p in d:d[p].add(s)
    return d

def _jaccard(a,b):
    if not a and not b:return None
    u=a|b
    return len(a&b)/len(u) if u else None

def _similarity(a,b):
    ca,cb=_cats(a),_cats(b); vals=[]
    for k in CATEGORIES:
        if ca[k]:
            z=_jaccard(ca[k],cb[k])
            if z is not None: vals.append(z)
    return sum(vals)/len(vals) if vals else 0.0

def _weighted_mean(pairs):
    sw=sum(w for w,_ in pairs)
    return None if sw<=0 else sum(w*x for w,x in pairs)/sw

def _score_state(cur,states,outcomes,now):
    h=int(cur["horizon_seconds"]); asset=_asset(cur.get("ticker"))
    t=float(cur["observed_epoch"]); hist=[]
    for s in states:
        if s.get("state_id")==cur.get("state_id"):continue
        if int(s.get("horizon_seconds",-1))!=h:continue
        if asset and _asset(s.get("ticker"))!=asset:continue
        if float(s.get("observed_epoch",0))>=t:continue
        o=outcomes.get(s.get("state_id"))
        if not o:continue
        if float(o.get("resolution_epoch",1e99))>t:continue
        sim=_similarity(cur.get("tokens") or [],s.get("tokens") or [])
        if sim<=0:continue
        try:r=float(o["future_return"]);mfe=float(o["mfe"]);mae=float(o["mae"])
        except Exception:continue
        hist.append((sim,s,o,r,mfe,mae))
    hist.sort(key=lambda z:(z[0],float(z[1].get("observed_epoch",0))),reverse=True)
    hist=hist[:MAX_NEIGHBORS]
    n=len(hist); tickers=len({x[1].get("ticker") for x in hist})
    mean_sim=sum(x[0] for x in hist)/n if n else 0.0
    wr=[(x[0],x[3]) for x in hist]
    mean_ret=_weighted_mean(wr)
    if hist:
        sw=sum(x[0] for x in hist)
        up_prob=sum(x[0]*(1.0 if x[3]>0 else .5 if x[3]==0 else 0.0) for x in hist)/sw
        mean_mfe=sum(x[0]*x[4] for x in hist)/sw
        mean_mae=sum(x[0]*x[5] for x in hist)/sw
    else: up_prob=mean_mfe=mean_mae=None
    direction=None; prob=None
    if up_prob is not None:
        direction="UP" if up_prob>=.5 else "DOWN"
        prob=up_prob if direction=="UP" else 1.0-up_prob
    directional_return=None if mean_ret is None else (mean_ret if direction=="UP" else -mean_ret)
    net=None if directional_return is None else directional_return-HURDLE

    curcats=_cats(cur.get("tokens") or []); votes={}
    for k in CATEGORIES:
        if not curcats[k]:continue
        pairs=[]
        for _,s,o,r,_,_ in hist:
            z=_jaccard(curcats[k],_cats(s.get("tokens") or [])[k])
            if z and z>0:pairs.append((z,r))
        m=_weighted_mean(pairs)
        votes[k]={"cases":len(pairs),"mean_return":m,"direction":None if m is None or abs(m)<1e-12 else ("UP" if m>0 else "DOWN")}
    directional_votes=[v["direction"] for v in votes.values() if v["direction"]]
    agree=(sum(v==direction for v in directional_votes)/len(directional_votes)) if direction and directional_votes else None

    age=max(0.0,float(now)-t)
    checks={
      "fresh_state":age<=MAX_STATE_AGE_SECONDS,
      "comparable_cases":n>=MIN_CASES,
      "ticker_breadth":tickers>=MIN_TICKERS,
      "mean_similarity":mean_sim>=MIN_MEAN_SIMILARITY,
      "direction_probability":prob is not None and prob>=MIN_DIRECTION_PROB,
      "net_edge":net is not None and net>=MIN_NET_EDGE,
      "evidence_agreement":agree is not None and len(directional_votes)>=2 and agree>=0.60,
    }
    return {"state":cur,"asset":asset,"horizon_seconds":h,"age_seconds":age,"comparable_cases":n,
      "unique_tickers":tickers,"mean_similarity":mean_sim,"direction":direction,"predicted_probability":prob,
      "expected_return":directional_return,"net_edge_after_2pct":net,"expected_mfe":mean_mfe,"expected_mae":mean_mae,
      "evidence_votes":votes,"evidence_agreement":agree,"checks":checks,"passed":all(checks.values())}

def run(root=None,now=None):
    root=Path(root or Path.cwd()).resolve(); now=float(time.time() if now is None else now)
    rt=root/"runtime"/"predictive_data"
    states=_rows(rt/"opd_032_prospective_state_ledger.jsonl")
    outs={x.get("state_id"):x for x in _rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
    print("="*112);print("ORACLE LIVE FULL-EVIDENCE FUSION PREDICTOR");print("="*112)
    if not states:
        print("LIVE_PREDICTION=ABSTAIN");print("REASON=NO_PROSPECTIVE_STATES");print("EXECUTION_AUTHORITY=FALSE");return None
    latest_epoch=max(float(x.get("observed_epoch",0)) for x in states)
    current=[x for x in states if float(x.get("observed_epoch",0))==latest_epoch]
    scores=[_score_state(x,states,outs,now) for x in current]
    for z in sorted(scores,key=lambda x:x["horizon_seconds"]):
        print("-"*112)
        print("TICKER=",z["state"].get("ticker"),"HORIZON=",z["horizon_seconds"],"AGE_SECONDS=",round(z["age_seconds"],3))
        print("EVIDENCE_TOKENS=",len(z["state"].get("tokens") or []),
              "K/CB/CC/L=",{k:len(_cats(z["state"].get("tokens") or [])[k]) for k in CATEGORIES})
        print("COMPARABLE_CASES=",z["comparable_cases"],"UNIQUE_TICKERS=",z["unique_tickers"],
              "MEAN_SIMILARITY=",round(z["mean_similarity"],6))
        print("EVIDENCE_VOTES=",json.dumps(z["evidence_votes"],sort_keys=True,separators=(",",":")))
        print("EVIDENCE_AGREEMENT=",z["evidence_agreement"])
        print("DIRECTION=",z["direction"],"PREDICTED_PROBABILITY=",z["predicted_probability"])
        print("EXPECTED_RETURN=",z["expected_return"],"NET_EDGE_AFTER_2PCT=",z["net_edge_after_2pct"])
        print("EXPECTED_MFE=",z["expected_mfe"],"EXPECTED_MAE=",z["expected_mae"])
        failed=[k for k,v in z["checks"].items() if not v]
        print("DECISION=" + (z["direction"] if z["passed"] else "ABSTAIN"),
              "FAILED_GATES=" + (",".join(failed) if failed else "NONE"))
    passed=[z for z in scores if z["passed"]]
    print("="*112)
    if passed:
        best=max(passed,key=lambda z:(float(z["net_edge_after_2pct"]),float(z["predicted_probability"])))
        print("LIVE_PREDICTION=",best["direction"])
        print("TICKER=",best["state"].get("ticker"))
        print("HORIZON_SECONDS=",best["horizon_seconds"])
        print("PREDICTED_PROBABILITY=",best["predicted_probability"])
        print("EXPECTED_RETURN=",best["expected_return"])
        print("NET_EXPECTED_EDGE_AFTER_2PCT=",best["net_edge_after_2pct"])
        print("COMPARABLE_CASES=",best["comparable_cases"])
        print("EVIDENCE_AGREEMENT=",best["evidence_agreement"])
        print("PROFITABILITY_STATUS=LIVE_CANDIDATE_UNPROVEN")
    else:
        print("LIVE_PREDICTION=ABSTAIN")
        print("REASON=NO_HORIZON_PASSES_FULL_EVIDENCE_LIVE_DECISION_GATES")
    print("CERTIFIED=FALSE")
    print("PUBLICATION_ALLOWED=FALSE")
    print("EXECUTION_AUTHORITY=FALSE")
    return scores

if __name__=="__main__":run()
"""

TEST=r"""
import json,tempfile,io,contextlib
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

def put(p,rows):p.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
with tempfile.TemporaryDirectory() as d:
 r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
 states=[];outs=[]
 for i in range(30):
  sid="h"+str(i);ep=1000+i
  states.append({"state_id":sid,"ticker":"KXBTC"+str(i%5),"observed_epoch":ep,"horizon_seconds":300,
    "tokens":["H:300","K:ANCHOR_PRICE:40_50C","CB:60:RET:GE_20BPS","CC:momentum:DIR:UP","L:TIMING_CERTIFIED:TRUE"]})
  outs.append({"state_id":sid,"resolution_epoch":ep+300,"future_return":0.06,"mfe":0.09,"mae":0.01,
    "hit_plus_05":True,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False})
 cur={"state_id":"cur","ticker":"KXBTC-LIVE","observed_epoch":2000,"horizon_seconds":300,
   "tokens":["H:300","K:ANCHOR_PRICE:40_50C","CB:60:RET:GE_20BPS","CC:momentum:DIR:UP","L:TIMING_CERTIFIED:TRUE"]}
 states.append(cur);put(rt/"opd_032_prospective_state_ledger.jsonl",states);put(rt/"opd_033_prospective_outcome_ledger.jsonl",outs)
 z=m.run(r,now=2001);best=z[0]
 assert best["passed"] and best["direction"]=="UP"
 assert best["predicted_probability"]==1.0 and best["net_edge_after_2pct"]>0.0
with tempfile.TemporaryDirectory() as d:
 r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
 put(rt/"opd_032_prospective_state_ledger.jsonl",[{"state_id":"x","ticker":"KXETH","observed_epoch":3000,"horizon_seconds":300,
   "tokens":["H:300","CB:60:RET:ZERO","CC:momentum:DIR:FLAT"]}])
 put(rt/"opd_033_prospective_outcome_ledger.jsonl",[])
 z=m.run(r,now=3001)
 assert z and not z[0]["passed"]
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
print("[PASS] full-evidence predictor fuses K/CB/CC/L tokens against strictly older resolved same-asset cases")
print("[PASS] current-state prediction requires support, breadth, similarity, probability, economics, and evidence agreement")
print("[PASS] outcome resolution after prediction time is excluded; execution/publication remain disabled")
"""

P.write_text(textwrap.dedent(MODULE).lstrip(),encoding="utf-8")
T.write_text(textwrap.dedent(TEST).lstrip(),encoding="utf-8")
compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")
print("[PASS] Oracle live full-evidence fusion predictor installed")
print(P);print(T)
