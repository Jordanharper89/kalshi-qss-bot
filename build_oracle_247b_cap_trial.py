"""ORACLE-247B: controlled read-only pair cap test. No execution."""
import argparse
import contextlib
import dis
import io
import json
import os
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE247B_CAP_TRIAL.json')


def find_cap(fn):
    """Locate the real global referenced by prepare_pairs bytecode."""
    names = {i.argval for i in dis.get_instructions(fn)
             if i.opname in ('LOAD_GLOBAL', 'LOAD_NAME')}
    g = fn.__globals__
    if 'MAX_PAIRS' not in names:
        return None, 'MAX_PAIRS_NOT_REFERENCED'
    value = g.get('MAX_PAIRS')
    if type(value) is not int or not 1 <= value <= 100:
        return None, 'MAX_PAIRS_NOT_SAFE_INTEGER'
    return (g, value), None


def identities(pairs):
    rows = []
    for p in pairs:
        rows.append({key: str(getattr(p, key, '')) for key in
                     ('token', 'pump_pool', 'meteora_pool')})
    return rows


def compare(base, trial, limit, error=None):
    def ids(rows):
        return {(r['token'], r['pump_pool'], r['meteora_pool']) for r in rows}
    a, b = ids(base), ids(trial)
    return {'configured_cap': limit, 'baseline': len(base), 'trial': len(trial),
            'new_pairs': len(b-a), 'baseline_retained': a <= b,
            'cap_effect_demonstrated': error is None and len(base) == limit
            and len(b-a) > 0 and a <= b}


def test():
    def example():
        if len([]) >= MAX_PAIRS:
            return []
        return []
    global MAX_PAIRS
    MAX_PAIRS = 4
    cap, reason = find_cap(example)
    assert reason is None and cap[1] == 4
    assert find_cap(lambda: 5)[0] is None
    a = [{'token':'A','pump_pool':'B','meteora_pool':'C'}]
    b = a + [{'token':'D','pump_pool':'E','meteora_pool':'F'}]
    assert compare(a,b,1)['cap_effect_demonstrated']
    assert not compare(a,b,2)['cap_effect_demonstrated']
    print('[ORACLE247B_TEST_PASS] bytecode_cap=TRUE comparisons=TRUE fail_closed=TRUE')


def run(target):
    if os.environ.get('QSB_LIVE_ARM','NO').upper() != 'NO':
        raise RuntimeError('HOLD_ARMED')
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT')
    if not os.environ.get('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('HOLD_RPC_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

    report = {'build':'ORACLE247B','signing':False,'broadcast':False,
              'execution_admission':False,'baseline':[],'trial':[], 'errors':[]}
    cap, issue = find_cap(pd.prepare_pairs)
    if issue:
        report['errors'].append(issue)
    elif r.q87.c is not pd.c:
        report['errors'].append('RPC_GUARD_MODULE_IDENTITY_MISMATCH')
    elif target <= cap[1]:
        report['errors'].append('TARGET_NOT_GREATER_THAN_BASELINE_CAP')
    else:
        glob, prior = cap
        prior_rpc = r.q87.c.rpc
        try:
            r.q87.c.rpc = guard.restricted_rpc_factory(prior_rpc)
            with contextlib.redirect_stdout(io.StringIO()):
                baseline, _ = pd.prepare_pairs(Path.cwd())
            report['baseline'] = identities(baseline)
            glob['MAX_PAIRS'] = target
            with contextlib.redirect_stdout(io.StringIO()):
                expanded, _ = pd.prepare_pairs(Path.cwd())
            report['trial'] = identities(expanded)
        except Exception as exc:
            report['errors'].append(type(exc).__name__)
        finally:
            glob['MAX_PAIRS'] = prior
            r.q87.c.rpc = prior_rpc
    report['audit'] = compare(report['baseline'], report['trial'],
                              cap[1] if cap else None,
                              report['errors'][0] if report['errors'] else None)
    report['status'] = ('RESEARCH_CAP_EFFECT_PROVEN'
                        if report['audit']['cap_effect_demonstrated']
                        else 'HOLD_CAP_EFFECT_NOT_PROVEN')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('[ORACLE247B_RESULT]',json.dumps({
        **report['audit'], 'errors':report['errors'], 'status':report['status'],
        'signing':False,'broadcast':False},sort_keys=True))
    for pair in report['trial']:
        print('[ORACLE247B_PAIR]',json.dumps({
            'token':pair['token'][:12], 'pump':pair['pump_pool'][:12],
            'meteora':pair['meteora_pool'][:12]},sort_keys=True))
    print('[REPORT]',OUT)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    p.add_argument('--target',type=int,default=12)
    a=p.parse_args()
    if not a.test and not a.run:
        p.error('use --test or --run')
    if a.test: test()
    if a.run: run(max(1,min(a.target,30)))