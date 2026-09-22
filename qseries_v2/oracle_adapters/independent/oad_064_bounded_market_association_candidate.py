from dataclasses import dataclass
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class AssociationCandidate: observation_id:str; market_id:str; overlap_terms:tuple; overlap_count:int; candidate_only:bool=True
def bounded_market_association_candidates(entity_terms,indexed_markets,max_candidates=10):
 if not isinstance(indexed_markets,dict): raise TypeError("pre-bounded indexed mapping required")
 et=set(entity_terms.terms); out=[]
 for mid,terms in indexed_markets.items():
  ov=tuple(sorted(et & {str(t).lower() for t in terms}))
  if ov: out.append(AssociationCandidate(entity_terms.observation_id,str(mid),ov,len(ov)))
 return tuple(sorted(out,key=lambda x:(-x.overlap_count,x.market_id))[:max_candidates])
