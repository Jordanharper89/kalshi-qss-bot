
from __future__ import annotations
from dataclasses import dataclass
from .certified_roles import load as load_roles

@dataclass(frozen=True)
class Subscription:
    venue:str
    pool:str
    account:str

def build(root):
    rows=load_roles(root);out=[];seen=set()
    for r in rows:
        for a in r.accounts:
            k=(r.venue,r.pool,a)
            if k in seen: continue
            seen.add(k);out.append(Subscription(*k))
    return out

def requests(subs):
    return [
      {"jsonrpc":"2.0","id":i+1,"method":"accountSubscribe",
       "params":[s.account,{"encoding":"base64","commitment":"processed"}]}
      for i,s in enumerate(subs)
    ]
