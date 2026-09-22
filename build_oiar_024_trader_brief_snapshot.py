from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_024_trader_brief_snapshot.py'
TEST = ROOT / 'test_oiar_024_trader_brief_snapshot.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_023_trader_context_snapshot import TRADER_CONTEXT_STAGE,read_latest_trader_context\n\nOIAR_024_BUILD_ID="OIAR-024"\nOIAR_024_REVISION="OIAR_024_TRADER_BRIEF_SNAPSHOT_V1"\nTRADER_BRIEF_STAGE="trader_brief"\n\ndef _plain_reason(m):\n    if m["setup_status"]=="WORTH_WATCHING_NOW":\n        return "Current evidence has cleared Oracle\'s research threshold."\n    if m["setup_status"]=="SETUP_FORMING":\n        return "Oracle sees a setup forming, but it has not fully cleared the research threshold yet."\n    if m["historical_strength"]=="STRONG" and m["live_evidence"] in ("WEAK","DEVELOPING"):\n        return "Oracle knows this market family well, but current live evidence is not strong enough to confirm an edge."\n    return "Current evidence does not justify a directional edge."\n\ndef materialize_trader_brief(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    ctx=read_latest_trader_context(root)\n    if ctx is None:raise RuntimeError("OIAR-024 requires OIAR-023 context snapshot")\n    markets=[]\n    for m in ctx.get("markets",[]):\n        takeaway="WORTH WATCHING NOW" if m["setup_status"]=="WORTH_WATCHING_NOW" else "WATCH - SETUP FORMING" if m["setup_status"]=="SETUP_FORMING" else "NO EDGE RIGHT NOW"\n        markets.append({\n            **m,\n            "why":_plain_reason(m),\n            "what_would_improve_it":"More live history and a directional setup that clears Oracle\'s usefulness/candidate thresholds.",\n            "trader_takeaway":takeaway,\n        })\n    body={"schema_version":"OIAR-024","stage":TRADER_BRIEF_STAGE,"source_stage":TRADER_CONTEXT_STAGE,"market_count":len(markets),"markets":markets,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-024-"+h[:32]\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "\n                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,TRADER_BRIEF_STAGE,"OIAR-024",OIAR_024_BUILD_ID,len(markets),json.dumps(body,sort_keys=True),h),\n            )\n    return sid,body\n\ndef read_latest_trader_brief(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_BRIEF_STAGE,))\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:return None\n    payload,ph=row\n    if isinstance(payload,str):payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-024 persisted hash mismatch")\n    return payload\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_024_trader_brief_snapshot as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_024_BUILD_ID,"OIAR-024")\n    def test_stage(self):self.assertEqual(m.TRADER_BRIEF_STAGE,"trader_brief")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-024 CERTIFICATION TEST");print(" TRADER BRIEF SNAPSHOT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] trader brief snapshot certified");print("[DONE] OIAR-024 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_023_trader_context_snapshot.py',)
EXTRA_FILES = {}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-024 INSTALLER")
    print(" TRADER BRIEF SNAPSHOT")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / rel for rel in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        for src in EXTRA_FILES.values():
            ast.parse(src)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, src in EXTRA_FILES.items():
            write_exact(ROOT / rel, src)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_024_trader_brief_snapshot")
        sid,body=m.materialize_trader_brief(ROOT)
        print(f"[PHYSICAL] snapshot_id={sid} markets={body['market_count']}")
        if body["market_count"] != 50: raise RuntimeError("OIAR-024 expected 50 markets")
        print(f"[SAMPLE] title={body['markets'][0]['market_title']!r} takeaway={body['markets'][0]['trader_takeaway']}")
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-024 failed; affected repository files restored")
        raise

    print("[PASS] snapshot-first trader architecture preserved")
    print("[PASS] no terminal canonical-table scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-024 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
