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
    oos = b.OpportunityOperatingSystem()
    result, reports = b.process_validated_slop([source], oos)
    expected = int(reports[0].is_accepted())
    require(result.input_count == expected, 'pipeline received rejected research')
    require(result.registered_count == expected, 'pipeline registration count differs')
    require(result.ranked_count == expected, 'pipeline ranking count differs')
    require(result.read_only is True, 'pipeline is not read-only')
    require(len(oos.all_records()) == expected, 'caller-owned OOS was not used')
    again, repeat_reports = b.process_validated_slop([copy.deepcopy(source)], oos)
    require(again.duplicate_count == expected, 'pipeline duplicate handling differs')
    require(len(oos.all_records()) == expected, 'pipeline replay duplicated registry records')
    require(semantic(reports[0]) == semantic(repeat_reports[0]), 'pipeline validation replay differs')
    for record in oos.all_records():
        verify(record.opportunity, source)
    require(vars(source) == before, 'pipeline mutated source')
    fresh = b.OpportunityOperatingSystem()
    empty, empty_reports = b.process_validated_slop([], fresh)
    require(empty.input_count == 0 and empty.ranked_count == 0 and empty_reports == [], 'empty pipeline failed')
    require(len(fresh.all_records()) == 0, 'empty pipeline created records')
    print('[PIPELINE_COUNTS]', result.input_count, result.registered_count, result.ranked_count)
    if not expected:
        print('[HOLD] Rejected fixture excluded from registry and ranked feed')
    print('[PASS] OOI-010B existing pipeline, caller-owned OOS, validation exclusion, deduplication')
    print('[PASS] execution_authority=FALSE')

def main():
    from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
    with fixed_validation_clock():
        run_checks()

if __name__ == '__main__':
    main()
