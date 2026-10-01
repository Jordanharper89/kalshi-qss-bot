import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_016_existing_oracle_launcher_integration_audit import audit, write_report

ROOT = Path(__file__).resolve().parent

class TestOSI016(unittest.TestCase):
    def test_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "run_oracle_live.py").write_bytes(
                b'import subprocess\r\n'
                b'def main():\r\n'
                b'    subprocess.Popen(["python","run_slop_buy_pressure_live.py"])\r\n'
                b'if __name__ == "__main__":\r\n'
                b'    main()\r\n'
            )
            result = audit(root)
            self.assertEqual(result["certification"], "SOURCE_CAPTURE_ONLY")
            self.assertTrue(result["anchors"])
            self.assertFalse(result["execution_authority"])
            self.assertFalse(result["safe_to_patch_claimed"])

    def test_physical(self):
        required = [
            ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_011_live_solana_source_boundary_certification.py",
            ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py",
            ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_013_live_prospective_research_worker.py",
            ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_014_live_outcome_maturity_worker.py",
            ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_015_continuous_learning_activation_gate.py",
        ]
        for path in required:
            self.assertTrue(path.is_file(), str(path))
        result = audit(ROOT)
        report = write_report(ROOT)
        self.assertTrue(report.is_file())
        self.assertFalse(result["execution_authority"])
        print("[REPORT]", report)
        print("[LAUNCHER_SHA256_RAW_WINDOWS_BYTES]", result["launcher_sha256_raw_windows_bytes"])
        print("[ANCHOR_COUNT]", len(result["anchors"]))
        print("[OSI_ALREADY_REGISTERED]", result["osi_already_registered"])
        print("[PASS] OSI-016 exact existing Oracle launcher source captured")
        print("[TRADER] Next patch can put OSI into the real 24/7 Oracle process without guessing or creating a second runtime")
        print("[SCOPE] Source capture only; no launcher modification, no 24/7 claim, execution_authority=FALSE")

if __name__ == "__main__":
    unittest.main()
