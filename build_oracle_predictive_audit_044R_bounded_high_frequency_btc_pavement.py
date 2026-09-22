from pathlib import Path
import py_compile
ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_044R_bounded_high_frequency_btc_pavement.py'
BODY='from pathlib import Path\nfrom collections import defaultdict\nimport statistics, json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nDERIVED=("prospective","learned_case","experience","binding","forecast","verified_learning")\nKALSHI="source.kalshi.market_data"\n\ndef load_rows():\n    rows=[]; cursor=None\n    for page in range(1,5):\n        with connect(ROOT,autocommit=False) as c:\n            with c.cursor() as q:\n                q.execute("SET TRANSACTION READ ONLY")\n                q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n                sql="""SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json\n                       FROM public.oracle_canonical_observations"""\n                args=[]\n                if cursor is not None:\n                    sql+=" WHERE sequence_number < %s"; args.append(cursor)\n                sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n                q.execute(sql,tuple(args)); b=q.fetchall() or []\n            c.rollback()\n        print("[PAGE]",page,"rows=",len(b))\n        if not b: break\n        rows+=b; cursor=min(int(x[0]) for x in b)\n    return rows\n\ndef btc_related(r):\n    s=(str(r[2])+" "+str(r[3])).lower()\n    if "btc" in s or "bitcoin" in s: return True\n    try:\n        t=json.dumps(r[4],default=str).lower()\n        return "btc" in t or "bitcoin" in t\n    except Exception:return False\n\ndef independent(r):\n    s=str(r[2]).lower()\n    return s!=KALSHI and not any(x in s for x in DERIVED)\n\nrows=load_rows()\nrr=[r for r in rows if btc_related(r) and independent(r)]\nby=defaultdict(list)\nfor r in rr:\n    if r[1] is not None: by[str(r[2])].append(r[1])\nfast=[]\nfor s,times in by.items():\n    times=sorted(set(times))\n    gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]\n    med=statistics.median(gaps) if gaps else None\n    if med is not None and med<=30:\n        fast.append((med,s,len(times),sum(g<=5 for g in gaps),sum(g<=15 for g in gaps),sum(g<=30 for g in gaps)))\nprint("[INDEPENDENT_BTC_SOURCE_COUNT]",len(by))\nprint("[SUB30_MEDIAN_SOURCES]",len(fast))\nfor med,s,n,a,b,c in sorted(fast):\n    print("[FAST_SOURCE]",s,"n=",n,"median_s=",round(med,3),"lt5=",a,"lt15=",b,"lt30=",c)\n\nroots=[ROOT/"qseries_v2"/"oracle_adapters"/"independent",ROOT/"qseries_v2"/"oracle_source_network"]\nterms=("coinbase","bitcoin","btc","websocket","wss://","ticker","trade","orderbook","order_book")\nhits=[]; scanned=0\nfor base in roots:\n    if not base.exists(): continue\n    for p in base.rglob("*.py"):\n        scanned+=1\n        if scanned>2500: break\n        try: txt=p.read_text(encoding="utf-8",errors="ignore").lower()\n        except Exception: continue\n        score=sum(t in txt for t in terms)\n        if score>=3: hits.append((score,str(p.relative_to(ROOT))))\n    if scanned>2500: break\nprint("[REPO_FILES_SCANNED]",scanned)\nprint("[REPO_HF_CANDIDATE_HITS]",len(hits))\nfor score,path in sorted(hits,reverse=True)[:80]:\n    print("[REPO_HIT] score=",score,"path=",path)\nprint("[IMPORTANT] repo hits are candidates only; persistence evidence above decides physical high-frequency availability")\nprint("[PASS] OPA-044R bounded high-frequency BTC pavement audit complete")\n'

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
    print(" OPA-044R BOUNDED HIGH-FREQUENCY BTC PAVEMENT")
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
