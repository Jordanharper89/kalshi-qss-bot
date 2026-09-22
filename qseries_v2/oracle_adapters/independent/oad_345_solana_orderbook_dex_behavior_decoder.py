\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaOrderBookDexBehavior:
    signature:str
    protocols:tuple
    mints:tuple
    flow_count:int
    behavior:str
    evidence:str
    execution_authority:bool=False

def decode_orderbook_dex_behaviors(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        protocols=tuple(p for p in a.economic_protocols if p in ("PHOENIX_ETERNAL","ARCHER_EXCHANGE"))
        if not protocols:
            continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({str(f.mint) for f in fs if getattr(f,"mint",None)}))
        pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
        neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
        if pos and neg and len(mints)>=2:
            behavior="ORDERBOOK_ASSET_EXCHANGE_FLOW"
            evidence="ORDER_BOOK_PROGRAM_PLUS_BIDIRECTIONAL_TOKEN_BALANCE_FLOW"
        elif fs:
            behavior="ORDERBOOK_TOKEN_FLOW"
            evidence="ORDER_BOOK_PROGRAM_PLUS_TOKEN_BALANCE_FLOW"
        else:
            behavior="ORDERBOOK_INTERACTION_UNRESOLVED"
            evidence="ORDER_BOOK_PROGRAM_INVOCATION_ONLY"
        out.append(SolanaOrderBookDexBehavior(
            e.signature,protocols,mints,len(fs),behavior,evidence,False
        ))
    return tuple(out)

