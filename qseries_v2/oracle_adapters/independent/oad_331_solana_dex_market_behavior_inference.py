\

from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDecodedMarketBehavior:
 signature:str;slot:int;behavior:str;dex_ids:tuple;owner:str|None;mints:tuple;flow_count:int;evidence:tuple;execution_authority:bool=False
def infer_solana_market_behavior(envelopes,attributions,flows):
    amap={x.signature:x for x in attributions};fmap=defaultdict(list)
    for f in flows:fmap[f.signature].append(f)
    out=[]
    for e in envelopes:
        a=amap.get(e.signature);fs=fmap.get(e.signature,[])
        byowner=defaultdict(list)
        for f in fs:
            if f.owner:byowner[f.owner].append(f)
        emitted=False
        for owner,rows in byowner.items():
            pos=[x for x in rows if x.delta>0];neg=[x for x in rows if x.delta<0]
            if a and a.attributed and pos and neg and len({x.mint for x in rows if x.mint})>=2:
                out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,"DEX_SWAP",a.dex_ids,owner,tuple(sorted({x.mint for x in rows if x.mint})),len(rows),a.matched_pool_accounts,False));emitted=True
            elif a and a.attributed and len(rows)>=2 and (pos or neg):
                b="DEX_LIQUIDITY_FLOW"
                out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,b,a.dex_ids,owner,tuple(sorted({x.mint for x in rows if x.mint})),len(rows),a.matched_pool_accounts,False));emitted=True
        if a and a.attributed and not emitted:
            out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,"DEX_INTERACTION_UNRESOLVED",a.dex_ids,None,tuple(),0,a.matched_pool_accounts,False))
    return tuple(out)

