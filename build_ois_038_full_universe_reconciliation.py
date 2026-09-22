from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_038_universe_reconciliation.py"
TEST = ROOT / "test_ois_038_full_universe_reconciliation.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_038_BUILD_ID="OIS-038"\nOIS_038_REVISION="OIS_038_FULL_UNIVERSE_RECONCILIATION_V1"\n\n@dataclass(frozen=True)\nclass UniverseReconciliation:\n    discovered:int\n    previous:int\n    added:tuple[str,...]\n    removed:tuple[str,...]\n    unchanged:tuple[str,...]\n    complete:bool\n\ndef reconcile_market_universe(previous_ids,discovered_ids):\n    prev=set(previous_ids)\n    new=set(discovered_ids)\n    if not new:\n        raise ValueError("discovered universe cannot be empty")\n    added=tuple(sorted(new-prev))\n    removed=tuple(sorted(prev-new))\n    unchanged=tuple(sorted(prev & new))\n    complete=len(new)==len(set(discovered_ids))\n    return UniverseReconciliation(len(new),len(prev),added,removed,unchanged,complete)\n\ndef verify_ois_038_full_universe_reconciliation():\n    r=reconcile_market_universe(("A","B"),("B","C"))\n    return r.added==("C",) and r.removed==("A",) and r.unchanged==("B",) and r.complete\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_038_universe_reconciliation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_038_full_universe_reconciliation())\n\n    def test_added_removed(self):\n        r=reconcile_market_universe(("A",),("B",))\n        self.assertEqual(r.added,("B",))\n        self.assertEqual(r.removed,("A",))\n\n    def test_empty_discovered(self):\n        with self.assertRaises(ValueError):\n            reconcile_market_universe(("A",),())\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-038 CERTIFICATION TEST");print(" FULL-UNIVERSE RECONCILIATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Deterministic full-universe adapter reconciliation certified")\n    print("[DONE] OIS-038 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_037_adapter_health")
    if getattr(upstream, "verify_ois_037_adapter_readiness_health")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_038_universe_reconciliation import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-038 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-038 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
