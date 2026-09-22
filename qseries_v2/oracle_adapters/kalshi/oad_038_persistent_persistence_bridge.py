from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import asyncio,json

from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import kalshi_rest_get,build_auth_headers
from .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket
from .oad_037_ola_postgres_router_binding import build_ola_production_persistence_router,persist_canonical_observation

OAD_038_BUILD_ID="OAD-038"
OAD_038_REVISION="OAD_038_PERSISTENT_KALSHI_TO_POSTGRESQL_BRIDGE_V1"

@dataclass(frozen=True)
class KalshiPersistenceBridgeSummary:
    websocket_connections:int
    subscription_acks:int
    market_events:int
    persisted_observations:int
    reconnects:int
    last_observation_id:str

async def _run(root,max_persisted,progress):
    try:
        import websockets
        from websockets.exceptions import ConnectionClosed
    except Exception as e:
        raise RuntimeError("websockets package required") from e

    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
    from .oad_011_websocket_foundation import build_subscribe_command

    creds=load_kalshi_credentials(root=root)
    router=build_ola_production_persistence_router(root)
    foundation=build_kalshi_adapter_foundation()
    markets=kalshi_rest_get(creds,"/markets",{"limit":1000,"status":"open"},15)
    tickers=tuple(str(m["ticker"]) for m in markets.body.get("markets",()) if m.get("ticker"))[:100]
    if not tickers: raise RuntimeError("No open markets")

    connections=acks=events=persisted=reconnects=0
    last=""
    while max_persisted is None or persisted<int(max_persisted):
        headers=build_auth_headers(creds,"GET","/trade-api/ws/v2")
        kwargs={"open_timeout":15.0,"ping_interval":20.0,"ping_timeout":20.0,"close_timeout":10.0}
        try:
            try: cm=websockets.connect(foundation.predictions_ws_url,additional_headers=headers,**kwargs)
            except TypeError: cm=websockets.connect(foundation.predictions_ws_url,extra_headers=headers,**kwargs)
            async with cm as ws:
                connections+=1
                await ws.send(json.dumps(build_subscribe_command(1,("ticker","trade"),tickers),separators=(",",":")))
                progress(f"[BRIDGE] websocket_connected markets={len(tickers)}")
                async for raw_text in ws:
                    raw=json.loads(raw_text)
                    typ=str(raw.get("type",""))
                    if typ in ("subscribed","ok"):
                        acks+=1
                        progress(f"[BRIDGE] subscription_ack={acks}")
                        continue
                    if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"):
                        continue
                    events+=1
                    now=datetime.now(timezone.utc)
                    batch_id=f"batch.oad038.{now.strftime('%Y%m%dT%H%M%S%fZ')}.{events}"
                    observation=build_ola_canonical_observation_from_websocket(
                        raw,received_at=now,acquisition_batch_id=batch_id
                    )
                    evidence=persist_canonical_observation(router,observation,routed_at=now)
                    persisted+=1
                    last=observation.observation_id
                    progress(f"[BRIDGE] event={events} type={typ} persisted={persisted} observation_id={last}")
                    if max_persisted is not None and persisted>=int(max_persisted):
                        break
        except asyncio.CancelledError: raise
        except KeyboardInterrupt: raise
        except ConnectionClosed as exc:
            reconnects+=1
            progress(f"[BRIDGE] websocket_closed reconnects={reconnects}")
            await asyncio.sleep(1)
        except Exception as exc:
            reconnects+=1
            progress(f"[BRIDGE] connection_failure={type(exc).__name__} reconnects={reconnects}")
            await asyncio.sleep(1)
    return KalshiPersistenceBridgeSummary(connections,acks,events,persisted,reconnects,last)

def run_kalshi_persistence_bridge(root=None,max_persisted=None,progress=print):
    root=Path(root or Path.cwd()).resolve()
    return asyncio.run(_run(root,max_persisted,progress))

def verify_oad_038_persistent_kalshi_to_postgresql_bridge():
    import inspect
    return inspect.signature(run_kalshi_persistence_bridge).parameters["max_persisted"].default is None
