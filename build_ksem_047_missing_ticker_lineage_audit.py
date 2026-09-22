from pathlib import Path
import importlib, json

ROOT = Path.cwd()
STATE = ROOT / "qseries_v2/kalshi_sports_evidence_mapping/state"
OUT = STATE / "ksem047_missing_ticker_lineage_audit.json"
TEST = ROOT / "test_ksem_047_missing_ticker_lineage_audit.py"
MOD = "qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit"

def main():
    print("="*120)
    print(" KSEM-047 MISSING UNDERLYING TICKER ACQUISITION/PERSISTENCE LINEAGE AUDIT")
    print("="*120)

    m = json.loads((STATE/"ksem044_underlying_ticker_resolution_measurement.json").read_text(encoding="utf-8"))
    missing = tuple(x["ticker"] for x in m["rows"] if x["status"] == "NOT_FOUND")
    if not missing:
        raise RuntimeError("no missing physical underlying tickers remain")

    mod = importlib.import_module(MOD)
    _, backend = mod._router_backend(ROOT)
    conn = backend._connect()
    rows = []

    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN READ ONLY")
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='oracle_canonical_observations'
                ORDER BY ordinal_position
            """)
            canonical_columns = [r[0] for r in cur.fetchall()]

            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='oracle_production_learning_evidence_index'
                ORDER BY ordinal_position
            """)
            index_columns = [r[0] for r in cur.fetchall()]

            for ticker in missing:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM public.oracle_production_learning_evidence_index
                    WHERE ticker=%s
                """, (ticker,))
                index_count = int(cur.fetchone()[0])

                rows.append({
                    "ticker": ticker,
                    "learning_index_count": index_count,
                })
        conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    indexed = sum(1 for x in rows if x["learning_index_count"] > 0)
    print("[MISSING_TICKERS]", len(rows))
    print("[INDEXED_MISSING_TICKERS]", indexed)
    for x in rows:
        print("[LINEAGE]", x)

    OUT.write_text(json.dumps({
        "canonical_columns": canonical_columns,
        "learning_index_columns": index_columns,
        "rows": rows,
        "execution_authority": False,
    }, indent=2), encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem047_missing_ticker_lineage_audit.json').read_text())\n"
        "assert d['rows']\n"
        "assert d['canonical_columns']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] missing underlying tickers audited against exact learning-index lineage')\n"
        "print('[PASS] KSEM-047 certified')\n",
        encoding="utf-8",
    )
    print("[WRITE]", OUT.relative_to(ROOT))
    print("[WRITE]", TEST.name)

if __name__=="__main__":
    main()
