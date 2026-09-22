from __future__ import annotations
from dataclasses import dataclass
import json
from .oad_287_gmgn_clean_provider_foundation import require_gmgn_provider, run_gmgn_cli, GMGNRateLimitError
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
ROUTES=("holders","traders")
@dataclass(frozen=True,slots=True)
class GMGNWalletTraderCapability:
    route:str
    help_ok:bool
    command_visible:bool
    execution_authority:bool=False
def _text(v):
    if isinstance(v,(bytes,bytearray)): return v.decode("utf-8","replace")
    return str(v or "")
def verify_wallet_trader_cli_capabilities(timeout_seconds=30.0):
    a=require_gmgn_provider(timeout_seconds); out=[]
    for route in ROUTES:
        p=run_gmgn_cli(a.cli_path,["token",route,"--help"],timeout_seconds,True)
        t=((p.stdout or "")+"\n"+(p.stderr or "")).strip()
        out.append(GMGNWalletTraderCapability(route,p.returncode==0 and bool(t),route.lower() in t.lower() or "usage" in t.lower(),False))
    return tuple(out)
def _decode_json(v):
    t=_text(v).strip()
    try: return json.loads(t)
    except Exception:
        a=t.find("{"); b=t.rfind("}")
        if a>=0 and b>a: return json.loads(t[a:b+1])
    raise RuntimeError("GMGN wallet/trader route returned non-JSON output")
def call_wallet_trader_route(route,token_address,timeout_seconds=30.0):
    route=str(route).strip().lower()
    if route not in ROUTES: raise ValueError("unsupported GMGN wallet/trader route")
    token=str(token_address).strip()
    if not token: raise ValueError("token_address required")
    a=require_gmgn_provider(timeout_seconds)
    p=run_gmgn_cli(a.cli_path,["token",route,"--chain","sol","--address",token,"--raw"],timeout_seconds,False)
    out=_text(p.stdout); err=_text(p.stderr); detail=(err or out).strip()
    if p.returncode!=0:
        u=detail.upper()
        if "429" in u or "RATE_LIMIT" in u: raise GMGNRateLimitError("GMGN_RATE_LIMITED",300.0)
        raise RuntimeError("GMGN "+route+" command failed rc="+str(p.returncode)+": "+detail[:1000])
    data=_decode_json(p.stdout)
    if isinstance(data,dict) and str(data.get("code"))=="429": raise GMGNRateLimitError("GMGN_RATE_LIMITED",300.0)
    return data
