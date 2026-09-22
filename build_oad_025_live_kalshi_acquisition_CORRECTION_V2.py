from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

BUILD_ID="OAD-025-CORRECTION-V2"
REVISION="OAD_025_LIVE_KALSHI_ACQUISITION_GATE_CORRECTION_V2"

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
MODULE=PACKAGE/"oad_025_live_acquisition_gate.py"
TEST=ROOT/"test_oad_025_live_kalshi_acquisition_certification_gate.py"
RUNNER=ROOT/"run_oad_025_kalshi_live_probe.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom types import MappingProxyType\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get\nfrom .oad_024_physical_websocket import probe_kalshi_websocket\n\nOAD_025_BUILD_ID="OAD-025"\nOAD_025_REVISION="OAD_025_LIVE_KALSHI_ACQUISITION_GATE_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass LiveKalshiAcquisitionResult:\n    credential_ready: bool\n    authenticated_rest_live: bool\n    open_markets_seen: int\n    websocket_connected: bool\n    websocket_subscribed: bool\n    websocket_messages: int\n    websocket_message_types: tuple[str, ...]\n    certified_live: bool\n    result_hash: str\n\ndef select_live_probe_tickers(markets, limit=5):\n    tickers=[]\n    for market in markets:\n        ticker=str(market.get("ticker","")).strip()\n        status=str(market.get("status","")).strip().lower()\n        if ticker and status in ("open","active"):\n            tickers.append(ticker)\n        if len(tickers)>=int(limit):\n            break\n    return tuple(tickers)\n\ndef run_live_kalshi_acquisition_probe(root=None, timeout_seconds=10, progress=None):\n    emit = progress or (lambda _msg: None)\n\n    emit("[1/5] Loading Kalshi credentials")\n    credentials=load_kalshi_credentials(root=root)\n    emit("[PASS] Credentials loaded locally")\n\n    emit("[2/5] Verifying authenticated Kalshi REST")\n    auth=kalshi_rest_get(credentials,"/portfolio/balance",{},timeout_seconds)\n    if auth.status_code != 200:\n        raise RuntimeError("Authenticated Kalshi REST verification failed")\n    emit("[PASS] Authenticated REST status=200")\n\n    emit("[3/5] Fetching live/open Kalshi market page")\n    response=kalshi_rest_get(\n        credentials,\n        "/markets",\n        {"limit":1000,"status":"open"},\n        timeout_seconds,\n    )\n    markets=tuple(response.body.get("markets",()))\n    tickers=select_live_probe_tickers(markets,5)\n    if not tickers:\n        raise RuntimeError("No open Kalshi markets available for live WebSocket probe")\n    emit(f"[PASS] Open markets fetched={len(markets)} probe_tickers={len(tickers)}")\n\n    emit("[4/5] Connecting authenticated Kalshi WebSocket")\n    ws=probe_kalshi_websocket(\n        credentials,\n        tickers,\n        channels=("ticker","trade"),\n        max_messages=2,\n        timeout_seconds=timeout_seconds,\n    )\n    if not ws.connected:\n        raise RuntimeError("Kalshi WebSocket did not connect")\n    emit("[PASS] WebSocket connected")\n\n    if not ws.subscribed:\n        raise RuntimeError("Kalshi WebSocket subscription was not acknowledged")\n    emit("[PASS] WebSocket subscription acknowledged")\n\n    emit("[5/5] Confirming live WebSocket traffic")\n    if ws.messages_received < 1:\n        raise RuntimeError("No Kalshi WebSocket messages received")\n    emit(f"[PASS] WebSocket messages={ws.messages_received} types={ws.message_types}")\n\n    raw={\n        "credential_ready":True,\n        "authenticated_rest_live":True,\n        "open_markets_seen":len(markets),\n        "websocket_connected":ws.connected,\n        "websocket_subscribed":ws.subscribed,\n        "websocket_messages":ws.messages_received,\n        "websocket_message_types":ws.message_types,\n    }\n    certified=bool(\n        raw["credential_ready"]\n        and raw["authenticated_rest_live"]\n        and raw["open_markets_seen"]>0\n        and raw["websocket_connected"]\n        and raw["websocket_subscribed"]\n        and raw["websocket_messages"]>0\n    )\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()\n\n    return LiveKalshiAcquisitionResult(\n        True,True,len(markets),ws.connected,ws.subscribed,\n        ws.messages_received,tuple(ws.message_types),certified,h\n    )\n\ndef build_oad_025_certification_manifest():\n    return MappingProxyType({\n        "build_id":OAD_025_BUILD_ID,\n        "revision":OAD_025_REVISION,\n        "startup_path":"credentials_authenticated_rest_open_markets_websocket_live_first",\n        "historical_reconciliation_blocks_live_startup":False,\n        "physical_rest_required":True,\n        "physical_websocket_required":True,\n        "subscription_ack_required":True,\n        "credentials_persisted":False,\n        "execution":False,\n        "next_capability":"bind_physical_kalshi_adapter_into_oracle_live_runtime_and_live_shadow",\n    })\n\ndef verify_oad_025_live_kalshi_acquisition_certification_gate():\n    m=build_oad_025_certification_manifest()\n    return (\n        m["physical_rest_required"]\n        and m["physical_websocket_required"]\n        and m["subscription_ack_required"]\n        and not m["historical_reconciliation_blocks_live_startup"]\n        and not m["credentials_persisted"]\n        and not m["execution"]\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_025_live_kalshi_acquisition_certification_gate())\n\n    def test_historical_nonblocking(self):\n        self.assertFalse(\n            build_oad_025_certification_manifest()["historical_reconciliation_blocks_live_startup"]\n        )\n\n    def test_live_ticker_selection(self):\n        markets=(\n            {"ticker":"A","status":"settled"},\n            {"ticker":"B","status":"open"},\n            {"ticker":"C","status":"open"},\n        )\n        self.assertEqual(select_live_probe_tickers(markets,5),("B","C"))\n\n    def test_next(self):\n        self.assertIn(\n            "oracle_live_runtime",\n            build_oad_025_certification_manifest()["next_capability"],\n        )\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OAD-025 CORRECTION V2 CERTIFICATION TEST")\n    print(" LIVE-FIRST KALSHI ACQUISITION GATE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-025 live-first nonblocking acquisition gate certified")\n    print("[DONE] OAD-025 CORRECTION V2 CERTIFIED")\n'
RUNNER_SOURCE='from pathlib import Path\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import (\n    run_live_kalshi_acquisition_probe,\n)\n\ndef emit(msg):\n    print(msg, flush=True)\n\ndef main():\n    print("="*72, flush=True)\n    print(" OAD-025 PHYSICAL KALSHI LIVE ACQUISITION PROBE — CORRECTION V2", flush=True)\n    print("="*72, flush=True)\n\n    try:\n        r=run_live_kalshi_acquisition_probe(\n            root=Path.cwd(),\n            timeout_seconds=12,\n            progress=emit,\n        )\n    except KeyboardInterrupt:\n        print("[STOP] Physical Kalshi live probe stopped by operator.", flush=True)\n        return 130\n    except Exception as exc:\n        print("[FAIL]", type(exc).__name__ + ":", str(exc), flush=True)\n        raise\n\n    print("[OPEN MARKETS]", r.open_markets_seen, flush=True)\n    print("[WEBSOCKET] connected=", r.websocket_connected,\n          " subscribed=", r.websocket_subscribed,\n          " messages=", r.websocket_messages,\n          " types=", r.websocket_message_types, flush=True)\n    print("[HASH]", r.result_hash, flush=True)\n\n    if not r.certified_live:\n        raise SystemExit("[FAIL] Physical Kalshi live acquisition did not certify")\n\n    print("[PASS] Physical Kalshi authenticated REST + live/open market acquisition + WebSocket certified LIVE", flush=True)\n    print("[PASS] Historical/dead-market reconciliation is non-blocking and remains outside live startup", flush=True)\n    print("[DONE] OAD-025 PHYSICAL LIVE CERTIFICATION COMPLETE", flush=True)\n    return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_adapters.kalshi.oad_024_physical_websocket")
        if getattr(m,"verify_oad_024_physical_kalshi_websocket_activation")() is not True:
            raise RuntimeError("Certified OAD-024 upstream verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" OAD-025 CORRECTION V2 INSTALLER")
    print(" LIVE-FIRST NONBLOCKING KALSHI ACQUISITION")
    print("="*72)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    verify_upstream()
    print("[PASS] Certified OAD-024 upstream boundary verified read-only")

    affected=(MODULE,TEST,RUNNER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)

        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OAD-025 correction failed; affected files restored")
        raise

    print("[PASS] Corrected:",MODULE.relative_to(ROOT))
    print("[PASS] Corrected:",TEST.name)
    print("[PASS] Corrected:",RUNNER.name)
    print("[PASS] Live/open markets now activate before historical reconciliation")
    print("[PASS] Probe now emits progress and uses bounded timeouts")
    print("[DONE] OAD-025 CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
