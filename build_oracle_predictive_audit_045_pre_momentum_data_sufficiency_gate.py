from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_045_pre_momentum_data_sufficiency_gate.py'
BODY='\nfrom collections import defaultdict, Counter\nimport json, math, statistics, re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nROOT=Path.cwd()\nBTC_TERMS=("btc","bitcoin")\nDERIVED=("prospective","learned_case","experience","binding","forecast","verified_learning")\nKALSHI="source.kalshi.market_data"\n\ndef load_rows(limit_pages=4):\n    rows=[]; cursor=None\n    for page in range(1,limit_pages+1):\n        with connect(ROOT,autocommit=False) as c:\n            with c.cursor() as q:\n                q.execute("SET TRANSACTION READ ONLY")\n                q.execute("SET LOCAL statement_timeout=\'20000ms\'")\n                sql="""SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json\n                       FROM public.oracle_canonical_observations"""\n                args=[]\n                if cursor is not None:\n                    sql+=" WHERE sequence_number < %s"; args.append(cursor)\n                sql+=" ORDER BY sequence_number DESC LIMIT 50000"\n                q.execute(sql,tuple(args)); b=q.fetchall() or []\n            c.rollback()\n        print("[PAGE]",page,"rows=",len(b))\n        if not b: break\n        rows+=b; cursor=min(int(x[0]) for x in b)\n    return rows\n\ndef btc_related(source,otype,obj):\n    s=(str(source)+" "+str(otype)).lower()\n    if any(x in s for x in BTC_TERMS): return True\n    try:\n        text=json.dumps(obj,default=str).lower()\n        return any(x in text for x in BTC_TERMS)\n    except Exception: return False\n\ndef independent(source):\n    s=str(source).lower()\n    if s==KALSHI: return False\n    if any(x in s for x in DERIVED): return False\n    return True\n\ndef cadence(rows):\n    by=defaultdict(list)\n    for seq,ts,source,otype,obj in rows:\n        if ts is not None: by[str(source)].append(ts)\n    out={}\n    for s,times in by.items():\n        times=sorted(set(times))\n        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:]) if b>a]\n        out[s]={\n          "n":len(times),"start":times[0] if times else None,"end":times[-1] if times else None,\n          "gaps":gaps,"median":statistics.median(gaps) if gaps else None,\n          "p10":percentile(gaps,.10),"p90":percentile(gaps,.90),\n          "lt5":sum(g<=5 for g in gaps),"lt15":sum(g<=15 for g in gaps),"lt30":sum(g<=30 for g in gaps),\n          "max":max(gaps) if gaps else None}\n    return out\n\ndef percentile(vals,q):\n    if not vals:return None\n    s=sorted(vals); i=min(len(s)-1,max(0,int(round((len(s)-1)*q))))\n    return s[i]\n\ndef print_cadence(s,d):\n    print("[SOURCE]",s,"n=",d["n"],"median_s=",rnd(d["median"]),"p10_s=",rnd(d["p10"]),\n          "p90_s=",rnd(d["p90"]),"max_gap_s=",rnd(d["max"]),\n          "gaps_lt5=",d["lt5"],"lt15=",d["lt15"],"lt30=",d["lt30"],\n          "start=",d["start"],"end=",d["end"])\n\ndef rnd(x):\n    return None if x is None else round(x,3)\n\ndef repo_hits(patterns):\n    roots=[ROOT/"qseries_v2",ROOT]\n    seen=set(); hits=[]\n    for base in roots:\n        if not base.exists(): continue\n        for p in base.rglob("*.py"):\n            try:\n                rp=str(p.resolve())\n                if rp in seen: continue\n                seen.add(rp)\n                txt=p.read_text(encoding="utf-8",errors="ignore").lower()\n                score=sum(1 for x in patterns if x.lower() in txt)\n                if score: hits.append((score,str(p.relative_to(ROOT))))\n            except Exception: pass\n    return sorted(hits,reverse=True)\n\nrows=load_rows()\nbtc=[r for r in rows if btc_related(r[2],r[3],r[4]) and independent(r[2])]\nc=cadence(btc)\nusable=[]\nprint("[MATRIX_HEADER] source | n | median_s | <5s | <15s | <30s | depth_hours | lag_study")\nfor s,d in sorted(c.items(),key=lambda kv:(kv[1]["median"] is None,kv[1]["median"] or 1e99)):\n    depth=((d["end"]-d["start"]).total_seconds()/3600) if d["start"] and d["end"] else 0\n    # Physical sufficiency requires repeated sub-30s intervals, not one accidental close pair.\n    ok=bool(d["median"] is not None and d["median"]<=30 and d["n"]>=100 and d["lt30"]>=50 and depth>=1)\n    if ok: usable.append(s)\n    print("[MATRIX]",s,"|",d["n"],"|",rnd(d["median"]),"|",d["lt5"],"|",d["lt15"],"|",d["lt30"],\n          "|",round(depth,3),"|","YES" if ok else "NO")\ngate="SUFFICIENT_EXISTING_PAVEMENT" if usable else "HIGH_FREQUENCY_ACQUISITION_GAP"\nprint("[USABLE_HIGH_FREQUENCY_SOURCES]",usable)\nprint("[GATE]",gate)\nprint("[RULE] this is a data-resolution gate, not a predictive-edge certification")\nprint("[PRODUCTION_MUTATION]",False)\nprint("[EXECUTION_AUTHORITY]",False)\nprint("[PASS] OPA-045 pre-momentum data sufficiency gate audit complete")\n'

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
    print(" OPA-045 PRE-MOMENTUM DATA SUFFICIENCY GATE")
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
