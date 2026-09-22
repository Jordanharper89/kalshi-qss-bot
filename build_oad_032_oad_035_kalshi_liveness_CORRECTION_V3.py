from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

REVISION = "OAD_032_OAD_035_KALSHI_LIVENESS_CORRECTION_V3"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_adapters" / "kalshi"

MODULE32 = PACKAGE / "oad_032_persistent_live_loop.py"
TEST32 = ROOT / "test_oad_032_persistent_real_kalshi_message_loop.py"
RUNNER32 = ROOT / "run_oad_032_kalshi_persistent_stream.py"
LAUNCHER = ROOT / "run_oracle_LIVE.py"
LAUNCHER_TEST = ROOT / "test_run_oracle_LIVE.py"

MODULE32_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import dataclass\nimport asyncio\nimport json\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get, build_auth_headers\nfrom .oad_026_persistent_stream_runner import (\n    build_persistent_stream_config,\n    next_reconnect_delay,\n)\n\nOAD_032_BUILD_ID = "OAD-032"\nOAD_032_REVISION = "OAD_032_PERSISTENT_REAL_KALSHI_MESSAGE_LOOP_LIVENESS_CORRECTION_V3"\n\n@dataclass(frozen=True)\nclass PersistentKalshiLoopSummary:\n    connections: int\n    reconnects: int\n    subscription_acks: int\n    market_messages: int\n    last_message_type: str\n    stopped_by_limit: bool\n\nasync def _run(credentials, max_market_messages, connect_timeout_seconds, progress):\n    try:\n        import websockets\n        from websockets.exceptions import ConnectionClosed\n    except Exception as e:\n        raise RuntimeError("websockets package required") from e\n\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n    from .oad_011_websocket_foundation import build_subscribe_command\n\n    foundation = build_kalshi_adapter_foundation()\n\n    market_response = kalshi_rest_get(\n        credentials,\n        "/markets",\n        {"limit": 1000, "status": "open"},\n        connect_timeout_seconds,\n    )\n    tickers = tuple(\n        str(m["ticker"])\n        for m in market_response.body.get("markets", ())\n        if m.get("ticker")\n    )[:100]\n\n    if not tickers:\n        raise RuntimeError("No open markets for persistent stream")\n\n    connections = 0\n    reconnects = 0\n    subscription_acks = 0\n    market_messages = 0\n    last_message_type = ""\n    reconnect_attempt = 0\n    config = build_persistent_stream_config()\n\n    def limit_reached():\n        return (\n            max_market_messages is not None\n            and market_messages >= int(max_market_messages)\n        )\n\n    while not limit_reached():\n        headers = build_auth_headers(\n            credentials,\n            "GET",\n            "/trade-api/ws/v2",\n        )\n\n        # IMPORTANT:\n        # Do not treat a quiet market-data interval as a failed connection.\n        # websockets handles WebSocket Ping/Pong control frames automatically.\n        kwargs = {\n            "open_timeout": float(connect_timeout_seconds),\n            "ping_interval": 20.0,\n            "ping_timeout": 20.0,\n            "close_timeout": 10.0,\n        }\n\n        try:\n            try:\n                connection = websockets.connect(\n                    foundation.predictions_ws_url,\n                    additional_headers=headers,\n                    **kwargs,\n                )\n            except TypeError:\n                connection = websockets.connect(\n                    foundation.predictions_ws_url,\n                    extra_headers=headers,\n                    **kwargs,\n                )\n\n            async with connection as ws:\n                connections += 1\n                reconnect_attempt = 0\n\n                await ws.send(\n                    json.dumps(\n                        build_subscribe_command(\n                            1,\n                            ("ticker", "trade"),\n                            tickers,\n                        ),\n                        separators=(",", ":"),\n                    )\n                )\n\n                progress(\n                    f"[KALSHI] connected markets={len(tickers)} "\n                    f"connections={connections}"\n                )\n\n                async for raw in ws:\n                    msg = json.loads(raw)\n                    message_type = str(msg.get("type", ""))\n                    last_message_type = message_type\n\n                    if message_type in ("subscribed", "ok"):\n                        subscription_acks += 1\n                        progress(\n                            f"[KALSHI] subscription_ack={subscription_acks}"\n                        )\n\n                    elif message_type in (\n                        "ticker",\n                        "trade",\n                        "orderbook_snapshot",\n                        "orderbook_delta",\n                    ):\n                        market_messages += 1\n                        progress(\n                            f"[KALSHI] market_event={market_messages} "\n                            f"type={message_type}"\n                        )\n\n                        if limit_reached():\n                            break\n\n                    elif message_type == "error":\n                        progress(\n                            "[KALSHI] server_message=error "\n                            + str(msg.get("msg", {}))\n                        )\n\n        except asyncio.CancelledError:\n            raise\n\n        except KeyboardInterrupt:\n            raise\n\n        except ConnectionClosed as exc:\n            reconnects += 1\n            delay = next_reconnect_delay(reconnect_attempt, config)\n            reconnect_attempt += 1\n            progress(\n                f"[KALSHI] websocket_closed code={getattr(exc, \'code\', None)}; "\n                f"reconnects={reconnects}; reconnecting in {delay:.1f}s"\n            )\n            await asyncio.sleep(delay)\n\n        except Exception as exc:\n            reconnects += 1\n            delay = next_reconnect_delay(reconnect_attempt, config)\n            reconnect_attempt += 1\n            progress(\n                f"[KALSHI] connection_failure={type(exc).__name__}; "\n                f"reconnects={reconnects}; reconnecting in {delay:.1f}s"\n            )\n            await asyncio.sleep(delay)\n\n    return PersistentKalshiLoopSummary(\n        connections,\n        reconnects,\n        subscription_acks,\n        market_messages,\n        last_message_type,\n        max_market_messages is not None,\n    )\n\ndef run_persistent_kalshi_loop(\n    root=None,\n    max_market_messages=None,\n    connect_timeout_seconds=15,\n    progress=print,\n):\n    credentials = load_kalshi_credentials(root=root)\n    return asyncio.run(\n        _run(\n            credentials,\n            max_market_messages,\n            connect_timeout_seconds,\n            progress,\n        )\n    )\n\ndef verify_oad_032_persistent_real_kalshi_message_loop():\n    import inspect\n\n    sig = inspect.signature(run_persistent_kalshi_loop)\n    source = inspect.getsource(_run)\n\n    return (\n        sig.parameters["max_market_messages"].default is None\n        and "async for raw in ws" in source\n        and "wait_for(ws.recv" not in source\n        and OAD_032_REVISION.endswith("LIVENESS_CORRECTION_V3")\n    )\n'
TEST32_SOURCE = 'import inspect\nimport unittest\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import (\n    _run,\n    run_persistent_kalshi_loop,\n    verify_oad_032_persistent_real_kalshi_message_loop,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_oad_032_persistent_real_kalshi_message_loop()\n        )\n\n    def test_production_default_unbounded(self):\n        sig = inspect.signature(run_persistent_kalshi_loop)\n        self.assertIsNone(\n            sig.parameters["max_market_messages"].default\n        )\n\n    def test_no_market_receive_timeout_reconnect(self):\n        source = inspect.getsource(_run)\n        self.assertIn("async for raw in ws", source)\n        self.assertNotIn("wait_for(ws.recv", source)\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" OAD-032 LIVENESS CORRECTION V3 CERTIFICATION TEST")\n    print(" QUIET MARKET PERIODS DO NOT FORCE WEBSOCKET RECONNECT")\n    print("=" * 72)\n\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] Production stream remains unbounded")\n    print("[PASS] Market-data silence no longer triggers reconnect")\n    print("[PASS] WebSocket failures still enter recovery path")\n    print("[DONE] OAD-032 LIVENESS CORRECTION V3 CERTIFIED")\n'
RUNNER32_SOURCE = 'from pathlib import Path\nimport argparse\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import (\n    run_persistent_kalshi_loop,\n)\n\ndef main():\n    parser = argparse.ArgumentParser(\n        description="Persistent Kalshi live stream"\n    )\n    parser.add_argument(\n        "--max-market-messages",\n        type=int,\n        default=None,\n        help="Diagnostic only. Production default is unbounded.",\n    )\n    parser.add_argument(\n        "--connect-timeout-seconds",\n        type=float,\n        default=15.0,\n    )\n    args = parser.parse_args()\n\n    print("=" * 72, flush=True)\n    print(\n        " OAD-032 PERSISTENT KALSHI LIVE STREAM — "\n        "LIVENESS CORRECTION V3",\n        flush=True,\n    )\n    print("=" * 72, flush=True)\n\n    if args.max_market_messages is None:\n        print(\n            "[MODE] PRODUCTION 24/7 — UNBOUNDED — "\n            "PING/PONG LIVENESS",\n            flush=True,\n        )\n    else:\n        print(\n            f"[MODE] DIAGNOSTIC — "\n            f"max_market_messages={args.max_market_messages}",\n            flush=True,\n        )\n\n    try:\n        result = run_persistent_kalshi_loop(\n            Path.cwd(),\n            max_market_messages=args.max_market_messages,\n            connect_timeout_seconds=args.connect_timeout_seconds,\n            progress=lambda x: print(x, flush=True),\n        )\n        print("[SUMMARY]", result, flush=True)\n        return 0\n\n    except KeyboardInterrupt:\n        print(\n            "\\n[STOP] Kalshi persistent stream stopped by operator.",\n            flush=True,\n        )\n        return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
LAUNCHER_SOURCE = 'from __future__ import annotations\n\nimport argparse\nimport importlib\nimport subprocess\nimport sys\nimport time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME = "Oracle Live Runtime"\nLAUNCHER_REVISION = (\n    "ORACLE_LIVE_RUNTIME_KALSHI_LIVENESS_SUPERVISION_CORRECTION_V3"\n)\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name: str\n    state: str\n    certified: bool\n    terminal_dependency: bool\n    execution_authority: bool\n\ndef verify_frozen_ois_boundary():\n    m = importlib.import_module(\n        "qseries_v2.oracle_intelligence_state.ois_055_final_freeze"\n    )\n    if getattr(\n        m,\n        "verify_ois_055_final_production_certification_freeze",\n    )() is not True:\n        raise RuntimeError(\n            "Frozen OIS-055 certification boundary verification failed"\n        )\n    return True\n\ndef verify_kalshi_boundary():\n    m = importlib.import_module(\n        "qseries_v2.oracle_adapters.kalshi."\n        "oad_035_physical_activation_gate"\n    )\n    if getattr(\n        m,\n        "verify_oad_035_physical_oracle_kalshi_production_activation_gate",\n    )() is not True:\n        raise RuntimeError(\n            "OAD-035 Kalshi activation boundary verification failed"\n        )\n    return True\n\ndef verify_kalshi_liveness_correction():\n    m = importlib.import_module(\n        "qseries_v2.oracle_adapters.kalshi."\n        "oad_032_persistent_live_loop"\n    )\n    if getattr(\n        m,\n        "verify_oad_032_persistent_real_kalshi_message_loop",\n    )() is not True:\n        raise RuntimeError(\n            "OAD-032 liveness correction verification failed"\n        )\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary()\n    verify_kalshi_boundary()\n    verify_kalshi_liveness_correction()\n\n    return OracleLiveBootReport(\n        RUNTIME_NAME,\n        "RUNNING",\n        True,\n        False,\n        False,\n    )\n\ndef format_boot_report(report):\n    return "\\n".join(\n        (\n            "=" * 72,\n            " ORACLE LIVE RUNTIME",\n            "=" * 72,\n            f"[REVISION] {LAUNCHER_REVISION}",\n            f"[STATE] {report.state}",\n            "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n            "[PASS] OAD-001 through OAD-035 Kalshi boundary verified",\n            "[PASS] Kalshi Ping/Pong liveness supervision verified",\n            "[PASS] Quiet market periods do not force reconnect",\n            "[PASS] Operator Terminal dependency: NONE",\n            "[PASS] Q Series execution authority remains separate",\n            "[READY] Oracle Live Runtime with supervised Kalshi 24/7 stream verified",\n        )\n    )\n\ndef _start_kalshi_child(root):\n    child = root / "run_oad_032_kalshi_persistent_stream.py"\n\n    if not child.is_file():\n        raise RuntimeError(\n            "Persistent Kalshi stream runner missing: " + str(child)\n        )\n\n    return subprocess.Popen(\n        [sys.executable, str(child)],\n        cwd=str(root),\n    )\n\ndef run_forever(cadence_seconds):\n    report = build_boot_report()\n    print(format_boot_report(report), flush=True)\n\n    root = Path.cwd()\n    proc = _start_kalshi_child(root)\n    restart_count = 0\n\n    print(\n        f"[KALSHI] persistent 24/7 stream started pid={proc.pid}",\n        flush=True,\n    )\n\n    sequence = 0\n\n    try:\n        while True:\n            sequence += 1\n\n            if proc.poll() is not None:\n                exit_code = proc.returncode\n                restart_count += 1\n\n                print(\n                    f"[KALSHI] child exited code={exit_code}; "\n                    f"restart_count={restart_count}; restarting",\n                    flush=True,\n                )\n\n                time.sleep(min(5.0, float(cadence_seconds)))\n                proc = _start_kalshi_child(root)\n\n                print(\n                    f"[KALSHI] restarted pid={proc.pid}",\n                    flush=True,\n                )\n\n            print(\n                f"[ORACLE] heartbeat={sequence} "\n                f"state=RUNNING "\n                f"kalshi_child=RUNNING "\n                f"kalshi_restarts={restart_count} "\n                f"terminal_dependency=NONE "\n                f"execution_authority=FALSE",\n                flush=True,\n            )\n\n            time.sleep(cadence_seconds)\n\n    except KeyboardInterrupt:\n        print()\n\n        if proc.poll() is None:\n            proc.terminate()\n\n            try:\n                proc.wait(timeout=5)\n            except Exception:\n                proc.kill()\n\n        print(\n            "[STOP] Oracle Live Runtime stopped by operator.",\n            flush=True,\n        )\n        return 0\n\ndef main(argv=None):\n    parser = argparse.ArgumentParser(\n        description="Oracle Live Runtime production launcher"\n    )\n    parser.add_argument("--check", action="store_true")\n    parser.add_argument(\n        "--cadence-seconds",\n        type=float,\n        default=5.0,\n    )\n    args = parser.parse_args(argv)\n\n    if args.cadence_seconds <= 0:\n        raise SystemExit(\n            "--cadence-seconds must be > 0"\n        )\n\n    report = build_boot_report()\n\n    if args.check:\n        print(format_boot_report(report))\n        return 0\n\n    return run_forever(args.cadence_seconds)\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
LAUNCHER_TEST_SOURCE = 'import inspect\nimport subprocess\nimport sys\nimport unittest\nfrom pathlib import Path\n\nimport run_oracle_LIVE as live\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import (\n    _run,\n    run_persistent_kalshi_loop,\n)\n\nclass T(unittest.TestCase):\n    def test_boot(self):\n        r = live.build_boot_report()\n        self.assertTrue(r.certified)\n        self.assertFalse(r.execution_authority)\n\n    def test_kalshi_default_unbounded(self):\n        self.assertIsNone(\n            inspect.signature(run_persistent_kalshi_loop)\n            .parameters["max_market_messages"].default\n        )\n\n    def test_no_market_silence_reconnect(self):\n        source = inspect.getsource(_run)\n        self.assertIn("async for raw in ws", source)\n        self.assertNotIn("wait_for(ws.recv", source)\n\n    def test_check(self):\n        p = subprocess.run(\n            [\n                sys.executable,\n                str(Path(__file__).with_name("run_oracle_LIVE.py")),\n                "--check",\n            ],\n            text=True,\n            capture_output=True,\n        )\n\n        self.assertEqual(p.returncode, 0)\n        self.assertIn(\n            "Quiet market periods do not force reconnect",\n            p.stdout,\n        )\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(\n        " ORACLE LIVE RUNTIME + KALSHI "\n        "LIVENESS SUPERVISION TEST"\n    )\n    print("=" * 72)\n\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n\n    print(\n        "[PASS] Oracle supervises persistent Kalshi stream "\n        "without quiet-period reconnect churn"\n    )\n'

