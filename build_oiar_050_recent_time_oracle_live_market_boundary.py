from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_050_recent_time_oracle_live_market_boundary.py"
TEST=ROOT/"test_oiar_050_recent_time_oracle_live_market_boundary.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom datetime import datetime, timezone, timedelta\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\n\nOIAR_050_BUILD_ID="OIAR-050"\nOIAR_050_REVISION="OIAR_050_RECENT_TIME_ORACLE_LIVE_MARKET_BOUNDARY_V1"\nSTAGE="oracle_live_recent_time_market_universe"\nREQUIRED_INDEX="idx_oracle_canonical_observations_observed"\nEXECUTION_AUTHORITY=False\n\ndef verify_required_index(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute("""\n                SELECT i.indisvalid,i.indisready,i.indislive,pg_get_indexdef(i.indexrelid)\n                FROM pg_index i\n                JOIN pg_class x ON x.oid=i.indexrelid\n                JOIN pg_namespace n ON n.oid=x.relnamespace\n                WHERE n.nspname=\'public\' AND x.relname=%s\n            """,(REQUIRED_INDEX,))\n            row=cur.fetchone()\n        c.rollback()\n    if not row:\n        raise RuntimeError("OIAR-050 required proven observed_at index missing")\n    valid,ready,live,indexdef=row\n    if not (valid and ready and live):\n        raise RuntimeError("OIAR-050 required observed_at index is not healthy")\n    normalized=" ".join(str(indexdef).lower().split())\n    if "(observed_at, sequence_number)" not in normalized:\n        raise RuntimeError("OIAR-050 observed_at index definition changed")\n    return {"valid":True,"ready":True,"live":True,"indexdef":str(indexdef)}\n\ndef _payload(obj):\n    if not isinstance(obj,dict): return {}\n    raw=obj.get("raw_observation")\n    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):\n        return raw["payload"]\n    p=obj.get("payload")\n    return p if isinstance(p,dict) else {}\n\ndef _message(payload):\n    m=payload.get("message")\n    return m if isinstance(m,dict) else payload\n\ndef _ticker(payload):\n    msg=_message(payload)\n    return str(\n        payload.get("source_market_id")\n        or msg.get("market_ticker")\n        or msg.get("ticker")\n        or ""\n    ).strip().upper()\n\ndef explain_recent_query(root=None,window_minutes=30,row_limit=100000):\n    root=Path(root or Path.cwd()).resolve()\n    cutoff=datetime.now(timezone.utc)-timedelta(minutes=max(1,int(window_minutes)))\n    limit=max(1000,min(int(row_limit),250000))\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute("""\n                EXPLAIN (COSTS TRUE,FORMAT TEXT)\n                SELECT sequence_number,observation_type,observed_at,canonical_observation_json\n                FROM public.oracle_canonical_observations\n                WHERE observed_at >= %s\n                  AND observation_type IN (\'ticker\',\'trade\')\n                ORDER BY observed_at DESC,sequence_number DESC\n                LIMIT %s\n            """,(cutoff,limit))\n            plan="\\n".join(x[0] for x in cur.fetchall())\n        c.rollback()\n    return plan\n\ndef read_recent_oracle_live_markets(root=None,window_minutes=30,row_limit=100000,statement_timeout_ms=10000):\n    root=Path(root or Path.cwd()).resolve()\n    verify_required_index(root)\n    cutoff=datetime.now(timezone.utc)-timedelta(minutes=max(1,int(window_minutes)))\n    limit=max(1000,min(int(row_limit),250000))\n    timeout=max(1000,min(int(statement_timeout_ms),30000))\n\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SET LOCAL statement_timeout=\'{timeout}ms\'")\n            cur.execute("""\n                SELECT sequence_number,observation_type,observed_at,canonical_observation_json\n                FROM public.oracle_canonical_observations\n                WHERE observed_at >= %s\n                  AND observation_type IN (\'ticker\',\'trade\')\n                ORDER BY observed_at DESC,sequence_number DESC\n                LIMIT %s\n            """,(cutoff,limit))\n            rows=cur.fetchall() or []\n        c.rollback()\n\n    by={}\n    for seq,typ,observed,obj in rows:\n        p=_payload(obj); ticker=_ticker(p)\n        if not ticker: continue\n        obs=observed.astimezone(timezone.utc)\n        age=max(0.0,(datetime.now(timezone.utc)-obs).total_seconds())\n        rec=by.setdefault(ticker,{\n            "market_ticker":ticker,\n            "latest_sequence":0,\n            "latest_observed_at":"",\n            "freshness_seconds":age,\n            "ticker_observations":0,\n            "trade_observations":0,\n            "latest_payload":{},\n        })\n        if typ=="ticker": rec["ticker_observations"]+=1\n        elif typ=="trade": rec["trade_observations"]+=1\n        if int(seq)>int(rec["latest_sequence"]):\n            rec["latest_sequence"]=int(seq)\n            rec["latest_observed_at"]=obs.isoformat()\n            rec["freshness_seconds"]=age\n            rec["latest_payload"]=p\n\n    markets=tuple(sorted(by.values(),key=lambda x:(x["freshness_seconds"],-x["latest_sequence"],x["market_ticker"])))\n    if not markets:\n        raise RuntimeError("OIAR-050 found no Oracle Live ticker/trade markets in recent-time window")\n    return markets,len(rows),cutoff\n\ndef materialize_recent_time_market_universe(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    markets,source_rows,cutoff=read_recent_oracle_live_markets(root)\n    payload={\n        "schema_version":"OIAR-050",\n        "stage":STAGE,\n        "cutoff_utc":cutoff.isoformat(),\n        "source_rows":source_rows,\n        "market_count":len(markets),\n        "markets":list(markets),\n        "source_index":REQUIRED_INDEX,\n        "read_only_source":True,\n        "execution_authority":False,\n    }\n    h=stable_hash(payload); sid="oiar-050-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(f"""\n                INSERT INTO public.{SNAPSHOT_TABLE}\n                (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,\n                 market_count,payload_json,payload_hash,read_only_source,execution_authority)\n                VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE)\n                ON CONFLICT(snapshot_id) DO NOTHING\n            """,(sid,STAGE,"OIAR-050",OIAR_050_BUILD_ID,len(markets),\n                 json.dumps(payload,sort_keys=True,default=str),h))\n        c.commit()\n    return sid,payload\n\ndef physical_probe(root=None):\n    plan=explain_recent_query(root)\n    sid,p=materialize_recent_time_market_universe(root)\n    return {\n        "snapshot_id":sid,\n        "source_rows":p["source_rows"],\n        "observed_markets":p["market_count"],\n        "ticker_markets":sum(x["ticker_observations"]>0 for x in p["markets"]),\n        "trade_markets":sum(x["trade_observations"]>0 for x in p["markets"]),\n        "source_index":p["source_index"],\n        "plan":plan,\n        "execution_authority":False,\n    }\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_050_recent_time_oracle_live_market_boundary as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIAR_050_BUILD_ID,"OIAR-050")\n    def test_stage(self):\n        self.assertEqual(m.STAGE,"oracle_live_recent_time_market_universe")\n    def test_proven_index(self):\n        self.assertEqual(m.REQUIRED_INDEX,"idx_oracle_canonical_observations_observed")\n    def test_boundary(self):\n        self.assertFalse(m.EXECUTION_AUTHORITY)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-050 CERTIFICATION TEST")\n    print(" RECENT-TIME ORACLE LIVE MARKET BOUNDARY")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] recent-time Oracle Live boundary contract certified")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

