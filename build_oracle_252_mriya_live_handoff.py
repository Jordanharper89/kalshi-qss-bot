"""ORACLE-252: observe Mriya-to-exact-candidate handoff, without trades."""
import argparse
import contextlib
import io
import json
import os
import re
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE252_MRIYA_HANDOFF.json')
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
KEYS = ('token', 'mint', 'token_mint', 'base_mint')


def identities(value, depth=0):
    """Explicit token fields and token-string collections; no pool-key guesses."""
    result = set()
    if depth > 5:
        return result
    if isinstance(value, str):
        if depth and B58.fullmatch(value):
            result.add(value)
    elif isinstance(value, (tuple, list, set)):
        for item in list(value)[:300]:
            result.update(identities(item, depth + 1))
    elif isinstance(value, dict):
        for key, item in list(value.items())[:300]:
            if key in KEYS and isinstance(item, str) and B58.fullmatch(item):
                result.add(item)
            elif isinstance(item, (list, tuple, set, dict)):
                result.update(identities(item, depth + 1))
    return result


def report(events, final, errors):
    hot = events.get('mriya_hot_tokens', [])
    raw = events.get('raw_candidate_universe', [])
    hot_ids = set().union(*(set(v['ids']) for v in hot)) if hot else set()
    raw_ids = set().union(*(set(v['ids']) for v in raw)) if raw else set()
    exact_ids = identities(final)
    return {
        'build': 'ORACLE252',
        'mriya_invocations': len(hot),
        'mriya_return_identities': len(hot_ids),
        'raw_universe_invocations': len(raw),
        'raw_identities': len(raw_ids),
        'exact_candidate_identities': len(exact_ids),
        'mriya_raw_overlap': sorted(hot_ids & raw_ids),
        'mriya_exact_overlap': sorted(hot_ids & exact_ids),
        'mriya_missing_from_raw': sorted(hot_ids - raw_ids),
        'mriya_missing_from_exact': sorted(hot_ids - exact_ids),
        'event_shapes': {name: [
            {'kind': v['kind'], 'count': v['count'], 'identities': len(v['ids'])}
            for v in calls] for name, calls in events.items()},
        'errors': errors,
        'live_event_provenance_certified': False,
        'live_event_freshness_certified': False,
        'same_slot_execution_certified': False,
        'signing': False, 'broadcast': False, 'execution_admission': False,
        'status': 'HOLD_MRIYA_ORIGIN_AND_FRESHNESS_UNVERIFIED',
    }


def test():
    a, b = 'A' * 32, 'B' * 32
    assert identities([{'token': a}, {'token': b}]) == {a, b}
    assert not identities({'private_key': a, 'pool': b})
    sample = {'mriya_hot_tokens': [{'ids': [a], 'kind': 'list', 'count': 1}],
              'raw_candidate_universe': [{'ids': [a,b], 'kind': 'list', 'count': 2}]}
    r = report(sample, [{'token': b}], [])
    assert r['mriya_raw_overlap'] == [a]
    assert r['mriya_exact_overlap'] == []
    assert r['execution_admission'] is False
    print('[ORACLE252_TEST_PASS] lineage=TRUE unknown_preserved=TRUE disarmed=TRUE')


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_ARMED')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('HOLD_RPC_NOT_CONFIGURED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as runtime
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

    if runtime.q87.c is not engine.c:
        raise RuntimeError('HOLD_RPC_GUARD_IDENTITY')
    originals = {}
    events = {}
    errors = []
    final = []
    rpc_original = runtime.q87.c.rpc

    def observe(name, func):
        def wrapped(*args, **kwargs):
            value = func(*args, **kwargs)
            try:
                ids = sorted(identities(value))
                count = len(value) if hasattr(value, '__len__') else None
                events.setdefault(name, []).append({
                    'ids': ids, 'kind': type(value).__name__, 'count': count
                })
            except Exception as exc:
                errors.append('OBSERVATION_' + type(exc).__name__)
            return value
        return wrapped

    try:
        runtime.q87.c.rpc = guard.restricted_rpc_factory(rpc_original)
        for name in ('mriya_hot_tokens', 'raw_candidate_universe'):
            fn = getattr(engine, name, None)
            if not callable(fn):
                errors.append('MISSING_' + name)
                continue
            originals[name] = fn
            setattr(engine, name, observe(name, fn))
        if len(originals) == 2:
            with contextlib.redirect_stdout(io.StringIO()):
                final = engine.candidate_universe(Path.cwd())
    except Exception as exc:
        errors.append('DISCOVERY_' + type(exc).__name__)
    finally:
        for name, fn in originals.items():
            setattr(engine, name, fn)
        runtime.q87.c.rpc = rpc_original

    result = report(events, final, errors)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE252_RESULT]', json.dumps({
        k: v for k, v in result.items()
        if k not in ('mriya_raw_overlap', 'mriya_exact_overlap',
                     'mriya_missing_from_raw', 'mriya_missing_from_exact')
    }, sort_keys=True))
    for key in ('mriya_raw_overlap', 'mriya_exact_overlap',
                'mriya_missing_from_raw', 'mriya_missing_from_exact'):
        print('[ORACLE252_LINEAGE]', key, json.dumps([x[:12] for x in result[key]]))
    print('[REPORT]', OUT)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    args = p.parse_args()
    if not args.test and not args.run:
        p.error('Specify --test or --run')
    if args.test:
        test()
    if args.run:
        run()