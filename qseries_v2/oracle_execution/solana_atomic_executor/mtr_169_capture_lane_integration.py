
"""MTR-169: Canonical pricing lane capture integration."""

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_168_fast_live_capture_boundary as m168
)

REVISION = "MTR169_CANONICAL_CAPTURE_LANE"


class IntegrationHold(RuntimeError):
    pass


def make_capture_lane(public_wallet, output_dir):
    """Create an unstarted, capture-only canonical pricing lane."""

    m168.validate_runtime_boundary()

    prepared = m168.prepare_capture(
        public_wallet,
        output_dir,
    )

    lane = rt.q20.LatestStateLane()

    safe_price = prepared["price"]

    if safe_price.__globals__.get("fast_live_attack") is not prepared["callback"]:
        raise IntegrationHold("CAPTURE_CALLBACK_NOT_BOUND")

    if safe_price.__globals__.get("compile_current") is not m168.forbidden:
        raise IntegrationHold("COMPILATION_GUARD_MISSING")

    if safe_price.__globals__.get("simulate_current") is not m168.forbidden:
        raise IntegrationHold("SIMULATION_GUARD_MISSING")

    lane._price = safe_price.__get__(
        lane,
        rt.q20.LatestStateLane,
    )

    if lane._price.__func__ is not safe_price:
        raise IntegrationHold("LANE_BINDING_FAILED")

    if lane._price.__self__ is not lane:
        raise IntegrationHold("LANE_INSTANCE_MISMATCH")

    return {
        "lane": lane,
        "callback": prepared["callback"],
        "counters": prepared["counters"],
        "safe_price": safe_price,
    }


def verify_lane(public_wallet, output_dir):
    original_price = rt.canonical_price
    original_attack = rt.fast_live_attack

    result = make_capture_lane(
        public_wallet,
        output_dir,
    )

    if rt.canonical_price is not original_price:
        raise IntegrationHold("PRODUCTION_PRICE_MUTATED")

    if rt.fast_live_attack is not original_attack:
        raise IntegrationHold("PRODUCTION_ATTACK_MUTATED")

    return result


def main():
    wallet = "11111111111111111111111111111111"

    result = verify_lane(
        wallet,
        "runtime_state/oracle/oracle_live_execution",
    )

    print("[MTR169_REVISION]", REVISION)
    print("[MTR169_LANE]", type(result["lane"]).__name__)
    print("[MTR169_CALLBACK]", "fast_live_attack")
    print("[MTR169_BINDING] PASS")
    print("[MTR169_CAPTURE_COUNTERS]", result["counters"])
    print("[LIVE_WEBSOCKET] NOT_STARTED")
    print("[PRODUCTION_RUNTIME] UNMODIFIED")
    print("[SCANNER] UNMODIFIED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")


if __name__ == "__main__":
    main()
