
"""MTR-172: isolated market-state startup, execution prohibited."""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

REVISION = "MTR172_ISOLATED_MARKET_STARTUP"
SECRET_NAMES = (
    "QSB_SOLANA_PRIVATE_KEY",
    "SOLANA_PRIVATE_KEY",
    "SOLANA_KEYPAIR",
    "WALLET_PRIVATE_KEY",
)

class StartupHold(RuntimeError):
    pass

def clean_environment(source):
    env = dict(source)
    for name in list(env):
        upper = name.upper()
        if name in SECRET_NAMES or (
            "PRIVATE" in upper and "KEY" in upper
        ) or "SEED_PHRASE" in upper or "MNEMONIC" in upper:
            env.pop(name, None)
    return env

def verify_transport():
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        mtr_168_fast_live_capture_boundary as m168
    )
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        mtr_169_capture_lane_integration as m169
    )

    if not asyncio.iscoroutinefunction(rt.serve_canonical):
        raise StartupHold("CANONICAL_TRANSPORT_NOT_ASYNC")

    if set(("process_event", "_coherence_flush")) - set(
        rt.serve_canonical.__code__.co_names
    ):
        raise StartupHold("TRANSPORT_EVENT_PATH_CHANGED")

    if "fast_live_attack" not in rt.canonical_price.__code__.co_names:
        raise StartupHold("PRICING_CALLBACK_CHANGED")

    m168.validate_runtime_boundary()

    if not callable(m169.make_capture_lane):
        raise StartupHold("CAPTURE_LANE_UNAVAILABLE")

    return rt

def child_probe():
    if any(k in os.environ for k in SECRET_NAMES):
        raise StartupHold("SECRET_ENVIRONMENT_NOT_ISOLATED")

    rt = verify_transport()
    root = Path.cwd()

    state, cap = rt.q25.prepare_once(root)

    pairs = list(state.get("pairs") or [])
    addresses = list(state.get("addresses") or [])

    if not pairs:
        raise StartupHold("NO_HYDRATED_PAIRS")

    rt.q25.bind_cached_state(state)

    report = {
        "revision": REVISION,
        "status": "HYDRATED",
        "pairs": len(pairs),
        "watched_addresses": len(addresses),
        "transport": "serve_canonical",
        "pricing_callback": "fast_live_attack",
        "capture_lane": "MTR169",
        "live_websocket_started": False,
        "template_construction_started": False,
        "signing_performed": False,
        "broadcast_performed": False,
        "atomic_transaction_proven": False,
        "capture_ready_for_live": False,
    }

    output = (
        root / "runtime_state/oracle/oracle_live_execution"
        / "mtr_172_startup_report.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[MTR172_STATUS] HYDRATED")
    print("[MTR172_PAIRS]", len(pairs))
    print("[MTR172_WATCHED_ADDRESSES]", len(addresses))
    print("[MTR172_REPORT]", output)
    print("[MTR172_CAPTURE_LANE] VERIFIED")
    print("[LIVE_WEBSOCKET] NOT_STARTED")
    print("[TRANSACTION_SIGNING] NOT_STARTED")
    print("[TRANSACTION_BROADCAST] NOT_STARTED")
    return 0

def parent_probe():
    env = clean_environment(os.environ)
    cmd = [
        sys.executable,
        "-m",
        "qseries_v2.oracle_execution.solana_atomic_executor."
        "mtr_172_isolated_market_startup",
        "--isolated-child",
    ]

    print("[MTR172] STARTING_ISOLATED_PROBE", flush=True)
    result = subprocess.run(
        cmd,
        env=env,
        cwd=str(Path.cwd()),
        check=False,
        timeout=120,
    )
    if result.returncode:
        raise StartupHold(
            "ISOLATED_PROBE_FAILED_CODE_" + str(result.returncode)
        )
    print("[MTR172] ISOLATED_STARTUP_PASS")
    print("[LIVE_CAPTURE] HOLD_PENDING_EXECUTION_ISOLATION")
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--isolated-child", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    if args.live:
        raise StartupHold("LIVE_NOT_AUTHORIZED_BY_MTR172")

    if args.isolated_child:
        return child_probe()

    return parent_probe()

if __name__ == "__main__":
    raise SystemExit(main())
