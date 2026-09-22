from pathlib import Path
import json,itertools,math,statistics
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=BASE/"opd_full_evidence_live_outcome_ledger.jsonl"
DEST=BASE/"opd_realized_edge_token_interaction_audit.json"
HURDLE=.020; MIN_N=12; MIN_TICKERS=3; Z=1.2815515655446004
MAX_DEGREE=3; MAX_TOKENS=80
REV="REALIZED_EDGE_TOKEN_INTERACTION_AUDIT_V1"

def rows(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def toks(p):
    cand=[]
    st=p.get("state")
    if isinstance(st,dict): cand += list(st.get("tokens") or [])
    cand += list(p.get("tokens") or [])
    cand += list(p.get("evidence_tokens") or [])
    good=[]
    for x in cand:
        s=str(x)
        if not s or len(s)>180: continue
        if s.startswith(("OUTCOME:","FUTURE:","RESOLVED:","PNL:","RETURN:")): continue
        good.append(s)
    return sorted(set(good))

def summ(rs):
    vals=[];ts=set();pos=0
    for r in rs:
        try:v=float(r["directional_return"])-HURDLE
        except Exception:continue
        vals.append(v);ts.add(str(r.get("ticker") or ""))
        if v>0:pos+=1
    if not vals:return None
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n)
    lb=m-Z*se
    return {"n":n,"unique_tickers":len(ts),"mean_net_after_2pct":m,
            "cumulative_net_after_2pct":sum(vals),"positive_net_rate":pos/n,
            "stddev":sd,"standard_error":se,"conservative_lower_bound":lb,
            "eligible_positive":n>=MIN_N and len(ts)>=MIN_TICKERS and lb>0}

def main():
    if not PRED.exists() or not OUT.exists():
        raise SystemExit("[FAIL] required prospective ledgers missing")
    pm={str(r.get("prediction_id")):r for r in rows(PRED) if r.get("prediction_id")}
    joined=[]
    for o in rows(OUT):
        if o.get("resolution_status")!="RESOLVED_EXACT_FUTURE":continue
        p=pm.get(str(o.get("prediction_id")))
        if not p:continue
        r=dict(o)
        for k,v in p.items():r.setdefault(k,v)
        if int(r.get("generation") or 2)!=2 or not bool(r.get("actionable_at_freeze")):continue
        r["_tokens"]=toks(p)
        joined.append(r)

    freq=defaultdict(int)
    for r in joined:
        for t in r["_tokens"]:freq[t]+=1
    universe=[t for t,n in sorted(freq.items(),key=lambda kv:(kv[1],kv[0]),reverse=True)
              if n>=MIN_N][:MAX_TOKENS]

    groups=defaultdict(list)
    for r in joined:
        present=[t for t in r["_tokens"] if t in universe]
        for d in range(1,MAX_DEGREE+1):
            for combo in itertools.combinations(present,d):
                groups[combo].append(r)

    arr=[]
    for combo,rs in groups.items():
        s=summ(rs)
        if not s or s["n"]<MIN_N or s["unique_tickers"]<MIN_TICKERS:continue
        arr.append({"tokens":list(combo),"degree":len(combo),**s})
    arr.sort(key=lambda x:(x["eligible_positive"],x["conservative_lower_bound"],x["n"]),reverse=True)
    winners=[x for x in arr if x["eligible_positive"]]

    pos=[r for r in joined if float(r.get("directional_return") or 0)-HURDLE>0]
    neg=[r for r in joined if float(r.get("directional_return") or 0)-HURDLE<=0]
    token_diag=[]
    for t in universe:
        pn=sum(t in r["_tokens"] for r in pos)
        nn=sum(t in r["_tokens"] for r in neg)
        token_diag.append({"token":t,"positive_rows":pn,"negative_rows":nn,
                           "positive_rate_with_token":pn/(pn+nn) if pn+nn else None})
    token_diag.sort(key=lambda x:(x["positive_rate_with_token"] or 0,x["positive_rows"]),reverse=True)

    report={"revision":REV,"hurdle":HURDLE,"min_n":MIN_N,"min_tickers":MIN_TICKERS,
            "z":Z,"max_degree":MAX_DEGREE,"resolved_actionable_gen2":len(joined),
            "rows_positive_after_hurdle":len(pos),"rows_nonpositive_after_hurdle":len(neg),
            "token_universe_size":len(universe),"tested_supported_interactions":len(arr),
            "positive_supported_interactions":winners,
            "top_interactions":arr[:100],"token_diagnostics":token_diag[:100]}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*112);print(" REALIZED-EDGE TOKEN INTERACTION AUDIT");print("="*112)
    print("[REVISION]",REV)
    print("[GEN2 RESOLVED ACTIONABLE]",len(joined))
    print("[POSITIVE AFTER 2PCT]",len(pos),"[NONPOSITIVE]",len(neg))
    print("[TOKEN UNIVERSE]",len(universe),"[SUPPORTED INTERACTIONS TESTED]",len(arr))
    print("[POSITIVE SUPPORTED INTERACTIONS]",len(winners))
    for i,w in enumerate(winners[:25],1):
        print("[WINNER]",i,"DEGREE=",w["degree"],"TOKENS="," + ".join(w["tokens"]),
              "N=",w["n"],"TICKERS=",w["unique_tickers"],
              "MEAN_NET=",round(w["mean_net_after_2pct"],6),
              "LOWER_BOUND=",round(w["conservative_lower_bound"],6),
              "POS_RATE=",round(w["positive_net_rate"],4))
    if winners: print("[RESULT] TOKEN_INTERACTIONS_EXIST_FOR_FROZEN_CHALLENGER_DESIGN")
    else: print("[RESULT] NO_SUPPORTED_POSITIVE_TOKEN_INTERACTION_FOUND")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
