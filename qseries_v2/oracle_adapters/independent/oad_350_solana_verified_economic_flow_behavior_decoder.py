\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaEconomicFlowBehavior:
    signature:str
    protocols:tuple
    mints:tuple
    flow_rows:int
    behavior:str
    evidence:str
    execution_authority:bool=False

_TARGETS={"TESSERA_V","BISONFI","OKX_LABS_2","DFLOW_AGGREGATOR_V4","HUMIDIFI"}

def decode_verified_economic_flow_behaviors(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a: continue
        protocols=tuple(p for p in a.economic_protocols if p in _TARGETS)
        if not protocols: continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({str(f.mint) for f in fs if getattr(f,"mint",None)}))
        pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
        neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
        if pos and neg and len(mints)>=2:
            behavior="VERIFIED_ECONOMIC_ASSET_EXCHANGE_FLOW"
            evidence="VERIFIED_PROGRAM_PLUS_BIDIRECTIONAL_TOKEN_BALANCE_FLOW"
        elif fs:
            behavior="VERIFIED_ECONOMIC_TOKEN_FLOW"
            evidence="VERIFIED_PROGRAM_PLUS_TOKEN_BALANCE_FLOW"
        else:
            behavior="VERIFIED_ECONOMIC_INTERACTION_UNRESOLVED"
            evidence="VERIFIED_PROGRAM_INVOCATION_ONLY"
        out.append(SolanaEconomicFlowBehavior(
            e.signature,protocols,mints,len(fs),behavior,evidence,False
        ))
    return tuple(out)

