\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter,defaultdict

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaDecoderCloseoutUnknown:
    program_id:str
    invocations:int
    transactions:int
    flow_transactions:int
    bidirectional_flow_transactions:int
    priority_score:int
    disposition:str
    execution_authority:bool=False

def rank_decoder_closeout_unknowns(attributions,flows):
    flow_by_sig=defaultdict(list)
    for f in flows: flow_by_sig[f.signature].append(f)
    inv=Counter(); sigs=defaultdict(set)
    for a in attributions:
        for pid in a.unknown_program_ids:
            inv[pid]+=1; sigs[pid].add(a.signature)
    rows=[]
    for pid,count in inv.items():
        ft=bi=0
        for sig in sigs[pid]:
            fs=flow_by_sig.get(sig,())
            if fs:
                ft+=1
                if any(float(getattr(f,"delta",0))>0 for f in fs) and any(float(getattr(f,"delta",0))<0 for f in fs):
                    bi+=1
        score=count+3*ft+5*bi
        disposition="RETAIN_UNRESOLVED_LOW_EVIDENCE"
        if ft: disposition="RETAIN_FOR_FUTURE_ECONOMIC_DECODER"
        if bi: disposition="HIGH_VALUE_UNRESOLVED_DEFERRED_AFTER_CLOSEOUT"
        rows.append(SolanaDecoderCloseoutUnknown(pid,count,len(sigs[pid]),ft,bi,score,disposition,False))
    return tuple(sorted(rows,key=lambda x:(-x.priority_score,-x.invocations,x.program_id)))

