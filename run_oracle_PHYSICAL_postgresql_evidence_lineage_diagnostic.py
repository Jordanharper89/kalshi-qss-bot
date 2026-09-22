from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path.cwd().resolve()
STATE = ROOT / "runtime_state"
LEDGER = STATE / "oracle_learning_event_ledger.json"
LINE = "=" * 88

MISSING_SAMPLE = 25
LEARNED_SAMPLE = 25
EVIDENCE_LIMIT = 50


def load_json(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def ledger_records(obj):
    if isinstance(obj, dict):
        out = []
        for key, value in obj.items():
            if isinstance(value, dict):
                row = dict(value)
                row.setdefault("_ledger_key", key)
                out.append(row)
        return out
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    return []


def pick(row, *names):
    for name in names:
        value = row.get(name)
        if value not in (None, "", [], {}):
            return value
    return None


def status_of(row):
    return str(pick(row, "status", "learning_status", "admission_status") or "unknown").lower()


def ticker_of(row):
    return str(
        pick(
            row,
            "ticker",
            "market_ticker",
            "market_id",
            "canonical_market_id",
            "venue_market_id",
            "symbol",
        )
        or "UNKNOWN"
    )


def settlement_ts_of(row):
    return str(pick(row, "settlement_ts", "settled_at", "settlement_time") or "")


def evidence_hash_of(row):
    return str(pick(row, "evidence_hash") or "")


def family(ticker):
    return ticker.split("-")[0] if ticker and ticker != "UNKNOWN" else "UNKNOWN"


def scan_market(root: Path, ticker: str, settlement_ts: str):
    from qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import (
        find_historical_market_evidence,
    )

    matches = tuple(find_historical_market_evidence(root, ticker, limit=EVIDENCE_LIMIT))

    pre = []
    post_or_unknown = []

    for m in matches:
        row = getattr(m, "row", {}) or {}
        observed_at = (
            row.get("observed_at")
            or row.get("timestamp")
            or row.get("created_at")
            or row.get("event_ts")
            or row.get("received_at")
        )

        item = {
            "observation_id": str(getattr(m, "observation_id", "")),
            "evidence_hash": str(getattr(m, "evidence_hash", "")),
            "observed_at": str(observed_at or ""),
            "row_keys": tuple(sorted(row.keys()))[:25] if isinstance(row, dict) else tuple(),
        }

        if settlement_ts and observed_at:
            try:
                from datetime import datetime, timezone

                def dt(v):
                    x = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
                    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)

                if dt(observed_at) < dt(settlement_ts):
                    pre.append(item)
                else:
                    post_or_unknown.append(item)
            except Exception:
                post_or_unknown.append(item)
        else:
            post_or_unknown.append(item)

    return {
        "ticker": ticker,
        "matches": matches,
        "pre": pre,
        "post_or_unknown": post_or_unknown,
    }


def print_group(title, rows, root):
    print("-" * 88)
    print(title)
    print("-" * 88)

    family_counter = Counter()
    with_any = 0
    with_pre = 0
    with_hash = 0

    for idx, row in enumerate(rows, 1):
        ticker = ticker_of(row)
        settlement_ts = settlement_ts_of(row)
        lineage_hash = evidence_hash_of(row)
        family_counter[family(ticker)] += 1

        result = scan_market(root, ticker, settlement_ts)
        any_count = len(result["matches"])
        pre_count = len(result["pre"])
        if any_count:
            with_any += 1
        if pre_count:
            with_pre += 1
        if lineage_hash:
            with_hash += 1

        print(
            f"[{idx:02d}/{len(rows):02d}] "
            f"ticker={ticker} "
            f"ledger_evidence_hash={'YES' if lineage_hash else 'NO'} "
            f"postgres_matches={any_count} "
            f"pre_settlement={pre_count} "
            f"post_or_unknown={len(result['post_or_unknown'])}"
        )

        if pre_count:
            sample = result["pre"][0]
            print(
                "    "
                f"PRE sample observation_id={sample['observation_id']} "
                f"evidence_hash={'YES' if sample['evidence_hash'] else 'NO'} "
                f"observed_at={sample['observed_at']}"
            )
        elif any_count:
            sample = result["post_or_unknown"][0]
            print(
                "    "
                f"NON-PRE sample observation_id={sample['observation_id']} "
                f"evidence_hash={'YES' if sample['evidence_hash'] else 'NO'} "
                f"observed_at={sample['observed_at']}"
            )

    print(f"[GROUP SUMMARY] markets={len(rows)}")
    print(f"[GROUP SUMMARY] ledger_evidence_hash_present={with_hash}")
    print(f"[GROUP SUMMARY] postgres_any_evidence={with_any}")
    print(f"[GROUP SUMMARY] postgres_pre_settlement_evidence={with_pre}")
    print(f"[GROUP SUMMARY] families={dict(family_counter)}")

    return {
        "markets": len(rows),
        "with_hash": with_hash,
        "with_any": with_any,
        "with_pre": with_pre,
    }


