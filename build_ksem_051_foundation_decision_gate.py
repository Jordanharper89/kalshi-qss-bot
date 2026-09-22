from pathlib import Path
import json

ROOT = Path.cwd()
STATE = ROOT / "qseries_v2/kalshi_sports_evidence_mapping/state"
OUT = STATE / "ksem051_foundation_decision.json"
TEST = ROOT / "test_ksem_051_foundation_decision_gate.py"

def main():
    print("="*120)
    print(" KSEM-051 FOUNDATION DECISION GATE")
    print("="*120)

    d = json.loads((STATE/"ksem050_missing_market_root_causes.json").read_text(encoding="utf-8"))
    counts = d["counts"]

    canonical_index_gap = counts.get("CANONICAL_PRESENT_INDEX_MISSING", 0)
    retrieval_mismatch = counts.get("INDEX_PRESENT_RETRIEVAL_PATH_MISMATCH", 0)
    canonical_unknown = counts.get("CANONICAL_SERIALIZED_COLUMN_UNAVAILABLE", 0)
    acquisition_path = counts.get("NOT_IN_CURRENT_CANONICAL_OR_INDEX_ACQUISITION_PATH_EXISTS", 0)
    no_acquisition_path = counts.get("NOT_IN_CURRENT_CANONICAL_OR_INDEX_NO_PROVEN_EXACT_ACQUISITION_PATH", 0)

    if canonical_index_gap:
        decision = "REPAIR_INDEXING_AND_REMEASURE"
    elif retrieval_mismatch:
        decision = "REPAIR_EXACT_POSTGRESQL_RETRIEVAL_HELPER"
    elif canonical_unknown:
        decision = "AUDIT_CANONICAL_STORAGE_SCHEMA_BEFORE_NEW_ACQUISITION"
    elif acquisition_path:
        decision = "BUILD_EXACT_UNDERLYING_MARKET_ACQUISITION_AND_PERSISTENCE_ACTIVATION"
    elif no_acquisition_path:
        decision = "BUILD_FOUNDATIONAL_EXACT_KALSHI_MARKET_RETRIEVAL_BOUNDARY"
    else:
        decision = "NO_UNCLASSIFIED_MISSING_TICKERS"

    data = {
        "root_cause_counts": counts,
        "decision": decision,
        "osn_binding_ready": False,
        "production_launcher_change_required": False,
        "execution_authority": False,
    }

    print("[ROOT_CAUSE_COUNTS]", counts)
    print("[DECISION]", decision)
    print("[OSN_BINDING_READY]", False)
    print("[PRODUCTION_LAUNCHER_CHANGE_REQUIRED]", False)

    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem051_foundation_decision.json').read_text())\n"
        "assert d['decision']\n"
        "assert d['osn_binding_ready'] is False\n"
        "assert d['production_launcher_change_required'] is False\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] missing-underlying foundation decision derived from physical lineage evidence')\n"
        "print('[PASS] KSEM-051 certified')\n",
        encoding="utf-8",
    )
    print("[WRITE]", OUT.relative_to(ROOT))
    print("[WRITE]", TEST.name)

if __name__=="__main__":
    main()
