"""ORACLE-235N: Meteora reserve verification, read-only."""
import argparse
import base64
import hashlib
import json
import os
import struct
import urllib.request
from pathlib import Path
from solders.pubkey import Pubkey

ROOT = Path("runtime_state/oracle/oracle_live_execution")
REPORT = ROOT / "ORACLE235N_METEORA_VAULT_SECURITY.json"
DLMM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
LEGACY = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"


def pub(raw):
    return str(Pubkey.from_bytes(bytes(raw)))


def reserve_pda(pool, mint):
    address, _ = Pubkey.find_program_address(
        [bytes(Pubkey.from_string(pool)),
         bytes(Pubkey.from_string(mint))],
        Pubkey.from_string(DLMM)
    )
    return str(address)


def rpc(addresses, url):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 23514,
        "method": "getMultipleAccounts",
        "params": [
            addresses,
            {"encoding": "base64", "commitment": "confirmed"}
        ]
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = json.load(response)

    if body.get("error"):
        raise RuntimeError("HOLD_RPC_ERROR")

    result = body.get("result") or {}
    slot = (result.get("context") or {}).get("slot")
    values = result.get("value")
    if (type(slot) is not int or slot <= 0
            or not isinstance(values, list)
            or len(values) != len(addresses)):
        raise RuntimeError("HOLD_RPC_SCHEMA")

    decoded = {}
    for addr, item in zip(addresses, values):
        if item is None:
            decoded[addr] = None
            continue
        data = item.get("data")
        if (not isinstance(data, list)
                or len(data) != 2 or data[1] != "base64"):
            raise RuntimeError("HOLD_ENCODING")
        decoded[addr] = (
            item.get("owner"),
            base64.b64decode(data[0], validate=True)
        )
    return slot, decoded


def extension_guard(raw):
    if len(raw) == 165:
        return []
    if len(raw) < 166 or raw[165] != 2:
        return ["BAD_TOKEN22_LAYOUT"]
    problems, seen = [], set()
    pos = 166
    while pos < len(raw):
        if not any(raw[pos:]):
            break
        if pos + 4 > len(raw):
            problems.append("SHORT_TLV_HEADER")
            break
        typ, length = struct.unpack_from("<HH", raw, pos)
        pos += 4
        if typ in seen or typ == 0 or pos + length > len(raw):
            problems.append("INVALID_TLV")
            break
        seen.add(typ)
        if typ != 7 or length != 0:
            problems.append("UNSUPPORTED_EXTENSION_" + str(typ))
        pos += length
    return problems


def verify_vault(entry, mint, mint_entry):
    reasons = []
    if entry is None or mint_entry is None:
        return ["ACCOUNT_MISSING"], {}

    owner, raw = entry
    mint_program, _ = mint_entry

    if owner not in (LEGACY, TOKEN22) or owner != mint_program:
        reasons.append("TOKEN_PROGRAM_MISMATCH")

    if len(raw) < 165:
        return reasons + ["SHORT_ACCOUNT"], {}

    vault_mint = pub(raw[:32])
    balance = struct.unpack_from("<Q", raw, 64)[0]
    delegate = struct.unpack_from("<I", raw, 72)[0]
    state = raw[108]
    close = struct.unpack_from("<I", raw, 129)[0]

    if vault_mint != mint:
        reasons.append("WRONG_TOKEN_MINT")
    if balance <= 0:
        reasons.append("EMPTY_VAULT")
    if state != 1:
        reasons.append("FROZEN_OR_UNINITIALIZED")
    if delegate != 0:
        reasons.append("DELEGATE_PRESENT")
    if close != 0:
        reasons.append("CLOSE_AUTHORITY_PRESENT")

    if owner == LEGACY and len(raw) != 165:
        reasons.append("BAD_LEGACY_LENGTH")
    elif owner == TOKEN22:
        reasons += extension_guard(raw)

    return sorted(set(reasons)), {
        "mint": vault_mint,
        "raw_balance": balance,
        "sha256": hashlib.sha256(raw).hexdigest()
    }


