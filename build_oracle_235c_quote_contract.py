"""ORACLE-235C: non-trading live quote contract inspection."""
import argparse
import json
import os
import time
from pathlib import Path

REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE235C_QUOTE_CONTRACT.json"
)
DIRECTIONS = {"METEORA_TO_PUMP", "PUMP_TO_METEORA"}
FIELDS = (
    "complete", "remaining_in", "remaining_raw",
    "raw_out", "amount_out", "requested_raw",
    "consumed_in", "bins_crossed", "missing_bin_id",
    "strict", "swap_for_y"
)


def inspect_mq(mq):
    if not isinstance(mq, dict):
        return {
            "type": type(mq).__name__,
            "fields": [],
            "complete_fill_proven": False
        }

    data = {
        "type": "dict",
        "fields": sorted(str(k) for k in mq.keys()),
        "complete_fill_proven": False
    }

    for key in FIELDS:
        if key in mq:
            value = mq[key]
            if type(value) in (int, float, bool, str):
                data[key] = value

    complete = mq.get("complete")
    remaining = mq.get(
        "remaining_in", mq.get("remaining_raw")
    )

    data["complete_fill_proven"] = (
        complete is True
        and type(remaining) is int
        and remaining == 0
    )
    return data


def summarize(quotes):
    if not isinstance(quotes, (list, tuple)):
        return {
            "status": "HOLD_INVALID_QUOTE_CONTAINER"
        }

    rows = []

    for q in quotes:
        if not isinstance(q, dict):
            return {"status": "HOLD_INVALID_QUOTE"}

        rows.append({
            "direction": q.get("direction"),
            "start": q.get("start"),
            "local_end": q.get("local_end"),
            "local_net": q.get("local_net"),
            "mq": inspect_mq(q.get("mq"))
        })

    directions = {r["direction"] for r in rows}

    both = len(rows) == 2 and directions == DIRECTIONS
    complete = both and all(
        r["mq"]["complete_fill_proven"] for r in rows
    )

    return {
        "status": (
            "PASS_FULL_FILL_CONTRACT"
            if complete else "HOLD_QUOTE_CONTRACT"
        ),
        "both_directions": both,
        "rows": rows
    }


def test():
    quote = [{
        "direction": d,
        "start": 10000000,
        "local_end": 10000010,
        "local_net": 10,
        "mq": {
            "complete": True,
            "remaining_in": 0,
            "raw_out": 10000010
        }
    } for d in sorted(DIRECTIONS)]

    assert summarize(quote)["status"] == (
        "PASS_FULL_FILL_CONTRACT"
    )

    quote[0]["mq"]["remaining_in"] = 100
    assert summarize(quote)["status"] == (
        "HOLD_QUOTE_CONTRACT"
    )

    quote[0]["mq"].pop("remaining_in")
    assert not inspect_mq(
        quote[0]["mq"]
    )["complete_fill_proven"]

    print(
        "[ORACLE235C_TEST_PASS] "
        "complete_fill=TRUE "
        "partial_rejection=TRUE "
        "unknown_schema_holds=TRUE"
    )


def run():
    if os.environ.get("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED_ENVIRONMENT")
    if os.environ.get("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")
    if not os.environ.get("SOLANA_RPC_URL", "").startswith(
        "https://"
    ):
        raise RuntimeError("HOLD_RPC_NOT_CONFIGURED")

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    import build_oracle_235b_live_quote_worker as prior

    original = r.q18.exact_snapshot_opportunities

    report = {
        "build": "ORACLE235C",
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
        "live_price_certified": False,
        "observations": []
    }

    def traced(snap, size):
        entry = {
            "token_prefix": str(
                snap.get("token", "")
            )[:12],
            "size_sol": size
        }

        try:
            quotes = original(snap, size)
            entry.update(summarize(quotes))
            return quotes
        except Exception as exc:
            entry["status"] = "HOLD_EXCEPTION"
            entry["exception_type"] = type(exc).__name__
            entry["exception_code"] = (
                str(exc)
                if str(exc) in (
                    "DLMM_PARTIAL",
                    "DLMM_DIRECTION",
                    "REVERSE_TOKEN_NET_ZERO",
                    "FORWARD_TOKEN_NET_ZERO"
                ) else "UNCLASSIFIED"
            )
            raise
        finally:
            report["observations"].append(entry)

    try:
        r.q18.exact_snapshot_opportunities = traced
        prior.launch(40, 12)
    finally:
        r.q18.exact_snapshot_opportunities = original
        REPORT.parent.mkdir(
            parents=True, exist_ok=True
        )
        REPORT.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )

    counts = {}

    for item in report["observations"]:
        key = item["status"]
        counts[key] = counts.get(key, 0) + 1

    print("[ORACLE235C_RESULT]", json.dumps({
        "quotes_inspected": len(report["observations"]),
        "outcomes": counts,
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for item in report["observations"]:
        print("[ORACLE235C_QUOTE]", json.dumps(
            item, sort_keys=True
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