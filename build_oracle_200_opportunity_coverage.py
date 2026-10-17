"""ORACLE200: Audit discovered-pair coverage without changing executor source."""
import argparse
import ast
import hashlib
import inspect
import json
import re
from pathlib import Path

ROOT = Path("qseries_v2/oracle_execution/solana_atomic_executor")
STATE = Path("runtime_state/oracle/oracle_live_execution")
FREEZE = STATE / "ORACLE199_EXECUTION_FREEZE.json"
RANKING = STATE / "ORACLE199_OPPORTUNITY_RANKING.json"
REPORT = STATE / "ORACLE200_OPPORTUNITY_COVERAGE.json"


def verify_freeze():
    if not FREEZE.is_file():
        raise RuntimeError("ORACLE200_NO_EXECUTION_FREEZE")
    stored = json.loads(FREEZE.read_text(encoding="utf-8"))["sha256"]
    actual = {
        p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ROOT.rglob("*.py"))
        if p.is_file()
    }
    if actual != stored:
        raise RuntimeError("ORACLE200_EXECUTION_FREEZE_CHANGED")
    print("[ORACLE200_FREEZE_PASS] files=%d unchanged=TRUE" % len(actual))


def inspect_bootstrap(fn):
    source = inspect.getsource(fn)
    ast.parse(source)
    findings = []
    for number, line in enumerate(source.splitlines(), 1):
        s = line.strip()
        if re.search(
            r"\bbreak\b|\breturn\b|\blimit\b|\bmax_pairs\b|"
            r"\btop\b|\bselected\b|\bready\b|\bwarm\b|"
            r"\bfilter\b|\bappend\b|\bsort\b|\[\s*:",
            s, re.I
        ):
            # Do not emit source code or embedded configuration values.
            findings.append({
                "relative_line": number,
                "category": (
                    "SELECTION_OR_LIMIT"
                    if re.search(r"limit|max_pairs|sort|top|\[\s*:", s, re.I)
                    else "FLOW_OR_ADMISSION"
                )
            })
    return {
        "source_lines": len(source.splitlines()),
        "potential_admission_points": findings[:80],
        "source_review_required": True,
    }


def summarize(report):
    rows = report.get("rows") or []
    errors = report.get("errors") or []
    pairs = int(report.get("scanned_pair_count") or 0)
    tokens = {r.get("token") for r in rows if r.get("token")}
    directions = {}
    reasons = {}
    for row in rows:
        direction = row.get("direction", "UNKNOWN")
        directions[direction] = directions.get(direction, 0) + 1
        for reason in row.get("hold_reasons") or []:
            reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "bootstrap_pairs": pairs,
        "quoted_tokens": len(tokens),
        "quoted_routes": len(rows),
        "direction_counts": directions,
        "hold_reason_counts": reasons,
        "quote_errors": errors,
        "provisional_positive": sum(
            bool(r.get("research_eligible")) for r in rows
        ),
        "source_quote_freshness_certified": False,
        "profit_certified": False,
        "execution_authorized": False,
        "broadcast": False,
    }


def test():
    sample = {
        "scanned_pair_count": 2,
        "rows": [
            {"token": "A", "direction": "METEORA_TO_PUMP",
             "research_eligible": False,
             "hold_reasons": ["NONPOSITIVE_GROSS_NET"]},
            {"token": "A", "direction": "PUMP_TO_METEORA",
             "research_eligible": False,
             "hold_reasons": ["NO_CONSERVATIVE_MIN_END"]},
        ],
        "errors": [],
    }
    result = summarize(sample)
    assert result["bootstrap_pairs"] == 2
    assert result["quoted_tokens"] == 1
    assert result["provisional_positive"] == 0
    assert result["hold_reason_counts"]["NONPOSITIVE_GROSS_NET"] == 1
    print("[TEST PASS] ORACLE200 coverage and hold accounting")


def run():
    verify_freeze()
    if not RANKING.is_file():
        raise RuntimeError("ORACLE200_RANKING_REPORT_MISSING")

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle186_direct_route_truth as diagnostic
    )

    previous = json.loads(RANKING.read_text(encoding="utf-8"))
    summary = summarize(previous)
    summary["bootstrap_source_audit"] = inspect_bootstrap(
        diagnostic.bootstrap
    )
    summary["scope"] = "READ_ONLY_EXISTING_RANKING_AND_SOURCE"
    summary["build"] = "ORACLE200"

    STATE.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(
        "[ORACLE200_COVERAGE] bootstrap_pairs=%d quoted_tokens=%d "
        "quotes=%d provisional_positive=%d broadcast=FALSE"
        % (
            summary["bootstrap_pairs"],
            summary["quoted_tokens"],
            summary["quoted_routes"],
            summary["provisional_positive"],
        )
    )
    print("[ORACLE200_DIRECTION_COUNTS]", summary["direction_counts"])
    print("[ORACLE200_HOLD_REASONS]", summary["hold_reason_counts"])
    print(
        "[ORACLE200_BOOTSTRAP_AUDIT]",
        summary["bootstrap_source_audit"],
    )
    print("[REPORT]", REPORT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    test() if args.test else run()