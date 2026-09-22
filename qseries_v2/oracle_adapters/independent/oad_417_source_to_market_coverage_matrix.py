from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_415_universal_source_registry import registry_by_family
from qseries_v2.oracle_adapters.independent.oad_416_kalshi_market_evidence_requirement_resolver import resolve_market_cohort
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class MarketCoverage:
 ticker:str; domain:str; required:tuple[str,...]; available:tuple[str,...]; missing:tuple[str,...]; state:str
def build_source_to_market_coverage_matrix(markets,root='.'):
 reg=registry_by_family(root); out=[]
 for r in resolve_market_cohort(markets):
  available=tuple(x for x in r.source_families if x in reg and reg[x].active)
  missing=tuple(x for x in r.source_families if x not in available)
  state='UNMAPPED' if r.state=='UNMAPPED' else ('COVERED' if not missing else ('PARTIAL' if available else 'NOT_COVERED'))
  out.append(MarketCoverage(r.ticker,r.domain,r.source_families,available,missing,state))
 return tuple(out)
