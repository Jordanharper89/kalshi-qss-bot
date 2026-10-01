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
    gate = importlib.import_module('qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate')
    source = fixture()
    before = copy.deepcopy(vars(source))
    opportunity, validation = b.validate_slop(source)
    # Gate the same accepted set used by the production bridge. Never relax validation.
    accepted = [opportunity] if validation.is_accepted() else []
    result = gate.run_opportunity_subsystem_integration_gate(
        opportunities=accepted, observed_at='2026-09-17T00:00:00Z', source=b.SOURCE)
    print('[INTEGRATION_PASSED]', result.passed)
    print('[ACCEPTED_COUNT]', len(accepted))
    for check in result.checks:
        print('[INTEGRATION_CHECK]', check)
    require(result.read_only is True and result.execution_allowed is False, 'integration authority boundary failed')
    require(result.verify_integration_hash(), 'integration hash verification failed')
    require(result.passed is True and result.fail_count == 0, 'existing integration gate failed; stop here')
    require(result.pass_count > 0, 'integration ran no passing checks')
    gate.assert_opportunity_subsystem_read_only(result)
    replay = gate.run_opportunity_subsystem_integration_gate(
        opportunities=accepted, observed_at='2026-09-17T00:00:00Z', source=b.SOURCE)
    require(replay.passed is True and replay.verify_integration_hash(), 'integration replay failed')
    require((result.pass_count, result.fail_count) == (replay.pass_count, replay.fail_count), 'integration check totals differ')
    verify(opportunity, source)
    require(vars(source) == before, 'integration mutated source')
    if not accepted:
        print('[HOLD] SLOP fixture is not accepted by existing validation; no admitted opportunity certified')
    print('[PASS] OOI-011B existing OOS integration contract; execution_authority=FALSE')
    print('[SCOPE] deterministic fixture certification; live runtime activation not claimed')

def main():
    from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock
    with fixed_validation_clock():
        run_checks()

if __name__ == '__main__':
    main()
