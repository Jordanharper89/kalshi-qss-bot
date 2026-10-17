"""ORACLE-235D: underlying DLMM quote verification; read-only."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE235D_DLMM_FILL_TRUTH.json"
)
DIRECTIONS = {"METEORA_TO_PUMP", "PUMP_TO_METEORA"}


def inspect_quote(q):
    def field(name):
        return q.get(name) if isinstance(q, dict) else getattr(q, name, None)

    complete = field("complete")
    remaining = field("remaining_in")
    if remaining is None:
        remaining = field("remaining_raw")

    return {
        "complete": complete,
        "remaining_in": remaining if type(remaining) is int else None,
        "bins_crossed": field("bins_crossed"),
        "missing_bin_id": field("missing_bin_id"),
        "full_fill": (
            complete is True
            and type(remaining) is int
            and remaining == 0
        )
    }


def classify(quotes, calls):
    if not isinstance(quotes, (list, tuple)):
        return "HOLD_INVALID_QUOTES"

    if len(quotes) != 2 or {
        q.get("direction") for q in quotes if isinstance(q, dict)
    } != DIRECTIONS:
        return "HOLD_MISSING_DIRECTION"

    if len(calls) < 2:
        return "HOLD_UNDERLYING_QUOTES_NOT_CAPTURED"

    if any(not q["full_fill"] for q in calls):
        return "HOLD_PARTIAL_OR_UNPROVEN_FILL"

    if any(
        type(q.get("local_net")) is not int
        or type(q.get("local_end")) is not int
        or q["local_net"] != q["local_end"] - 10_000_000
        for q in quotes
    ):
        return "HOLD_AMOUNT_MISMATCH"

    return "PASS_UNDERLYING_FULL_FILL"


def test():
    class Quote:
        complete = True
        remaining_in = 0
        bins_crossed = 2

    assert inspect_quote(Quote())["full_fill"]
    assert not inspect_quote({"raw_out": 42})["full_fill"]

    q = [
        {"direction": d, "local_end": 10_000_001, "local_net": 1}
        for d in sorted(DIRECTIONS)
    ]

    assert classify(q, [inspect_quote(Quote())] * 2) == (
        "PASS_UNDERLYING_FULL_FILL"
    )
    assert classify(q, [{"full_fill": False}] * 2) == (
        "HOLD_PARTIAL_OR_UNPROVEN_FILL"
    )
    print("[ORACLE235D_TEST_PASS] sdk_fill_proof=TRUE")


def run():
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED_ENVIRONMENT")
    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")
    if not os.getenv("SOLANA_RPC_URL", "").startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    import meteora_dlmm
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    import build_oracle_235b_live_quote_worker as prior

    original_dlmm = meteora_dlmm.quote
    original_exact = r.q18.exact_snapshot_opportunities

    report = {
        "build": "ORACLE235D",
        "mode": "RESEARCH_ONLY",
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
        "ws_reconciled": False,
        "mriya_certified": False,
        "routes": []
    }
    active = {"calls": []}

    def traced_dlmm(*args, **kwargs):
        try:
            result = original_dlmm(*args, **kwargs)
            active["calls"].append(inspect_quote(result))
            return result
        except Exception as exc:
            active["calls"].append({
                "full_fill": False,
                "exception_type": type(exc).__name__,
                "code": str(exc) if str(exc) in (
                    "DLMM_PARTIAL", "DLMM_DIRECTION"
                ) else "UNCLASSIFIED"
            })
            raise

    def traced_exact(snap, size):
        active["calls"] = []
        row = {
            "token_prefix": str(snap.get("token", ""))[:12],
            "size_sol": size
        }
        try:
            quotes = original_exact(snap, size)
            row["gross_quotes"] = [
                {
                    "direction": q.get("direction"),
                    "local_net": q.get("local_net"),
                    "local_end": q.get("local_end")
                }
                for q in quotes
            ]
            row["status"] = classify(quotes, active["calls"])
            return quotes
        except Exception as exc:
            row["status"] = "HOLD_QUOTE_EXCEPTION"
            row["exception_type"] = type(exc).__name__
            row["exception_code"] = str(exc) if str(exc) in (
                "DLMM_PARTIAL", "DLMM_DIRECTION",
                "REVERSE_TOKEN_NET_ZERO", "FORWARD_TOKEN_NET_ZERO"
            ) else "UNCLASSIFIED"
            raise
        finally:
            row["dlmm_calls"] = list(active["calls"])
            report["routes"].append(row)

    try:
        meteora_dlmm.quote = traced_dlmm
        r.q18.exact_snapshot_opportunities = traced_exact
        prior.launch(40, 12)
    finally:
        meteora_dlmm.quote = original_dlmm
        r.q18.exact_snapshot_opportunities = original_exact
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )

    counts = Counter(x["status"] for x in report["routes"])
    print("[ORACLE235D_RESULT]", json.dumps({
        "routes_tested": len(report["routes"]),
        "outcomes": dict(counts),
        "ws_reconciled": False,
        "mriya_certified": False,
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for row in report["routes"]:
        print("[ORACLE235D_ROUTE]", json.dumps(
            row, sort_keys=True
        ))

    print("[REPORT]", REPORT)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    a = p.parse_args()

    if a.test:
        test()
    if a.run:
        run()