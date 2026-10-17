from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"

MODULE = r'''
"""MTR-173: bounded live market capture; no trade authority."""
import argparse
import asyncio
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_169_capture_lane_integration as m169
)

REVISION = "MTR173_LIVE_CAPTURE_ONLY"
SECRET_MARKERS = (
    "PRIVATE_KEY", "SECRET_KEY", "KEYPAIR",
    "SEED_PHRASE", "MNEMONIC",
)

class CaptureHold(RuntimeError):
    pass

def sensitive(name):
    name = name.upper()
    return any(x in name for x in SECRET_MARKERS)

def clean_environment(source):
    return {
        key: value for key, value in source.items()
        if not sensitive(key)
    }

def denied(*args, **kwargs):
    raise CaptureHold("TRANSACTION_EXECUTION_DENIED")

def protect_rpc():
    """Deny known JSON-RPC transaction submission methods."""
    import urllib.request

    def forbidden_payload(value):
        if isinstance(value, bytes):
            value = value.decode("utf-8", "ignore")
        if isinstance(value, dict):
            if value.get("method") in (
                "sendTransaction", "sendRawTransaction",
                "requestAirdrop",
            ):
                return True
            return any(forbidden_payload(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return any(forbidden_payload(v) for v in value)
        if isinstance(value, str):
            return any(
                x in value for x in (
                    '"method":"sendTransaction"',
                    '"method": "sendTransaction"',
                    '"method":"sendRawTransaction"',
                    '"method": "sendRawTransaction"',
                    '"method":"requestAirdrop"',
                    '"method": "requestAirdrop"',
                )
            )
        return False

    original_urlopen = urllib.request.urlopen

    def safe_urlopen(url, *args, **kwargs):
        data = getattr(url, "data", None)
        if data is None:
            data = kwargs.get("data")
        if forbidden_payload(data):
            raise CaptureHold("BROADCAST_RPC_BLOCKED")
        return original_urlopen(url, *args, **kwargs)

    urllib.request.urlopen = safe_urlopen

    try:
        import requests
        original_request = requests.sessions.Session.request

        def safe_request(self, method, url, **kwargs):
            if forbidden_payload(kwargs.get("json")) or forbidden_payload(
                kwargs.get("data")
            ):
                raise CaptureHold("BROADCAST_RPC_BLOCKED")
            return original_request(self, method, url, **kwargs)

        requests.sessions.Session.request = safe_request
    except ImportError:
        pass

    for name in (
        "sim_identity", "signed_tx",
        "send_transaction", "send_raw_transaction",
    ):
        target = getattr(rt.q87.c, name, None)
        if callable(target):
            setattr(rt.q87.c, name, denied)

    for name in ("fast_live_attack", "attack"):
        if callable(getattr(rt, name, None)):
            setattr(rt, name, denied)

def signature_matches(source, replacement):
    s = inspect.signature(source)
    r = inspect.signature(replacement)

    def count(sig):
        return len([
            p for p in sig.parameters.values()
            if p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ) and p.default is inspect.Parameter.empty
        ])

    return count(s) == count(r)

def validate(public_wallet):
    if any(sensitive(key) for key in os.environ):
        raise CaptureHold("CHILD_SECRET_ENV_PRESENT")

    if not (5 <= len(public_wallet) <= 60):
        raise CaptureHold("INVALID_PUBLIC_WALLET")

    try:
        if len(rt.q87.c.b58d(public_wallet)) != 32:
            raise CaptureHold("INVALID_PUBLIC_WALLET")
    except Exception as exc:
        raise CaptureHold("INVALID_PUBLIC_WALLET") from exc

    if not inspect.iscoroutinefunction(rt.serve_canonical):
        raise CaptureHold("CANONICAL_TRANSPORT_CHANGED")

    transport = set(rt.serve_canonical.__code__.co_names)
    if not {"process_event", "_coherence_flush"} <= transport:
        raise CaptureHold("CANONICAL_EVENT_PIPELINE_CHANGED")

    if "fast_live_attack" not in rt.canonical_price.__code__.co_names:
        raise CaptureHold("CANONICAL_CALLBACK_CHANGED")

def counters_snapshot(result):
    return {
        k: int(v)
        for k, v in result["counters"].items()
        if isinstance(v, (int, float))
    }

def capture_child(seconds, public_wallet, output_dir):
    validate(public_wallet)
    if not 5 <= seconds <= 90:
        raise CaptureHold("INVALID_OBSERVATION_DURATION")

    original_attack = rt.fast_live_attack
    prepared = m169.verify_lane(public_wallet, output_dir)

    if not signature_matches(
        original_attack, prepared["callback"]
    ):
        raise CaptureHold("CAPTURE_CALLBACK_SIGNATURE_MISMATCH")

    if prepared["safe_price"].__globals__.get(
        "fast_live_attack"
    ) is not prepared["callback"]:
        raise CaptureHold("CAPTURE_PRICE_BINDING_MISSING")

    protect_rpc()

    root = Path.cwd()
    report_path = (
        root / "runtime_state/oracle/oracle_live_execution"
        / "mtr_173_capture_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "revision": REVISION,
        "status": "STARTING",
        "pairs": 0,
        "watched_addresses": 0,
        "ready_tokens": 0,
        "processed": 0,
        "positives": 0,
        "captured": 0,
        "live_canary_sent": False,
        "atomic_profit_verified": False,
        "hold_reason": None,
    }

    lane = prepared["lane"]

    try:
        state, cap = rt.q25.prepare_once(root)
        rt.q25.bind_cached_state(state)

        report["pairs"] = len(state.get("pairs") or [])
        report["watched_addresses"] = len(
            state.get("addresses") or []
        )

        print("[MTR173_PAIRS]", report["pairs"], flush=True)
        print(
            "[MTR173_WATCHED_ADDRESSES]",
            report["watched_addresses"],
            flush=True,
        )

        # Only the supplied public address is used for templates.
        rt.USER = public_wallet

        warmed = rt.install_proven_hot_math(state)

        pump_count = rt.prebuild_templates(
            state, public_wallet
        )
        meteora_count = rt.prebuild_meteora_templates(
            state, public_wallet, warmed
        )
        sell_count = rt.prebuild_sell_templates(
            state, public_wallet
        )

        report["pump_templates"] = pump_count
        report["meteora_templates"] = meteora_count
        report["sell_templates"] = sell_count

        report["ready_tokens"] = len(rt.READY_TOKENS)

        if not report["ready_tokens"]:
            raise CaptureHold("ZERO_READY_TOKENS")

        print(
            "[MTR173_READY_TOKENS]",
            report["ready_tokens"],
            flush=True,
        )

        # The lane points to the isolated capture callback.
        if lane._price.__func__ is not prepared["safe_price"]:
            raise CaptureHold("CAPTURE_LANE_REPLACED")

        lane.start()

        print("[MTR173_WEBSOCKET] STARTING", flush=True)
        print("[MTR173_SECONDS]", seconds, flush=True)

        asyncio.run(
            rt.serve_canonical(state, float(seconds), lane)
        )

        report["status"] = "OBSERVATION_COMPLETED"

    except Exception as exc:
        report["status"] = "HOLD"
        report["hold_reason"] = (
            type(exc).__name__ + ":" + str(exc)
        )
        print(
            "[MTR173_HOLD]", report["hold_reason"],
            flush=True,
        )

    finally:
        report["processed"] = int(
            getattr(lane, "processed", 0)
        )
        report["positives"] = int(
            getattr(lane, "positive", 0)
        )
        report["submitted"] = int(
            getattr(lane, "submitted", 0)
        )
        report["replaced"] = int(
            getattr(lane, "replaced", 0)
        )
        report["capture_counters"] = counters_snapshot(
            prepared
        )
        report["captured"] = report[
            "capture_counters"
        ].get("captured", 0)

        report_path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8",
        )

        print(
            "[MTR173_REPORT]", report_path,
            flush=True,
        )
        print(
            "[MTR173_PROCESSED]",
            report["processed"], flush=True,
        )
        print(
            "[MTR173_POSITIVES]",
            report["positives"], flush=True,
        )
        print(
            "[MTR173_CAPTURED]",
            report["captured"], flush=True,
        )
        print(
            "[MTR173_CAPTURE_COUNTERS]",
            json.dumps(report["capture_counters"]),
            flush=True,
        )
        print("[CANARY_SENT] FALSE", flush=True)
        print("[ATOMIC_PROFIT_VERIFIED] FALSE", flush=True)

    if report["status"] == "HOLD":
        return 2
    return 0

def launch(seconds, public_wallet, output_dir):
    if not public_wallet:
        raise CaptureHold("PUBLIC_WALLET_REQUIRED")
    if not 5 <= seconds <= 90:
        raise CaptureHold("DURATION_OUT_OF_RANGE")

    env = clean_environment(os.environ)
    cmd = [
        sys.executable,
        "-m",
        "qseries_v2.oracle_execution.solana_atomic_executor."
        "mtr_173_live_capture_activation",
        "--isolated-child",
        "--seconds", str(seconds),
        "--public-wallet", public_wallet,
        "--output-dir", str(output_dir),
    ]

    print("[MTR173] ISOLATED_LIVE_CAPTURE", flush=True)
    print("[MTR173] NO_SIGNING_CREDENTIALS_PASSED", flush=True)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(Path.cwd()),
            env=env,
            timeout=seconds + 180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CaptureHold(
            "ISOLATED_CAPTURE_TIMEOUT"
        ) from exc

    if result.returncode:
        raise CaptureHold(
            "CAPTURE_CHILD_EXIT_" + str(result.returncode)
        )

    return 0

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--isolated-child", action="store_true")
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--public-wallet")
    parser.add_argument(
        "--output-dir",
        default="runtime_state/oracle/oracle_live_execution",
    )
    args = parser.parse_args(argv)

    if args.isolated_child:
        if not args.public_wallet:
            raise CaptureHold("PUBLIC_WALLET_REQUIRED")
        return capture_child(
            args.seconds, args.public_wallet, args.output_dir
        )

    if not args.live:
        print("[MTR173_REVISION]", REVISION)
        print("[MTR173_STATUS] INSTALLED")
        print("[LIVE_WEBSOCKET] NOT_STARTED")
        print("[SIGNING] DISABLED")
        print("[BROADCAST] DISABLED")
        return 0

    return launch(
        args.seconds, args.public_wallet, args.output_dir
    )

if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST = r'''
import inspect
import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_173_live_capture_activation as m
)


class Tests(unittest.TestCase):

    def test_secret_environment_scrub(self):
        env = m.clean_environment({
            "QSB_SOLANA_PRIVATE_KEY": "example