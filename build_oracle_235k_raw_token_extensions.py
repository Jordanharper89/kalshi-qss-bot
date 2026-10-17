"""ORACLE-235K: raw mint authority and Token-2022 TLV gate."""
import argparse
import base64
import hashlib
import json
import os
import sqlite3
import struct
import urllib.request
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path("runtime_state/oracle/oracle_live_execution")
DB = ROOT / "ORACLE218_DISCOVERY.sqlite3"
REPORT = ROOT / "ORACLE235K_RAW_TOKEN_EXTENSIONS.json"

LEGACY = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
METADATA_ONLY = {18, 19}
EXT_NAMES = {18: "MetadataPointer", 19: "TokenMetadata"}


def inspect(mint, owner, raw):
    reasons = []
    types = []

    def hold(reason):
        reasons.append(reason)

    if owner not in (LEGACY, TOKEN22):
        hold("UNKNOWN_TOKEN_PROGRAM")

    if len(raw) < 82:
        hold("MINT_TOO_SHORT")
        return {
            "mint": mint, "status": "HOLD",
            "reasons": reasons, "extensions": []
        }

    mint_option = struct.unpack_from("<I", raw, 0)[0]
    freeze_option = struct.unpack_from("<I", raw, 46)[0]
    supply = struct.unpack_from("<Q", raw, 36)[0]
    decimals = raw[44]
    initialized = raw[45]

    if mint_option != 0:
        hold("MINT_AUTHORITY_ACTIVE_OR_MALFORMED")
    if freeze_option != 0:
        hold("FREEZE_AUTHORITY_ACTIVE_OR_MALFORMED")
    if initialized != 1:
        hold("MINT_NOT_INITIALIZED")
    if decimals > 18:
        hold("DECIMALS_UNSUPPORTED")
    if supply == 0:
        hold("ZERO_SUPPLY")

    if owner == LEGACY:
        if len(raw) != 82:
            hold("LEGACY_MINT_LENGTH_INVALID")

    elif owner == TOKEN22:
        if len(raw) == 82:
            pass
        elif len(raw) < 166:
            hold("TOKEN22_TRUNCATED_LAYOUT")
        else:
            if any(raw[82:165]):
                hold("INVALID_MINT_PADDING")
            if raw[165] != 1:
                hold("INVALID_MINT_ACCOUNT_TYPE")

            pos = 166
            while pos < len(raw):
                if not any(raw[pos:]):
                    break
                if pos + 4 > len(raw):
                    hold("TRUNCATED_EXTENSION_HEADER")
                    break

                typ, length = struct.unpack_from(
                    "<HH", raw, pos
                )
                pos += 4

                if typ == 0 or typ in types:
                    hold("UNKNOWN_OR_DUPLICATE_EXTENSION")
                types.append(typ)

                if pos + length > len(raw):
                    hold("TRUNCATED_EXTENSION_BODY")
                    break

                if typ not in METADATA_ONLY:
                    hold("UNSUPPORTED_EXTENSION_" + str(typ))

                # MetadataPointer has two optional pubkeys.
                if typ == 18 and length != 64:
                    hold("INVALID_METADATA_POINTER_LENGTH")

                if typ == 19 and length < 32:
                    hold("INVALID_TOKEN_METADATA_LENGTH")

                pos += length

    status = "HOLD" if reasons else (
        "PASS_METADATA_ONLY_MINT"
        if owner == TOKEN22 and types
        else "PASS_MINT_STRUCTURE_ONLY"
    )

    return {
        "mint": mint,
        "token_program": owner,
        "status": status,
        "reasons": sorted(set(reasons)),
        "extension_ids": types,
        "extensions": [
            EXT_NAMES.get(t, "UNSUPPORTED_" + str(t))
            for t in types
        ],
        "decimals": decimals,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "transaction_safe": False,
    }


