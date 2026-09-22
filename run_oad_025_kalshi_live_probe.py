from pathlib import Path

from qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import (
    run_live_kalshi_acquisition_probe,
)

def emit(msg):
    print(msg, flush=True)

def main():
    print("="*72, flush=True)
    print(" OAD-025 PHYSICAL KALSHI LIVE ACQUISITION PROBE — CORRECTION V2", flush=True)
    print("="*72, flush=True)

    try:
        r=run_live_kalshi_acquisition_probe(
            root=Path.cwd(),
            timeout_seconds=12,
            progress=emit,
        )
    except KeyboardInterrupt:
        print("[STOP] Physical Kalshi live probe stopped by operator.", flush=True)
        return 130
    except Exception as exc:
        print("[FAIL]", type(exc).__name__ + ":", str(exc), flush=True)
        raise

    print("[OPEN MARKETS]", r.open_markets_seen, flush=True)
    print("[WEBSOCKET] connected=", r.websocket_connected,
          " subscribed=", r.websocket_subscribed,
          " messages=", r.websocket_messages,
          " types=", r.websocket_message_types, flush=True)
    print("[HASH]", r.result_hash, flush=True)

    if not r.certified_live:
        raise SystemExit("[FAIL] Physical Kalshi live acquisition did not certify")

    print("[PASS] Physical Kalshi authenticated REST + live/open market acquisition + WebSocket certified LIVE", flush=True)
    print("[PASS] Historical/dead-market reconciliation is non-blocking and remains outside live startup", flush=True)
    print("[DONE] OAD-025 PHYSICAL LIVE CERTIFICATION COMPLETE", flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
