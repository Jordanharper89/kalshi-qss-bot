\

from __future__ import annotations
from dataclasses import dataclass
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def _program_id(ix,account_keys):
    if not isinstance(ix,dict):
        return ""
    pid=ix.get("programId") or ix.get("program_id")
    if isinstance(pid,dict):
        pid=pid.get("pubkey") or pid.get("key")
    if pid:
        return str(pid)
    idx=ix.get("programIdIndex")
    if isinstance(idx,int) and 0<=idx<len(account_keys):
        return str(account_keys[idx])
    return ""

def _walk_inner(inner,account_keys):
    for group in inner or ():
        if not isinstance(group,dict):
            continue
        for ix in group.get("instructions") or ():
            pid=_program_id(ix,account_keys)
            if pid:
                yield pid

@dataclass(frozen=True,slots=True)
class SolanaProtocolAttribution:
    signature:str
    slot:int
    top_level_program_ids:tuple
    inner_program_ids:tuple
    known_protocols:tuple
    infrastructure_programs:tuple
    unknown_programs:tuple
    market_relevant:bool
    execution_authority:bool=False

def attribute_transaction_protocols(envelopes):
    out=[]
    for e in envelopes:
        keys=tuple(e.account_keys or ())
        top=tuple(pid for pid in (_program_id(ix,keys) for ix in (e.instructions or ())) if pid)
        inner=tuple(_walk_inner(e.inner_instructions or (),keys))
        ids=top+inner
        known=[];infra=[];unknown=[]
        for pid in ids:
            x=identify_solana_program(pid)
            if not x.known:
                unknown.append(pid)
            elif x.category=="INFRASTRUCTURE":
                infra.append(x.name)
            elif x.name not in known:
                known.append(x.name)
        out.append(SolanaProtocolAttribution(
            e.signature,e.slot,top,inner,tuple(known),tuple(sorted(set(infra))),
            tuple(sorted(set(unknown))),bool(known),False
        ))
    return tuple(out)

