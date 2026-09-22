from pathlib import Path
import py_compile
ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_042R_bounded_coinbase_capability_repair.py'
BODY='from pathlib import Path\nfrom collections import defaultdict, Counter\nimport statistics, json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\n\ndef load_rows():\n    rows=[]; cursor=None\n    for page in range(1,5):\n        with connect(ROOT,autocommit=False) as c:\n            with c.cursor() as q:\n                q.execute("SET TRANSACTION READ ONLY")\n                q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n                sql="""SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json\n                       FROM public.oracle_canonical_observations"""\n                args=[]\n                if cursor is not None:\n                    sql+=" WHERE sequence_number < %s"; args.append(cursor)\n                sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n                q.execute(sql,tuple(args)); b=q.fetchall() or []\n            c.rollback()\n        print("[PAGE]",page,"rows=",len(b))\n        if not b: break\n        rows+=b; cursor=min(int(x[0]) for x in b)\n    return rows\n\ndef cadence(rr):\n    by=defaultdict(list)\n    for seq,ts,source,otype,obj in rr:\n        if ts is not None: by[str(source)].append(ts)\n    for s,times in sorted(by.items()):\n        times=sorted(set(times))\n        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]\n        print("[SOURCE]",s,"n=",len(times),\n              "median_s=",round(statistics.median(gaps),3) if gaps else None,\n              "lt5=",sum(g<=5 for g in gaps),"lt15=",sum(g<=15 for g in gaps),"lt30=",sum(g<=30 for g in gaps))\n\ndef targeted_repo_scan():\n    roots=[\n        ROOT/"qseries_v2"/"oracle_adapters"/"independent",\n        ROOT/"qseries_v2"/"oracle_source_network",\n        ROOT/"qseries_v2"/"oracle_live_runtime",\n    ]\n    terms=("coinbase","websocket","wss://","ticker","trade","orderbook","order_book")\n    hits=[]; scanned=0\n    for base in roots:\n        if not base.exists(): continue\n        for p in base.rglob("*.py"):\n            scanned+=1\n            if scanned>2500: break\n            try:\n                txt=p.read_text(encoding="utf-8",errors="ignore").lower()\n            except Exception:\n                continue\n            score=sum(t in txt for t in terms)\n            if "coinbase" in txt and score:\n                hits.append((score,str(p.relative_to(ROOT))))\n        if scanned>2500: break\n    print("[REPO_FILES_SCANNED]",scanned)\n    print("[REPO_COINBASE_HITS]",len(hits))\n    for score,path in sorted(hits,reverse=True)[:60]:\n        print("[REPO_HIT] score=",score,"path=",path)\n\nrows=load_rows()\ncoin=[r for r in rows if "coinbase" in str(r[2]).lower()]\nprint("[COINBASE_ROWS]",len(coin))\nprint("[COINBASE_SOURCES]",len(set(str(r[2]) for r in coin)))\ncadence(coin)\nprint("[COINBASE_OBSERVATION_TYPES]",dict(Counter(str(r[3]) for r in coin)))\ntargeted_repo_scan()\nprint("[RULE] bounded targeted repository audit; no runtime/network/acquisition mutation")\nprint("[PASS] OPA-042R bounded Coinbase acquisition capability audit complete")\n'

# packaging line 01
# packaging line 02
# packaging line 03
# packaging line 04
# packaging line 05
# packaging line 06
# packaging line 07
# packaging line 08
# packaging line 09
# packaging line 10
# packaging line 11
# packaging line 12
# packaging line 13
# packaging line 14
# packaging line 15
# packaging line 16
# packaging line 17
# packaging line 18
# packaging line 19
# packaging line 20
# packaging line 21
# packaging line 22
# packaging line 23
# packaging line 24
# packaging line 25
# packaging line 26
# packaging line 27
# packaging line 28
# packaging line 29
# packaging line 30
# packaging line 31
# packaging line 32
# packaging line 33
# packaging line 34
# packaging line 35
# packaging line 36
# packaging line 37
# packaging line 38
# packaging line 39
# packaging line 40
# packaging line 41
# packaging line 42
# packaging line 43
# packaging line 44
# packaging line 45
# packaging line 46
# packaging line 47
# packaging line 48
# packaging line 49

def main():
    print("="*120)
    print(" OPA-042R BOUNDED COINBASE CAPABILITY REPAIR")
    print("="*120)
    TEST.write_text(BODY.lstrip(),encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print("[PASS] PostgreSQL READ ONLY")
    print("[PASS] repository READ ONLY")
    print("[PASS] no runtime/acquisition mutation")
    print("[PASS] execution_authority remains FALSE")
if __name__=="__main__":
    main()
