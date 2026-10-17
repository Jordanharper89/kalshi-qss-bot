"""ORACLE212 isolated, read-only quote failure classifier."""
import argparse
import json
import os
import subprocess
import sys
import traceback
from collections import Counter
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE212_QUOTE_ROOT_CAUSE.json')
SIZES = (0.010, 0.015, 0.025, 0.050)
KNOWN = {'DLMM_PARTIAL', 'DLMM_DIRECTION', 'REVERSE_TOKEN_NET_ZERO',
         'FORWARD_TOKEN_NET_ZERO'}


def pair_module(r):
    b2 = r.q25.prepare_once.__globals__['q60b2']
    b = b2.prepare_once.__globals__['q60b']
    return b.extended_prepare.__globals__['_ORIG_PREPARE'].__globals__['pd']


def classify(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    last = frames[-1] if frames else None
    raw = str(exc)
    return {'exception': type(exc).__name__,
            'code': raw if raw in KNOWN else 'UNCLASSIFIED',
            'origin_file': Path(last.filename).name if last else 'UNKNOWN',
            'origin_function': last.name if last else 'UNKNOWN',
            'origin_line': last.lineno if last else 0}


def test():
    try:
        raise RuntimeError('DLMM_PARTIAL')
    except RuntimeError as exc:
        assert classify(exc)['code'] == 'DLMM_PARTIAL'
    try:
        raise RuntimeError('private_key=SECRET_VALUE')
    except RuntimeError as exc:
        x = classify(exc)
        assert x['code'] == 'UNCLASSIFIED'
        assert 'SECRET_VALUE' not in json.dumps(x)
    print('[ORACLE212_TEST_PASS] exact_codes=TRUE secret_redaction=TRUE')


def research():
    if os.environ.get('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE212_LIVE_ARM_REFUSED')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        oracle186_direct_route_truth as d,
        runtime as r,
    )
    freeze.freeze()
    d.safety()
    pd = pair_module(r)
    original_cap = pd.MAX_PAIRS
    original_rpc = r.q87.c.rpc
    blockhash_cls = type(r.BLOCKHASH)
    original_refresh = blockhash_cls.refresh
    if not isinstance(original_cap, int) or not 0 < original_cap <= 100:
        raise RuntimeError('ORACLE212_BAD_PAIR_CAP')
    errors, successful, pairs = [], [], []
    try:
        pd.MAX_PAIRS = max(original_cap, 12)
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)
        # Quotes read immutable pool snapshots; blockhash is only needed for
        # compiling/sending transactions, which this research never does.
        blockhash_cls.refresh = lambda self: None
        print('[ORACLE212_RESEARCH] cap=%d blockhash_refresh=SKIPPED '
              'signing=FALSE broadcast=FALSE' % pd.MAX_PAIRS, flush=True)
        pairs, _ = d.bootstrap()
        for pair in pairs:
            token = str(pair.token)
            try:
                snap = r.immutable_snapshot(pair)
            except Exception as exc:
                errors.append({'token': token[:12], 'stage': 'SNAPSHOT',
                               **classify(exc)})
                continue
            for size in SIZES:
                try:
                    quotes = r.q18.exact_snapshot_opportunities(snap, size)
                    successful.append({'token': token[:12], 'size_sol': size,
                                       'directions': [str(q.get('direction'))
                                                      for q in quotes]})
                except Exception as exc:
                    errors.append({'token': token[:12], 'size_sol': size,
                                   'stage': 'QUOTE', **classify(exc)})
    finally:
        blockhash_cls.refresh = original_refresh
        r.q87.c.rpc = original_rpc
        pd.MAX_PAIRS = original_cap
        freeze.freeze()
        print('[ORACLE212_RESTORED] cap=%d blockhash_refresh=ORIGINAL '
              'execution_freeze=PASS' % original_cap, flush=True)
    counts = dict(Counter(x['code'] for x in errors))
    report = {'build': 'ORACLE212', 'status': 'RESEARCH_ONLY',
              'prepared_pairs': len(pairs), 'successful_size_calls': len(successful),
              'successful_quote_slots': sum(len(x['directions']) for x in successful),
              'failure_count': len(errors), 'failures_by_code': counts,
              'errors': errors, 'successful': successful,
              'signing': False, 'broadcast': False,
              'profit_certified': False}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE212_RESULT] pairs=%d quote_slots=%d failures=%d codes=%s '
          'broadcast=FALSE' % (len(pairs), report['successful_quote_slots'],
                               len(errors), counts), flush=True)
    for e in errors:
        print('[ORACLE212_FAILURE] token=%s size=%s code=%s origin=%s:%s' %
              (e['token'], e.get('size_sol', '-'), e['code'],
               e['origin_file'], e['origin_line']), flush=True)
    print('[REPORT]', OUT, flush=True)


def launch():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
    )
    freeze.freeze()
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    h = vault.load(db, vault.HELIUS)
    k = vault.load(db, vault.SOLANA)
    if not h or not k:
        raise RuntimeError('ORACLE212_CREDENTIALS_MISSING')
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
    a = p.parse_args()
    if a.test:
        test()
    elif a.run:
        sys.exit(launch())
    else:
        research()