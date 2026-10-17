"""ORACLE-235L: candidate swap-vault token-account verification."""
import argparse
import json
import os
import urllib.request
from pathlib import Path
from collections import Counter

ROOT = Path("runtime_state/oracle/oracle_live_execution")
REPORT = ROOT / "ORACLE235L_VAULT_SECURITY.json"
LEGACY = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
WSOL = "So11111111111111111111111111111111111111112"


def is_address(value):
    if not isinstance(value, str):
        return False
    try:
        from solders.pubkey import Pubkey
        Pubkey.from_string(value)
        return True
    except (ValueError, TypeError):
        return False


def candidates(pair):
    result = {}
    try:
        fields = vars(pair)
    except TypeError:
        fields = {}

    for name, value in fields.items():
        low = name.lower()
        if (
            "vault" in low
            or "token_account" in low
            or "reserve_account" in low
        ):
            address = str(value)
            if is_address(address):
                result[name] = address
    return result


def assess(account, expected_mints):
    reasons = []

    if not isinstance(account, dict):
        return ["ACCOUNT_MISSING"]

    if account.get("owner") not in (LEGACY, TOKEN22):
        reasons.append("NOT_TOKEN_PROGRAM_OWNED")

    data = account.get("data")
    if not isinstance(data, dict):
        return reasons + ["PARSED_DATA_MISSING"]

    if data.get("program") not in (
        "spl-token", "spl-token-2022"
    ):
        reasons.append("PARSER_PROGRAM_UNKNOWN")

    parsed = data.get("parsed") or {}
    if parsed.get("type") != "account":
        return reasons + ["NOT_TOKEN_ACCOUNT"]

    info = parsed.get("info") or {}

    if info.get("mint") not in expected_mints:
        reasons.append("WRONG_VAULT_MINT")

    if info.get("state") != "initialized":
        reasons.append("ACCOUNT_NOT_INITIALIZED_OR_FROZEN")

    balance = info.get("tokenAmount") or {}
    amount = balance.get("amount")
    try:
        if int(amount) <= 0:
            reasons.append("NO_TOKEN_LIQUIDITY")
    except (ValueError, TypeError):
        reasons.append("BALANCE_UNVERIFIED")

    if info.get("delegate") is not None:
        reasons.append("DELEGATE_PRESENT")

    if info.get("closeAuthority") is not None:
        reasons.append("CLOSE_AUTHORITY_REQUIRES_REVIEW")

    if account.get("owner") == TOKEN22:
        extensions = info.get("extensions")
        if extensions:
            reasons.append("TOKEN22_ACCOUNT_EXTENSIONS_REVIEW")
        elif extensions is None:
            reasons.append("TOKEN22_ACCOUNT_TLV_NOT_AUDITED")

    return sorted(set(reasons))


def fetch(addresses, url):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 23512,
        "method": "getMultipleAccounts",
        "params": [
            addresses,
            {
                "encoding": "jsonParsed",
                "commitment": "confirmed"
            }
        ]
    }).encode()

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(
        request, timeout=30
    ) as response:
        data = json.load(response)

    if data.get("error"):
        raise RuntimeError("HOLD_VAULT_RPC_ERROR")

    result = data.get("result") or {}
    slot = (result.get("context") or {}).get("slot")
    accounts = result.get("value")

    if (
        type(slot) is not int
        or not isinstance(accounts, list)
        or len(accounts) != len(addresses)
    ):
        raise RuntimeError("HOLD_RPC_ACCOUNT_SCHEMA")

    return slot, dict(zip(addresses, accounts))


def test():
    good = {
        "owner": LEGACY,
        "data": {
            "program": "spl-token",
            "parsed": {
                "type": "account",
                "info": {
                    "mint": "token",
                    "state": "initialized",
                    "tokenAmount": {"amount": "1000"},
                    "delegate": None,
                    "closeAuthority": None
                }
            }
        }
    }

    assert not assess(good, {"token"})

    bad = json.loads(json.dumps(good))
    bad["data"]["parsed"]["info"]["state"] = "frozen"
    assert "ACCOUNT_NOT_INITIALIZED_OR_FROZEN" in assess(
        bad, {"token"}
    )

    bad = json.loads(json.dumps(good))
    bad["data"]["parsed"]["info"]["mint"] = "other"
    assert "WRONG_VAULT_MINT" in assess(
        bad, {"token"}
    )

    assert assess(None, {"token"}) == ["ACCOUNT_MISSING"]

    print(
        "[ORACLE235L_TEST_PASS] "
        "frozen=BLOCKED wrong_mint=BLOCKED "
        "missing_account=BLOCKED"
    )


def run():
    if os.environ.get("QSB_LIVE_ARM", "NO").upper() != "NO":
        raise RuntimeError("HOLD_LIVE_ARM")

    if os.environ.get("QSB_SOLANA_PRIVATE_KEY"):
        raise RuntimeError("HOLD_PRIVATE_KEY_PRESENT")

    url = os.environ.get("SOLANA_RPC_URL", "")
    if not url.startswith("https://"):
        raise RuntimeError("HOLD_RPC_MISSING")

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    original_rpc = r.q87.c.rpc
    report = {
        "build": "ORACLE235L",
        "mode": "READ_ONLY",
        "signing": False,
        "broadcast": False,
        "vault_role_certified": False,
        "execution_admission": False,
        "pairs": [],
        "errors": []
    }

    try:
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)
        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)

        pairs = list(state.get("pairs") or [])[:12]

        for pair in pairs:
            mint = str(pair.token)
            found = candidates(pair)

            row = {
                "token_prefix": mint[:12],
                "candidate_fields": found,
                "vault_role_verified": False,
                "accounts": [],
                "status": "HOLD_VAULT_ROLE_NOT_PROVEN"
            }

            if found:
                addresses = list(dict.fromkeys(found.values()))
                if len(addresses) <= 100:
                    slot, values = fetch(addresses, url)
                    row["context_slot"] = slot

                    for field, address in found.items():
                        reasons = assess(
                            values[address], {mint, WSOL}
                        )
                        row["accounts"].append({
                            "field": field,
                            "address": address,
                            "account_checks": (
                                "PASS_ACCOUNT_FIELDS_ONLY"
                                if not reasons else "HOLD"
                            ),
                            "reasons": reasons
                        })

            report["pairs"].append(row)

    except Exception as exc:
        report["errors"].append(
            "PREPARATION_" + type(exc).__name__
        )

    finally:
        r.q87.c.rpc = original_rpc

        report["status"] = (
            "HOLD_ACTUAL_VAULT_MAPPING_AND_ATOMIC_SAFETY"
        )

        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )

    count = Counter(
        p["status"] for p in report["pairs"]
    )

    print("[ORACLE235L_RESULT]", json.dumps({
        "pairs": len(report["pairs"]),
        "candidate_accounts": sum(
            len(p["accounts"]) for p in report["pairs"]
        ),
        "outcomes": dict(count),
        "errors": report["errors"],
        "execution_admission": False,
        "signing": False,
        "broadcast": False
    }, sort_keys=True))

    for row in report["pairs"]:
        print("[ORACLE235L_PAIR]", json.dumps({
            "token": row["token_prefix"],
            "fields": list(row["candidate_fields"]),
            "accounts": row["accounts"],
            "status": row["status"]
        }, sort_keys=True))

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