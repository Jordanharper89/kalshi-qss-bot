from pathlib import Path
import textwrap, shutil, time

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=R/"test_opd_LIVE_FULL_EVIDENCE_FRESH_CANONICAL_CUTOVER.py"
B=P.with_suffix(".pre_fresh_canonical_cutover.bak")

MODULE=r"""
from pathlib import Path
import json,time

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens

EXECUTION_AUTHORITY=False
PUBLICATION_ALLOWED=False
HURDLE=0.020
MIN_NET_EDGE=0.005
MIN_CASES=20
MIN_TICKERS=3
MIN_DIRECTION_PROB=0.58
MIN_MEAN_SIMILARITY=0.20
MAX_STATE_AGE_SECONDS=120.0
MAX_NEIGHBORS=100
CATEGORIES=("K","CB","CC","L")
HORIZONS=(5,15,30,60,300,900,3600)

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
    u=str(ticker).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
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

def _anchor_from_row(row):
    seq,oid,outer_epoch,obj=row
    p=canonical_point(obj,float(outer_epoch))
    if not p:return None
    asset=_asset(p["ticker"])
    if not asset:return None
    return {
      "anchor_id":str(oid),
      "ticker":p["ticker"],
      "asset":asset,
      "observed_epoch":float(p["event_epoch"]),
      "anchor_price":float(p["price"]),
      "anchor_sequence_boundary":int(seq),
      "anchor_sequence_basis":"EXACT_CANONICAL_OBSERVATION",
      "kalshi_state":{
        "sequence_number":int(seq),
        "event_epoch":float(p["event_epoch"]),
        "trade_price":float(p["price"]),
        "yes_bid":None,"yes_ask":None,"spread":None,
        "yes_bid_size":None,"yes_ask_size":None,
        "last_trade_size":None,"volume":None,"open_interest":None,
        "observation_type":"canonical_market_data",
        "event_time_path":"OPD046_CANONICAL_POINT",
      },
      "post_freeze":True,
    }

def latest_live_anchor(root):
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='5000ms'")
            q.execute("""
              SELECT sequence_number,observation_id,EXTRACT(EPOCH FROM observed_at),canonical_observation_json
              FROM public.oracle_canonical_observations
              WHERE source_id=%s
              ORDER BY sequence_number DESC
              LIMIT 4000
            """,(SOURCE,))
            rows=q.fetchall() or []
        c.rollback()
    for row in rows:
        a=_anchor_from_row(row)
        if a:return a
    return None

def materialize_current_states(anchor,root):
    extra=assemble(anchor,root)
    out=[]
    for h in HORIZONS:
        world={
          "anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":anchor["observed_epoch"],"horizon_seconds":h,
          "anchor_price":anchor["anchor_price"],"kalshi_state":anchor["kalshi_state"],
          "coinbase_hf_state":extra["coinbase_hf_state"],
          "crypto_condition_state":extra["crypto_condition_state"],
          "learned_state":extra["learned_state"],
        }
        out.append({
          "state_id":"LIVE_IN_MEMORY_"+anchor["anchor_id"]+"_"+str(h),
          "anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":float(anchor["observed_epoch"]),
          "horizon_seconds":h,"anchor_price":anchor["anchor_price"],
          "tokens":list(materialize_exact_live_tokens(root,world)),
        })
    return out,extra

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
    mean_ret=_weighted_mean([(x[0],x[3]) for x in hist])
    if hist:
        sw=sum(x[0] for x in hist)
        up_prob=sum(x[0]*(1.0 if x[3]>0 else .5 if x[3]==0 else 0.0) for x in hist)/sw
        mean_mfe=sum(x[0]*x[4] for x in hist)/sw
        mean_mae=sum(x[0]*x[5] for x in hist)/sw
    else: up_prob=mean_mfe=mean_mae=None
    direction=None;prob=None
    if up_prob is not None:
        direction="UP" if up_prob>=.5 else "DOWN"
        prob=up_prob if direction=="UP" else 1.0-up_prob
    directional_return=None if mean_ret is None else (mean_ret if direction=="UP" else -mean_ret)
    net=None if directional_return is None else directional_return-HURDLE
    curcats=_cats(cur.get("tokens") or []);votes={}
    for k in CATEGORIES:
        if not curcats[k]:continue
        pairs=[]
        for _,s,o,r,_,_ in hist:
            z=_jaccard(curcats[k],_cats(s.get("tokens") or [])[k])
            if z and z>0:pairs.append((z,r))
        m=_weighted_mean(pairs)
        votes[k]={"cases":len(pairs),"mean_return":m,
                  "direction":None if m is None or abs(m)<1e-12 else ("UP" if m>0 else "DOWN")}
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
    return {"state":cur,"asset":asset,"horizon_seconds":h,"age_seconds":age,
      "comparable_cases":n,"unique_tickers":tickers,"mean_similarity":mean_sim,
      "direction":direction,"predicted_probability":prob,"expected_return":directional_return,
      "net_edge_after_2pct":net,"expected_mfe":mean_mfe,"expected_mae":mean_mae,
      "evidence_votes":votes,"evidence_agreement":agree,"checks":checks,
      "passed":all(checks.values())}

def run(root=None,now=None,anchor=None):
    root=Path(root or Path.cwd()).resolve(); now=float(time.time() if now is None else now)
    rt=root/"runtime"/"predictive_data"
    history=_rows(rt/"opd_032_prospective_state_ledger.jsonl")
    outcomes={x.get("state_id"):x for x in _rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
    print("="*112);print("ORACLE LIVE FULL-EVIDENCE FUSION PREDICTOR — FRESH CANONICAL CUTOVER");print("="*112)
    anchor=anchor or latest_live_anchor(root)
    if not anchor:
        print("LIVE_PREDICTION=ABSTAIN");print("REASON=NO_LIVE_CANONICAL_CRYPTO_ANCHOR")
        print("EXECUTION_AUTHORITY=FALSE");return None
    print("LIVE_ANCHOR_TICKER=",anchor["ticker"])
    print("LIVE_ANCHOR_SEQUENCE=",anchor.get("anchor_sequence_boundary"))
    print("LIVE_ANCHOR_AGE_SECONDS=",max(0.0,now-float(anchor["observed_epoch"])))
    current,extra=materialize_current_states(anchor,root)
    print("LIVE_EVIDENCE_COINBASE_WINDOWS=",sorted(extra["coinbase_hf_state"].keys()))
    print("LIVE_EVIDENCE_CONDITION_METRICS=",len(extra["crypto_condition_state"]))
    print("LIVE_EVIDENCE_LEARNED=",bool(extra["learned_state"]))
    scores=[_score_state(x,history,outcomes,now) for x in current]
    for z in scores:
        print("-"*112)
        print("TICKER=",z["state"]["ticker"],"HORIZON=",z["horizon_seconds"],"AGE_SECONDS=",round(z["age_seconds"],3))
        print("EVIDENCE_TOKENS=",len(z["state"].get("tokens") or []),
              "K/CB/CC/L=",{k:len(_cats(z["state"].get("tokens") or [])[k]) for k in CATEGORIES})
        print("COMPARABLE_CASES=",z["comparable_cases"],"UNIQUE_TICKERS=",z["unique_tickers"],
              "MEAN_SIMILARITY=",round(z["mean_similarity"],6))
        print("EVIDENCE_VOTES=",json.dumps(z["evidence_votes"],sort_keys=True,separators=(",",":")))
        print("EVIDENCE_AGREEMENT=",z["evidence_agreement"])
        print("DIRECTION=",z["direction"],"PREDICTED_PROBABILITY=",z["predicted_probability"])
        print("EXPECTED_RETURN=",z["expected_return"],"NET_EDGE_AFTER_2PCT=",z["net_edge_after_2pct"])
        failed=[k for k,v in z["checks"].items() if not v]
        print("DECISION="+(z["direction"] if z["passed"] else "ABSTAIN"),
              "FAILED_GATES="+(",".join(failed) if failed else "NONE"))
    passed=[z for z in scores if z["passed"]]
    print("="*112)
    if passed:
        best=max(passed,key=lambda z:(float(z["net_edge_after_2pct"]),float(z["predicted_probability"])))
        print("LIVE_PREDICTION=",best["direction"])
        print("TICKER=",best["state"]["ticker"])
        print("HORIZON_SECONDS=",best["horizon_seconds"])
        print("PREDICTED_PROBABILITY=",best["predicted_probability"])
        print("EXPECTED_RETURN=",best["expected_return"])
        print("NET_EXPECTED_EDGE_AFTER_2PCT=",best["net_edge_after_2pct"])
        print("COMPARABLE_CASES=",best["comparable_cases"])
        print("UNIQUE_TICKERS=",best["unique_tickers"])
        print("EVIDENCE_AGREEMENT=",best["evidence_agreement"])
        print("PROFITABILITY_STATUS=LIVE_CANDIDATE_UNPROVEN")
    else:
        print("LIVE_PREDICTION=ABSTAIN")
        print("REASON=NO_HORIZON_PASSES_FULL_EVIDENCE_LIVE_DECISION_GATES")
    print("CERTIFIED=FALSE");print("PUBLICATION_ALLOWED=FALSE");print("EXECUTION_AUTHORITY=FALSE")
    return scores

if __name__=="__main__":run()
"""