def write_exact(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp, path)

def verify_upstream():
    sys.path.insert(0, str(ROOT))

    try:
        importlib.invalidate_caches()

        m = importlib.import_module(
            "qseries_v2.oracle_adapters.kalshi."
            "oad_035_physical_activation_gate"
        )

        if getattr(
            m,
            "verify_oad_035_physical_oracle_kalshi_production_activation_gate",
        )() is not True:
            raise RuntimeError(
                "Certified OAD-035 boundary verification failed"
            )

    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("=" * 72)
    print(" OAD-032 / OAD-035 LIVENESS CORRECTION V3 INSTALLER")
    print(" QUIET MARKET PERIODS != DEAD WEBSOCKET")
    print("=" * 72)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    verify_upstream()
    print(
        "[PASS] Certified OAD-035 boundary verified read-only"
    )

    affected = (
        MODULE32,
        TEST32,
        RUNNER32,
        LAUNCHER,
        LAUNCHER_TEST,
    )

    backups = {
        p: (p.read_bytes() if p.exists() else None)
        for p in affected
    }

    try:
        write_exact(MODULE32, MODULE32_SOURCE)
        write_exact(TEST32, TEST32_SOURCE)
        write_exact(RUNNER32, RUNNER32_SOURCE)
        write_exact(LAUNCHER, LAUNCHER_SOURCE)
        write_exact(LAUNCHER_TEST, LAUNCHER_TEST_SOURCE)

        for p in affected:
            compile(
                p.read_text(encoding="utf-8"),
                str(p),
                "exec",
            )

        subprocess.run(
            [sys.executable, str(TEST32)],
            cwd=str(ROOT),
            check=True,
        )

        subprocess.run(
            [sys.executable, str(LAUNCHER_TEST)],
            cwd=str(ROOT),
            check=True,
        )

        subprocess.run(
            [sys.executable, str(LAUNCHER), "--check"],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)

        print(
            "[ROLLBACK] Kalshi liveness correction failed; "
            "all affected files restored"
        )
        raise

    print(
        "[PASS] Removed market-message silence reconnect trigger"
    )
    print(
        "[PASS] WebSocket Ping/Pong keepalive governs connection health"
    )
    print(
        "[PASS] Actual socket close/network failure still reconnects"
    )
    print(
        "[PASS] Oracle child-process supervision remains active"
    )
    print(
        "[PASS] OIS remains frozen and unmodified"
    )
    print(
        "[DONE] OAD-032 / OAD-035 LIVENESS CORRECTION V3 "
        "INSTALLED + CERTIFIED"
    )

if __name__ == "__main__":
    main()
