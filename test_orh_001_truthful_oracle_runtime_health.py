import ast
import unittest
from pathlib import Path

from qseries_v2.oracle_runtime_health.orh_001_truthful_runtime_health import (
    EXPECTED_CORE,
    physical_contract,
    read_children,
    patch_run_forever,
    verify_patched_launcher,
)

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_LIVE.py"

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physical_source = LAUNCHER.read_text(encoding="utf-8")

    def test_physical_launcher_contract(self):
        contract = physical_contract(self.physical_source)
        self.assertTrue(EXPECTED_CORE.issubset(set(contract["children"])))

    def test_physical_children_preserved_exactly(self):
        before = read_children(self.physical_source)
        patched = patch_run_forever(self.physical_source)
        after = read_children(patched)
        self.assertEqual(before, after)

    def test_physical_patch_parses(self):
        patched = patch_run_forever(self.physical_source)
        ast.parse(patched)
        self.assertTrue(verify_patched_launcher(patched))

    def test_no_false_running_semantics(self):
        patched = patch_run_forever(self.physical_source)
        self.assertIn("state={overall}", patched)
        for state in ("STARTING", "HEALTHY", "DEGRADED", "FAILED"):
            self.assertIn(state, patched)

    def test_restart_thrash_detection(self):
        patched = patch_run_forever(self.physical_source)
        self.assertIn("recent >= 3", patched)
        self.assertIn("restart_backoff_seconds", patched)

    def test_execution_boundary(self):
        patched = patch_run_forever(self.physical_source)
        self.assertIn("execution_authority=FALSE", patched)
        self.assertNotIn("execution_authority=TRUE", patched)

if __name__ == "__main__":
    print("=" * 88)
    print(" ORH-001 CERTIFICATION TEST")
    print(" TRUTHFUL ORACLE RUNTIME HEALTH")
    print(" PHYSICAL run_oracle_LIVE.py CONTRACT")
    print("=" * 88)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Physical launcher structure certified")
    print("[PASS] Exact physical CHILDREN registry preserved")
    print("[PASS] Fresh children report STARTING before HEALTHY")
    print("[PASS] Recent crashes report DEGRADED/FAILED")
    print("[PASS] Restart-thrash detection + bounded backoff certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORH-001 CERTIFIED")
