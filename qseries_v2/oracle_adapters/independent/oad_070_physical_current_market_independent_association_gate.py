from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from qseries_v2.oracle_adapters.independent.oad_063_independent_entity_term_projection import extract_independent_entity_terms
from qseries_v2.oracle_adapters.independent.oad_064_bounded_market_association_candidate import bounded_market_association_candidates
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class PhysicalAssociationReport:
    observations:int;current_markets:int;observations_with_candidates:int;association_candidates:int;candidates:tuple
def run_physical_current_market_association(per_source_limit=2,market_limit=1000):
    raw=acquire_independent_production_bundle(per_source_limit);canonical=canonicalize_independent_bundle(raw,"oad070.physical")
    entities=tuple(extract_independent_entity_terms(x) for x in canonical);markets,index=fetch_current_open_kalshi_market_index(limit=market_limit)
    groups=tuple((e,bounded_market_association_candidates(e,index,max_candidates=5)) for e in entities);flat=tuple(c for _,cs in groups for c in cs)
    return PhysicalAssociationReport(len(canonical),len(markets),sum(bool(cs) for _,cs in groups),len(flat),flat)
