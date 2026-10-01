from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_023_certified_solana_physical_source_lineage_audit.py"
TEST = ROOT / "test_osi_023_certified_solana_physical_source_lineage_audit.py"

TARGETS = [
    "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
    "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
    "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
    "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
    "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
    "qseries_v2/oracle_adapters/independent/oad_360_solana_exact_observation_readback.py",
    "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity.py",
]

MOD_TEXT = r"""from __future__ import annotations
import json
import re
from pathlib import Path

PATH_PATTERNS = (
    r"runtime_state",
    r"runtime[/\\]",
    r"\.jsonl?",
    r"\.sqlite3?",
    r"\.db",
    r"postgres",
    r"psycopg",
    r"Path\(",
    r"open\(",
    r"read_text",
    r"write_text",
    r"read_bytes",
    r"write_bytes",
    r"INSERT INTO",
    r"SELECT ",
    r"CREATE TABLE",
    r"pool",
    r"mint",
    r"token",
    r"swap",
    r"signature",
    r"slot",
    r"block_time",
    r"observed_at",
)

def inspect_source(root: Path, relative: str) -> dict:
    path = root / relative
    if not path.is_file():
        return {"path": relative, "exists": False, "matches": []}
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = []
    for number, line in enumerate(text.splitlines(), 1):
        if any(re.search(pattern, line, re.I) for pattern in PATH_PATTERNS):
            matches.append({"line": number, "text": line[:700]})
    return {
        "path": relative,
        "exists": True,
        "matches": matches[:500],
    }

def runtime_inventory(root: Path) -> list[dict]:
    rows = []
    for base_name in ("runtime_state", "runtime"):
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            low = str(path).lower()
            if not any(term in low for term in ("solana", "mint", "pool", "swap", "token", "wallet")):
                continue
            stat = path.stat()
            rows.append({
                "path": str(path.relative_to(root)),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "suffix": path.suffix.lower(),
            })
    rows.sort(key=lambda x: x["mtime_ns"], reverse=True)
    return rows[:500]

def audit(root: Path, targets: list[str]) -> dict:
    sources = [inspect_source(root, target) for target in targets]
    existing = [x for x in sources if x["exists"]]
    return {
        "revision": "OSI_023",
        "purpose": "Locate the exact certified Solana physical persistence/readback boundary for OSI live opportunity intake.",
        "source_modules": sources,
        "existing_source_count": len(existing),
        "runtime_inventory": runtime_inventory(root),
        "execution_authority": False,
        "read_only": True,
        "certification": "LINEAGE_AUDIT_ONLY",
    }

def write_report(root: Path, targets: list[str]) -> Path:
    data = audit(root, targets)
    path = root / "OSI_023_CERTIFIED_SOLANA_PHYSICAL_SOURCE_LINEAGE_AUDIT.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
"""

TEST_TEXT = r"""import json
import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_023_certified_solana_physical_source_lineage_audit import audit, write_report

ROOT = Path(__file__).resolve().parent
TARGETS = %s

class T(unittest.TestCase):
    def test_physical(self):
        result = audit(ROOT, TARGETS)
        report = write_report(ROOT, TARGETS)
        self.assertTrue(report.is_file())
        self.assertGreater(result["existing_source_count"], 0)
        self.assertFalse(result["execution_authority"])
        print("[REPORT]", report)
        print("[CERTIFIED_MODULES_FOUND]", result["existing_source_count"])
        print("[RUNTIME_INVENTORY_COUNT]", len(result["runtime_inventory"]))
        for src in result["source_modules"]:
            if src["exists"]:
                print("[SOURCE]", src["path"], "matches=", len(src["matches"]))
        if result["runtime_inventory"]:
            print("[TOP_RUNTIME_FILE]", json.dumps(result["runtime_inventory"][0], sort_keys=True))
        print("[PASS] OSI-023 certified Solana physical source lineage audit")
        print("[TRADER] Locates the real Solana tape already produced by certified Oracle pavement")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Read-only lineage audit; no new feed and no source mutation")

if __name__ == "__main__":
    unittest.main()
""" % repr(TARGETS)

def main():
    print("=" * 116)
    print(" OSI-023 CERTIFIED SOLANA PHYSICAL SOURCE LINEAGE AUDIT")
    print("=" * 116)
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] installed:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Find existing certified Solana persistence/readback source; no duplicate subsystem")

if __name__ == "__main__":
    main()
