\

from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

MARKET_PROTOCOLS={"PUMP_FUN_BONDING_CURVE","PUMP_FUN_AMM","METEORA_DLMM"}

@dataclass(frozen=True,slots=True)
class SolanaProtocolMarketBehavior:
    signature:str
    slot:int
    protocol:str
    behavior:str
    owner:str|None
    mints:tuple
    evidence_count:int
    confidence_basis:str
    execution_authority:bool=False

def decode_protocol_market_behaviors(envelopes,attributions,flows):
    amap={x.signature:x for x in attributions}
    fmap=defaultdict(list)
    for f in flows:
        fmap[f.signature].append(f)
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        ps=tuple(p for p in a.known_protocols if p in MARKET_PROTOCOLS)
        if not ps:
            continue
        byowner=defaultdict(list)
        for f in fmap.get(e.signature,()):
            if getattr(f,"owner",None):
                byowner[f.owner].append(f)
        if not byowner:
            for p in ps:
                out.append(SolanaProtocolMarketBehavior(e.signature,e.slot,p,"PROTOCOL_INTERACTION_UNRESOLVED",None,tuple(),0,"PROGRAM_INVOCATION_ONLY",False))
            continue
        for owner,rows in byowner.items():
            neg=[x for x in rows if x.delta<0 and x.mint]
            pos=[x for x in rows if x.delta>0 and x.mint]
            mints=tuple(sorted({x.mint for x in rows if x.mint}))
            for p in ps:
                if neg and pos and len(mints)>=2:
                    behavior="SWAP"
                    basis="PROGRAM_PLUS_BIDIRECTIONAL_TOKEN_FLOW"
                elif len(rows)>=2 and (neg or pos):
                    behavior="LIQUIDITY_OR_POSITION_FLOW"
                    basis="PROGRAM_PLUS_MULTI_TOKEN_FLOW"
                else:
                    behavior="PROTOCOL_INTERACTION_UNRESOLVED"
                    basis="PROGRAM_PLUS_INSUFFICIENT_FLOW"
                out.append(SolanaProtocolMarketBehavior(e.signature,e.slot,p,behavior,owner,mints,len(rows),basis,False))
    return tuple(out)

