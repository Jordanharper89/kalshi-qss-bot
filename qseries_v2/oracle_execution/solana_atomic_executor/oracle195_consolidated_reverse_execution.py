"""ORACLE195: funded reverse path with IDL validation; simulation only."""
import argparse
import os
import subprocess
import sys

from . import runtime as r
from . import oracle193_reverse_direction_aware_swap2 as q193
from . import oracle194_reverse_wsol_execution as q194


def funded_lock(original, funding):
    def bound(*args, **kwargs):
        result = original(*args, **kwargs)
        if not isinstance(result, tuple) or len(result) != 3:
            raise RuntimeError("ORACLE195_LOCK_CONTRACT_DRIFT")

        direction = args[1] if len(args) > 1 else kwargs.get("direction")
        if direction not in ("METEORA_TO_PUMP", "PUMP_TO_METEORA"):
            raise RuntimeError("ORACLE195_DIRECTION_UNKNOWN")

        route, second, third = result
        if not isinstance(route, dict):
            raise RuntimeError("ORACLE195_ROUTE_CONTRACT_DRIFT")

        if direction == "METEORA_TO_PUMP":
            route = funding(route, direction)
            if not isinstance(route, dict):
                raise RuntimeError("ORACLE195_FUNDING_CONTRACT_DRIFT")
            print(
                "[ORACLE195_REVERSE_CHAIN] "
                "WSOL_FUNDING -> IDL_VALIDATION -> REVERSE_BINDING "
                "-> NATIVE_COMPILE -> SIGNED_SIM broadcast=FALSE",
                flush=True,
            )
        return route, second, third
    return bound


def worker():
    if os.getenv("QSB_LIVE_ARM", "").upper() == "YES":
        raise RuntimeError("ORACLE195_ARMED_REFUSED")

    armed = getattr(r, "_live_010_armed", None)
    if not callable(armed) or armed():
        raise RuntimeError("ORACLE195_DISARM_NOT_CERTIFIED")

    old = r._fast_010_profit_lock_route
    r._fast_010_profit_lock_route = funded_lock(old, q194.inject)
    try:
        # ORACLE193 calls ORACLE192, which validates the resulting
        # funded candidate and its Swap2 instruction before compiling.
        q193.worker()
    finally:
        r._fast_010_profit_lock_route = old


def launch():
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    helius = vault.load(db, vault.HELIUS)
    wallet = vault.load(db, vault.SOLANA)
    if not helius or not wallet:
        raise RuntimeError("ORACLE195_STORED_CREDENTIALS_MISSING")

    env = os.environ.copy()
    env["QSB_SOLANA_PRIVATE_KEY"] = wallet
    env["SOLANA_RPC_URL"] = (
        "https://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    env["SOLANA_WS_URL"] = (
        "wss://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    env["QSB_LIVE_ARM"] = "NO"

    return subprocess.call(
        [
            sys.executable, "-m",
            "qseries_v2.oracle_execution.solana_atomic_executor."
            "oracle195_consolidated_reverse_execution",
            "--worker",
        ],
        env=env,
    )


def test():
    calls = []
    def original(route, direction, bound):
        calls.append("LOCK")
        return route, 1, 2

    def funding(route, direction):
        calls.append("FUND")
        return dict(route, funded=True)

    fn = funded_lock(original, funding)
    result = fn({}, "METEORA_TO_PUMP", 100)
    assert result[0]["funded"] is True
    assert calls == ["LOCK", "FUND"]

    calls.clear()
    fn({}, "PUMP_TO_METEORA", 100)
    assert calls == ["LOCK"]

    try:
        fn({}, "UNSUPPORTED", 100)
    except RuntimeError as exc:
        assert str(exc) == "ORACLE195_DIRECTION_UNKNOWN"
    else:
        raise AssertionError("Unknown direction accepted")

    print("[TEST PASS] ORACLE195 funding order and direction guards")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.test:
        test()
    elif args.run:
        sys.exit(launch())
    else:
        worker()
