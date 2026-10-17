"""ORACLE-255: one-call, in-memory Mriya-to-Pump tape eligibility trace."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE255_MRIYA_TAPE_BOUNDARY.json')
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


def token(value):
    if isinstance(value, str) and B58.fullmatch(value):
        return value
    if isinstance(value, dict):
        for name in ('token', 'mint', 'token_mint', 'base_mint'):
            v = value.get(name)
            if isinstance(v, str) and B58.fullmatch(v):
                return v
    return None


def classify(hot, tape, raw):
    hot_ids = {x for row in hot if (x := token(row))}
    tape_ids = {str(row[0]) for row in tape if isinstance(row, (list, tuple)) and len(row) == 2 and B58.fullmatch(str(row[0]))}
    raw_ids = {x for row in raw if (x := token(row))}
    return [{'token': t, 'in_pump_tape': t in tape_ids,
             'in_raw_universe': t in raw_ids,
             'classification': ('IN_RAW' if t in raw_ids else
                                'NOT_IN_PUMP_TAPE' if t not in tape_ids else
                                'TAPE_MATCH_NOT_ADMITTED')}
            for t in sorted(hot_ids)]


def test():
    a, b, c = ('A'*32, 'B'*32, 'C'*32)
    rows = classify([{'token': a}, {'token': b}, {'token': c}],
                    [(a, {'pool': 'P'}), (b, {'pool': 'Q'})], [{'token': a}])
    assert [r['classification'] for r in rows] == ['IN_RAW', 'TAPE_MATCH_NOT_ADMITTED', 'NOT_IN_PUMP_TAPE']
    assert token({'private_key': a}) is None
    print('[ORACLE255_TEST_PASS] tape_join=TRUE exclusion_reasons=TRUE no_execution=TRUE')


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
    if r.q87.c is not engine.c:
        raise RuntimeError('RPC_GUARD_IDENTITY_UNPROVEN')
    fn = engine.raw_candidate_universe
    original_hot, original_rpc = engine.mriya_hot_tokens, r.q87.c.rpc
    seen = {'hot': [], 'tape': None, 'raw': [], 'trace_return': False}
    def hot_spy(*args, **kwargs):
        v = original_hot(*args, **kwargs)
        seen['hot'] = list(v) if isinstance(v, (tuple, list)) else []
        return v
    def trace(frame, event, arg):
        if frame.f_code is fn.__code__:
            if event == 'return':
                v = frame.f_locals.get('tape')
                if isinstance(v, (list, tuple)):
                    seen['tape'] = list(v)
                seen['trace_return'] = True
        return trace
    error = None
    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(original_rpc)
        engine.mriya_hot_tokens = hot_spy
        sys.settrace(trace)
        try:
            result = fn(Path.cwd())
            if isinstance(result, (list, tuple)):
                seen['raw'] = list(result)
            else:
                error = 'UNEXPECTED_RAW_RESULT_TYPE'
        finally:
            sys.settrace(None)
    except Exception as exc:
        error = type(exc).__name__
    finally:
        engine.mriya_hot_tokens = original_hot
        r.q87.c.rpc = original_rpc
    tape = seen['tape']
    rows = classify(seen['hot'], tape or [], seen['raw'])
    counts = {kind: sum(x['classification'] == kind for x in rows)
              for kind in ('IN_RAW', 'NOT_IN_PUMP_TAPE', 'TAPE_MATCH_NOT_ADMITTED')}
    report = {'build': 'ORACLE255', 'mriya_count': len(rows),
              'pump_tape_count': len(tape) if tape is not None else None,
              'raw_universe_count': len(seen['raw']), 'counts': counts,
              'rows': rows, 'tape_captured': tape is not None,
              'trace_return': seen['trace_return'], 'error': error,
              'live_freshness_certified': False, 'execution_admission': False,
              'signing': False, 'broadcast': False,
              'status': 'HOLD_LIVE_ORIGIN_AND_EXECUTION_UNVERIFIED'}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE255_RESULT]', json.dumps({k: v for k, v in report.items() if k != 'rows'}, sort_keys=True))
    for row in rows:
        print('[ORACLE255_MRIYA]', json.dumps({'token': row['token'][:12],
              'tape': row['in_pump_tape'], 'raw': row['in_raw_universe'],
              'reason': row['classification']}, sort_keys=True))
    print('[REPORT]', OUT)
    if error or tape is None:
        raise SystemExit(1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    a = ap.parse_args()
    if not (a.test or a.run):
        ap.error('Specify --test or --run')
    if a.test:
        test()
    if a.run:
        run()