"""ORACLE-247: isolated hydrated-pair capacity experiment; disarmed."""
import argparse
import contextlib
import inspect
import io
import json
import os
import re
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE247_PAIR_CAP_TRIAL.json')
DISC = re.compile(r'\[CROSSLIST_DISCOVERY\].*?exact_pairs=(\d+)')


def identity(pair):
    return {
        'token': str(getattr(pair, 'token', '')),
        'pump_pool': str(getattr(pair, 'pump_pool', '')),
        'meteora_pool': str(getattr(pair, 'meteora_pool', '')),
    }


def assess(baseline, trial, limit, errors=None):
    b = {tuple(x.values()) for x in baseline}
    t = {tuple(x.values()) for x in trial}
    return {
        'configured_cap': limit,
        'baseline_count': len(baseline),
        'trial_count': len(trial),
        'new_unique_pairs': len(t - b),
        'baseline_retained': b.issubset(t),
        'trial_error': errors,
        'cap_constrained_evidence': (
            isinstance(limit, int) and len(baseline) == limit
            and len(trial) > len(baseline) and b.issubset(t)
            and errors is None
        ),
    }


def test():
    def item(n):
        return {'token': str(n), 'pump_pool': str(n+10), 'meteora_pool': str(n+20)}
    x = assess([item(1), item(2)], [item(1), item(2), item(3)], 2)
    assert x['cap_constrained_evidence'] and x['new_unique_pairs'] == 1
    assert not assess([item(1)], [item(2)], 1)['cap_constrained_evidence']
    assert not assess([item(1)], [item(1)], 1)['cap_constrained_evidence']
    assert not assess([item(1)], [item(1), item(2)], 1, 'RuntimeError')['cap_constrained_evidence']
    print('[ORACLE247_TEST_PASS] cap_trial=TRUE identity=TRUE fail_closed=TRUE execution=FALSE')


def run(target):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('ARMED_ENV_REFUSED')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_PRESENT_REFUSED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

    source = inspect.getsource(pd.prepare_pairs)
    if 'len(out) >= MAX_PAIRS' not in source or not hasattr(pd, 'MAX_PAIRS'):
        raise RuntimeError('EXPECTED_CAP_NOT_FOUND_REFUSED')
    original_cap = pd.MAX_PAIRS
    if type(original_cap) is not int or not 1 <= original_cap <= 100:
        raise RuntimeError('UNEXPECTED_CAP_VALUE_REFUSED')
    if r.q87.c is not pd.c:
        raise RuntimeError('RPC_GUARD_MODULE_IDENTITY_NOT_PROVEN')
    old_rpc = r.q87.c.rpc
    report = {'build': 'ORACLE247', 'configured_cap': original_cap,
              'requested_trial_cap': target, 'execution_admission': False,
              'signing': False, 'broadcast': False,
              'security_certified': False, 'fees_certified': False,
              'same_slot_state_certified': False,
              'baseline': [], 'trial': [], 'errors': [], 'audit': {}}
    baseline_log = io.StringIO()
    trial_log = io.StringIO()
    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(old_rpc)
        with contextlib.redirect_stdout(baseline_log):
            baseline, _ = pd.prepare_pairs(Path.cwd())
        report['baseline'] = [identity(x) for x in baseline]
        pd.MAX_PAIRS = min(30, max(original_cap, target))
        with contextlib.redirect_stdout(trial_log):
            trial, _ = pd.prepare_pairs(Path.cwd())
        report['trial'] = [identity(x) for x in trial]
    except Exception as exc:
        report['errors'].append(type(exc).__name__)
    finally:
        pd.MAX_PAIRS = original_cap
        r.q87.c.rpc = old_rpc
    report['audit'] = assess(report['baseline'], report['trial'], original_cap,
                             report['errors'][0] if report['errors'] else None)
    for field, captured in [('baseline', baseline_log), ('trial', trial_log)]:
        lines = captured.getvalue()
        matches = DISC.findall(lines)
        report['audit'][field + '_discovered_exact'] = int(matches[-1]) if matches else None
    report['status'] = 'RESEARCH_CAP_INCREASE_DEMONSTRATED' if report['audit']['cap_constrained_evidence'] else 'HOLD_PAIR_CAP_EFFECT_NOT_DEMONSTRATED'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE247_RESULT]', json.dumps({
        'configured_cap': original_cap, 'target_cap': target,
        'baseline': len(report['baseline']), 'trial': len(report['trial']),
        'new_unique': report['audit']['new_unique_pairs'],
        'baseline_retained': report['audit']['baseline_retained'],
        'error_types': report['errors'], 'status': report['status'],
        'signing': False, 'broadcast': False}, sort_keys=True))
    for row in report['trial']:
        print('[ORACLE247_TRIAL_PAIR]', json.dumps({
            'token': row['token'][:12], 'pump': row['pump_pool'][:12],
            'meteora': row['meteora_pool'][:12]}, sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--target', type=int, default=12)
    args = ap.parse_args()
    if not (args.test or args.run):
        ap.error('use --test or --run')
    if args.test:
        test()
    if args.run:
        run(max(1, min(args.target, 30)))