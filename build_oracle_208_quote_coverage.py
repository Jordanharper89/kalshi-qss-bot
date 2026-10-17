"""ORACLE208: Inspect quote failures from expanded opportunity research."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

STATE = Path("runtime_state/oracle/oracle_live_execution")
SOURCE = STATE / "ORACLE207_EXPANDED_RESEARCH.json"
OUT = STATE / "ORACLE208_QUOTE_COVERAGE.json"

SIZES = (0.010, 0.015, 0.025, 0.050)
DIRECTIONS = ("METEORA_TO_PUMP", "PUMP_TO_METEORA")


def analyze(report):
    pairs = report.get("pairs") or []
    rows = report.get("rows") or []
    errors = report.get("errors") or []

    tokens = list(dict.fromkeys(
        str(p["token"]) for p in pairs if p.get("token")
    ))

    by_token = defaultdict(list)
    for row in rows:
        by_token[str(row.get("token"))].append(row)

    failed = defaultdict(list)
    error_types = Counter()

    for error in errors:
        token = str(error.get("token", "UNKNOWN"))
        failed[token].append(error)
        error_types[
            str(error.get("stage", "UNKNOWN")) + ":" +
            str(error.get("error_type", "UNKNOWN"))
        ] += 1

    coverage = []
    missing = []
    reason_counts = Counter()

    for token in tokens:
        token_rows = by_token.get(token, [])
        quoted_sizes = set()

        for size in SIZES:
            matches = [
                r for r in token_rows
                if abs(float(r.get("size_sol", -1)) - size) < 1e-8
            ]
            directions = {r.get("direction") for r in matches}

            for direction in DIRECTIONS:
                if direction not in directions:
                    missing.append({
                        "token": token,
                        "size_sol": size,
                        "direction": direction,
                    })

            if len(directions.intersection(DIRECTIONS)) == 2:
                quoted_sizes.add(size)

        for row in token_rows:
            for reason in row.get("hold_reasons") or []:
                reason_counts[str(reason)] += 1

        coverage.append({
            "token": token,
            "quotes": len(token_rows),
            "complete_sizes": sorted(quoted_sizes),
            "quote_errors": [
                {
                    "size_sol": e.get("size"),
                    "stage": e.get("stage"),
                    "error_type": e.get("error_type"),
                }
                for e in failed.get(token, [])
            ],
        })

    positive = [
        row for row in rows if row.get("research_eligible") is True
    ]

    return {
        "build": "ORACLE208",
        "scope": "EXISTING_RESEARCH_REPORT_ONLY",
        "prepared_pairs": len(tokens),
        "expected_quotes": len(tokens) * len(SIZES) * len(DIRECTIONS),
        "actual_quotes": len(rows),
        "missing_quote_slots": len(missing),
        "positive_research_candidates": len(positive),
        "error_types": dict(error_types),
        "hold_reasons": dict(reason_counts),
        "pair_coverage": coverage,
        "missing": missing,
        "execution_authorized": False,
        "signing": False,
        "broadcast": False,
    }


def test():
    data = {
        "pairs": [{"token": "A"}, {"token": "B"}],
        "rows": [
            {
                "token": "A",
                "size_sol": 0.010,
                "direction": "METEORA_TO_PUMP",
                "research_eligible": False,
            },
            {
                "token": "A",
                "size_sol": 0.010,
                "direction": "PUMP_TO_METEORA",
                "research_eligible": False,
            },
        ],
        "errors": [
            {
                "token": "B",
                "size": 0.010,
                "stage": "QUOTE",
                "error_type": "RuntimeError",
            }
        ],
    }

    result = analyze(data)
    assert result["expected_quotes"] == 16
    assert result["actual_quotes"] == 2
    assert result["missing_quote_slots"] == 14
    assert result["pair_coverage"][0]["complete_sizes"] == [0.010]
    assert result["positive_research_candidates"] == 0
    print("[TEST PASS] ORACLE208 missing quote and error classification")


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
    )

    freeze.freeze()

    if not SOURCE.is_file():
        raise RuntimeError("ORACLE208_ORACLE207_REPORT_MISSING")

    report = json.loads(SOURCE.read_text(encoding="utf-8"))
    if report.get("build") != "ORACLE207":
        raise RuntimeError("ORACLE208_SOURCE_IDENTITY_INVALID")
    if report.get("broadcast") is not False:
        raise RuntimeError("ORACLE208_SOURCE_BROADCAST_NOT_FALSE")

    result = analyze(report)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(
        "[ORACLE208_COVERAGE] pairs=%d expected=%d actual=%d "
        "missing=%d provisional_positive=%d broadcast=FALSE"
        % (
            result["prepared_pairs"],
            result["expected_quotes"],
            result["actual_quotes"],
            result["missing_quote_slots"],
            result["positive_research_candidates"],
        )
    )

    print("[ORACLE208_ERROR_TYPES]", result["error_types"])
    print("[ORACLE208_HOLD_REASONS]", result["hold_reasons"])

    for pair in result["pair_coverage"]:
        print(
            "[ORACLE208_PAIR] token=%s quotes=%d complete_sizes=%s errors=%s"
            % (
                pair["token"],
                pair["quotes"],
                pair["complete_sizes"],
                pair["quote_errors"],
            )
        )

    print("[REPORT]", OUT)
    freeze.freeze()
    print("[ORACLE208_PASS] executor_unchanged=TRUE broadcast=FALSE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.test:
        test()
    else:
        run()