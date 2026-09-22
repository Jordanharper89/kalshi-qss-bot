from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import verify_or_persist_independent_cohort
from qseries_v2.oracle_adapters.independent.oad_072_independent_umd115_descriptor_adapter import descriptors_from_canonical
from qseries_v2.oracle_adapters.independent.oad_073_current_market_umd_dependency_index import build_current_market_dependency_index
from qseries_v2.oracle_adapters.independent.oad_074_strong_structured_market_association import strong_associations
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class AssociationQualityReport:
 persisted_observations:int;descriptors_with_facts:int;current_markets:int;structured_associations:int;observations_with_associations:int;associations:tuple
def run_persisted_independent_association_quality_gate(market_limit=1000):
    persisted=verify_or_persist_independent_cohort(timeout_seconds=120.0)
    rows=tuple(persisted["rows"])
    descriptors=descriptors_from_canonical(rows)
    markets,index,_=build_current_market_dependency_index(market_limit)
    groups=tuple((d,strong_associations(d,index,10)) for d in descriptors)
    flat=tuple(a for _,xs in groups for a in xs)
    return AssociationQualityReport(len(rows),sum(bool(d.facts) for d in descriptors),len(markets),len(flat),sum(bool(xs) for _,xs in groups),flat)
