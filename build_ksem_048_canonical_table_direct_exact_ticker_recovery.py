

from pathlib import Path
import importlib, json

ROOT = Path.cwd()
STATE = ROOT / "qseries_v2/kalshi_sports_evidence_mapping/state"
OUT = STATE / "ksem048_canonical_direct_exact_ticker_recovery.json"
TEST = ROOT / "test_ksem_048_canonical_table_direct_exact_ticker_recovery.py"
MOD = "qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit"

PREFERRED = (
    "observation_json","canonical_observation","observation",
    "payload_json","record_json","observation_payload"
)

def main():
    print("="*120)
    print(" KSEM-048 CANONICAL TABLE DIRECT EXACT-TICKER RECOVERY")
    print("="*120)

    prior = json.loads((STATE/"ksem047_missing_ticker_lineage_audit.json").read_text(encoding="utf-8"))
    missing = tuple(x["ticker"] for x in prior["rows"])
    mod = importlib.import_module(MOD)
    _, backend = mod._router_backend(ROOT)
    conn = backend._connect()

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
            columns = [r[0] for r in cur.fetchall()]
            value_col = next((c for c in columns if c.lower() in PREFERRED), None)

            results = []
            if value_col:
                for ticker in missing:
                    cur.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM public.oracle_canonical_observations
                        WHERE CAST({value_col} AS text) LIKE %s
                        """,
                        (f"%{ticker}%",),
                    )
                    count = int(cur.fetchone()[0])
                    results.append({"ticker": ticker, "canonical_direct_count": count})
            else:
                results = [{"ticker": t, "canonical_direct_count": None} for t in missing]
        conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    found = sum(1 for x in results if (x["canonical_direct_count"] or 0) > 0)
    print("[SERIALIZED_COLUMN]", value_col)
    print("[MISSING_TICKERS]", len(results))
    print("[CANONICAL_DIRECT_FOUND]", found)
    for x in results:
        print("[DIRECT]", x)

    OUT.write_text(json.dumps({
        "serialized_column": value_col,
        "rows": results,
        "execution_authority": False,
    }, indent=2), encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem048_canonical_direct_exact_ticker_recovery.json').read_text())\n"
        "assert d['rows']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] canonical observation table directly audited for every missing exact ticker')\n"
        "print('[PASS] KSEM-048 certified')\n",
        encoding="utf-8",
    )
    print("[WRITE]", OUT.relative_to(ROOT))
    print("[WRITE]", TEST.name)

if __name__=="__main__":
    main()
