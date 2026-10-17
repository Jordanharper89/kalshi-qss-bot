"""ORACLE209: read-only exact quote failure evidence across expanded pairs."""
import argparse
import json
import os
import subprocess
import sys
import traceback
from collections import Counter
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE209_QUOTE_FAILURE_TRACE.json')
SIZES = (0.010, 0.015, 0.025, 0.050)
CAP = 12


def pair_module(r):
    q60b2 = r.q25.prepare_once.__globals__['q60b2']
    q60b = q60b2.prepare_once.__globals__['q60b']
    orig = q60b.extended_prepare.__globals__['_ORIG_PREPARE']
    return orig.__globals__['pd']


def error_evidence(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    return {'exception_type': type(exc).__name__,
            'trace': [{'file': Path(f.filename).name, 'function': f.name,
                       'line': f.lineno} for f in frames[-7:]]}


def test():
    try:
        def local_failure():
            raise RuntimeError('SECRET_SHOULD_NOT_APPEAR')
        local_failure()
    except RuntimeError as exc:
        e = error_evidence(exc)
    assert e['exception_type'] == 'RuntimeError'
    assert any(f['function'] == 'local_failure' for f in e['trace'])
    assert 'SECRET_SHOULD_NOT_APPEAR' not in json.dumps(e)
    print('[ORACLE209_TEST_PASS] safe_exception_location=TRUE secret_values_excluded=TRUE')


def research():
    if os.environ.get('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE209_LIVE_ARM_REFUSED')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as ranker,
        oracle186_direct_route_truth as diagnostic,
        runtime as r,
    )
    ranker.freeze()
    diagnostic.safety()
    pd = pair_module(r)
    old_cap, old_rpc = pd.MAX_PAIRS, r.q87.c.rpc
    if not isinstance(old_cap, int) or not 0 < old_cap <= 100:
        raise RuntimeError('ORACLE209_CAP_UNKNOWN')
    errors, quoted, pairs, positive = [], [], [], 0
    try:
        pd.MAX_PAIRS = max(CAP, old_cap)
        r.q87.c.rpc = diagnostic.restricted_rpc_factory(old_rpc)
        pairs, _ = diagnostic.bootstrap()
        for pair in pairs:
            token = str(pair.token)
            try:
                snapshot = r.immutable_snapshot(pair)
            except Exception as exc:
                errors.append({'token': token[:12], 'stage': 'SNAPSHOT',
                               **error_evidence(exc)})
                continue
            for size in SIZES:
                try:
                    quotes = r.q18.exact_snapshot_opportunities(snapshot, size)
                    evaluated = ranker.evaluate(quotes, token, size)
                    quoted.extend(evaluated)
                    positive += sum(bool(x['research_eligible']) for x in evaluated)
                except Exception as exc:
                    errors.append({'token': token[:12], 'size_sol': size,
                                   'stage': 'QUOTE', **error_evidence(exc)})
    finally:
        pd.MAX_PAIRS = old_cap
        r.q87.c.rpc = old_rpc
        w = getattr(r.q18, '_worker', None)
        if w is not None:
            try:
                w.close()
                r.q18._worker = None
            except Exception:
                pass
        ranker.freeze()
        print('[ORACLE209_RESTORED] cap=%d freeze=PASS broadcast=FALSE' % old_cap)
    summary = dict(Counter((x['stage'] + ':' + x['exception_type']) for x in errors))
    report = {'build': 'ORACLE209', 'status': 'RESEARCH_ONLY',
              'pairs': len(pairs), 'quotes': len(quoted),
              'provisional_positive': positive, 'error_summary': summary,
              'errors': errors, 'execution_authorized': False,
              'signing': False, 'broadcast': False}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE209_COVERAGE] pairs=%d quotes=%d positive=%d errors=%d broadcast=FALSE' %
          (len(pairs), len(quoted), positive, len(errors)))
    for e in errors:
        origin = e['trace'][-1] if e['trace'] else {'file': 'UNKNOWN', 'function': 'UNKNOWN', 'line': 0}
        print('[ORACLE209_FAILURE] token=%s size=%s type=%s origin=%s:%d function=%s' %
              (e['token'], e.get('size_sol', 'N/A'), e['exception_type'],
               origin['file'], origin['line'], origin['function']))
    print('[REPORT]', OUT)


def launch():
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle199_opportunity_freeze as f
    f.freeze()
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    h, k = vault.load(db, vault.HELIUS), vault.load(db, vault.SOLANA)
    if not h or not k:
        raise RuntimeError('ORACLE209_CREDENTIALS_MISSING')
    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = k
    env['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['SOLANA_WS_URL'] = 'wss://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['QSB_LIVE_ARM'] = 'NO'
    return subprocess.call([sys.executable, __file__, '--worker'], env=env)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--run', action='store_true')
    g.add_argument('--worker', action='store_true')
    args = p.parse_args()
    if args.test:
        test()
    elif args.run:
        sys.exit(launch())
    else:
        research()