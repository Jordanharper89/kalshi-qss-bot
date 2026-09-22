from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import asyncio,json
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import build_auth_headers
from qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket
from qseries_v2.oracle_adapters.kalshi.oad_037_ola_postgres_router_binding import build_ola_production_persistence_router,persist_canonical_observation
from qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import build_kalshi_subscription_command
from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import classify_persistence_failure
from qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap import freeze_trade
ORH_008_BUILD_ID="ORH-008"
async def _persist_without_transport_reconnect(router,observation,now,ticker,typ,max_attempts=8):
    for attempt in range(1,max_attempts+1):
        try:
            persist_canonical_observation(router,observation,routed_at=now);return
        except Exception as exc:
            c=classify_persistence_failure(exc)
            if c.terminal or not c.retryable:raise
            delay=min(5.0,0.1*(2**min(attempt-1,6)))
            print(f"[FAST PERSIST RETRY] type={typ} ticker={ticker} category={c.category} attempt={attempt} retry_in={delay:.2f}s transport_reconnect=FALSE",flush=True)
            if attempt>=max_attempts:raise
            await asyncio.sleep(delay)
async def run_forever(root):
    import websockets
    from qseries_v2.oracle_adapters.kalshi.oad_006_kalshi_foundation import build_kalshi_adapter_foundation
    credentials=load_kalshi_credentials(root=root);router=build_ola_production_persistence_router(root);foundation=build_kalshi_adapter_foundation()
    reconnects=0;persisted=0
    while True:
        headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")
        kwargs={"open_timeout":15.0,"ping_interval":20.0,"ping_timeout":20.0,"close_timeout":10.0}
        try:
            try:cm=websockets.connect(foundation.predictions_ws_url,additional_headers=headers,**kwargs)
            except TypeError:cm=websockets.connect(foundation.predictions_ws_url,extra_headers=headers,**kwargs)
            async with cm as ws:
                await ws.send(json.dumps(build_kalshi_subscription_command(1,("ticker","trade"),None),separators=(",",":")))
                print(f"[FAST LANE] CONNECTED coverage=ALL reconnects={reconnects}",flush=True)
                async for raw_text in ws:
                    raw=json.loads(raw_text);typ=str(raw.get("type",""))
                    if typ in ("subscribed","ok"):
                        print("[FAST LANE] subscription_ack",flush=True);continue
                    if typ not in ("ticker","trade"):continue
                    msg=raw.get("msg") or {};ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()
                    now=datetime.now(timezone.utc)
                    observation=build_ola_canonical_observation_from_websocket(raw,received_at=now,acquisition_batch_id=f"batch.oad054.{persisted+1}.{now.strftime('%Y%m%dT%H%M%S%fZ')}")
                    freeze_trade(raw,now,observation.observation_id,root)
                    await _persist_without_transport_reconnect(router,observation,now,ticker,typ)
                    persisted+=1
                    print(f"[FAST PERSIST] event={persisted} type={typ} ticker={ticker} observation_id={observation.observation_id}",flush=True)
        except asyncio.CancelledError:raise
        except Exception as exc:
            reconnects+=1;delay=min(30.0,2.0**min(reconnects-1,5))
            print(f"[FAST LANE] connection_failure={type(exc).__name__} reconnects={reconnects} reconnecting_in={delay:.1f}s",flush=True)
            await asyncio.sleep(delay)
def main():
    root=Path.cwd();print("="*72,flush=True);print(" OAD-054 KALSHI GLOBAL FAST LANE - 24/7 UNBOUNDED — ORH-008",flush=True);print("="*72,flush=True)
    try:return asyncio.run(run_forever(root))
    except KeyboardInterrupt:
        print("\n[STOP] Global fast lane stopped by operator.",flush=True);return 0
if __name__=="__main__":raise SystemExit(main())
