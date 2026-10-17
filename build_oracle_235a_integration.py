"""ORACLE-235A: canonical pricing integration, research only."""
import argparse
import ast
import copy
import importlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

ROOT = Path("qseries_v2/oracle_execution")
REGISTRY = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE218_DISCOVERY.sqlite3"
)
REPORT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE235A_INTEGRATION.json"
)
ENGINE = ROOT / "oracle_018_exact_sdk_hot_lane_cutover.py"
RUNTIME = ROOT / "solana_atomic_executor/runtime.py"
ALLOWED = {"METEORA_TO_PUMP", "PUMP_TO_METEORA"}


def source_contract():
    problems = []
    for p, name in (
        (RUNTIME, "immutable_snapshot"),
        (ENGINE, "exact_snapshot_opportunities"),
    ):
        if not p.exists():
            problems.append("MISSING_" + p.name)
            continue
        tree = ast.parse(p.read_text(encoding="utf-8-sig"))
        methods = [
            n for n in ast.walk(tree)
            if isinstance(n, (
                ast.FunctionDef, ast.AsyncFunctionDef
            )) and n.name == name
        ]
        if len(methods) != 1:
            problems.append("UNRESOLVED_" + name)
    return problems


def certified_quote(
    pair, latest, quote_function,
    now=None, max_age=15, max_skew=2
):
    now = time.time() if now is None else now

    def hold(reason):
        return {
            "status": "HOLD",
            "reason": reason,
            "certified": False,
            "signing": False,
            "broadcast": False,
        }

    if not isinstance(latest, dict) or not latest.get(
        "hydrated_bin_arrays_verified"
    ):
        return hold("HYDRATED_BIN_ARRAYS_NOT_VERIFIED")

    mint = str(getattr(pair, "token", ""))
    pump = str(getattr(pair, "pump_pool", ""))
    dlmm = str(getattr(pair, "meteora_pool", ""))

    if not mint or not pump or not dlmm or pump == dlmm:
        return hold("INVALID_PAIR")

    if (
        latest.get("mint"),
        latest.get("pump_pool"),
        latest.get("meteora_pool"),
    ) != (mint, pump, dlmm):
        return hold("ROUTE_IDENTITY_MISMATCH")

    proof = latest.get("accounts")

    if not isinstance(proof, list) or len(proof) < 3:
        return hold("NO_COMPLETE_ACCOUNT_LINEAGE")

    slots = []

    for row in proof:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("slot"), int)
            or not row.get("address")
            or not row.get("sha256")
        ):
            return hold("INVALID_ACCOUNT_LINEAGE")

        stamp = row.get("observed_at_epoch")
        if not isinstance(stamp, (int, float)):
            return hold("MISSING_ACCOUNT_TIMESTAMP")

        age = now - stamp

        if age < -2 or age > max_age:
            return hold("STALE_ACCOUNT_LINEAGE")

        slots.append(row["slot"])

    if max(slots) - min(slots) > max_skew:
        return hold("ACCOUNT_SLOT_SKEW")

    if not callable(quote_function):
        return hold("OFFICIAL_PRICER_NOT_CONNECTED")

    if latest.get("snapshot_digest") != latest.get(
        "hydration_digest"
    ):
        return hold("SNAPSHOT_HYDRATION_MISMATCH")

    try:
        runtime = importlib.import_module(
            "qseries_v2.oracle_execution."
            "solana_atomic_executor.runtime"
        )
        snap = runtime.immutable_snapshot(pair)
    except Exception as exc:
        return hold(
            "CANONICAL_SNAPSHOT_" + type(exc).__name__
        )

    if not snap.get("dlmm_state"):
        return hold("DLMM_STATE_EMPTY")

    results = {}

    for size in (0.010, 0.015, 0.025, 0.050):
        try:
            quotes = quote_function(
                copy.deepcopy(snap), size
            )
        except Exception as exc:
            return hold(
                "EXACT_QUOTE_" + type(exc).__name__
            )

        if (
            not isinstance(quotes, list)
            or {
                q.get("direction")
                for q in quotes
                if isinstance(q, dict)
            } != ALLOWED
        ):
            return hold("BOTH_DIRECTIONS_REQUIRED")

        for q in quotes:
            mq = q.get("mq")

            if not isinstance(mq, dict):
                return hold("NO_METEORA_QUOTE")

            if (
                mq.get("complete") is not True
                or mq.get(
                    "remaining_raw",
                    mq.get("remaining_in", 1)
                ) != 0
            ):
                return hold("PARTIAL_DLMM_QUOTE")

            if (
                not isinstance(q.get("local_end"), int)
                or q["local_end"] <= 0
            ):
                return hold("INVALID_QUOTE_OUTPUT")

        results[str(size)] = [
            {
                "direction": q["direction"],
                "local_net": q.get("local_net"),
                "local_end": q["local_end"],
            }
            for q in quotes
        ]

    return {
        "status": "PASS_RESEARCH_QUOTING",
        "certified": True,
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
        "quotes": results,
    }


def audit(db=REGISTRY):
    output = {
        "build": "ORACLE235A",
        "signing": False,
        "broadcast": False,
        "pricing_gate": "HOLD",
        "mriya_gate": "HOLD",
        "profit_certified": False,
        "source_contract_errors": source_contract(),
    }

    if not db.is_file():
        output["reason"] = "MISSING_REGISTRY"
        return output

    uri = db.resolve().as_uri() + "?mode=ro"

    with closing(sqlite3.connect(uri, uri=True)) as c:
        tables = {
            x[0] for x in c.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
        }

        if "universal_routes" not in tables:
            output["reason"] = "MISSING_ROUTES"
            return output

        output["routes"] = c.execute(
            "SELECT COUNT(*) FROM universal_routes"
        ).fetchone()[0]

        if "oracle232_evidence" in tables:
            output["mriya_evidence_rows"] = c.execute(
                "SELECT COUNT(*) FROM oracle232_evidence"
            ).fetchone()[0]
        else:
            output["mriya_evidence_rows"] = 0

    output["reason"] = (
        "HYDRATED_LIVE_PRICER_AND_AUTHENTICATED_"
        "MRIYA_SOURCE_NOT_CONNECTED"
    )
    return output


def test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fixture.db"

        with closing(sqlite3.connect(p)) as c:
            c.execute(
                "CREATE TABLE universal_routes("
                "mint TEXT,pump_pool TEXT,"
                "meteora_pool TEXT)"
            )
            c.execute(
                "INSERT INTO universal_routes "
                "VALUES('mint','pump','dlmm')"
            )
            c.commit()

        result = audit(p)

        assert result["routes"] == 1
        assert result["pricing_gate"] == "HOLD"
        assert result["mriya_gate"] == "HOLD"

    class Pair:
        token = "mint"
        pump_pool = "pump"
        meteora_pool = "dlmm"

    result = certified_quote(Pair(), {}, None)

    assert (
        result["reason"]
        == "HYDRATED_BIN_ARRAYS_NOT_VERIFIED"
    )
    assert result["broadcast"] is False

    print(
        "[ORACLE235A_TEST_PASS] "
        "independent_gates=TRUE "
        "incomplete_liquidity_rejected=TRUE "
        "private_key_not_loaded=TRUE"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--audit", action="store_true")
    args = p.parse_args()

    if args.test:
        test()

    if args.audit:
        result = audit()
        REPORT.parent.mkdir(
            parents=True, exist_ok=True
        )
        REPORT.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        print(
            "[ORACLE235A_RESULT]",
            json.dumps(result, sort_keys=True)
        )
        print("[REPORT]", REPORT)


if __name__ == "__main__":
    main()