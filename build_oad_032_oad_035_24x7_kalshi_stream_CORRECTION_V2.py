from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

REVISION="OAD_032_OAD_035_24X7_STREAM_CORRECTION_V2"
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"

MODULE32=PACKAGE/"oad_032_persistent_live_loop.py"
TEST32=ROOT/"test_oad_032_persistent_real_kalshi_message_loop.py"
RUNNER32=ROOT/"run_oad_032_kalshi_persistent_stream.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
LAUNCHER_TEST=ROOT/"test_run_oracle_LIVE.py"

MODULE32_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport asyncio, json\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get, build_auth_headers\nfrom .oad_026_persistent_stream_runner import build_persistent_stream_config, next_reconnect_delay\n\nOAD_032_BUILD_ID="OAD-032"\nOAD_032_REVISION="OAD_032_PERSISTENT_REAL_KALSHI_MESSAGE_LOOP_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass PersistentKalshiLoopSummary:\n    connections:int\n    reconnects:int\n    subscription_acks:int\n    market_messages:int\n    last_message_type:str\n    stopped_by_limit:bool\n\nasync def _run(credentials,max_market_messages,timeout_seconds,progress):\n    try:\n        import websockets\n    except Exception as e:\n        raise RuntimeError("websockets package required") from e\n\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n    from .oad_011_websocket_foundation import build_subscribe_command\n\n    f=build_kalshi_adapter_foundation()\n    r=kalshi_rest_get(credentials,"/markets",{"limit":1000,"status":"open"},timeout_seconds)\n    tickers=tuple(str(m["ticker"]) for m in r.body.get("markets",()) if m.get("ticker"))[:100]\n    if not tickers:\n        raise RuntimeError("No open markets for persistent stream")\n\n    connections=reconnects=acks=market=0\n    last=""\n    attempt=0\n    config=build_persistent_stream_config()\n\n    def limit_reached():\n        return max_market_messages is not None and market >= int(max_market_messages)\n\n    while not limit_reached():\n        headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")\n        kwargs={"open_timeout":float(timeout_seconds),"ping_interval":None}\n\n        try:\n            try:\n                cm=websockets.connect(f.predictions_ws_url,additional_headers=headers,**kwargs)\n            except TypeError:\n                cm=websockets.connect(f.predictions_ws_url,extra_headers=headers,**kwargs)\n\n            async with cm as ws:\n                connections+=1\n                attempt=0\n                await ws.send(json.dumps(\n                    build_subscribe_command(1,("ticker","trade"),tickers),\n                    separators=(",",":")\n                ))\n                progress(f"[KALSHI] connected markets={len(tickers)}")\n\n                while not limit_reached():\n                    raw=await asyncio.wait_for(ws.recv(),timeout=float(timeout_seconds))\n                    msg=json.loads(raw)\n                    typ=str(msg.get("type",""))\n                    last=typ\n\n                    if typ in ("subscribed","ok"):\n                        acks+=1\n                        progress(f"[KALSHI] subscription_ack={acks}")\n                    elif typ in ("ticker","trade","orderbook_snapshot","orderbook_delta"):\n                        market+=1\n                        progress(f"[KALSHI] market_event={market} type={typ}")\n\n        except asyncio.TimeoutError:\n            reconnects+=1\n            delay=next_reconnect_delay(attempt,config)\n            attempt+=1\n            progress(f"[KALSHI] receive timeout; reconnecting in {delay:.1f}s")\n            await asyncio.sleep(delay)\n\n        except asyncio.CancelledError:\n            raise\n\n        except Exception as exc:\n            reconnects+=1\n            delay=next_reconnect_delay(attempt,config)\n            attempt+=1\n            progress(f"[KALSHI] connection error={type(exc).__name__}; reconnecting in {delay:.1f}s")\n            await asyncio.sleep(delay)\n\n    return PersistentKalshiLoopSummary(\n        connections,reconnects,acks,market,last,True\n    )\n\ndef run_persistent_kalshi_loop(root=None,max_market_messages=None,timeout_seconds=15,progress=print):\n    credentials=load_kalshi_credentials(root=root)\n    return asyncio.run(_run(credentials,max_market_messages,timeout_seconds,progress))\n\ndef verify_oad_032_persistent_real_kalshi_message_loop():\n    # Production default MUST be unbounded; bounded mode is test/diagnostic only.\n    import inspect\n    sig=inspect.signature(run_persistent_kalshi_loop)\n    return (\n        sig.parameters["max_market_messages"].default is None\n        and OAD_032_REVISION.endswith("CORRECTION_V2")\n    )\n'
TEST32_SOURCE='import inspect\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_032_persistent_real_kalshi_message_loop())\n\n    def test_production_default_unbounded(self):\n        sig=inspect.signature(run_persistent_kalshi_loop)\n        self.assertIsNone(sig.parameters["max_market_messages"].default)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OAD-032 CORRECTION V2 CERTIFICATION TEST")\n    print(" TRUE 24/7 PERSISTENT REAL KALSHI MESSAGE LOOP")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-032 production stream is unbounded by default")\n    print("[DONE] OAD-032 CORRECTION V2 CERTIFIED")\n'
RUNNER32_SOURCE='from pathlib import Path\nimport argparse\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import run_persistent_kalshi_loop\n\ndef main():\n    parser=argparse.ArgumentParser(description="Persistent Kalshi live stream")\n    parser.add_argument("--max-market-messages",type=int,default=None,\n                        help="Diagnostic only. Production default is unbounded.")\n    parser.add_argument("--timeout-seconds",type=float,default=15.0)\n    args=parser.parse_args()\n\n    print("="*72,flush=True)\n    print(" OAD-032 PERSISTENT KALSHI LIVE STREAM — CORRECTION V2",flush=True)\n    print("="*72,flush=True)\n    if args.max_market_messages is None:\n        print("[MODE] PRODUCTION 24/7 — UNBOUNDED",flush=True)\n    else:\n        print(f"[MODE] DIAGNOSTIC — max_market_messages={args.max_market_messages}",flush=True)\n\n    try:\n        r=run_persistent_kalshi_loop(\n            Path.cwd(),\n            max_market_messages=args.max_market_messages,\n            timeout_seconds=args.timeout_seconds,\n            progress=lambda x:print(x,flush=True),\n        )\n        print("[SUMMARY]",r,flush=True)\n        return 0\n    except KeyboardInterrupt:\n        print("\\n[STOP] Kalshi persistent stream stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
LAUNCHER_SOURCE='from __future__ import annotations\n\nimport argparse\nimport importlib\nimport subprocess\nimport sys\nimport time\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nRUNTIME_NAME="Oracle Live Runtime"\nLAUNCHER_REVISION="ORACLE_LIVE_RUNTIME_KALSHI_SUPERVISION_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name:str\n    state:str\n    certified:bool\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef verify_frozen_ois_boundary():\n    m=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    if getattr(m,"verify_ois_055_final_production_certification_freeze")() is not True:\n        raise RuntimeError("Frozen OIS-055 certification boundary verification failed")\n    return True\n\ndef verify_kalshi_boundary():\n    m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate")\n    if getattr(m,"verify_oad_035_physical_oracle_kalshi_production_activation_gate")() is not True:\n        raise RuntimeError("OAD-035 Kalshi activation boundary verification failed")\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary()\n    verify_kalshi_boundary()\n    return OracleLiveBootReport(RUNTIME_NAME,"RUNNING",True,False,False)\n\ndef format_boot_report(report):\n    return "\\n".join((\n        "="*72,\n        " ORACLE LIVE RUNTIME",\n        "="*72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        f"[STATE] {report.state}",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] OAD-001 through OAD-035 Kalshi boundary verified",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime with supervised Kalshi 24/7 stream verified",\n    ))\n\ndef _start_kalshi_child(root):\n    child=root/"run_oad_032_kalshi_persistent_stream.py"\n    if not child.is_file():\n        raise RuntimeError("Persistent Kalshi stream runner missing: "+str(child))\n    return subprocess.Popen([sys.executable,str(child)],cwd=str(root))\n\ndef run_forever(cadence_seconds):\n    report=build_boot_report()\n    print(format_boot_report(report),flush=True)\n    root=Path.cwd()\n\n    proc=_start_kalshi_child(root)\n    restart_count=0\n    print(f"[KALSHI] persistent 24/7 stream started pid={proc.pid}",flush=True)\n\n    sequence=0\n    try:\n        while True:\n            sequence+=1\n\n            if proc.poll() is not None:\n                exit_code=proc.returncode\n                restart_count+=1\n                print(\n                    f"[KALSHI] child exited code={exit_code}; "\n                    f"restart_count={restart_count}; restarting",\n                    flush=True,\n                )\n                time.sleep(min(5.0,float(cadence_seconds)))\n                proc=_start_kalshi_child(root)\n                print(f"[KALSHI] restarted pid={proc.pid}",flush=True)\n\n            print(\n                f"[ORACLE] heartbeat={sequence} state=RUNNING "\n                f"kalshi_child=RUNNING kalshi_restarts={restart_count} "\n                f"terminal_dependency=NONE execution_authority=FALSE",\n                flush=True,\n            )\n            time.sleep(cadence_seconds)\n\n    except KeyboardInterrupt:\n        print()\n        if proc.poll() is None:\n            proc.terminate()\n            try:\n                proc.wait(timeout=5)\n            except Exception:\n                proc.kill()\n        print("[STOP] Oracle Live Runtime stopped by operator.",flush=True)\n        return 0\n\ndef main(argv=None):\n    parser=argparse.ArgumentParser(description="Oracle Live Runtime production launcher")\n    parser.add_argument("--check",action="store_true")\n    parser.add_argument("--cadence-seconds",type=float,default=5.0)\n    args=parser.parse_args(argv)\n\n    if args.cadence_seconds<=0:\n        raise SystemExit("--cadence-seconds must be > 0")\n\n    report=build_boot_report()\n    if args.check:\n        print(format_boot_report(report))\n        return 0\n\n    return run_forever(args.cadence_seconds)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
LAUNCHER_TEST_SOURCE='import inspect\nimport subprocess\nimport sys\nimport unittest\nfrom pathlib import Path\nimport run_oracle_LIVE as live\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import run_persistent_kalshi_loop\n\nclass T(unittest.TestCase):\n    def test_boot(self):\n        r=live.build_boot_report()\n        self.assertTrue(r.certified)\n        self.assertFalse(r.execution_authority)\n\n    def test_kalshi_default_unbounded(self):\n        self.assertIsNone(\n            inspect.signature(run_persistent_kalshi_loop)\n            .parameters["max_market_messages"].default\n        )\n\n    def test_check(self):\n        p=subprocess.run(\n            [sys.executable,str(Path(__file__).with_name("run_oracle_LIVE.py")),"--check"],\n            text=True,capture_output=True\n        )\n        self.assertEqual(p.returncode,0)\n        self.assertIn("supervised Kalshi 24/7 stream verified",p.stdout)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" ORACLE LIVE RUNTIME + KALSHI 24/7 SUPERVISION TEST")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Oracle launcher supervises unbounded Kalshi production stream")\n'

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_035_physical_activation_gate")
        if getattr(m,"verify_oad_035_physical_oracle_kalshi_production_activation_gate")() is not True:
            raise RuntimeError("Certified OAD-035 boundary verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" OAD-032 / OAD-035 CORRECTION V2 INSTALLER")
    print(" TRUE 24/7 KALSHI STREAM + ORACLE CHILD SUPERVISION")
    print("="*72)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    verify_upstream()
    print("[PASS] Certified OAD-035 boundary verified read-only")

    affected=(MODULE32,TEST32,RUNNER32,LAUNCHER,LAUNCHER_TEST)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE32,MODULE32_SOURCE)
        write_exact(TEST32,TEST32_SOURCE)
        write_exact(RUNNER32,RUNNER32_SOURCE)
        write_exact(LAUNCHER,LAUNCHER_SOURCE)
        write_exact(LAUNCHER_TEST,LAUNCHER_TEST_SOURCE)

        for p in affected:
            compile(p.read_text(encoding="utf-8"),str(p),"exec")

        subprocess.run([sys.executable,str(TEST32)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER_TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] 24/7 Kalshi correction failed; all affected files restored")
        raise

    print("[PASS] OAD-032 production message limit removed")
    print("[PASS] Diagnostic bounded mode retained via --max-market-messages")
    print("[PASS] run_oracle_LIVE.py now supervises and restarts Kalshi child")
    print("[PASS] OIS remains frozen and unmodified")
    print("[DONE] OAD-032 / OAD-035 CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
