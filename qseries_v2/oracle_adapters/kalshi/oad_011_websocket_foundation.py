from dataclasses import dataclass
from types import MappingProxyType
from .oad_007_transport_auth import build_kalshi_transport_auth_boundary

OAD_011_BUILD_ID="OAD-011"
OAD_011_REVISION="OAD_011_KALSHI_WEBSOCKET_MARKET_DATA_FOUNDATION_V1"

PUBLIC_MARKET_DATA_CHANNELS=("orderbook_delta","ticker","trade")

@dataclass(frozen=True)
class KalshiWebSocketMarketDataFoundation:
    websocket_url:str
    authenticated_handshake_required:bool
    channels:tuple[str,...]
    read_only:bool
    execution_authority:bool

def build_websocket_market_data_foundation():
    auth=build_kalshi_transport_auth_boundary()
    return KalshiWebSocketMarketDataFoundation(
        auth.websocket_url,True,PUBLIC_MARKET_DATA_CHANNELS,True,False
    )

def build_subscribe_command(command_id,channels,market_tickers):
    channels=tuple(channels); tickers=tuple(market_tickers)
    if int(command_id)<1 or not channels or not tickers:
        raise ValueError("positive command id, channels, and market_tickers required")
    unknown=tuple(x for x in channels if x not in PUBLIC_MARKET_DATA_CHANNELS)
    if unknown: raise ValueError("unsupported read-only channel(s): "+",".join(unknown))
    return {
        "id":int(command_id),
        "cmd":"subscribe",
        "params":{"channels":list(channels),"market_tickers":list(tickers)}
    }

def build_oad_011_certification_manifest():
    x=build_websocket_market_data_foundation()
    return MappingProxyType({"build_id":OAD_011_BUILD_ID,"revision":OAD_011_REVISION,
        "authenticated_handshake_required":True,"channels":x.channels,"read_only":True,"execution":False})

def verify_oad_011_kalshi_websocket_market_data_foundation():
    x=build_websocket_market_data_foundation()
    c=build_subscribe_command(1,("orderbook_delta","ticker","trade"),("KXTEST",))
    return x.authenticated_handshake_required and x.read_only and not x.execution_authority and c["cmd"]=="subscribe"