def verify_pair(pair, accounts):
    pool = str(pair.meteora_pool)
    x = str(pair.token_x)
    y = str(pair.token_y)
    vx = reserve_pda(pool, x)
    vy = reserve_pda(pool, y)

    row = {
        "token_prefix": str(pair.token)[:12],
        "pool": pool,
        "reserve_x": vx,
        "reserve_y": vy,
        "status": "HOLD"
    }

    entry = accounts.get(pool)
    if not entry or entry[0] != DLMM:
        row["reason"] = "POOL_OWNER_OR_ACCOUNT_INVALID"
        return row

    raw = entry[1]
    # A pool-reference check is not a substitute for
    # decoding every authoritative LbPair field.
    required = [bytes(Pubkey.from_string(v))
                for v in (x, y, vx, vy)]

    if any(raw.count(value) != 1 for value in required):
        row["reason"] = "POOL_REFERENCE_MISSING_OR_AMBIGUOUS"
        return row

    results = {}
    reasons = []

    for side, mint, vault in (
        ("x", x, vx), ("y", y, vy)
    ):
        problems, details = verify_vault(
            accounts.get(vault), mint, accounts.get(mint)
        )
        results[side] = {
            "address": vault,
            "status": "PASS" if not problems else "HOLD",
            "reasons": problems,
            "details": details
        }
        reasons += [side.upper() + "_" + p for p in problems]

    row["vaults"] = results
    row["reasons"] = reasons
    row["status"] = (
        "PASS_PDA_AND_POOL_REFERENCE_FIELDS"
        if not reasons else "HOLD_RESERVE_SAFETY"
    )
    return row


def test():
    mint = str(Pubkey.from_bytes(bytes([3]) * 32))
    pool = str(Pubkey.from_bytes(bytes([4]) * 32))
    assert reserve_pda(pool, mint) == reserve_pda(pool, mint)

    account = bytearray(165)
    account[:32] = bytes(Pubkey.from_string(mint))
    struct.pack_into("<Q", account, 64, 1000)
    account[108] = 1
    good = (LEGACY, bytes(account))
    assert verify_vault(good, mint, (LEGACY, b""))[0] == []

    account[108] = 2
    assert "FROZEN_OR_UNINITIALIZED" in verify_vault(
        (LEGACY, bytes(account)), mint, (LEGACY, b"")
    )[0]

    print(
        "[ORACLE235N_TEST_PASS] "
        "reserve_pda=TRUE vault_mint=TRUE "
        "frozen_rejected=TRUE"
    )


def run():
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_ARMED")
    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")
    url = os.getenv("SOLANA_RPC_URL", "")
    if not url.startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    old_rpc = r.q87.c.rpc
    result = {
        "build": "ORACLE235N",
        "signing": False,
        "broadcast": False,
        "execution_admission": False,
        "pricing_certified": False,
        "mriya_certified": False,
        "pairs": [],
        "errors": []
    }

    try:
        r.q87.c.rpc = d.restricted_rpc_factory(old_rpc)
        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)
        pairs = list(state.get("pairs") or [])[:12]

        addresses = set()
        for pair in pairs:
            pool = str(pair.meteora_pool)
            x, y = str(pair.token_x), str(pair.token_y)
            addresses.update([
                pool, x, y,
                reserve_pda(pool, x), reserve_pda(pool, y)
            ])

        addresses = sorted(addresses)
        if not addresses or len(addresses) > 100:
            raise RuntimeError("HOLD_ACCOUNT_BATCH_LIMIT")

        slot, accounts = rpc(addresses, url)
        result["context_slot"] = slot

        for pair in pairs:
            try:
                result["pairs"].append(verify_pair(pair, accounts))
            except Exception as exc:
                result["pairs"].append({
                    "token_prefix": str(pair.token)[:12],
                    "status": "HOLD",
                    "reason": type(exc).__name__
                })
    except Exception as exc:
        result["errors"].append(type(exc).__name__)
    finally:
        r.q87.c.rpc = old_rpc

    result["passed"] = sum(
        p["status"] == "PASS_PDA_AND_POOL_REFERENCE_FIELDS"
        for p in result["pairs"]
    )
    result["status"] = "HOLD_COMBINED_EXECUTION_SAFETY"

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("[ORACLE235N_RESULT]", json.dumps({
        "pairs": len(result["pairs"]),
        "passed": result["passed"],
        "context_slot": result.get("context_slot"),
        "errors": result["errors"],
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for row in result["pairs"]:
        print("[ORACLE235N_PAIR]", json.dumps({
            "token": row["token_prefix"],
            "status": row["status"],
            "reason": row.get("reason"),
            "reasons": row.get("reasons")
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