from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_056_current_market_research_ranking.py'
TEST = ROOT / 'test_oiar_056_current_market_research_ranking.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom decimal import Decimal, InvalidOperation\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\nfrom .oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics\n\nOIAR_056_BUILD_ID="OIAR-056"\nSTAGE="current_market_research_ranking"\n\ndef _num(v):\n    try: return Decimal(str(v))\n    except (InvalidOperation, TypeError, ValueError): return Decimal("0")\n\ndef _research_score(m):\n    usefulness=_num(m.get("usefulness",{}).get("usefulness_score"))\n    admission=_num(m.get("admission",{}).get("admission_score"))\n    volume=_num(m.get("features",{}).get("latest_volume_fp"))\n    obs=_num(m.get("features",{}).get("observation_count"))\n    movement=_num(m.get("features",{}).get("absolute_movement_dollars"))\n    # Ranking is research priority, not trade authorization.\n    return usefulness + admission + min(volume/Decimal("1000"), Decimal("20")) + min(obs/Decimal("10"), Decimal("10")) + movement*Decimal("100")\n\ndef materialize_current_market_research_ranking(root=None, limit=100):\n    root=Path(root or Path.cwd()).resolve()\n    src=read_latest_current_trader_analytics(root)\n    if not src: raise RuntimeError("OIAR-056 requires certified OIAR-054 analytics snapshot")\n    ranked=[]\n    for m in src.get("markets",[]):\n        item={\n            "market_id":m.get("market_id"),\n            "title":m.get("market",{}).get("title",""),\n            "status":m.get("market",{}).get("status",""),\n            "event_ticker":m.get("market",{}).get("event_ticker",""),\n            "research_score":str(_research_score(m).quantize(Decimal("0.01"))),\n            "admission_status":m.get("admission",{}).get("admission_status","unknown"),\n            "admission_score":m.get("admission",{}).get("admission_score","0"),\n            "usefulness_classification":m.get("usefulness",{}).get("classification","unknown"),\n            "usefulness_score":m.get("usefulness",{}).get("usefulness_score","0"),\n            "direction":m.get("candidate",{}).get("research_direction","neutral"),\n            "history_rows":m.get("history_rows",0),\n            "reason_codes":m.get("usefulness",{}).get("reason_codes",[]),\n        }\n        ranked.append(item)\n    ranked.sort(key=lambda x:(-_num(x["research_score"]), str(x["market_id"])))\n    ranked=ranked[:max(1,int(limit))]\n    for i,x in enumerate(ranked,1): x["rank"]=i\n    body={"schema_version":"OIAR-056","stage":STAGE,"market_count":len(ranked),"markets":ranked,\n          "ranking_is_research_priority_only":True,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body); sid="oiar-056-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor()\n        q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,"OIAR-056",OIAR_056_BUILD_ID,datetime.now(timezone.utc),len(ranked),\n         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h))\n        c.commit()\n    return body\n\ndef read_latest_current_market_research_ranking(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor(); q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone(); c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-056 snapshot hash mismatch")\n    return p\n\ndef physical_probe(root=None):\n    x=materialize_current_market_research_ranking(root)\n    return {"ranked_markets":x["market_count"],"top_market":x["markets"][0]["market_id"],"execution_authority":False}\n'
TEST_SOURCE = 'import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_056_current_market_research_ranking as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_056_BUILD_ID,"OIAR-056")\n    def test_snapshot(self):\n        x=m.read_latest_current_market_research_ranking()\n        self.assertTrue(x); self.assertGreater(x["market_count"],0)\n        self.assertTrue(x["ranking_is_research_priority_only"]); self.assertFalse(x["execution_authority"])\n        self.assertEqual([v["rank"] for v in x["markets"]], list(range(1,len(x["markets"])+1)))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-056 CERTIFICATION TEST");print(" CURRENT MARKET RESEARCH RANKING");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] current research ranking certified");print("[DONE] OIAR-056 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_054_proven_current_trader_analytics.py',)

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-056 INSTALLER")
    print(" CURRENT MARKET RESEARCH RANKING")
    print("="*88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError("Required proven upstream missing: " + rel)

    old_mod = MOD.read_bytes() if MOD.exists() else None
    old_test = TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        importlib.invalidate_caches()

        m = importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_056_current_market_research_ranking")
        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["ranked_markets"]<=0: raise RuntimeError("OIAR-056 ranked zero markets")
        if x["execution_authority"]: raise RuntimeError("OIAR-056 execution authority invariant violated")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=120)

    except Exception:
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-056 failed; affected files restored")
        raise

    print("[PASS] snapshot-only intelligence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-056 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
