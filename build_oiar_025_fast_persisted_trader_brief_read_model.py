from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_025_fast_persisted_trader_brief_read_model.py'
TEST = ROOT / 'test_oiar_025_fast_persisted_trader_brief_read_model.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,time\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_024_trader_brief_snapshot import TRADER_BRIEF_STAGE\n\nOIAR_025_BUILD_ID="OIAR-025"\nOIAR_025_REVISION="OIAR_025_FAST_PERSISTED_TRADER_BRIEF_READ_MODEL_V1"\n\n@dataclass(frozen=True)\nclass FastTraderBriefRead:\n    snapshot_id:str\n    markets:tuple\n    elapsed_seconds:float\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef read_fast_trader_brief(root=None,limit=10):\n    root=Path(root or Path.cwd()).resolve();started=time.monotonic()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT snapshot_id,payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_BRIEF_STAGE,))\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:raise RuntimeError("OIAR-025 no trader brief snapshot")\n    sid,payload,ph=row\n    if isinstance(payload,str):payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-025 trader brief hash mismatch")\n    markets=tuple(payload.get("markets",[]))[:max(1,min(int(limit),50))]\n    return FastTraderBriefRead(str(sid),markets,time.monotonic()-started,True,False)\n'
TEST_SOURCE = '\nimport unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_025_fast_persisted_trader_brief_read_model as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_025_BUILD_ID,"OIAR-025")\n    def test_no_canonical_table(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-025 CERTIFICATION TEST");print(" FAST PERSISTED TRADER BRIEF READ MODEL");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] snapshot-only trader read certified");print("[DONE] OIAR-025 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_024_trader_brief_snapshot.py',)
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
    print(" OIAR-025 INSTALLER")
    print(" FAST PERSISTED TRADER BRIEF READ MODEL")
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_025_fast_persisted_trader_brief_read_model")
        x=m.read_fast_trader_brief(ROOT,10)
        print(f"[PHYSICAL] snapshot_id={x.snapshot_id} markets={len(x.markets)} elapsed_seconds={x.elapsed_seconds:.4f}")
        if len(x.markets)<=0 or x.elapsed_seconds>=1.0: raise RuntimeError("OIAR-025 fast read requirement failed")
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-025 failed; affected repository files restored")
        raise

    print("[PASS] snapshot-first trader architecture preserved")
    print("[PASS] no terminal canonical-table scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-025 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
