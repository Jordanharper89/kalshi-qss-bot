
"""ORACLE196: execution evidence using existing ORACLE195. No module installation."""
import argparse
import os
import re

def inspect_logs(logs):
    found = []
    for line in logs or []:
        s = str(line)
        if "AnchorError" in s:
            account = re.search(
                r"caused by account:\s*([A-Za-z_][A-Za-z_0-9]{0,55})", s
            )
            error = re.search(
                r"Error Code:\s*([A-Za-z_][A-Za-z_0-9]{0,55})", s
            )
            found.append((
                error.group(1) if error else "UNKNOWN",
                account.group(1) if account else "UNKNOWN",
            ))
        elif "insufficient funds" in s.lower():
            found.append(("INSUFFICIENT_FUNDS", "UNKNOWN"))
        elif "slippage" in s.lower():
            found.append(("SLIPPAGE", "UNKNOWN"))
    return found[:12]

def test():
    rows = inspect_logs([
        "Program log: AnchorError caused by account: bin_array. "
        "Error Code: AccountNotEnoughKeys. Error Number: 3005.",
        "Program log: insufficient funds",
    ])
    assert rows == [
        ("AccountNotEnoughKeys", "bin_array"),
        ("INSUFFICIENT_FUNDS", "UNKNOWN"),
    ]
    print("[TEST PASS] ORACLE196 safe error and account classification")

def run():
    if os.environ.get("QSB_LIVE_ARM", "").upper() == "YES":
        raise RuntimeError("ORACLE196_ARMED_REFUSED")

    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    helius = vault.load(db, vault.HELIUS)
    wallet_key = vault.load(db, vault.SOLANA)
    if not helius or not wallet_key:
        raise RuntimeError("ORACLE196_VAULT_MISSING")

    os.environ["QSB_SOLANA_PRIVATE_KEY"] = wallet_key
    os.environ["SOLANA_RPC_URL"] = (
        "https://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    os.environ["SOLANA_WS_URL"] = (
        "wss://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    os.environ["QSB_LIVE_ARM"] = "NO"

    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle195_consolidated_reverse_execution as existing
    )

    armed = getattr(r, "_live_010_armed", None)
    if not callable(armed) or armed():
        raise RuntimeError("ORACLE196_DISARM_UNCERTIFIED")

    old_sim = r.simulate_current
    old_reverse = r.build_meteora_buy_ix_hot
    old_forward = r.build_meteora_ix_hot

    def inspect_quote(fn, direction):
        def wrapped(token, amount, quote):
            template = r.METEORA_TEMPLATES.get(str(token), {})
            result = fn(token, amount, quote)
            accounts = result.get("accounts") or []
            available = len(template.get("arrays") or [])
            selected = max(0, len(accounts) - 16)
            print(
                "[ORACLE196_BIN_SELECTION] direction=%s "
                "available=%d selected=%d crossed=%s "
                "quote_complete=%s" %
                (
                    direction, available, selected,
                    str(quote.get("bins_crossed", "UNKNOWN"))[:20],
                    str(quote.get("complete", "UNKNOWN"))[:20],
                ),
                flush=True,
            )
            return result
        return wrapped

    def inspect_sim(compiled, user):
        result = old_sim(compiled, user)
        if isinstance(result, dict):
            err = result.get("err")
            evidence = inspect_logs(result.get("logs"))
            if err is not None:
                print(
                    "[ORACLE196_SIM_CAUSE] "
                    "error_type=%s account_evidence=%s broadcast=FALSE" %
                    (
                        "INSTRUCTION_ERROR" if isinstance(err, dict)
                        else type(err).__name__,
                        evidence if evidence else "NO_CLASSIFIED_ACCOUNT",
                    ),
                    flush=True,
                )
        return result

    r.simulate_current = inspect_sim
    r.build_meteora_buy_ix_hot = inspect_quote(
        old_reverse, "METEORA_TO_PUMP"
    )
    r.build_meteora_ix_hot = inspect_quote(
        old_forward, "PUMP_TO_METEORA"
    )

    try:
        existing.worker()
    finally:
        r.simulate_current = old_sim
        r.build_meteora_buy_ix_hot = old_reverse
        r.build_meteora_ix_hot = old_forward
        os.environ.pop("QSB_SOLANA_PRIVATE_KEY", None)
        print("[ORACLE196_COMPLETE] broadcast=FALSE", flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    a = p.parse_args()
    if a.test:
        test()
    elif a.run:
        run()
    else:
        p.error("Choose --test or --run")