def fetch(mints, url):
    request = urllib.request.Request(
        url,
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": 23511,
            "method": "getMultipleAccounts",
            "params": [
                mints,
                {
                    "encoding": "base64",
                    "commitment": "confirmed"
                }
            ]
        }).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(
        request, timeout=30
    ) as response:
        body = json.load(response)

    if body.get("error"):
        raise RuntimeError("HOLD_RPC_ERROR")

    result = body.get("result") or {}
    slot = (result.get("context") or {}).get("slot")
    accounts = result.get("value")

    if (
        type(slot) is not int
        or not isinstance(accounts, list)
        or len(accounts) != len(mints)
    ):
        raise RuntimeError("HOLD_RPC_SCHEMA")

    rows = []

    for mint, entry in zip(mints, accounts):
        if entry is None:
            rows.append({
                "mint": mint, "status": "HOLD",
                "reasons": ["MINT_ACCOUNT_MISSING"]
            })
            continue

        data = entry.get("data")
        if (
            not isinstance(data, list)
            or len(data) != 2
            or data[1] != "base64"
        ):
            raise RuntimeError("HOLD_ACCOUNT_ENCODING")

        raw = base64.b64decode(data[0], validate=True)
        rows.append(inspect(mint, entry.get("owner"), raw))

    return slot, rows


def test():
    raw = bytearray(82)
    struct.pack_into("<Q", raw, 36, 1000000)
    raw[44] = 6
    raw[45] = 1

    assert inspect("m", LEGACY, raw)["status"] == (
        "PASS_MINT_STRUCTURE_ONLY"
    )

    struct.pack_into("<I", raw, 46, 1)
    assert inspect("m", LEGACY, raw)["status"] == "HOLD"
    struct.pack_into("<I", raw, 46, 0)

    extended = raw + bytes(83) + bytes([1])
    extended += struct.pack("<HH", 18, 64) + bytes(64)
    extended += struct.pack("<HH", 19, 32) + bytes(32)

    assert inspect("m", TOKEN22, extended)["status"] == (
        "PASS_METADATA_ONLY_MINT"
    )

    risky = extended + struct.pack("<HH", 14, 0)
    assert inspect("m", TOKEN22, risky)["status"] == "HOLD"

    broken = extended + struct.pack("<HH", 19, 100)
    assert inspect("m", TOKEN22, broken)["status"] == "HOLD"

    print(
        "[ORACLE235K_TEST_PASS] "
        "raw_authority=TRUE metadata_only=TRUE "
        "transfer_hook_blocked=TRUE malformed_blocked=TRUE"
    )


def run():
    if os.getenv("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_LIVE_ARM")
    if os.getenv("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")

    url = os.getenv("SOLANA_RPC_URL", "")
    if not url.startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    with closing(sqlite3.connect(
        DB.resolve().as_uri() + "?mode=ro", uri=True
    )) as db:
        mints = sorted({
            r[0] for r in db.execute(
                "SELECT mint FROM universal_routes"
            )
        })

    if not mints or len(mints) > 100:
        raise RuntimeError("HOLD_MINT_COUNT")

    slot, rows = fetch(mints, url)
    counts = dict(Counter(r["status"] for r in rows))

    report = {
        "build": "ORACLE235K",
        "context_slot": slot,
        "mints_checked": len(rows),
        "outcomes": counts,
        "execution_admission": False,
        "liquidity_reconciled": False,
        "transfer_account_audit_complete": False,
        "mriya_certified": False,
        "profit_certified": False,
        "signing": False,
        "broadcast": False,
        "tokens": rows
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("[ORACLE235K_RESULT]", json.dumps({
        k: v for k, v in report.items()
        if k != "tokens"
    }, sort_keys=True))

    for row in rows:
        print("[ORACLE235K_TOKEN]", json.dumps({
            "mint": row["mint"][:12],
            "status": row["status"],
            "extensions": row.get("extensions", []),
            "reasons": row["reasons"]
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