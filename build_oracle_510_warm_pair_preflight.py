
from pathlib import Path
import ast, os

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "oracle_510_warm_pair_preflight.py"
)

SOURCE = r'''
from __future__ import annotations
import argparse, base64, collections, json, os, struct, time
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import (
    oracle_509_exact_pair_qualification as q509
)
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core as c
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    live_account_stream as pd
)
from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover as q18,
    oracle_023_persistent_token_net_worker as q23
)

ROOT = Path("runtime_state/oracle/oracle_live_execution")
CHECKS = ROOT / "oracle_509_checks.json"
REPORT = ROOT / "oracle_510_warm_preflight.json"
REGISTRY = ROOT / "oracle_510_warm_registry.json"
SIZE = 0.010
DIRECTIONS = {"PUMP_TO_METEORA", "METEORA_TO_PUMP"}


class Hold(RuntimeError):
    pass


def selected(checks, limit):
    rows = []
    for token, v in checks.items():
        if not isinstance(v, dict) or v.get("qualified") is not True:
            continue
        if v.get("reason") != "API_MATCH_OWNER_VERIFIED":
            continue
        fields = ("pump_pool", "meteora_pool", "token_x", "token_y")
        if not all(isinstance(v.get(k), str) and v[k] for k in fields):
            continue
        if {v["token_x"], v["token_y"]} != {token, c.WSOL}:
            continue
        rows.append(dict(v, token=token))
    rows.sort(key=lambda x: (-float(x.get("checked_at", 0)), x["token"]))
    return rows[:limit], len(rows)


def decode_response(packet, addrs):
    rows = packet.get("value") if isinstance(packet, dict) else None
    slot = (
        (packet.get("context") or {}).get("slot")
        if isinstance(packet, dict) else None
    )
    if not isinstance(rows, list) or len(rows) != len(addrs):
        raise Hold("COHERENT_ACCOUNT_RESPONSE_REQUIRED")
    if not isinstance(slot, int) or slot <= 0:
        raise Hold("COHERENT_ACCOUNT_RESPONSE_REQUIRED")
    out = {}
    for addr, v in zip(addrs, rows):
        if not isinstance(v, dict) or v.get("executable"):
            raise Hold("ACCOUNT_MISSING_OR_EXECUTABLE")
        if not isinstance(v.get("owner"), str):
            raise Hold("ACCOUNT_MISSING_OR_EXECUTABLE")
        d = v.get("data")
        if not isinstance(d, list) or len(d) < 2 or d[1] != "base64":
            raise Hold("ACCOUNT_ENCODING_INVALID")
        try:
            raw = base64.b64decode(d[0], validate=True)
        except (ValueError, TypeError):
            raise Hold("ACCOUNT_BYTES_INVALID")
        out[addr] = (raw, v["owner"])
    return slot, out


def mint_decimals(item):
    raw, owner = item
    if owner not in (c.TOKEN, c.TOKEN22) or len(raw) < 82:
        raise Hold("MINT_ACCOUNT_INVALID")
    decimals = int(raw[44])
    if decimals > 18:
        raise Hold("MINT_DECIMALS_INVALID")
    return decimals, owner


def check_vault(item, expected_mint):
    raw, owner = item
    if owner not in (c.TOKEN, c.TOKEN22) or len(raw) < 72:
        raise Hold("TOKEN_VAULT_INVALID")
    if raw[:32] != c.b58d(expected_mint):
        raise Hold("VAULT_MINT_MISMATCH")
    amount = struct.unpack_from("<Q", raw, 64)[0]
    if amount <= 0:
        raise Hold("ZERO_VAULT_LIQUIDITY")
    return amount


def prepare(row, probe, arrays, make_state):
    token = row["token"]
    pump = row["pump_pool"]
    dlmm = row["meteora_pool"]

    pool_raw, _ = probe([pump])[1][pump]
    pump_meta = c.decode_pump_pool(pool_raw)
    if pump_meta.get("base_mint") != token:
        raise Hold("PUMP_ONCHAIN_IDENTITY_MISMATCH")
    if pump_meta.get("quote_mint") != c.WSOL:
        raise Hold("PUMP_ONCHAIN_IDENTITY_MISMATCH")

    addrs = list(dict.fromkeys([
        pump, dlmm, token, c.WSOL,
        pump_meta["base_vault"], pump_meta["quote_vault"]
    ]))
    slot, account = probe(addrs)

    if account[pump][1] != c.PUMP or account[dlmm][1] != c.DLMM:
        raise Hold("POOL_OWNER_MISMATCH")

    decoded = c.decode_pump_pool(account[pump][0])
    if decoded.get("base_mint") != token:
        raise Hold("PUMP_ONCHAIN_IDENTITY_MISMATCH")
    if decoded.get("quote_mint") != c.WSOL:
        raise Hold("PUMP_ONCHAIN_IDENTITY_MISMATCH")

    lb_raw = account[dlmm][0]
    if c.b58d(row["token_x"]) not in lb_raw:
        raise Hold("DLMM_LB_MINT_BYTES_NOT_PRESENT")
    if c.b58d(row["token_y"]) not in lb_raw:
        raise Hold("DLMM_LB_MINT_BYTES_NOT_PRESENT")

    dx, px = mint_decimals(account[row["token_x"]])
    dy, py = mint_decimals(account[row["token_y"]])

    br = check_vault(account[decoded["base_vault"]], token)
    qr = check_vault(account[decoded["quote_vault"]], c.WSOL)

    if account[decoded["base_vault"]][1] != px:
        raise Hold("VAULT_TOKEN_PROGRAM_MISMATCH")
    if account[decoded["quote_vault"]][1] != mint_decimals(account[c.WSOL])[1]:
        raise Hold("VAULT_TOKEN_PROGRAM_MISMATCH")

    aa = arrays(dlmm)
    if not aa:
        raise Hold("NO_METEORA_BIN_ARRAYS")

    for a in aa:
        if len(a) != 3 or not isinstance(a[2], bytes):
            raise Hold("BIN_ARRAY_PARENT_MISMATCH")
        if len(a[2]) < 56 or a[2][24:56] != c.b58d(dlmm):
            raise Hold("BIN_ARRAY_PARENT_MISMATCH")

    pair = pd.PairState(
        token=token,
        pump_pool=pump,
        meteora_pool=dlmm,
        token_x=row["token_x"],
        token_y=row["token_y"],
        decimals_x=dx,
        decimals_y=dy,
        pump_base_vault=decoded["base_vault"],
        pump_quote_vault=decoded["quote_vault"],
        pump_base_reserve=br,
        pump_quote_reserve=qr,
        lb_bytes=lb_raw,
        arrays=list(aa),
        dlmm_state=None,
        last_slot=slot,
    )
    pair.dlmm_state = make_state(pair)

    snap = {
        "token": token,
        "pump_pool": pump,
        "meteora": {
            "address": dlmm,
            "token_x": row["token_x"],
            "token_y": row["token_y"],
            "decimals_x": dx,
            "decimals_y": dy,
        },
        "dlmm_state": pair.dlmm_state,
        "pump_base_reserve": br,
        "pump_quote_reserve": qr,
    }
    watched = list(dict.fromkeys(
        [decoded["base_vault"], decoded["quote_vault"], dlmm]
        + [a[1] for a in aa]
    ))
    return snap, {
        "slot": slot,
        "bin_arrays": len(aa),
        "watched": watched,
        "mint_program_x": px,
        "mint_program_y": py,
    }


def assess_quotes(quotes):
    if not isinstance(quotes, (list, tuple)):
        raise Hold("BIDIRECTIONAL_QUOTE_MISSING")
    if {x.get("direction") for x in quotes if isinstance(x, dict)} != DIRECTIONS:
        raise Hold("BIDIRECTIONAL_QUOTE_MISSING")

    result = []
    for direction in sorted(DIRECTIONS):
        x = next(z for z in quotes if z["direction"] == direction)
        if x.get("pump_model") not in (
            "SAE003_PUMPSWAP_EXACT_QUOTE_IN",
            "EXACT_PUMPSWAP_SDK",
        ):
            raise Hold("NON_SDK_PUMP_MATH_REFUSED")
        if int(x["start"]) != 10_000_000 or int(x["local_end"]) <= 0:
            raise Hold("QUOTE_SIZE_OR_OUTPUT_INVALID")
        if int(x["local_net"]) != int(x["local_end"]) - int(x["start"]):
            raise Hold("QUOTE_ARITHMETIC_MISMATCH")

        result.append({
            "direction": direction,
            "gross_lamports": int(x["local_net"]),
            "gross_bps": round(
                int(x["local_net"]) / int(x["start"]) * 10000, 2
            ),
            "pump_model": x["pump_model"],
        })
    return result


def warm_one(row):
    token = row["token"]

    live = q509.qualify(
        {"token": token, "sources": row.get("sources", [])},
        c.http, c.rpc, q509.pump_pda, c.decode_pump_pool, 100
    )
    if not live.get("qualified"):
        raise Hold(
            "FRESH_509_REVALIDATION_" + str(live.get("reason"))
        )
    if live["pump_pool"] != row["pump_pool"]:
        raise Hold("PUMP_POOL_IDENTITY_CHANGED")
    if live["meteora_pool"] != row["meteora_pool"]:
        raise Hold("METEORA_POOL_SELECTION_CHANGED")

    def probe(addrs):
        packet = c.rpc("getMultipleAccounts", [
            addrs, {"encoding": "base64", "commitment": "confirmed"}
        ])
        return decode_response(packet, addrs)

    start = time.perf_counter()
    snap, meta = prepare(row, probe, c.dlmm_arrays, pd._build_dlmm_state)

    q23.worker().warm(token)
    q23.install_hot_token_net()
    q23.worker().refresh_epoch()
    q18.worker().warm(row["pump_pool"])

    quotes = assess_quotes(
        q18.exact_snapshot_opportunities(snap, SIZE)
    )

    return {
        "token": token,
        "pump_pool": row["pump_pool"],
        "meteora_pool": row["meteora_pool"],
        "directions": quotes,
        "quote_size_sol": SIZE,
        "prepared_at": time.time(),
        "warm_ms": round((time.perf_counter() - start) * 1000, 1),
        "slot": meta["slot"],
        "bin_arrays": meta["bin_arrays"],
        "watched_addresses": meta["watched"],
        "read_only": True,
        "scanner_admitted": False,
        "native_tx_ready": False,
        "signing": False,
        "broadcast": False,
    }


def audit(limit):
    if not CHECKS.exists():
        raise Hold("ORACLE509_CHECKS_MISSING")

    rows, total = selected(q509.load(CHECKS), limit)
    if not rows:
        raise Hold("NO_509_VERIFIED_CANDIDATES")

    outcomes = []
    ready = []
    try:
        for row in rows:
            try:
                result = warm_one(row)
                ready.append(result)
                outcomes.append({
                    "token": row["token"],
                    "reason": "SDK_BIDIRECTIONAL_WARM_PASS",
                })
            except Exception as exc:
                outcomes.append({
                    "token": row["token"],
                    "reason": "WARM_HOLD_" + type(exc).__name__,
                    "stage": str(exc) if isinstance(exc, Hold)
                             else "SDK_OR_RPC_FAILURE",
                })
            print(
                "[ORACLE510_PAIR]",
                json.dumps(outcomes[-1], sort_keys=True),
                flush=True,
            )
    finally:
        if getattr(q18, "_worker", None) is not None:
            q18._worker.close()
            q18._worker = None
        if getattr(q23, "_worker", None) is not None:
            q23._worker.close()
            q23._worker = None

    registry = {
        "generated_at": time.time(),
        "ttl_seconds": 60,
        "warm_quoted_pairs": ready,
        "scanner_admitted": False,
        "execution_authority": False,
        "signing": False,
        "broadcast": False,
        "note": "OBSERVATION_ONLY_REHYDRATE_BEFORE_ADMISSION",
    }
    q509.save(REGISTRY, registry)

    report = {
        "status": "PASS_WARM_PREFLIGHT" if ready
                  else "HOLD_NO_EXACT_WARM_PAIR",
        "source_verified_pairs": total,
        "attempted": len(rows),
        "bidirectional_quote_pass": len(ready),
        "holds": dict(collections.Counter(
            x["reason"] for x in outcomes
            if x["reason"] != "SDK_BIDIRECTIONAL_WARM_PASS"
        )),
        "scanner_admitted": False,
        "native_tx_ready": False,
        "signing": False,
        "broadcast": False,
    }
    q509.save(REPORT, report)

    print("[ORACLE510]", json.dumps(report, sort_keys=True), flush=True)
    print("[REPORT]", REPORT, flush=True)

    if not ready:
        raise SystemExit(2)


def tests():
    x = "X" * 32
    y = "Y" * 32
    rows, n = selected({
        x: {
            "qualified": True,
            "reason": "API_MATCH_OWNER_VERIFIED",
            "pump_pool": "A" * 32,
            "meteora_pool": "B" * 32,
            "token_x": x,
            "token_y": c.WSOL,
        },
        y: {
            "qualified": True,
            "reason": "STRUCTURE_VERIFIED",
            "pump_pool": "A" * 32,
            "meteora_pool": "B" * 32,
        },
    }, 5)
    assert n == 1 and rows[0]["token"] == x

    def quote(direction, end, model):
        return {
            "direction": direction,
            "start": 10_000_000,
            "local_end": end,
            "local_net": end - 10_000_000,
            "pump_model": model,
        }

    values = assess_quotes([
        quote("PUMP_TO_METEORA", 9900000, "EXACT_PUMPSWAP_SDK"),
        quote("METEORA_TO_PUMP", 10010000,
              "SAE003_PUMPSWAP_EXACT_QUOTE_IN"),
    ])
    assert len(values) == 2
    assert min(v["gross_lamports"] for v in values) < 0

    try:
        assess_quotes([
            quote("PUMP_TO_METEORA", 9900000, "FIXED_120_BPS")
        ])
    except Hold:
        pass
    else:
        raise AssertionError("REJECT_NON_EXACT_MATH")

    mint = bytearray(82)
    mint[44] = 6
    assert mint_decimals((bytes(mint), c.TOKEN)) == (6, c.TOKEN)

    try:
        check_vault((bytes(72), c.TOKEN), c.WSOL)
    except Hold:
        pass
    else:
        raise AssertionError("REJECT_WRONG_VAULT_MINT")

    try:
        decode_response({"context": {"slot": 0}, "value": []}, [])
    except Hold:
        pass
    else:
        raise AssertionError("REJECT_INVALID_SLOT")

    print(
        "[PASS] ORACLE510 offline identity accounts vault liquidity "
        "sdk_only bidirectional failclosed"
    )


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--test", action="store_true")
    action.add_argument("--audit", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    if args.test:
        tests()
        return

    if not 1 <= args.limit <= 8:
        parser.error("INVALID_LIMIT")

    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise Hold("READONLY_SECRET_ISOLATION_REQUIRED")
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise Hold("READONLY_SECRET_ISOLATION_REQUIRED")

    audit(args.limit)


if __name__ == "__main__":
    main()
'''


def main():
    pricing = Path(
        "qseries_v2/oracle_execution/"
        "oracle_018_exact_sdk_hot_lane_cutover.py"
    )
    token_net = Path(
        "qseries_v2/oracle_execution/"
        "oracle_023_persistent_token_net_worker.py"
    )

    if not TARGET.parent.is_dir():
        raise SystemExit("HOLD_SOURCE_CONTRACT_MISSING")
    if not pricing.is_file() or not token_net.is_file():
        raise SystemExit("HOLD_SOURCE_CONTRACT_MISSING")
    if "def exact_snapshot_opportunities(" not in pricing.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("HOLD_EXACT_PRICER_CONTRACT_DRIFT")

    ast.parse(SOURCE)
    TARGET.write_text(SOURCE, encoding="utf-8")

    print(
        "[PASS] ORACLE510_INSTALLED "
        "scanner_frozen unsigned_no_broadcast"
    )
    print("[INSTALLED]", TARGET)


if __name__ == "__main__":
    main()
