from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class StrongAssociation:
 observation_id:str;market_id:str;matched_facts:tuple;association_strength:str;candidate_only:bool=True
def strong_associations(descriptor,dependency_index,max_candidates=10):
    hits={}
    for kind,key in descriptor.facts:
        sk=semantic_key(key)
        ids=tuple(dependency_index.get(kind+"="+sk,()))
        for mid in ids:hits.setdefault(mid,set()).add((kind,sk))
    out=[]
    for mid,facts in hits.items():
        # One structured exact UMD fact is materially stronger than generic token overlap.
        if not facts: continue
        strength="MULTI_FACT" if len(facts)>=2 else "STRUCTURED_EXACT"
        out.append(StrongAssociation(descriptor.observation_id,mid,tuple(sorted(facts)),strength,True))
    return tuple(sorted(out,key=lambda x:(-len(x.matched_facts),x.market_id))[:max_candidates])
