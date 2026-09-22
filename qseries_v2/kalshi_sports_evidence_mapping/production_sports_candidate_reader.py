from qseries_v2.oracle_adapters.independent.oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort
from qseries_v2.oracle_adapters.independent.oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows
from qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates

def read_production_sports_candidates(root=None, cohort_timeout=30, acquisition_timeout=15, market_limit=100, market_timeout=20):
    cohort=load_persisted_authoritative_sports_cohort(
        root=root,
        timeout_seconds=cohort_timeout,
        acquisition_timeout_seconds=acquisition_timeout)
    descriptors=descriptors_from_persisted_sports_rows(cohort.rows)
    markets,groups=fetch_current_market_sports_candidates(
        descriptors,
        limit=market_limit,
        timeout_seconds=market_timeout)
    return cohort,tuple(descriptors),tuple(markets),tuple(groups)
