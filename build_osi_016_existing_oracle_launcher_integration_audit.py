from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_016_existing_oracle_launcher_integration_audit.py"
TEST = ROOT / "test_osi_016_existing_oracle_launcher_integration_audit.py"

MOD_TEXT = r"""from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

EXECUTION_AUTHORITY = False
READ_ONLY = True

ANCHOR_PATTERNS = (
    r'if\s+__name__\s*==\s*["\']__main__["\']',
    r'subprocess\.Popen',
    r'threading\.Thread',
    r'multiprocessing',
    r'run_slop_buy_pressure_live',
    r'oracle_live',
)

def _sha256_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(root: Path) -> dict:
    launcher = root / "run_oracle_live.py"
    if not launcher.is_file():
        raise RuntimeError("Missing existing production launcher: run_oracle_live.py")

    raw = launcher.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    anchors = []

    for number, line in enumerate(lines, 1):
        matched = [pattern for pattern in ANCHOR_PATTERNS if re.search(pattern, line, re.I)]
        if matched:
            anchors.append({
                "line": number,
                "text": line[:500],
                "matched": matched,
            })

    existing_osi_refs = [
        {"line": n, "text": line[:500]}
        for n, line in enumerate(lines, 1)
        if "solana_intelligence" in line.lower() or "osi_" in line.lower()
    ]

    report = {
        "revision": "OSI_016",
        "purpose": "Capture the exact existing Oracle production launcher before OSI 24/7 registration.",
        "launcher": "run_oracle_live.py",
        "launcher_sha256_raw_windows_bytes": _sha256_raw(launcher),
        "launcher_size_bytes": len(raw),
        "anchors": anchors,
        "existing_osi_refs": existing_osi_refs,
        "osi_already_registered": bool(existing_osi_refs),
        "safe_to_patch_claimed": False,
        "execution_authority": False,
        "read_only": True,
        "certification": "SOURCE_CAPTURE_ONLY",
    }
    return report

def write_report(root: Path) -> Path:
    data = audit(root)
    path = root / "OSI_016_EXISTING_ORACLE_LAUNCHER_INTEGRATION_AUDIT.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
"""

TEST_TEXT = r"""import json
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
"""

def main():
    print("=" * 116)
    print(" OSI-016 EXISTING ORACLE LAUNCHER INTEGRATION AUDIT")
    print("=" * 116)
    launcher = ROOT / "run_oracle_live.py"
    if not launcher.is_file():
        raise RuntimeError("Missing existing production launcher: run_oracle_live.py")
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] existing launcher found:", launcher.name)
    print("[PASS] installed:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Exact raw-byte capture before production registration; launcher unchanged")

if __name__ == "__main__":
    main()
