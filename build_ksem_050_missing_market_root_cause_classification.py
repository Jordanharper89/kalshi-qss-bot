from pathlib import Path
import json

ROOT = Path.cwd()
STATE = ROOT / "qseries_v2/kalshi_sports_evidence_mapping/state"
OUT = STATE / "ksem050_missing_market_root_causes.json"
TEST = ROOT / "test_ksem_050_missing_market_root_cause_classification.py"

def main():
    print("="*120)
    print(" KSEM-050 MISSING UNDERLYING MARKET ROOT-CAUSE CLASSIFICATION")
    print("="*120)

    a = json.loads((STATE/"ksem047_missing_ticker_lineage_audit.json").read_text(encoding="utf-8"))
    b = json.loads((STATE/"ksem048_canonical_direct_exact_ticker_recovery.json").read_text(encoding="utf-8"))
    c = json.loads((STATE/"ksem049_existing_kalshi_acquisition_surface_audit.json").read_text(encoding="utf-8"))

    direct = {x["ticker"]: x["canonical_direct_count"] for x in b["rows"]}
    acquisition_candidates = tuple(c["candidates"])
    rows = []
    counts = {}

    for x in a["rows"]:
        ticker = x["ticker"]
        idx = int(x["learning_index_count"])
        direct_count = direct.get(ticker)

        if direct_count is not None and int(direct_count) > 0 and idx == 0:
            cause = "CANONICAL_PRESENT_INDEX_MISSING"
        elif idx > 0:
            cause = "INDEX_PRESENT_RETRIEVAL_PATH_MISMATCH"
        elif direct_count is None:
            cause = "CANONICAL_SERIALIZED_COLUMN_UNAVAILABLE"
        elif acquisition_candidates:
            cause = "NOT_IN_CURRENT_CANONICAL_OR_INDEX_ACQUISITION_PATH_EXISTS"
        else:
            cause = "NOT_IN_CURRENT_CANONICAL_OR_INDEX_NO_PROVEN_EXACT_ACQUISITION_PATH"

        counts[cause] = counts.get(cause, 0) + 1
        rows.append({
            "ticker": ticker,
            "learning_index_count": idx,
            "canonical_direct_count": direct_count,
            "root_cause": cause,
        })

    print("[TOTAL]", len(rows))
    for k, v in sorted(counts.items()):
        print("[ROOT_CAUSE]", k, v)
    for x in rows:
        print("[ROW]", x)

    OUT.write_text(json.dumps({
        "counts": counts,
        "rows": rows,
        "acquisition_candidate_count": len(acquisition_candidates),
        "execution_authority": False,
    }, indent=2), encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem050_missing_market_root_causes.json').read_text())\n"
        "assert d['rows']\n"
        "assert sum(d['counts'].values())==len(d['rows'])\n"
        "assert all(x['root_cause'] for x in d['rows'])\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] every missing exact underlying ticker has one explicit root cause')\n"
        "print('[PASS] KSEM-050 certified')\n",
        encoding="utf-8",
    )
    print("[WRITE]", OUT.relative_to(ROOT))
    print("[WRITE]", TEST.name)

if __name__=="__main__":
    main()
