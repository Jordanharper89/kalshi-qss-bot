\
from __future__ import annotations
from dataclasses import dataclass
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaToken2022Activity:
    signature:str
    slot:int
    token2022_invocations:int
    flow_count:int
    mints:tuple
    behavior:str
    execution_authority:bool=False

def decode_token2022_activity(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        ids=tuple(a.top_level_program_ids)+tuple(a.inner_program_ids)
        n=sum(
            1 for pid in ids
            if identify_reconciled_program(pid).name=="TOKEN_2022"
        )
        if not n:
            continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({f.mint for f in fs if getattr(f,"mint",None)}))
        pos=any(getattr(f,"delta",0)>0 for f in fs)
        neg=any(getattr(f,"delta",0)<0 for f in fs)

        behavior="TOKEN_2022_INSTRUCTION_ONLY"
        if fs:
            behavior="TOKEN_2022_BALANCE_FLOW"
        if pos and neg:
            behavior="TOKEN_2022_TRANSFER_OR_SWAP_FLOW"

        out.append(
            SolanaToken2022Activity(
                e.signature,
                e.slot,
                n,
                len(fs),
                mints,
                behavior,
                False
            )
        )
    return tuple(out)
