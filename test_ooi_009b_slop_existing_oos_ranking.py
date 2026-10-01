import copy
import importlib
import math
from types import SimpleNamespace

b = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')

def require(value, message):
    if not value:
        raise AssertionError(message)

def fixture():
    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',
        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},
        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)

def verify(opportunity, source):
    require(opportunity.read_only is True, 'read_only changed')
    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')
    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):
        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)
    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')

def semantic(report):
    return (report.opportunity_id, report.fingerprint, report.status,
        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,
        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))

def run_checks():
    source = fixture()
    before = copy.deepcopy(vars(source))
    result, reports = b.rank_validated_slop([source])
    replay, repeat_reports = b.rank_validated_slop([copy.deepcopy(source)])
    require(len(reports) == 1, 'validation report missing')
    expected = 1 if reports[0].is_accepted() else 0
    require(result.ranked_count == expected == len(result.opportunities), 'rejected research entered ranked feed')
    require(result.read_only is True, 'ranking is not read-only')
    require([r.fingerprint for r in result.opportunities] == [r.fingerprint for r in replay.opportunities], 'ranking identity/order differs')
    require([semantic(r) for r in reports] == [semantic(r) for r in repeat_reports], 'validation replay differs')
    for ranked in result.opportunities:
        require(math.isfinite(float(ranked.score)), 'nonfinite score')
        verify(ranked.opportunity, source)
    # Direct engine compatibility probe is test-only and never enters the accepted feed.
    opportunity = b._canonical(source)
    raw = b.OpportunityRankingEngine().rank([opportunity])
    require(raw.ranked_count == 1 and len(raw.opportunities) == 1, 'existing ranker cannot score canonical SLOP')
    require(raw.opportunities[0].fingerprint == opportunity.fingerprint(), 'ranker fingerprint mismatch')
    require(math.isfinite(float(raw.opportunities[0].score)), 'nonfinite direct score')
    empty, empty_reports = b.rank_validated_slop([])
    require(empty.ranked_count == 0 and empty_reports == [], 'empty ranking contract failed')
    require(vars(source) == before, 'ranking mutated source')
    print('[ACCEPTED_FEED_COUNT]', result.ranked_count)
    if not reports[0].is_accepted():
        print('[HOLD] Default validation rejected the fixture; no admitted opportunity certified')
    print('[PASS] OOI-009B existing ranker compatibility and validation-filtered feed')
    print('[PASS] ranking is research only; execution_authority=FALSE')

def main():
    from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
    with fixed_validation_clock():
        run_checks()

if __name__ == '__main__':
    main()
