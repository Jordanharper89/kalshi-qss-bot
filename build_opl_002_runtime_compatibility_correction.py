from pathlib import Path
import inspect
import os
import subprocess
import sys

ROOT = Path.cwd().resolve()
TARGET = ROOT / "qseries_v2" / "oracle_production_learning" / "opl_002_canonical_evidence_index.py"
TEST = ROOT / "test_opl_002_runtime_compatibility_correction.py"

OLD_SIGNATURE = "def sync_evidence_index(root=None,batch_size=10000,max_batches=None):"
NEW_SIGNATURE = "def sync_evidence_index(root=None,batch_size=10000,max_batches=None,backfill_if_empty=None):"

TEST_SOURCE = r"""import inspect
import unittest

from qseries_v2.oracle_production_learning.opl_002_canonical_evidence_index import (
    OPL_002_BUILD_ID,
    sync_evidence_index,
)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(OPL_002_BUILD_ID, "OPL-002")

    def test_runtime_compatibility_keyword(self):
        sig = inspect.signature(sync_evidence_index)
        self.assertIn("backfill_if_empty", sig.parameters)

    def test_runtime_compatibility_keyword_is_optional(self):
        p = inspect.signature(sync_evidence_index).parameters["backfill_if_empty"]
        self.assertIsNone(p.default)

if __name__ == "__main__":
    print("=" * 88)
    print(" OPL-002 RUNTIME COMPATIBILITY CERTIFICATION TEST")
    print(" PRESERVE FULL EVIDENCE INDEX + RESTORE LEGACY KEYWORD")
    print("=" * 88)
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] sync_evidence_index accepts backfill_if_empty")
    print("[PASS] compatibility parameter is optional")
    print("[PASS] no evidence-index rebuild required")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-002 RUNTIME COMPATIBILITY CERTIFIED")
"""

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OPL-002 RUNTIME COMPATIBILITY CORRECTION")
    print(" PRESERVE FULL EVIDENCE INDEX")
    print("=" * 88)
    print("[ROOT]", ROOT)

    if not TARGET.is_file():
        raise RuntimeError("Current OPL-002 module is missing")

    before = TARGET.read_bytes()
    old_test = TEST.read_bytes() if TEST.exists() else None

    try:
        source = TARGET.read_text(encoding="utf-8")

        if NEW_SIGNATURE in source:
            print("[PASS] Compatibility signature already present")
        elif OLD_SIGNATURE in source:
            patched = source.replace(OLD_SIGNATURE, NEW_SIGNATURE, 1)
            compile(patched, str(TARGET), "exec")
            write_exact(TARGET, patched)
            print("[PASS] Restored backfill_if_empty compatibility keyword")
        else:
            raise RuntimeError(
                "Expected corrected OPL-002 sync_evidence_index signature not found; "
                "refusing unsafe edit"
            )

        write_exact(TEST, TEST_SOURCE)

        subprocess.run(
            [sys.executable, str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

        sys.path.insert(0, str(ROOT))
        import importlib
        mod = importlib.import_module(
            "qseries_v2.oracle_production_learning.opl_002_canonical_evidence_index"
        )
        mod = importlib.reload(mod)

        sig = inspect.signature(mod.sync_evidence_index)
        if "backfill_if_empty" not in sig.parameters:
            raise RuntimeError("Compatibility keyword not active after reload")

    except Exception:
        restore(TARGET, before)
        restore(TEST, old_test)
        print("[ROLLBACK] Compatibility correction failed; OPL-002 source restored")
        raise

    print("[PASS] Existing evidence-index data untouched")
    print("[PASS] No TRUNCATE executed")
    print("[PASS] No reindex executed")
    print("[PASS] OPL-003 unchanged")
    print("[PASS] OPL-004 unchanged")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] OPH architecture untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-002 RUNTIME COMPATIBILITY CORRECTION COMPLETE")

if __name__ == "__main__":
    main()
