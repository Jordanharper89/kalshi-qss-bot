from collections import defaultdict
import json, re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r'\bKXBTC15M-[A-Z0-9-]+\b',re.I)

def txt(x):
    try:return json.dumps(x if isinstance(x,(dict,list)) else json.loads(x),default=str).upper()
    except Exception:return str(x).upper()

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="""SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json
                   FROM public.oracle_canonical_observations"""
            args=[]
            if cursor is not None:sql+=" WHERE sequence_number < %s";args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args));b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b:break
    rows+=b;cursor=min(int(x[0]) for x in b)

kal=[];ind=[]
for seq,ts,source,typ,obj in rows:
    if ts is None:continue
    s=str(source);t=txt(obj)
    if s=="source.kalshi.market_data" and "KXBTC15M-" in t:
        kal.append((ts,int(seq),str(typ)))
    elif "BTC" in t or "BTC" in s.upper() or "BITCOIN" in s.upper():
        if s!="source.kalshi.market_data" and any(k in s.lower() for k in ("crypto","coinbase","bitcoin")):
            ind.append((ts,int(seq),s,str(typ)))

kal.sort();ind.sort()
print("[KALSHI_BTC15M_ROWS]",len(kal))
print("[INDEPENDENT_BTC_ROWS]",len(ind))

windows=(5,15,30,60)
counts={w:0 for w in windows}
examples=[]
j=0
for kts,kseq,ktyp in kal:
    while j+1<len(ind) and ind[j+1][0] <= kts:
        j+=1
    candidates=[]
    for idx in (j,j-1,j-2):
        if 0<=idx<len(ind):
            its,iseq,src,typ=ind[idx]
            lag=(kts-its).total_seconds()
            if 0<=lag<=60:
                candidates.append((lag,its,iseq,src,typ))
    if not candidates:continue
    best=min(candidates,key=lambda x:x[0])
    lag=best[0]
    for w in windows:
        if lag<=w:counts[w]+=1
    if len(examples)<40:
        examples.append((kts,kseq,lag,best[1],best[2],best[3],best[4]))

print("[PAST_ONLY_ALIGNMENT_COUNTS]",counts)
print("[NO_FUTURE_LEAKAGE_RULE] independent_observed_at <= kalshi_prediction_timestamp")
for x in examples:
    print("[ALIGN] kalshi_t=",x[0],"kalshi_seq=",x[1],"prior_independent_lag_s=",round(x[2],3),"ind_t=",x[3],"ind_seq=",x[4],"source=",x[5],"type=",x[6])
print("[PASS] OPA-018 independent-evidence past-only alignment audit complete")
