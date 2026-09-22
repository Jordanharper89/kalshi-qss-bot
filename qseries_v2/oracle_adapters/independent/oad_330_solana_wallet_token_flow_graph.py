\

from __future__ import annotations
from dataclasses import dataclass
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
def _amt(x):
    u=x.get("uiTokenAmount") or {};v=u.get("uiAmountString")
    try:return float(v)
    except (TypeError,ValueError):return float(u.get("uiAmount") or 0.0)
@dataclass(frozen=True,slots=True)
class SolanaWalletTokenFlow:
 signature:str;slot:int;owner:str;mint:str;delta:float;account_index:int|None;execution_authority:bool=False
def build_wallet_token_flows(envelopes):
    out=[]
    for e in envelopes:
        pre={(x.get("accountIndex"),str(x.get("mint") or ""),str(x.get("owner") or "")):_amt(x) for x in e.pre_token_balances}
        post={(x.get("accountIndex"),str(x.get("mint") or ""),str(x.get("owner") or "")):_amt(x) for x in e.post_token_balances}
        for k in sorted(set(pre)|set(post),key=str):
            d=post.get(k,0.0)-pre.get(k,0.0)
            if abs(d)>0:out.append(SolanaWalletTokenFlow(e.signature,e.slot,k[2],k[1],d,k[0],False))
    return tuple(out)

