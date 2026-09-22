from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_417_source_to_market_coverage_matrix import build_source_to_market_coverage_matrix
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class EvidenceGapPriority:
 rank:int; source_family:str; affected_markets:int; domains:tuple[str,...]; priority_score:int
def rank_evidence_gaps(markets,root='.'):
 rows=build_source_to_market_coverage_matrix(markets,root); count=Counter(); domains={}
 for r in rows:
  for fam in r.missing:
   count[fam]+=1; domains.setdefault(fam,set()).add(r.domain)
 ranked=sorted(count,key=lambda f:(-count[f],f))
 return tuple(EvidenceGapPriority(i+1,f,count[f],tuple(sorted(domains[f])),count[f]*1000+len(domains[f])) for i,f in enumerate(ranked))
def recommend_next_source(markets,root='.'):
 x=rank_evidence_gaps(markets,root); return x[0] if x else None
