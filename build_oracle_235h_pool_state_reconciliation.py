"""ORACLE-235H: compare canonical hydration to live RPC pool bytes."""
import argparse
import base64
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path("runtime_state/oracle/oracle_live_execution")
REPORT = ROOT / "ORACLE235H_POOL_RECONCILIATION.json"
DLMM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"


def normalized_arrays(state):
    arrays = getattr(state, "loaded_arrays", None)
    if not isinstance(arrays, (set, list, tuple)):
        return {"count": 0, "type": type(arrays).__name__}

    values = list(arrays)
    return {
        "count": len(values),
        "value_types": sorted({type(v).__name__ for v in values}),
        "sample": [str(v)[:80] for v in sorted(
            values, key=lambda v: str(v)
        )[:12]]
    }


def compare_states(existing, decoded):
    fields = ("active_id", "bin_step",
              "token_x_mint", "token_y_mint")
    result = {}

    for field in fields:
        a = getattr(existing, field, None)
        b = getattr(decoded, field, None)
        result[field] = a is not None and a == b

    result["all_pool_fields_match"] = all(result.values())
    return result


def fetch_accounts(addresses, url):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 2358,
        "method": "getMultipleAccounts",
        "params": [
            addresses,
            {"encoding": "base64", "commitment": "confirmed"}
        ]
    }).encode()

    request = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        body = json.load(response)

    if body.get("error"):
        raise RuntimeError("HOLD_RPC_ERROR")

    result = body.get("result") or {}
    slot = (result.get("context") or {}).get("slot")
    values = result.get("value")

    if type(slot) is not int or slot <= 0:
        raise RuntimeError("HOLD_CONTEXT_MISSING")

    if not isinstance(values, list) or len(values) != len(addresses):
        raise RuntimeError("HOLD_ACCOUNT_COUNT_MISMATCH")

    decoded = {}

    for address, entry in zip(addresses, values):
        if entry is None:
            decoded[address] = None
            continue

        if entry.get("owner") != DLMM:
            decoded[address] = None
            continue

        content = entry.get("data")

        if not isinstance(content, list) or len(content) != 2:
            raise RuntimeError("HOLD_ENCODING_UNKNOWN")
        if content[1] != "base64":
            raise RuntimeError("HOLD_ENCODING_UNKNOWN")

        raw = base64.b64decode(content[0], validate=True)
        decoded[address] = {
            "raw": raw,
            "sha256": hashlib.sha256(raw).hexdigest()
        }

    return slot, decoded


def test():
    class State:
        active_id = 100
        bin_step = 25
        token_x_mint = b"x" * 32
        token_y_mint = b"y" * 32
        loaded_arrays = {-1, 0, 1}

    x = State()
    y = State()

    assert compare_states(x, y)["all_pool_fields_match"]
    assert normalized_arrays(x)["count"] == 3

    y.active_id = 101
    assert not compare_states(x, y)["all_pool_fields_match"]

    print(
        "[ORACLE235H_TEST_PASS] "
        "pool_fields=TRUE mismatch_rejected=TRUE "
        "array_inventory=TRUE"
    )


def run():
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED_ENVIRONMENT")

    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")

    url = os.getenv("SOLANA_RPC_URL", "")

    if not url.startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    from meteora_dlmm import PoolState
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    original_rpc = r.q87.c.rpc

    output = {
        "build": "ORACLE235H",
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
        "bin_array_lineage_verified": False,
        "ws_to_quote_reconciled": False,
        "mriya_certified": False,
        "routes": [],
        "errors": []
    }

    try:
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)

        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)

        pairs = list(state.get("pairs") or [])[:30]
        addresses = sorted({
            str(pair.meteora_pool) for pair in pairs
        })

        slot, account_map = fetch_accounts(addresses, url)
        output["rpc_context_slot"] = slot
        output["observed_at_epoch"] = time.time()

        for pair in pairs:
            address = str(pair.meteora_pool)
            row = {
                "token_prefix": str(pair.token)[:12],
                "pool": address,
                "status": "HOLD",
            }

            try:
                observed = account_map.get(address)

                if not observed:
                    raise RuntimeError("POOL_ACCOUNT_MISSING")

                hydrated = r.immutable_snapshot(pair)["dlmm_state"]

                row["loaded_arrays"] = normalized_arrays(hydrated)
                row["hydrated_bins"] = len(
                    getattr(hydrated, "bins", {})
                )
                row["hydrated_exhaustive"] = getattr(
                    hydrated, "exhaustive", None
                )
                row["rpc_pool_sha256"] = observed["sha256"]

                reconstructed = PoolState.from_accounts(
                    observed["raw"],
                    [],
                    decimals_x=int(pair.decimals_x),
                    decimals_y=int(pair.decimals_y),
                    exhaustive=False
                )

                checks = compare_states(
                    hydrated, reconstructed
                )
                row["pool_field_checks"] = checks

                row["status"] = (
                    "PASS_POOL_FIELDS_ONLY"
                    if checks["all_pool_fields_match"]
                    else "HOLD_HYDRATED_POOL_FIELD_DRIFT"
                )

            except Exception as exc:
                row["status"] = (
                    "HOLD_" + type(exc).__name__
                )

            output["routes"].append(row)

    except Exception as exc:
        output["errors"].append(
            "PREPARATION_" + type(exc).__name__
        )

    finally:
        r.q87.c.rpc = original_rpc

        output["pool_field_pass"] = sum(
            row["status"] == "PASS_POOL_FIELDS_ONLY"
            for row in output["routes"]
        )
        output["status"] = (
            "HOLD_BIN_ARRAY_LINEAGE_NOT_VERIFIED"
        )

        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8"
        )

    print("[ORACLE235H_RESULT]", json.dumps({
        "routes": len(output["routes"]),
        "pool_field_pass": output["pool_field_pass"],
        "context_slot": output.get("rpc_context_slot"),
        "errors": output["errors"],
        "bin_array_lineage_verified": False,
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for row in output["routes"]:
        print("[ORACLE235H_ROUTE]", json.dumps({
            "token": row["token_prefix"],
            "status": row["status"],
            "loaded_arrays": row.get("loaded_arrays"),
            "hydrated_bins": row.get("hydrated_bins"),
            "hydrated_exhaustive": row.get("hydrated_exhaustive"),
            "pool_field_checks": row.get("pool_field_checks")
        }, sort_keys=True))

    print("[REPORT]", REPORT)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    args = p.parse_args()

    if args.test:
        test()
    if args.run:
        run()