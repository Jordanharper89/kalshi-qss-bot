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
    original = copy.deepcopy(vars(source))
    oos = b.OpportunityOperatingSystem()
    opportunity, first = b.intake_slop(source, oos)
    verify(opportunity, source)
    fp = opportunity.fingerprint()
    require(first.fingerprint == fp, 'intake fingerprint mismatch')
    require(first.duplicate is False, 'first intake reported duplicate')
    record = oos.get(fp)
    require(record is not None, 'intake did not register opportunity')
    require(record.opportunity.opportunity_id == opportunity.opportunity_id, 'registered identity mismatch')
    repeated, second = b.intake_slop(copy.deepcopy(source), oos)
    require(second.duplicate is True, 'duplicate was not detected')
    require(second.fingerprint == fp == repeated.fingerprint(), 'duplicate fingerprint mismatch')
    require(len(oos.all_records()) == 1, 'duplicate created an extra registry record')
    require(vars(source) == original, 'source mutated')
    independent = b.OpportunityOperatingSystem()
    _, replay = b.intake_slop(copy.deepcopy(source), independent)
    require(replay.fingerprint == fp and replay.duplicate is False, 'independent replay differs')
    require(len(independent.all_records()) == 1, 'independent intake failed')
    print('[PASS] OOI-007B existing OOS intake, readback, deduplication, replay')
    print('[PASS] frozen thesis preserved; execution_authority=FALSE')

if __name__ == '__main__':
    main()