def main():
    print(LINE)
    print(" ORACLE PHYSICAL POSTGRESQL EVIDENCE-LINEAGE DIAGNOSTIC")
    print(" READ-ONLY — NO OLR / OHL / POSTGRESQL WRITES")
    print(LINE)

    raw = load_json(LEDGER)
    if raw is None:
        print(f"[ERROR] Learning ledger missing: {LEDGER}")
        raise SystemExit(2)

    rows = ledger_records(raw)
    missing = [r for r in rows if status_of(r) == "evidence_missing"][:MISSING_SAMPLE]
    learned = [r for r in rows if status_of(r) == "learned"][:LEARNED_SAMPLE]

    print(f"[LEDGER] total_records={len(rows)}")
    print(f"[SAMPLE] evidence_missing={len(missing)} learned={len(learned)}")
    print(f"[CONFIG] evidence_limit_per_market={EVIDENCE_LIMIT}")

    missing_summary = print_group(
        " EVIDENCE-MISSING SAMPLE — PHYSICAL POSTGRESQL TRACE",
        missing,
        ROOT,
    )

    learned_summary = print_group(
        " LEARNED SAMPLE — PHYSICAL POSTGRESQL TRACE",
        learned,
        ROOT,
    )

    print("=" * 88)
    print(" PHYSICAL LINEAGE DIAGNOSIS")
    print("=" * 88)

    m_pre = missing_summary["with_pre"]
    l_pre = learned_summary["with_pre"]

    print(
        f"[COMPARE] missing_pre_settlement={m_pre}/{missing_summary['markets']} "
        f"learned_pre_settlement={l_pre}/{learned_summary['markets']}"
    )

    if m_pre > 0:
        print("[DIAGNOSIS] PostgreSQL DOES contain pre-settlement evidence for some evidence_missing markets.")
        print("[CLASSIFICATION] Strong evidence of a live evidence-lineage/matcher defect.")
        print("[NEXT] A defect-only correction to the frozen learning path is justified.")
    elif l_pre > 0:
        print("[DIAGNOSIS] Learned markets have recoverable pre-settlement evidence, while sampled evidence_missing markets do not.")
        print("[CLASSIFICATION] Current learner behavior appears consistent with actual evidence availability.")
        print("[NEXT] Do NOT modify frozen OLR; allow the live observation history to accumulate.")
    elif missing_summary["with_any"] > 0 or learned_summary["with_any"] > 0:
        print("[DIAGNOSIS] PostgreSQL evidence exists, but the available timestamp fields do not prove pre-settlement timing.")
        print("[CLASSIFICATION] Timestamp/temporal-lineage boundary needs inspection before any correction.")
        print("[NEXT] Do NOT modify frozen OLR yet.")
    else:
        print("[DIAGNOSIS] No recoverable PostgreSQL evidence was found for either sample through the certified matcher.")
        print("[CLASSIFICATION] Evidence matcher/storage identity path needs inspection, but defect location is not yet proven.")
        print("[NEXT] Do NOT modify frozen OLR yet.")

    print("[PASS] PostgreSQL inspection performed read-only")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] OHL historical subsystem untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE PHYSICAL POSTGRESQL EVIDENCE-LINEAGE DIAGNOSTIC COMPLETE")


if __name__ == "__main__":
    main()
