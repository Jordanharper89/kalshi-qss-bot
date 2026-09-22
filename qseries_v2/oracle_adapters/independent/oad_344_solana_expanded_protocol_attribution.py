\

from __future__ import annotations
from dataclasses import dataclass
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaExpandedProtocolAttribution:
    signature:str
    top_level_program_ids:tuple
    inner_program_ids:tuple
    economic_protocols:tuple
    infrastructure_protocols:tuple
    unknown_program_ids:tuple
    execution_authority:bool=False

def attribute_expanded_protocols(envelopes):
    base=attribute_transaction_protocols(envelopes)
    out=[]
    for a in base:
        top=tuple(a.top_level_program_ids)
        inner=tuple(a.inner_program_ids)
        econ=[];infra=[];unknown=[]
        for pid in top+inner:
            x=identify_expanded_program(pid)
            if not x.known:
                unknown.append(pid)
            elif x.market_relevant:
                econ.append(x.name)
            else:
                infra.append(x.name)
        out.append(SolanaExpandedProtocolAttribution(
            a.signature,top,inner,
            tuple(dict.fromkeys(econ)),
            tuple(dict.fromkeys(infra)),
            tuple(unknown),
            False
        ))
    return tuple(out)

