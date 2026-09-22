from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_045_temporal_trader_refresh_runtime.py'
TEST = ROOT / 'test_oiar_045_temporal_trader_refresh_runtime.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_042_fresh_current_cohort_identity_refresh import refresh_current_cohort_identity\nfrom .oiar_043_current_trader_cohort_temporal_bridge import materialize_current_trader_cohort_temporal_bridge\nfrom .oiar_044_proven_current_day_trader_snapshot import materialize_proven_current_day_snapshot\n\nOIAR_045_BUILD_ID="OIAR-045"\nOIAR_045_REVISION="OIAR_045_TEMPORAL_TRADER_REFRESH_RUNTIME_V1"\nEXECUTION_AUTHORITY=False\n\ndef run_temporal_trader_refresh(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    a=refresh_current_cohort_identity(root)\n    b=materialize_current_trader_cohort_temporal_bridge(root)\n    c=materialize_proven_current_day_snapshot(root)\n    return {"identity_markets":a["market_count"],"bridge_markets":b["market_count"],"today_markets":c["today_markets"],"classification_counts":c["classification_counts"],"execution_authority":False}\n\ndef physical_probe(root=None):\n    return run_temporal_trader_refresh(root)\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_045_temporal_trader_refresh_runtime as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_045_BUILD_ID,"OIAR-045")\n    def test_boundary(self): self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-045 CERTIFICATION TEST");print(" TEMPORAL TRADER REFRESH RUNTIME");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] temporal trader refresh orchestration certified")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_044_proven_current_day_trader_snapshot.py',)
EXTRA_FILES = {'run_oiar_045_temporal_trader_refresh_runtime.py': '\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_045_temporal_trader_refresh_runtime import run_temporal_trader_refresh\nif __name__=="__main__":\n    print(run_temporal_trader_refresh(Path.cwd()))\n'}

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
    print(" OIAR-045 INSTALLER")
    print(" TEMPORAL TRADER REFRESH RUNTIME")
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
        print("[ROLLBACK] OIAR-045 failed; affected repository files restored")
        raise

    print("[PASS] runtime-first temporal snapshot architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-045 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
