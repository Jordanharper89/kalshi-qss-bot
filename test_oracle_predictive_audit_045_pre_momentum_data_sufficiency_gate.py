from collections import defaultdict, Counter
import json, math, statistics, re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
BTC_TERMS=("btc","bitcoin")
DERIVED=("prospective","learned_case","experience","binding","forecast","verified_learning")
KALSHI="source.kalshi.market_data"

def load_rows(limit_pages=4):
    rows=[]; cursor=None
    for page in range(1,limit_pages+1):
        with connect(ROOT,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='20000ms'")
                sql="""SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json
                       FROM public.oracle_canonical_observations"""
                args=[]
                if cursor is not None:
                    sql+=" WHERE sequence_number < %s"; args.append(cursor)
                sql+=" ORDER BY sequence_number DESC LIMIT 50000"
                q.execute(sql,tuple(args)); b=q.fetchall() or []
            c.rollback()
        print("[PAGE]",page,"rows=",len(b))
        if not b: break
        rows+=b; cursor=min(int(x[0]) for x in b)
    return rows

def btc_related(source,otype,obj):
    s=(str(source)+" "+str(otype)).lower()
    if any(x in s for x in BTC_TERMS): return True
    try:
        text=json.dumps(obj,default=str).lower()
        return any(x in text for x in BTC_TERMS)
    except Exception: return False

def independent(source):
    s=str(source).lower()
    if s==KALSHI: return False
    if any(x in s for x in DERIVED): return False
    return True

def cadence(rows):
    by=defaultdict(list)
    for seq,ts,source,otype,obj in rows:
        if ts is not None: by[str(source)].append(ts)
    out={}
    for s,times in by.items():
        times=sorted(set(times))
        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]
        out[s]={
          "n":len(times),"start":times[0] if times else None,"end":times[-1] if times else None,
          "gaps":gaps,"median":statistics.median(gaps) if gaps else None,
          "p10":percentile(gaps,.10),"p90":percentile(gaps,.90),
          "lt5":sum(g<=5 for g in gaps),"lt15":sum(g<=15 for g in gaps),"lt30":sum(g<=30 for g in gaps),
          "max":max(gaps) if gaps else None}
    return out

def percentile(vals,q):
    if not vals:return None
    s=sorted(vals); i=min(len(s)-1,max(0,int(round((len(s)-1)*q))))
    return s[i]

def print_cadence(s,d):
    print("[SOURCE]",s,"n=",d["n"],"median_s=",rnd(d["median"]),"p10_s=",rnd(d["p10"]),
          "p90_s=",rnd(d["p90"]),"max_gap_s=",rnd(d["max"]),
          "gaps_lt5=",d["lt5"],"lt15=",d["lt15"],"lt30=",d["lt30"],
          "start=",d["start"],"end=",d["end"])

def rnd(x):
    return None if x is None else round(x,3)

def repo_hits(patterns):
    roots=[ROOT/"qseries_v2",ROOT]
    seen=set(); hits=[]
    for base in roots:
        if not base.exists(): continue
        for p in base.rglob("*.py"):
            try:
                rp=str(p.resolve())
                if rp in seen: continue
                seen.add(rp)
                txt=p.read_text(encoding="utf-8",errors="ignore").lower()
                score=sum(1 for x in patterns if x.lower() in txt)
                if score: hits.append((score,str(p.relative_to(ROOT))))
            except Exception: pass
    return sorted(hits,reverse=True)

rows=load_rows()
btc=[r for r in rows if btc_related(r[2],r[3],r[4]) and independent(r[2])]
c=cadence(btc)
usable=[]
print("[MATRIX_HEADER] source | n | median_s | <5s | <15s | <30s | depth_hours | lag_study")
for s,d in sorted(c.items(),key=lambda kv:(kv[1]["median"] is None,kv[1]["median"] or 1e99)):
    depth=((d["end"]-d["start"]).total_seconds()/3600) if d["start"] and d["end"] else 0
    # Physical sufficiency requires repeated sub-30s intervals, not one accidental close pair.
    ok=bool(d["median"] is not None and d["median"]<=30 and d["n"]>=100 and d["lt30"]>=50 and depth>=1)
    if ok: usable.append(s)
    print("[MATRIX]",s,"|",d["n"],"|",rnd(d["median"]),"|",d["lt5"],"|",d["lt15"],"|",d["lt30"],
          "|",round(depth,3),"|","YES" if ok else "NO")
gate="SUFFICIENT_EXISTING_PAVEMENT" if usable else "HIGH_FREQUENCY_ACQUISITION_GAP"
print("[USABLE_HIGH_FREQUENCY_SOURCES]",usable)
print("[GATE]",gate)
print("[RULE] this is a data-resolution gate, not a predictive-edge certification")
print("[PRODUCTION_MUTATION]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] OPA-045 pre-momentum data sufficiency gate audit complete")
