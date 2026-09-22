\

from __future__ import annotations
from dataclasses import dataclass
from .oad_328_solana_live_dex_pool_identity_registry import dex_by_pair
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDexTransactionAttribution:
 signature:str;slot:int;matched_pool_accounts:tuple;dex_ids:tuple;attributed:bool;execution_authority:bool=False
def attribute_transactions_to_live_dex_pools(envelopes,registry):
    pairs=dex_by_pair(registry);out=[]
    for e in envelopes:
        matched=tuple(sorted({a for a in e.account_keys if a in pairs}))
        dexes=tuple(sorted({pairs[a] for a in matched}))
        out.append(SolanaDexTransactionAttribution(e.signature,e.slot,matched,dexes,bool(matched),False))
    return tuple(out)

