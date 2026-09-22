from pathlib import Path
from collections import defaultdict
import statistics, json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
DERIVED=("prospective","learned_case","experience","binding","forecast","verified_learning")
KALSHI="source.kalshi.market_data"

def load_rows():
    rows=[]; cursor=None
    for page in range(1,5):
        with connect(ROOT,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='15000ms'")
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

def btc_related(r):
    s=(str(r[2])+" "+str(r[3])).lower()
    if "btc" in s or "bitcoin" in s: return True
    try:
        t=json.dumps(r[4],default=str).lower()
        return "btc" in t or "bitcoin" in t
    except Exception:return False

def independent(r):
    s=str(r[2]).lower()
    return s!=KALSHI and not any(x in s for x in DERIVED)

rows=load_rows()
rr=[r for r in rows if btc_related(r) and independent(r)]
by=defaultdict(list)
for r in rr:
    if r[1] is not None: by[str(r[2])].append(r[1])
fast=[]
for s,times in by.items():
    times=sorted(set(times))
    gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]
    med=statistics.median(gaps) if gaps else None
    if med is not None and med<=30:
        fast.append((med,s,len(times),sum(g<=5 for g in gaps),sum(g<=15 for g in gaps),sum(g<=30 for g in gaps)))
print("[INDEPENDENT_BTC_SOURCE_COUNT]",len(by))
print("[SUB30_MEDIAN_SOURCES]",len(fast))
for med,s,n,a,b,c in sorted(fast):
    print("[FAST_SOURCE]",s,"n=",n,"median_s=",round(med,3),"lt5=",a,"lt15=",b,"lt30=",c)

roots=[ROOT/"qseries_v2"/"oracle_adapters"/"independent",ROOT/"qseries_v2"/"oracle_source_network"]
terms=("coinbase","bitcoin","btc","websocket","wss://","ticker","trade","orderbook","order_book")
hits=[]; scanned=0
for base in roots:
    if not base.exists(): continue
    for p in base.rglob("*.py"):
        scanned+=1
        if scanned>2500: break
        try: txt=p.read_text(encoding="utf-8",errors="ignore").lower()
        except Exception: continue
        score=sum(t in txt for t in terms)
        if score>=3: hits.append((score,str(p.relative_to(ROOT))))
    if scanned>2500: break
print("[REPO_FILES_SCANNED]",scanned)
print("[REPO_HF_CANDIDATE_HITS]",len(hits))
for score,path in sorted(hits,reverse=True)[:80]:
    print("[REPO_HIT] score=",score,"path=",path)
print("[IMPORTANT] repo hits are candidates only; persistence evidence above decides physical high-frequency availability")
print("[PASS] OPA-044R bounded high-frequency BTC pavement audit complete")
