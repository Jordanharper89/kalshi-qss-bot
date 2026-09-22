from dataclasses import dataclass
from .oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from .oad_062_independent_canonical_provenance_validation import validate_independent_canonical
from .oad_063_independent_entity_term_projection import extract_independent_entity_terms
READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class IndependentCanonicalBatch: canonical_observations:tuple; provenance_validated:int; entity_projected:int; ready_for_existing_persistence_router:bool
def build_independent_canonical_batch(report,acquisition_batch_id):
 c=canonicalize_independent_bundle(report,acquisition_batch_id); v=[validate_independent_canonical(x) for x in c]; e=[extract_independent_entity_terms(x) for x in c]
 ready=bool(c) and all(x.valid for x in v) and all(x.terms for x in e)
 return IndependentCanonicalBatch(c,sum(x.valid for x in v),sum(bool(x.terms) for x in e),ready)
