from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import urlsplit
from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation

OAD_007_BUILD_ID="OAD-007"
OAD_007_REVISION="OAD_007_KALSHI_TRANSPORT_AUTH_BOUNDARY_V1"

@dataclass(frozen=True)
class KalshiTransportAuthBoundary:
    rest_base:str
    websocket_url:str
    websocket_handshake_path:str
    signing_algorithm:str
    required_headers:tuple[str,...]
    private_key_material_stored:bool
    order_methods_allowed:bool

def signing_message(timestamp_ms,method,path):
    if int(timestamp_ms)<0: raise ValueError("non-negative timestamp required")
    method=str(method).upper()
    clean=urlsplit(path).path
    if not clean.startswith("/"): raise ValueError("absolute request path required")
    return str(int(timestamp_ms))+method+clean

def build_kalshi_transport_auth_boundary():
    f=build_kalshi_adapter_foundation()
    return KalshiTransportAuthBoundary(
        f.predictions_rest_base,f.predictions_ws_url,"/trade-api/ws/v2",
        "RSA-PSS-SHA256",
        ("KALSHI-ACCESS-KEY","KALSHI-ACCESS-TIMESTAMP","KALSHI-ACCESS-SIGNATURE"),
        False,False
    )

def build_oad_007_certification_manifest():
    x=build_kalshi_transport_auth_boundary()
    return MappingProxyType({"build_id":OAD_007_BUILD_ID,"revision":OAD_007_REVISION,
        "signing_algorithm":x.signing_algorithm,"private_key_material_stored":False,"order_methods_allowed":False})

def verify_oad_007_kalshi_transport_auth_boundary():
    x=build_kalshi_transport_auth_boundary()
    msg=signing_message(123,"get","/trade-api/v2/markets?limit=1000")
    return msg=="123GET/trade-api/v2/markets" and len(x.required_headers)==3 and not x.private_key_material_stored and not x.order_methods_allowed
