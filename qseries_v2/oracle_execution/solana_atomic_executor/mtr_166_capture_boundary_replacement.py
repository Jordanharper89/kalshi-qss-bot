
"""MTR-166: clean, capture-only callback replacement."""
import json
import time
from pathlib import Path

REVISION = "MTR166_CLEAN_CAPTURE_BOUNDARY"

COUNTER_NAMES = (
    "positive_seen",
    "captured",
    "wrong_direction",
    "wrong_size",
    "route_holds",
    "superseded",
)

def new_counters():
    return {name: 0 for name in COUNTER_NAMES}

def capture_callback(public_user, output_dir, counters):
    """Record a canonical route; never compile, sign, or broadcast."""
    if not isinstance(counters, dict):
        raise TypeError("COUNTERS_MUST_BE_DICTIONARY")

    for name in COUNTER_NAMES:
        counters.setdefault(name, 0)

    def capture(lane, token, snap, opportunity,
                slot, received_ns, generation):

        counters["positive_seen"] += 1

        if lane.newer_waiting(token, generation):
            counters["superseded"] += 1
            return

        if opportunity.get("direction") != "PUMP_TO_METEORA":
            counters["wrong_direction"] += 1
            return

        if int(opportunity.get("start", 0)) != 10000000:
            counters["wrong_size"] += 1
            return

        try:
            from qseries_v2.oracle_execution.solana_atomic_executor import runtime
            from qseries_v2.oracle_execution.solana_atomic_executor.mtr_164_live_route_capture import verify

            route = runtime.same_snapshot_route(
                public_user, snap, opportunity
            )
            evidence = verify(route)

        except Exception as exc:
            counters["route_holds"] += 1
            print(
                "[MTR166_ROUTE_HOLD]",
                type(exc).__name__,
                str(exc)[:100],
                flush=True,
            )
            return

        record = {
            "route": route,
            "token": token,
            "slot": int(slot),
            "captured_at": time.time(),
            "evidence": evidence,
            "protected_bounds_verified": False,
            "atomic_simulation_passed": False,
            "profit_certified": False,
            "broadcast_authorized": False,
        }

        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        destination = output / "mtr_166_captured_route.json"

        destination.write_text(
            json.dumps(record, indent=2, default=str),
            encoding="utf-8",
        )

        counters["captured"] += 1

        print("[MTR166_ROUTE_CAPTURED]", destination)

    return capture


def main():
    counters = new_counters()
    print("[MTR166] CLEAN_CAPTURE_BOUNDARY_READY")
    print("[MTR166_REVISION]", REVISION)
    print("[MTR166_COUNTERS]", json.dumps(counters))
    print("[LIVE_ROUTE] NOT_YET_CAPTURED")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")


if __name__ == "__main__":
    main()
