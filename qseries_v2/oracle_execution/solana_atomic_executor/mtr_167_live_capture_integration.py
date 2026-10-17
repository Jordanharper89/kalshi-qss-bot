
"""MTR-167: isolated canonical WebSocket route capture."""
import argparse
import json
import types
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_166_capture_boundary_replacement import (
    capture_callback, new_counters
)

REVISION = "MTR167_ISOLATED_LIVE_CAPTURE"

def forbidden(*args, **kwargs):
    raise RuntimeError("MTR167_EXECUTION_DISABLED")

def public_identity(public_wallet):
    return None, public_wallet

def validate_public_wallet(wallet):
    if not isinstance(wallet, str):
        raise ValueError("PUBLIC_WALLET_REQUIRED")
    raw = rt.q87.c.b58d(wallet)
    if len(raw) != 32:
        raise ValueError("INVALID_PUBLIC_WALLET")
    return wallet

def make_safe_price(callback):
    source = rt.canonical_price

    if "attack" not in source.__code__.co_names:
        raise RuntimeError("CANONICAL_ATTACK_BOUNDARY_CHANGED")

    safe_globals = source.__globals__.copy()
    safe_globals["attack"] = callback
    safe_globals["compile_current"] = forbidden
    safe_globals["simulate_current"] = forbidden
    safe_globals["_execute_route_once"] = forbidden

    return types.FunctionType(
        source.__code__,
        safe_globals,
        source.__name__,
        source.__defaults__,
        source.__closure__,
    )

def make_safe_run(safe_price, wallet):
    source = rt.run

    sensitive = {
        "compile_current", "simulate_current",
        "signed_tx", "keypair", "send",
        "_execute_route_once", "attack"
    }

    direct = sensitive.intersection(source.__code__.co_names)

    if direct:
        raise RuntimeError(
            "UNSAFE_CANONICAL_RUN_DEPENDENCIES:" +
            ",".join(sorted(direct))
        )

    safe_globals = source.__globals__.copy()

    q87_proxy = types.SimpleNamespace(**{
        name: getattr(rt.q87, name)
        for name in (
            "repaired_candidates",
            "compile_candidate",
        )
        if hasattr(rt.q87, name)
    })

    core_proxy = types.SimpleNamespace(
        sim_identity=lambda: public_identity(wallet)
    )

    q87_proxy.c = core_proxy

    safe_globals["q87"] = q87_proxy
    safe_globals["canonical_price"] = safe_price
    safe_globals["compile_current"] = forbidden
    safe_globals["simulate_current"] = forbidden
    safe_globals["_execute_route_once"] = forbidden
    safe_globals["attack"] = forbidden

    return types.FunctionType(
        source.__code__,
        safe_globals,
        source.__name__,
        source.__defaults__,
        source.__closure__,
    )

def run_capture(seconds, wallet, output_dir):
    validate_public_wallet(wallet)

    if not 5 <= seconds <= 300:
        raise ValueError("CAPTURE_DURATION_OUT_OF_BOUNDS")

    counters = new_counters()

    callback = capture_callback(
        wallet, output_dir, counters
    )

    safe_price = make_safe_price(callback)
    safe_run = make_safe_run(safe_price, wallet)

    if rt.canonical_price is safe_price:
        raise RuntimeError("PRODUCTION_PRICE_MUTATED")

    if rt.run is safe_run:
        raise RuntimeError("PRODUCTION_RUN_MUTATED")

    print("[MTR167] ISOLATED_LIVE_CAPTURE")
    print("[CAPTURE_CALLBACK] MTR166")
    print("[PRODUCTION_RUNTIME] UNMODIFIED")
    print("[SIGNING] DISABLED_IN_CAPTURE_PATH")
    print("[BROADCAST] DISABLED_IN_CAPTURE_PATH")

    try:
        result = safe_run(seconds)
    finally:
        print(
            "[MTR167_COUNTS]",
            json.dumps(counters, sort_keys=True)
        )

    return result, counters

def main(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--seconds", type=float, default=30
    )

    parser.add_argument(
        "--public-wallet", type=str
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() /
        "runtime_state/oracle/oracle_live_execution"
    )

    args = parser.parse_args(argv)

    if not args.public_wallet:
        print("[MTR167] LIVE_CAPTURE_INTEGRATION_READY")
        print("[MTR167_RUN] HOLD_PUBLIC_WALLET_REQUIRED")
        print("[SCANNER] UNMODIFIED")
        print("[SIGNING] FALSE")
        print("[BROADCAST] FALSE")
        return

    run_capture(
        args.seconds,
        args.public_wallet,
        args.output_dir,
    )

if __name__ == "__main__":
    main()