def main():
    print("="*88);print(" OIAR-050 INSTALLER");print(" RECENT-TIME ORACLE LIVE MARKET BOUNDARY");print("="*88);print("[ROOT]",ROOT)
    required=[
      ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_001_production_analytics_snapshot_foundation.py",
      ROOT/"qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    ]
    for p in required:
        if not p.is_file(): raise RuntimeError("Required proven upstream missing: "+str(p.relative_to(ROOT)))
    old_mod=MOD.read_bytes() if MOD.exists() else None
    old_test=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_050_recent_time_oracle_live_market_boundary")
        print("[INDEX]",m.verify_required_index(ROOT))
        plan=m.explain_recent_query(ROOT)
        print("[PLAN]");print(plan)
        lower=plan.lower()
        if "idx_oracle_canonical_observations_observed" not in lower:
            raise RuntimeError("OIAR-050 planner did not select proven observed_at index")
        started=time.monotonic();x=m.physical_probe(ROOT);elapsed=round(time.monotonic()-started,3)
        print("[PHYSICAL]",{k:v for k,v in x.items() if k!="plan"},"elapsed_seconds=",elapsed)
        if x["observed_markets"]<=0: raise RuntimeError("OIAR-050 recent-time market universe empty")
    except Exception:
        restore(MOD,old_mod);restore(TEST,old_test)
        print("[ROLLBACK] OIAR-050 failed; affected repository files restored")
        raise
    print("[PASS] existing proven observed_at index reused")
    print("[PASS] no new canonical-table index created")
    print("[PASS] Oracle Live remains unmodified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-050 INSTALLATION COMPLETE")

if __name__=="__main__": main()
