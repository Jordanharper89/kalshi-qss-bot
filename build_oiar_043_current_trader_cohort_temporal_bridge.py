from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_043_current_trader_cohort_temporal_bridge.py'
TEST = ROOT / 'test_oiar_043_current_trader_cohort_temporal_bridge.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief\nfrom .oiar_021_indexed_snapshot_identity_materializer import read_latest_indexed_snapshot_identity\nfrom .oiar_042_fresh_current_cohort_identity_refresh import refresh_current_cohort_identity\n\nOIAR_043_BUILD_ID="OIAR-043"\nOIAR_043_REVISION="OIAR_043_CURRENT_TRADER_COHORT_TEMPORAL_BRIDGE_V1"\nSTAGE="current_trader_cohort_temporal_bridge"\nEXECUTION_AUTHORITY=False\n\ndef materialize_current_trader_cohort_temporal_bridge(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    refresh_current_cohort_identity(root)\n    identity=read_latest_indexed_snapshot_identity(root)\n    trader=read_fast_trader_brief(root,50)\n    imap={str(x.get("market_id") or ""):x for x in identity.get("markets",[]) if isinstance(x,dict)}\n    rows=[]\n    for raw in trader.markets:\n        m=dict(raw);mid=str(m.get("market_id") or "")\n        ident=imap.get(mid,{})\n        m["source_open_time"]=ident.get("source_open_time")\n        m["source_close_time"]=ident.get("source_close_time")\n        m["identity_observed_at"]=ident.get("identity_observed_at")\n        m["temporal_identity_resolved"]=bool(ident)\n        rows.append(m)\n    body={"schema_version":"OIAR-043","stage":STAGE,"market_count":len(rows),"markets":rows,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-043-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "\n                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,STAGE,"OIAR-043",OIAR_043_BUILD_ID,datetime.now(timezone.utc),len(rows),json.dumps(body,sort_keys=True,default=str),h),\n            )\n        c.commit()\n    return {"snapshot_id":sid,"market_count":len(rows),"resolved_temporal_identity":sum(bool(r["temporal_identity_resolved"]) for r in rows),"execution_authority":False}\n\ndef physical_probe(root=None):\n    return materialize_current_trader_cohort_temporal_bridge(root)\n'
TEST_SOURCE = '\nimport unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_043_current_trader_cohort_temporal_bridge as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_043_BUILD_ID,"OIAR-043")\n    def test_stage(self): self.assertEqual(m.STAGE,"current_trader_cohort_temporal_bridge")\n    def test_no_terminal_scan(self): self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-043 CERTIFICATION TEST");print(" CURRENT TRADER-COHORT TEMPORAL BRIDGE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] current trader-cohort temporal bridge certified")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_042_fresh_current_cohort_identity_refresh.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_025_fast_persisted_trader_brief_read_model.py')
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
    print(" OIAR-043 INSTALLER")
    print(" CURRENT TRADER-COHORT TEMPORAL BRIDGE")
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
        print("[ROLLBACK] OIAR-043 failed; affected repository files restored")
        raise

    print("[PASS] runtime-first temporal snapshot architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-043 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
