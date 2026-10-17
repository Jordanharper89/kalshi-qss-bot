"""ORACLE-256: bounded Mriya exact-route admission audit, no transactions."""
import argparse
import contextlib
import io
import json
import os
import re
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE256_MRIYA_EXACT_ADMISSION.json')
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
FIELDS = ('token', 'mint', 'token_mint', 'base_mint')


def mint(row):
    if isinstance(row, str) and B58.fullmatch(row):
        return row
    if isinstance(row, dict):
        for field in FIELDS:
            value = row.get(field)
            if isinstance(value, str) and B58.fullmatch(value):
                return value
    return None


def collect(rows):
    if not isinstance(rows, (list, tuple)):
        return set()
    return {m for row in rows[:2000] if (m := mint(row))}


def analyze(seen, errors, diagnostics):
    hot, raw, exact = (collect(seen.get(k, [])) for k in ('hot', 'raw', 'exact'))
    results = []
    for token in sorted(hot):
        stage = ('EXACT_PAIR' if token in exact else
                 'RAW_ONLY_EXACT_NOT_ESTABLISHED' if token in raw else
                 'HOT_ONLY_RAW_NOT_ADMITTED')
        results.append({'token': token, 'stage': stage, 'raw': token in raw,
                        'exact': token in exact, 'rejection_reason_proven': False})
    return {'build': 'ORACLE256', 'mriya_hot': len(hot), 'raw_tokens': len(raw),
            'exact_tokens': len(exact), 'mriya_raw': len(hot & raw),
            'mriya_exact': len(hot & exact), 'rows': results,
            'discovery_diagnostics': diagnostics, 'errors': errors,
            'freshness_certified': False, 'net_profit_certified': False,
            'signing': False, 'broadcast': False, 'execution_admission': False,
            'status': 'HOLD_EXACT_ELIGIBILITY_AND_LIVE_PROFIT_UNVERIFIED'}


def test():
    a, b, c = 'A'*32, 'B'*32, 'C'*32
    report = analyze({'hot': [{'token': a}, {'token': b}, {'token': c}],
                      'raw': [{'token': a}, {'token': b}],
                      'exact': [{'token': a}]}, [], {})
    assert report['mriya_hot'] == 3 and report['mriya_exact'] == 1
    assert [x['stage'] for x in report['rows']] == [
        'EXACT_PAIR', 'RAW_ONLY_EXACT_NOT_ESTABLISHED', 'HOT_ONLY_RAW_NOT_ADMITTED']
    assert mint({'private_key': a, 'pool': b}) is None
    assert not report['signing'] and not report['broadcast']
    print('[ORACLE256_TEST_PASS] identity=TRUE stage_lineage=TRUE fail_closed=TRUE')


def run():
    if os.environ.get('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('ARMED_REFUSED')
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_ENV_REFUSED')
    if not os.environ.get('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('RPC_MISSING')

    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as runtime
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

    if runtime.q87.c is not engine.c:
        raise RuntimeError('RPC_MODULE_IDENTITY_UNPROVEN')

    originals = {name: getattr(engine, name) for name in
                 ('mriya_hot_tokens', 'raw_candidate_universe')}
    prior_rpc = runtime.q87.c.rpc
    seen, errors, diag = {}, [], {}
    captured = io.StringIO()

    def instrument(name, fn):
        def wrapped(*a, **kw):
            result = fn(*a, **kw)
            if isinstance(result, (list, tuple)):
                seen[name] = list(result)
            else:
                errors.append('UNEXPECTED_' + name.upper() + '_RETURN')
            return result
        return wrapped

    try:
        runtime.q87.c.rpc = guard.restricted_rpc_factory(prior_rpc)
        engine.mriya_hot_tokens = instrument('hot', originals['mriya_hot_tokens'])
        engine.raw_candidate_universe = instrument('raw', originals['raw_candidate_universe'])
        with contextlib.redirect_stdout(captured):
            exact = engine.candidate_universe(Path.cwd())
        if isinstance(exact, (list, tuple)):
            seen['exact'] = list(exact)
        else:
            errors.append('UNEXPECTED_EXACT_RETURN')
    except Exception as exc:
        errors.append(type(exc).__name__)
    finally:
        for name, fn in originals.items():
            setattr(engine, name, fn)
        runtime.q87.c.rpc = prior_rpc

    for line in captured.getvalue().splitlines():
        if line.startswith('[CROSSLIST_DISCOVERY]'):
            diag['crosslist_summary'] = re.sub(
                r'[^a-zA-Z0-9_{}": ,=-]', '', line
            )[:500]

    report = analyze(seen, errors, diag)
    report['invoked_hot'] = 'hot' in seen
    report['invoked_raw'] = 'raw' in seen
    report['returned_exact'] = 'exact' in seen
    report['uncached_call_chain_observed'] = all((
        report['invoked_hot'],
        report['invoked_raw'],
        report['returned_exact']
    ))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')

    print('[ORACLE256_RESULT]', json.dumps({
        k: v for k, v in report.items() if k != 'rows'
    }, sort_keys=True))

    for row in report['rows']:
        print('[ORACLE256_MRIYA]', json.dumps({
            'token': row['token'][:12],
            'stage': row['stage']
        }, sort_keys=True))

    print('[REPORT]', OUT)

    if errors or not report['uncached_call_chain_observed']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()

    if not (args.test or args.run):
        parser.error('Specify --test or --run')

    if args.test:
        test()
    if args.run:
        run()