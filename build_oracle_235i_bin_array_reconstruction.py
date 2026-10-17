"""ORACLE-235I: on-chain DLMM bin-array reconstruction. Read-only."""
import argparse
import base64
import hashlib
import json
import os
import struct
import urllib.request
from pathlib import Path

ROOT = Path("runtime_state/oracle/oracle_live_execution")
REPORT = ROOT / "ORACLE235I_BIN_ARRAY_RECONSTRUCTION.json"
DLMM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
MAX_ACCOUNTS = 100


def pda(pool, index):
    from solders.pubkey import Pubkey

    index = int(index)
    if not -(2**63) <= index < 2**63:
        raise ValueError("INVALID_BIN_ARRAY_INDEX")

    address, _ = Pubkey.find_program_address(
        [
            b"bin_array",
            bytes(Pubkey.from_string(pool)),
            struct.pack("<q", index),
        ],
        Pubkey.from_string(DLMM),
    )
    return str(address)


def rpc_accounts(addresses, url):
    if not addresses or len(addresses) > MAX_ACCOUNTS:
        raise RuntimeError("HOLD_ACCOUNT_BATCH_LIMIT")

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 2359,
        "method": "getMultipleAccounts",
        "params": [
            addresses,
            {
                "encoding": "base64",
                "commitment": "confirmed"
            }
        ]
    }).encode()

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)

    if body.get("error"):
        raise RuntimeError("HOLD_RPC_ERROR")

    result = body.get("result") or {}
    slot = (result.get("context") or {}).get("slot")
    values = result.get("value")

    if type(slot) is not int or slot <= 0:
        raise RuntimeError("HOLD_RPC_CONTEXT")

    if not isinstance(values, list) or len(values) != len(addresses):
        raise RuntimeError("HOLD_RPC_ACCOUNT_COUNT")

    accounts = {}

    for address, item in zip(addresses, values):
        if item is None:
            raise RuntimeError("HOLD_MISSING_BIN_ARRAY_OR_POOL")

        if item.get("owner") != DLMM:
            raise RuntimeError("HOLD_DLMM_OWNER_MISMATCH")

        data = item.get("data")

        if (
            not isinstance(data, list)
            or len(data) != 2
            or data[1] != "base64"
        ):
            raise RuntimeError("HOLD_ACCOUNT_ENCODING")

        raw = base64.b64decode(data[0], validate=True)

        if not raw:
            raise RuntimeError("HOLD_EMPTY_ACCOUNT")

        accounts[address] = {
            "raw": raw,
            "sha256": hashlib.sha256(raw).hexdigest()
        }

    return slot, accounts


def liquidity(state):
    bins = getattr(state, "bins", None)

    if not isinstance(bins, dict):
        raise RuntimeError("HOLD_BIN_STRUCTURE_UNKNOWN")

    output = {}

    for bin_id, value in bins.items():
        x = getattr(value, "amount_x", None)
        y = getattr(value, "amount_y", None)

        if type(x) is not int or type(y) is not int:
            raise RuntimeError("HOLD_BIN_LIQUIDITY_UNKNOWN")

        output[int(bin_id)] = (x, y)

    return output


def compare(existing, rebuilt):
    fields = (
        "active_id",
        "bin_step",
        "token_x_mint",
        "token_y_mint",
    )

    checks = {
        name: (
            getattr(existing, name, None)
            == getattr(rebuilt, name, None)
        )
        for name in fields
    }

    old = liquidity(existing)
    new = liquidity(rebuilt)

    return {
        "pool_fields_match": all(checks.values()),
        "individual_checks": checks,
        "hydrated_bins": len(old),
        "reconstructed_bins": len(new),
        "bin_ids_match": set(old) == set(new),
        "liquidity_matches": old == new,
        "match": all(checks.values()) and old == new,
    }


def test():
    class Bin:
        def __init__(self, x, y):
            self.amount_x = x
            self.amount_y = y

    class State:
        active_id = 10
        bin_step = 25
        token_x_mint = b"x" * 32
        token_y_mint = b"y" * 32

        def __init__(self):
            self.bins = {
                10: Bin(100, 200),
                11: Bin(300, 400),
            }

    a = State()
    b = State()

    assert compare(a, b)["match"]

    b.bins[11].amount_x += 1
    assert not compare(a, b)["liquidity_matches"]

    from solders.pubkey import Pubkey
    pool = str(Pubkey.from_bytes(bytes([7]) * 32))

    assert pda(pool, -3) == pda(pool, -3)
    assert pda(pool, -3) != pda(pool, 3)

    print(
        "[ORACLE235I_TEST_PASS] "
        "pda_derivation=TRUE "
        "liquidity_comparison=TRUE "
        "mismatch_rejection=TRUE"
    )


