from importlib import import_module
from dataclasses import is_dataclass,asdict
ROLE_BINDINGS={
'market_type':('qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver','resolve_sports_market_type'),
'entity':('qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition','recognize_sports_entity_type'),
'decomposition':('qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition','decompose_mixed_market'),
'classification':('qseries_v2.oracle_adapters.independent.oad_101_universal_classification_exhaustive_diagnostic','classify_isolated_root_cause')}
def _load(role):
    m,f=ROLE_BINDINGS[role]
    return getattr(import_module(m),f)
def normalize_output(v):
    if is_dataclass(v):return asdict(v)
    if isinstance(v,(list,tuple)):return [normalize_output(x) for x in v]
    if isinstance(v,dict):return {str(k):normalize_output(x) for k,x in v.items()}
    return v
def run_market_type(market):return normalize_output(_load('market_type')(market))
def run_entity(text):return normalize_output(_load('entity')(text))
def run_decomposition(market):return normalize_output(_load('decomposition')(market))
def run_classification(leg,parent_market,sibling_legs):return normalize_output(_load('classification')(leg,parent_market,sibling_legs))
