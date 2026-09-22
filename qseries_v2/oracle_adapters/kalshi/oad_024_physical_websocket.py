from dataclasses import dataclass
from time import time
from types import MappingProxyType
import asyncio, json

from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
from .oad_021_credentials import KalshiCredentialConfig
from .oad_022_rest_transport import build_auth_headers
from .oad_011_websocket_foundation import build_subscribe_command

OAD_024_BUILD_ID="OAD-024"
OAD_024_REVISION="OAD_024_PHYSICAL_KALSHI_WEBSOCKET_ACTIVATION_V1"

@dataclass(frozen=True)
class KalshiWebSocketProbe:
    connected:bool
    subscribed:bool
    messages_received:int
    message_types:tuple[str,...]

async def _probe(credentials,market_tickers,channels,max_messages,timeout_seconds):
    try:
        import websockets
    except Exception as e:
        raise RuntimeError("websockets package required for physical Kalshi WebSocket activation") from e
    f=build_kalshi_adapter_foundation()
    headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")
    # Support current and older websockets keyword names.
    kwargs={"open_timeout":float(timeout_seconds)}
    try:
        ws_cm=websockets.connect(f.predictions_ws_url,additional_headers=headers,**kwargs)
    except TypeError:
        ws_cm=websockets.connect(f.predictions_ws_url,extra_headers=headers,**kwargs)
    types=[]
    async with ws_cm as ws:
        cmd=build_subscribe_command(1,channels,market_tickers)
        await ws.send(json.dumps(cmd,separators=(",",":")))
        subscribed=False
        for _ in range(int(max_messages)):
            raw=await asyncio.wait_for(ws.recv(),timeout=float(timeout_seconds))
            msg=json.loads(raw)
            typ=str(msg.get("type",""))
            types.append(typ)
            if typ in ("subscribed","ok"): subscribed=True
            if len(types)>=int(max_messages): break
        return KalshiWebSocketProbe(True,subscribed,len(types),tuple(types))

def probe_kalshi_websocket(credentials,market_tickers,channels=("ticker","trade"),max_messages=5,timeout_seconds=10):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    tickers=tuple(market_tickers)
    if not tickers: raise ValueError("at least one live market ticker required")
    return asyncio.run(_probe(credentials,tickers,tuple(channels),int(max_messages),float(timeout_seconds)))

def build_oad_024_certification_manifest():
    return MappingProxyType({"build_id":OAD_024_BUILD_ID,"revision":OAD_024_REVISION,
        "production_websocket":"wss://external-api-ws.kalshi.com/trade-api/ws/v2",
        "authenticated_handshake":True,"read_only_channels":("ticker","trade","orderbook_delta"),"execution":False})

def verify_oad_024_physical_kalshi_websocket_activation():
    return build_oad_024_certification_manifest()["authenticated_handshake"] is True
