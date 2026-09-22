from __future__ import annotations
from dataclasses import dataclass
import json,os,urllib.request
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class LiveHeadObservation:
    slot:int
    source:str
    commitment:str="finalized"
    execution_authority:bool=False

def http_finalized_head(rpc_url=None,timeout_seconds=10.0):
    url=rpc_url or os.environ.get("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-QSeries-ZeroCost/1"})
    with urllib.request.urlopen(req,timeout=timeout_seconds) as resp:
        payload=json.loads(resp.read().decode())
        if "error" in payload: raise RuntimeError(payload["error"])
        return int(payload["result"])

def observe_live_head(websocket_head_fn=None,rpc_head_fn=None):
    if websocket_head_fn is not None:
        try:
            v=websocket_head_fn()
            if v is not None: return LiveHeadObservation(int(v),"WEBSOCKET_SIGNAL","finalized",False)
        except Exception:
            pass
    fn=rpc_head_fn or http_finalized_head
    return LiveHeadObservation(int(fn()),"HTTP_FINALIZED_FALLBACK","finalized",False)