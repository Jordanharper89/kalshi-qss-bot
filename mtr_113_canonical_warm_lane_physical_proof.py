import json
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_025_single_hydration_exact_live_reuse as q25
)
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core
)

OUT = Path("mtr_113_canonical_warm_lane_physical_proof.json")

def main():
    print("[MTR-113] START", flush=True)
    print("[SCOPE] canonical single-hydration warm WebSocket pricing proof", flush=True)

    # Permanent MTR-080 direction contract must already exist.
    import inspect
    src = inspect.getsource(core.dlmm_quote_snapshot)

    x_ok = "input_mint==meta[\"token_x\"]" in src and "swap_for_y=True" in src
    y_ok = "input_mint==meta[\"token_y\"]" in src and "swap_for_y=False" in src

    print(f"[MTR080_DIRECTION] token_x_to_y={x_ok} token_y_to_x={y_ok}", flush=True)

    if not (x_ok and y_ok):
        raise RuntimeError("CORRECTED_METEORA_DIRECTION_NOT_PRESENT")

    # Existing canonical path:
    # one hydration -> cached state -> existing WS mutation ->
    # latest immutable snapshot -> coalesced exact pricing.
    rc = q25.run(seconds=60.0)

    report_path = Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_020_latest_state_exact_pricing_worker.json"
    )

    if not report_path.exists():
        raise RuntimeError("ORACLE020_REPORT_NOT_FOUND")

    r = json.loads(report_path.read_text(encoding="utf-8"))

    result = {
        "mtr": "MTR-113",
        "corrected_meteora_direction": True,
        "submitted": r.get("submitted"),
        "replaced_before_start": r.get("replaced_before_start"),
        "processed": r.get("processed"),
        "stale_drops": r.get("stale_drops"),
        "scan_replaced": r.get("scan_replaced"),
        "evaluations": r.get("evaluations"),
        "positive": r.get("positive"),
        "p99_event_start_ms": r.get("p99_event_start_ms"),
        "p99_scan_ms": r.get("p99_scan_ms"),
        "best": r.get("best"),
        "execution_authority": False,
        "broadcast": False,
        "private_key_used": False,
        "return_code": rc,
    }

    OUT.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str),
        encoding="utf-8"
    )

    print(
        "[SUMMARY] submitted=%s processed=%s replaced=%s stale=%s "
        "scan_replaced=%s positive=%s p99_start_ms=%s p99_scan_ms=%s"
        % (
            result["submitted"],
            result["processed"],
            result["replaced_before_start"],
            result["stale_drops"],
            result["scan_replaced"],
            result["positive"],
            result["p99_event_start_ms"],
            result["p99_scan_ms"],
        ),
        flush=True,
    )

    if int(result["processed"] or 0) > 0:
        print("[RESULT] CANONICAL_WARM_EVENT_PRICING_PHYSICALLY_ACTIVE", flush=True)
    else:
        print("[RESULT] CANONICAL_WARM_EVENT_PRICING_NOT_OBSERVED", flush=True)

    print(f"[OUTPUT] {OUT}", flush=True)
    print("[PRIVATE_KEY] NOT_USED", flush=True)
    print("[BROADCAST] FALSE", flush=True)
    print("[MTR-113] COMPLETE", flush=True)

if __name__ == "__main__":
    main()
