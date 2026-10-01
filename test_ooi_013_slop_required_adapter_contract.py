import copy
import importlib
from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock, fixture, verify

b = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')

def require(value, message):
    if not value:
        raise AssertionError(message)

def main():
    source = fixture()
    original = copy.deepcopy(vars(source))
    with fixed_validation_clock():
        opportunity, report = b.validate_slop(source)
        verify(opportunity, source)
        require(opportunity.execution.required_execution_adapter == 'solana_wallet', 'wrong adapter requirement')
        require(opportunity.confidence == 0 and opportunity.expected_edge == 0, 'unproven confidence or edge introduced')
        checks = {check.check_id: check for check in report.checks}
        require(checks['business.execution_adapter_required'].passed is True, 'adapter declaration not recognized')
        require(checks['business.confidence_minimum'].passed is False, 'confidence guard bypassed')
        require(checks['business.edge_minimum'].passed is False, 'edge guard bypassed')
        require(report.is_accepted() is False, 'unproven opportunity admitted')
        replay, repeated = b.validate_slop(copy.deepcopy(source))
        require(opportunity.fingerprint() == replay.fingerprint(), 'identity differs on replay')
        require(report.is_accepted() == repeated.is_accepted(), 'decision differs on replay')
        result, reports = b.rank_validated_slop([source])
        require(result.ranked_count == 0 and not reports[0].is_accepted(), 'rejected candidate entered feed')
    require(vars(source) == original, 'SLOP input mutated')
    print('[PASS] OOI-013 canonical required adapter metadata: solana_wallet')
    print('[PASS] confidence/edge remain zero; default validation still rejects candidate')
    print('[PASS] frozen thesis and execution_authority=FALSE preserved')
    print('[SCOPE] Requirement declaration only; no adapter resolution, invocation, or availability certification')

if __name__ == '__main__':
    main()
