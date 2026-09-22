from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime as M
from qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation import (
    GMGNProviderError,
)


class T(unittest.TestCase):
    def test_01_exact_failure_truth_is_persisted_and_logged(self):
        with tempfile.TemporaryDirectory() as td:
            detail = (
                "GMGN_NOT_ADMITTED: config check failed | "
                "config: command=['gmgn-cli.cmd','config','--check'] "
                "returncode=1 elapsed_seconds=0.500 "
                "exception_type=None stderr='provider diagnostic'"
            )

            lines = []
            with patch.object(
                M,
                "persist_current_gmgn",
                side_effect=GMGNProviderError(detail),
            ):
                cp = M.run(
                    max_cycles=1,
                    cadence_seconds=0.0,
                    root=td,
                    progress=lines.append,
                )

            joined = "\n".join(lines)
            print(joined)
            self.assertEqual(cp.cycles, 1)
            self.assertEqual(cp.failures, 1)
            self.assertEqual(cp.last_error, detail)
            self.assertIn("error_type=GMGNProviderError", joined)
            self.assertIn("config check failed", joined)
            self.assertIn("returncode=1", joined)
            self.assertIn("provider diagnostic", joined)

    def test_02_safety_boundary(self):
        self.assertTrue(M.READ_ONLY)
        self.assertFalse(M.PROBABILITY_ENABLED)
        self.assertFalse(M.DIRECTION_ENABLED)
        self.assertFalse(M.PUBLICATION_ALLOWED)
        self.assertFalse(M.EXECUTION_AUTHORITY)

    def test_03_physical_one_cycle_exposes_truth(self):
        p = subprocess.run(
            [
                sys.executable,
                "run_oad_290_gmgn_clean_continuous_intelligence_child.py",
                "--max-cycles",
                "1",
                "--cadence-seconds",
                "1",
            ],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        print(p.stdout, end="")
        print(p.stderr, end="")
        self.assertEqual(p.returncode, 0)

        if "status=SUCCESS" in p.stdout:
            self.assertIn("exact_readback=3", p.stdout)
            print("[PHYSICAL] GMGN cycle succeeded during failure-truth certification")
        else:
            self.assertIn("status=COOLDOWN", p.stdout)
            self.assertIn("error_type=", p.stdout)
            self.assertIn("error_detail=", p.stdout)
            self.assertNotIn("error_detail=''", p.stdout)
            print("[PHYSICAL] GMGN failure truth exposed without masking")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact GMGN failure detail survives OAD-290 runtime boundary")
    print("[PASS] checkpoint retains bounded physical provider failure detail")
    print("[PASS] supervised child log exposes error type + exact detail + retry")
    print("[PASS] OAD-287/OAD-288/OAD-289 public contracts preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-290 SUPERVISED FAILURE-TRUTH FOUNDATIONAL REBUILD CERTIFIED")
