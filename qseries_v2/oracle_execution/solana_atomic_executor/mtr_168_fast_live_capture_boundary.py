
"""MTR-168: correct isolated fast_live_attack capture boundary."""

import types

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_166_capture_boundary_replacement import (
    capture_callback,
    new_counters,
)

REVISION = "MTR168_FAST_LIVE_ATTACK_BOUNDARY"
CALLBACK_NAME = "fast_live_attack"


class BoundaryHold(RuntimeError):
    pass


def forbidden(*args, **kwargs):
    raise BoundaryHold("MTR168_EXECUTION_DISABLED")


def validate_runtime_boundary():
    price = rt.canonical_price

    names = set(price.__code__.co_names)

    if CALLBACK_NAME not in names:
        raise BoundaryHold("FAST_LIVE_ATTACK_NOT_IN_PRICE")

    if "attack" in names:
        raise BoundaryHold("AMBIGUOUS_ATTACK_BOUNDARY")

    if CALLBACK_NAME not in price.__globals__:
        raise BoundaryHold("FAST_LIVE_ATTACK_GLOBAL_MISSING")

    if not callable(price.__globals__[CALLBACK_NAME]):
        raise BoundaryHold("FAST_LIVE_ATTACK_NOT_CALLABLE")

    if price.__code__.co_freevars:
        raise BoundaryHold("UNEXPECTED_PRICE_CLOSURE")

    return {
        "revision": REVISION,
        "callback": CALLBACK_NAME,
        "source_file": price.__code__.co_filename,
        "source_line": price.__code__.co_firstlineno,
        "boundary_verified": True,
    }


def make_capture_price(callback):
    validate_runtime_boundary()

    original = rt.canonical_price

    isolated = dict(original.__globals__)

    isolated[CALLBACK_NAME] = callback

    # Any accidental attempt to reach these names must fail.
    for name in (
        "attack",
        "compile_current",
        "simulate_current",
        "_execute_route_once",
        "signed_tx",
        "send",
        "keypair",
    ):
        isolated[name] = forbidden

    safe = types.FunctionType(
        original.__code__,
        isolated,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )

    if safe is original:
        raise BoundaryHold("FUNCTION_NOT_ISOLATED")

    if safe.__globals__[CALLBACK_NAME] is not callback:
        raise BoundaryHold("CALLBACK_BINDING_FAILED")

    if rt.canonical_price is not original:
        raise BoundaryHold("PRODUCTION_PRICE_MUTATED")

    return safe


def prepare_capture(public_wallet, output_dir):
    if not isinstance(public_wallet, str):
        raise BoundaryHold("PUBLIC_WALLET_REQUIRED")

    try:
        raw = rt.q87.c.b58d(public_wallet)
    except Exception as exc:
        raise BoundaryHold("INVALID_PUBLIC_WALLET") from exc

    if len(raw) != 32:
        raise BoundaryHold("INVALID_PUBLIC_WALLET_LENGTH")

    counters = new_counters()

    callback = capture_callback(
        public_wallet,
        output_dir,
        counters,
    )

    price = make_capture_price(callback)

    return {
        "price": price,
        "callback": callback,
        "counters": counters,
    }


def main():
    result = validate_runtime_boundary()

    print("[MTR168_REVISION]", result["revision"])
    print("[MTR168_CALLBACK]", result["callback"])
    print("[MTR168_SOURCE]", result["source_file"])
    print("[MTR168_SOURCE_LINE]", result["source_line"])
    print("[MTR168_BOUNDARY] PASS")
    print("[LIVE_WEBSOCKET] NOT_STARTED")
    print("[PRODUCTION_RUNTIME] UNMODIFIED")
    print("[SCANNER] UNMODIFIED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")


if __name__ == "__main__":
    main()
