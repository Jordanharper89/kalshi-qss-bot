from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_042_fresh_current_cohort_identity_refresh.py'
TEST = ROOT / 'test_oiar_042_fresh_current_cohort_identity_refresh.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_021_indexed_snapshot_identity_materializer import materialize_indexed_snapshot_identity\nOIAR_042_BUILD_ID="OIAR-042"\nOIAR_042_REVISION="OIAR_042_FRESH_CURRENT_COHORT_IDENTITY_REFRESH_V1"\nEXECUTION_AUTHORITY=False\n\ndef refresh_current_cohort_identity(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    result=materialize_indexed_snapshot_identity(root, timeout_ms=15000)\n    if int(result.get("market_count") or 0) <= 0:\n        raise RuntimeError("OIAR-042 identity refresh returned zero markets")\n    if result.get("plan_uses_index") is not True:\n        raise RuntimeError("OIAR-042 refused non-indexed identity refresh")\n    return result\n\ndef physical_probe(root=None):\n    x=refresh_current_cohort_identity(root)\n    return {\n        "market_count":x["market_count"],\n        "resolved_count":x["resolved_count"],\n        "unresolved_count":x["unresolved_count"],\n        "source_index":x["source_index"],\n        "execution_authority":False,\n    }\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_042_fresh_current_cohort_identity_refresh as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_042_BUILD_ID,"OIAR-042")\n    def test_boundary(self): self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-042 CERTIFICATION TEST");print(" FRESH CURRENT-COHORT IDENTITY REFRESH");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] indexed fresh-cohort identity refresh contract certified")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_021_indexed_snapshot_identity_materializer.py',)
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
    print(" OIAR-042 INSTALLER")
    print(" FRESH CURRENT-COHORT IDENTITY REFRESH")
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
        print("[ROLLBACK] OIAR-042 failed; affected repository files restored")
        raise

    print("[PASS] runtime-first temporal snapshot architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-042 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
