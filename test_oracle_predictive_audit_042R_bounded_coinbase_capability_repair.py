from pathlib import Path
from collections import defaultdict, Counter
import statistics, json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()

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

def cadence(rr):
    by=defaultdict(list)
    for seq,ts,source,otype,obj in rr:
        if ts is not None: by[str(source)].append(ts)
    for s,times in sorted(by.items()):
        times=sorted(set(times))
        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]
        print("[SOURCE]",s,"n=",len(times),
              "median_s=",round(statistics.median(gaps),3) if gaps else None,
              "lt5=",sum(g<=5 for g in gaps),"lt15=",sum(g<=15 for g in gaps),"lt30=",sum(g<=30 for g in gaps))

def targeted_repo_scan():
    roots=[
        ROOT/"qseries_v2"/"oracle_adapters"/"independent",
        ROOT/"qseries_v2"/"oracle_source_network",
        ROOT/"qseries_v2"/"oracle_live_runtime",
    ]
    terms=("coinbase","websocket","wss://","ticker","trade","orderbook","order_book")
    hits=[]; scanned=0
    for base in roots:
        if not base.exists(): continue
        for p in base.rglob("*.py"):
            scanned+=1
            if scanned>2500: break
            try:
                txt=p.read_text(encoding="utf-8",errors="ignore").lower()
            except Exception:
                continue
            score=sum(t in txt for t in terms)
            if "coinbase" in txt and score:
                hits.append((score,str(p.relative_to(ROOT))))
        if scanned>2500: break
    print("[REPO_FILES_SCANNED]",scanned)
    print("[REPO_COINBASE_HITS]",len(hits))
    for score,path in sorted(hits,reverse=True)[:60]:
        print("[REPO_HIT] score=",score,"path=",path)

rows=load_rows()
coin=[r for r in rows if "coinbase" in str(r[2]).lower()]
print("[COINBASE_ROWS]",len(coin))
print("[COINBASE_SOURCES]",len(set(str(r[2]) for r in coin)))
cadence(coin)
print("[COINBASE_OBSERVATION_TYPES]",dict(Counter(str(r[3]) for r in coin)))
targeted_repo_scan()
print("[RULE] bounded targeted repository audit; no runtime/network/acquisition mutation")
print("[PASS] OPA-042R bounded Coinbase acquisition capability audit complete")
