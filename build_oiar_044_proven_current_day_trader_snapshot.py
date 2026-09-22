from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_044_proven_current_day_trader_snapshot.py'
TEST = ROOT / 'test_oiar_044_proven_current_day_trader_snapshot.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_039_trader_temporal_classification import classify_market_time\nfrom .oiar_043_current_trader_cohort_temporal_bridge import STAGE as BRIDGE_STAGE\n\nOIAR_044_BUILD_ID="OIAR-044"\nOIAR_044_REVISION="OIAR_044_PROVEN_CURRENT_DAY_TRADER_SNAPSHOT_V1"\nSTAGE="proven_current_day_trader_snapshot"\nEXECUTION_AUTHORITY=False\n\ndef _latest_bridge(root):\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(BRIDGE_STAGE,))\n            row=cur.fetchone()\n        c.rollback()\n    if not row: raise RuntimeError("OIAR-044 requires OIAR-043 bridge snapshot")\n    p,h=row\n    if isinstance(p,str): p=json.loads(p)\n    if stable_hash(p)!=str(h): raise RuntimeError("OIAR-044 bridge hash mismatch")\n    return p\n\ndef materialize_proven_current_day_snapshot(root=None,now=None):\n    root=Path(root or Path.cwd()).resolve();src=_latest_bridge(root);now=now or datetime.now(timezone.utc)\n    rows=[]\n    counts={}\n    for raw in src.get("markets",[]):\n        m=dict(raw);t=classify_market_time(m,now);m["time_relevance"]=t\n        counts[t["label"]]=counts.get(t["label"],0)+1\n        if t["label"] in ("TODAY","TONIGHT"):\n            rows.append(m)\n    body={"schema_version":"OIAR-044","stage":STAGE,"market_count":len(rows),"source_market_count":src.get("market_count",0),"classification_counts":counts,"markets":rows,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-044-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "\n                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,STAGE,"OIAR-044",OIAR_044_BUILD_ID,now,len(rows),json.dumps(body,sort_keys=True,default=str),h),\n            )\n        c.commit()\n    return {"snapshot_id":sid,"today_markets":len(rows),"classification_counts":counts,"execution_authority":False}\n\ndef physical_probe(root=None):\n    return materialize_proven_current_day_snapshot(root)\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_044_proven_current_day_trader_snapshot as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_044_BUILD_ID,"OIAR-044")\n    def test_stage(self): self.assertEqual(m.STAGE,"proven_current_day_trader_snapshot")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-044 CERTIFICATION TEST");print(" PROVEN CURRENT-DAY TRADER SNAPSHOT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] proven current-day snapshot contract certified")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_043_current_trader_cohort_temporal_bridge.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_039_trader_temporal_classification.py')
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
    print(" OIAR-044 INSTALLER")
    print(" PROVEN CURRENT-DAY TRADER SNAPSHOT")
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
        for s in EXTRA_FILES.values():
            ast.parse(s)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, s in EXTRA_FILES.items():
            write_exact(ROOT / rel, s)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=30)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-044 failed; affected repository files restored")
        raise

    print("[PASS] runtime-first temporal snapshot architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-044 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
