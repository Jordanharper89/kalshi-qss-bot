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
class SolanaUnresolvedEconomicEvidence:
    program_id:str
    invocations:int
    transactions:int
    transactions_with_token_flows:int
    flow_rows:int
    distinct_mints:int
    bidirectional_flow_transactions:int
    evidence_class:str
    execution_authority:bool=False

def profile_unresolved_economic_evidence(envelopes,attributions,flows):
    flow_by_sig=defaultdict(list)
    for f in flows:
        flow_by_sig[f.signature].append(f)
    sigs_by_program=defaultdict(set)
    inv=Counter()
    for a in attributions:
        for pid in a.unknown_program_ids:
            inv[pid]+=1
            sigs_by_program[pid].add(a.signature)
    out=[]
    for pid,count in inv.most_common():
        sigs=sigs_by_program[pid]
        rows=[];mints=set();with_flow=0;bidir=0
        for sig in sigs:
            fs=flow_by_sig.get(sig,[])
            if fs:
                with_flow+=1
                rows.extend(fs)
                mints.update(str(f.mint) for f in fs if getattr(f,"mint",None))
                pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
                neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
                if pos and neg:
                    bidir+=1
        evidence="NO_TOKEN_FLOW_EVIDENCE"
        if with_flow:
            evidence="TOKEN_FLOW_ASSOCIATED_UNKNOWN_PROGRAM"
        if bidir:
            evidence="BIDIRECTIONAL_TOKEN_FLOW_ASSOCIATED_UNKNOWN_PROGRAM"
        out.append(SolanaUnresolvedEconomicEvidence(
            pid,count,len(sigs),with_flow,len(rows),len(mints),bidir,evidence,False
        ))
    return tuple(out)

