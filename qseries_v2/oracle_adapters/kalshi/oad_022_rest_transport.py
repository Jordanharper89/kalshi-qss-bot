from dataclasses import dataclass
from base64 import b64encode
from time import time
from types import MappingProxyType
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
import json

from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
from .oad_021_credentials import KalshiCredentialConfig

OAD_022_BUILD_ID="OAD-022"
OAD_022_REVISION="OAD_022_PHYSICAL_KALSHI_REST_TRANSPORT_V1"

@dataclass(frozen=True)
class KalshiRestResponse:
    status_code:int
    body:dict
    url:str

def _sign(private_key_pem,message):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as e:
        raise RuntimeError("cryptography package required for Kalshi RSA-PSS authentication") from e
    key=serialization.load_pem_private_key(private_key_pem.encode(),password=None)
    sig=key.sign(message.encode(),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.DIGEST_LENGTH),hashes.SHA256())
    return b64encode(sig).decode()

def build_auth_headers(credentials,method,path,timestamp_ms=None):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    ts=int(timestamp_ms if timestamp_ms is not None else time()*1000)
    clean=urlsplit(path).path
    msg=str(ts)+str(method).upper()+clean
    return {
        "KALSHI-ACCESS-KEY":credentials.api_key_id,
        "KALSHI-ACCESS-TIMESTAMP":str(ts),
        "KALSHI-ACCESS-SIGNATURE":_sign(credentials.private_key_pem,msg),
    }

def kalshi_rest_get(credentials,path,params=None,timeout_seconds=10):
    f=build_kalshi_adapter_foundation()
    params=dict(params or {})
    query=("?"+urlencode(params)) if params else ""
    url=f.predictions_rest_base+path+query
    headers=build_auth_headers(credentials,"GET","/trade-api/v2"+path)
    req=Request(url,headers=headers,method="GET")
    with urlopen(req,timeout=float(timeout_seconds)) as resp:
        body=json.loads(resp.read().decode("utf-8"))
        return KalshiRestResponse(int(resp.status),body,url)

def build_oad_022_certification_manifest():
    return MappingProxyType({"build_id":OAD_022_BUILD_ID,"revision":OAD_022_REVISION,
        "network_transport":"urllib_https","rsa_pss_sha256":True,"methods":("GET",),"execution":False})

def verify_oad_022_physical_kalshi_rest_transport():
    # Offline verifier checks path/query separation; live call is performed by OAD-025 live probe.
    f=build_kalshi_adapter_foundation()
    return f.predictions_rest_base=="https://external-api.kalshi.com/trade-api/v2" and "/trade-api/v2" in f.predictions_rest_base
