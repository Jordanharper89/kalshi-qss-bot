from importlib import import_module
READER=('qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_production_kalshi_current_eligibility_boundary','read_current_kalshi_markets')
SPORTS=('qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index','fetch_current_market_sports_candidates')
def _load(spec):
    return getattr(import_module(spec[0]),spec[1])
def read_current_markets(*args,**kwargs):
    return _load(READER)(*args,**kwargs)
def read_current_sports_candidates(*args,**kwargs):
    return _load(SPORTS)(*args,**kwargs)
