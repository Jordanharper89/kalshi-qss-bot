\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPostCommitReconciliation:
    committed_ids: tuple
    found_ids: tuple
    missing_ids: tuple
    duplicate_committed_ids: tuple
    reconciliation_state: str
    execution_authority: bool=False

def reconcile_post_commit_ids(committed_ids, readback_result):
    raw=tuple(str(x) for x in committed_ids)
    seen=set(); dup=[]
    for x in raw:
        if x in seen and x not in dup:
            dup.append(x)
        seen.add(x)
    unique=tuple(dict.fromkeys(raw))
    found=tuple(str(x) for x in getattr(readback_result,"found_ids",()))
    missing=tuple(x for x in unique if x not in set(found))
    if dup:
        state="DUPLICATE_COMMIT_ID_INPUT"
    elif missing:
        state="POST_COMMIT_READBACK_INCOMPLETE"
    else:
        state="POST_COMMIT_RECONCILED"
    return SolanaPostCommitReconciliation(unique,found,missing,tuple(dup),state,False)