def run():
    if os.environ.get("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED_ENVIRONMENT")

    if os.environ.get("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")

    url = os.environ.get("SOLANA_RPC_URL", "")

    if not url.startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    from meteora_dlmm import PoolState
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    report = {
        "build": "ORACLE235I",
        "signing": False,
        "broadcast": False,
        "profit_certified": False,
        "pricing_certified": False,
        "mriya_certified": False,
        "pairs": [],
        "errors": [],
    }

    original_rpc = r.q87.c.rpc

    try:
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)

        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)

        pairs = list(state.get("pairs") or [])[:12]

        for pair in pairs:
            pool = str(pair.meteora_pool)
            existing = pair.dlmm_state

            row = {
                "token_prefix": str(pair.token)[:12],
                "pool": pool,
                "status": "HOLD",
            }

            try:
                indices = sorted(
                    int(x) for x in existing.loaded_arrays
                )

                if not indices:
                    raise RuntimeError("NO_LOADED_BIN_ARRAYS")

                addresses = [
                    pda(pool, index) for index in indices
                ]

                if len(set(addresses)) != len(addresses):
                    raise RuntimeError("DUPLICATE_ARRAY_ADDRESS")

                batch = [pool] + addresses

                if len(batch) > MAX_ACCOUNTS:
                    raise RuntimeError(
                        "TOO_MANY_ARRAYS_FOR_SAME_CONTEXT"
                    )

                slot, accounts = rpc_accounts(batch, url)

                raw_arrays = [
                    accounts[address]["raw"]
                    for address in addresses
                ]

                rebuilt = PoolState.from_accounts(
                    accounts[pool]["raw"],
                    raw_arrays,
                    decimals_x=int(pair.decimals_x),
                    decimals_y=int(pair.decimals_y),
                    exhaustive=False,
                )

                checks = compare(existing, rebuilt)

                row.update({
                    "context_slot": slot,
                    "array_count": len(indices),
                    "min_array_index": min(indices),
                    "max_array_index": max(indices),
                    "account_count": len(batch),
                    "pool_sha256": accounts[pool]["sha256"],
                    "array_hash_count": len(raw_arrays),
                    "comparison": checks,
                })

                row["status"] = (
                    "PASS_BIN_LIQUIDITY_MATCH"
                    if checks["match"]
                    else "HOLD_BIN_LIQUIDITY_DRIFT"
                )

            except Exception as exc:
                row["status"] = (
                    "HOLD_" + type(exc).__name__
                )
                row["reason"] = (
                    str(exc)
                    if str(exc).startswith(
                        ("HOLD_", "NO_", "TOO_", "DUPLICATE_")
                    )
                    else "RECONSTRUCTION_FAILURE"
                )

            report["pairs"].append(row)

    except Exception as exc:
        report["errors"].append(
            "PREPARATION_" + type(exc).__name__
        )

    finally:
        r.q87.c.rpc = original_rpc

        report["reconstructed_matches"] = sum(
            x["status"] == "PASS_BIN_LIQUIDITY_MATCH"
            for x in report["pairs"]
        )

        report["status"] = (
            "HOLD_FULL_QUOTE_LINEAGE_AND_MRIYA_ATTRIBUTION"
        )

        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )

    print("[ORACLE235I_RESULT]", json.dumps({
        "pairs": len(report["pairs"]),
        "reconstructed_matches": report["reconstructed_matches"],
        "errors": report["errors"],
        "pricing_certified": False,
        "mriya_certified": False,
        "signing": False,
        "broadcast": False,
    }, sort_keys=True))

    for row in report["pairs"]:
        print("[ORACLE235I_PAIR]", json.dumps({
            "token": row["token_prefix"],
            "status": row["status"],
            "context_slot": row.get("context_slot"),
            "array_count": row.get("array_count"),
            "comparison": row.get("comparison"),
            "reason": row.get("reason"),
        }, sort_keys=True))

    print("[REPORT]", REPORT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.test:
        test()

    if args.run:
        run()