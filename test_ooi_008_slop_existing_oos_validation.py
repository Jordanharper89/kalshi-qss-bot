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

def main():
    source = fixture()
    before = copy.deepcopy(vars(source))
    opportunity, report = b.validate_slop(source)
    verify(opportunity, source)
    _, replay = b.validate_slop(copy.deepcopy(source))
    require(report.fingerprint == opportunity.fingerprint(), 'validation fingerprint mismatch')
    require(report.opportunity_id == opportunity.opportunity_id, 'validation identity mismatch')
    require(report.read_only is True, 'validation is not read-only')
    require(type(report.is_accepted()) is bool, 'non-boolean validation decision')
    require(len(report.checks) > 0, 'validation performed no checks')
    require(semantic(report) == semantic(replay), 'validation decisions are not repeatable')
    require(vars(source) == before, 'validation mutated source')
    print('[VALIDATION_STATUS]', getattr(report.status, 'value', report.status))
    print('[ACCEPTED]', report.is_accepted())
    for check in report.checks:
        if not check.passed:
            print('[CHECK]', check.check_id, getattr(check.severity, 'value', check.severity), check.message)
    print('[PASS] OOI-008 existing default validation executed; decision preserved')
    print('[PASS] contract certification only; no admission threshold bypass; execution_authority=FALSE')

if __name__ == '__main__':
    main()