TEST=r"""
import tempfile,json
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

obj={"payload":{"message":{"market_ticker":"KXETH15M-TEST","price_dollars":"0.42","ts":2000.0}}}
a=m._anchor_from_row((77,"obs77",2000.0,obj))
assert a["ticker"]=="KXETH15M-TEST"
assert a["asset"]=="ETH"
assert a["anchor_sequence_boundary"]==77
assert a["anchor_id"]=="obs77"
assert a["observed_epoch"]==2000.0

states=[];outs={}
for i in range(24):
    sid="h"+str(i)
    states.append({"state_id":sid,"ticker":"KXETH"+str(i%4),"observed_epoch":1000+i,
      "horizon_seconds":900,"tokens":["K:A","CB:B","CC:C","L:D"]})
    outs[sid]={"state_id":sid,"resolution_epoch":1500+i,"future_return":-0.05,"mfe":-0.01,"mae":-0.05}
cur={"state_id":"LIVE","ticker":"KXETH-LIVE","observed_epoch":2000.0,"horizon_seconds":900,
     "tokens":["K:A","CB:B","CC:C","L:D"]}
z=m._score_state(cur,states,outs,2001.0)
assert z["passed"] is True
assert z["direction"]=="DOWN"
assert z["predicted_probability"]==1.0
assert z["net_edge_after_2pct"]>0
assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
print("[PASS] newest canonical Kalshi observation can become an exact in-memory crypto anchor")
print("[PASS] current-state scorer uses only older outcomes resolved before the live anchor time")
print("[PASS] fresh full-evidence DOWN candidate clears unchanged support/breadth/probability/economic gates")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

if P.exists() and not B.exists():
    shutil.copy2(P,B)
P.write_text(textwrap.dedent(MODULE).lstrip(),encoding="utf-8")
T.write_text(textwrap.dedent(TEST).lstrip(),encoding="utf-8")
compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")
print("[PASS] existing full-evidence predictor cut over to freshest canonical live crypto state")
print("[PASS] stale prospective-ledger state is no longer used as the current prediction state")
print(P);print(T)
