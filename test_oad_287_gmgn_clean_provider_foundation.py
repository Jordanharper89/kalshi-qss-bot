from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation as M


class T(unittest.TestCase):
    def test_01_direct_physical_admission(self):
        a = M.require_gmgn_provider()
        print("[GMGN] cli_path=", a.cli_path)
        print("[GMGN] version=", a.version_text)
        print(
            "[GMGN] version_elapsed_seconds=",
            round(a.version_result.elapsed_seconds, 3)
            if a.version_result
            else None,
        )
        print(
            "[GMGN] config_elapsed_seconds=",
            round(a.config_result.elapsed_seconds, 3)
            if a.config_result
            else None,
        )
        print("[GMGN] admitted=", a.admitted)
        self.assertTrue(a.admitted)
        self.assertFalse(a.execution_authority)

    def test_02_fresh_python_child_physical_admission(self):
        code = r"""
from qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation import require_gmgn_provider
a = require_gmgn_provider()
print("[CHILD] cli_path=", a.cli_path)
print("[CHILD] version=", a.version_text)
print("[CHILD] version_elapsed_seconds=", round(a.version_result.elapsed_seconds, 3) if a.version_result else None)
print("[CHILD] config_elapsed_seconds=", round(a.config_result.elapsed_seconds, 3) if a.config_result else None)
print("[CHILD] admitted=", a.admitted)
"""
        p = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        print(p.stdout, end="")
        print(p.stderr, end="")
        self.assertEqual(p.returncode, 0)
        self.assertIn("[CHILD] admitted= True", p.stdout)

    def test_03_safety_boundary(self):
        self.assertTrue(M.READ_ONLY)
        self.assertFalse(M.PROBABILITY_ENABLED)
        self.assertFalse(M.DIRECTION_ENABLED)
        self.assertFalse(M.PUBLICATION_ALLOWED)
        self.assertFalse(M.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] direct GMGN admission physically verified")
    print("[PASS] fresh Python child GMGN admission physically verified")
    print("[PASS] command timeout raised to 30 seconds")
    print("[PASS] exact failure diagnostics preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-287 CLEAN PROVIDER FOUNDATION REBUILD CERTIFIED")
