"""ORACLE213: inspect strict DLMM incomplete quotes without altering execution."""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE213_DLMM_PARTIAL_EVIDENCE.json')
SIZES = (0.010, 0.015, 0.025, 0.050)


def pair_module(r):
    b2 = r.q25.prepare_once.__globals__['q60b2']
    b = b2.prepare_once.__globals__['q60b']
    return b.extended_prepare.__globals__['_ORIG_PREPARE'].__globals__['pd']


def summary(q, requested):
    remaining = getattr(q, 'remaining_in', None)
    complete = getattr(q, 'complete', None)
    return {
        'requested_raw': int(requested),
        'remaining_raw': int(remaining) if remaining is not None else None,
        'complete': complete if isinstance(complete, bool) else None,
        'bins_crossed': int(getattr(q, 'bins_crossed', 0) or 0),
        'output_raw': int(getattr(q, 'amount_out', 0) or 0),
    }


def test():
    class Q:
        complete = False
        remaining_in = 123
        bins_crossed = 2
        amount_out = 900
    result = summary(Q(), 1000)
    assert result['remaining_raw'] == 123 and result['complete'] is False
    assert result['requested_raw'] == 1000 and result['bins_crossed'] == 2
    assert not result['complete']
    print('[ORACLE213_TEST_PASS] partial_quantity_accounting=TRUE')


def run_worker():
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE213_ARMED_REFUSED')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        oracle186_direct_route_truth as d,
        runtime as r,
    )
    import meteora_dlmm

    freeze.freeze()
    d.safety()
    pd = pair_module(r)
    old_cap = pd.MAX_PAIRS
    old_rpc = r.q87.c.rpc
    bh_cls = type(r.BLOCKHASH)
    old_refresh = bh_cls.refresh
    old_quote = meteora_dlmm.quote
    if not isinstance(old_cap, int) or not 0 < old_cap <= 100:
        raise RuntimeError('ORACLE213_CAP_UNKNOWN')
    captures, failures, pairs, completed = [], [], [], 0
    context = {'token': None, 'size': None}

    def traced_quote(state, *args, **kwargs):
        requested = kwargs.get('amount_in', args[0] if args else None)
        record = {'token': context['token'], 'size_sol': context['size'],
                  'swap_for_y': kwargs.get('swap_for_y'), 'strict': kwargs.get('strict')}
        try:
            q = old_quote(state, *args, **kwargs)
            record.update(summary(q, requested))
            captures.append(record)
            return q
        except Exception as exc:
            record['quote_exception_type'] = type(exc).__name__
            captures.append(record)
            raise

    try:
        pd.MAX_PAIRS = max(old_cap, 12)
        r.q87.c.rpc = d.restricted_rpc_factory(old_rpc)
        bh_cls.refresh = lambda self: None
        meteora_dlmm.quote = traced_quote
        pairs, _ = d.bootstrap()
        for pair in pairs:
            token = str(pair.token)
            try:
                snap = r.immutable_snapshot(pair)
            except Exception as exc:
                failures.append({'token': token[:12], 'stage': 'SNAPSHOT',
                                 'type': type(exc).__name__})
                continue
            for size in SIZES:
                context.update(token=token[:12], size=size)
                try:
                    quotes = r.q18.exact_snapshot_opportunities(snap, size)
                    completed += len(quotes)
                except Exception as exc:
                    failures.append({'token': token[:12], 'size_sol': size,
                                     'stage': 'EXACT_QUOTE', 'type': type(exc).__name__,
                                     'code': str(exc) if str(exc) in (
                                         'DLMM_PARTIAL', 'DLMM_DIRECTION',
                                         'REVERSE_TOKEN_NET_ZERO', 'FORWARD_TOKEN_NET_ZERO')
                                     else 'UNCLASSIFIED'})
        counts = dict(Counter(x.get('code', x['type']) for x in failures))
        report = {'build': 'ORACLE213', 'mode': 'RESEARCH_ONLY',
                  'prepared_pairs': len(pairs), 'completed_quote_slots': completed,
                  'captured_dlmm_calls': captures, 'failures': failures,
                  'failure_codes': counts, 'max_pairs_restored': old_cap,
                  'signing': False, 'broadcast': False,
                  'profit_certified': False}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('[ORACLE213_RESULT] pairs=%d quotes=%d dlmm_calls=%d failures=%s broadcast=FALSE' %
              (len(pairs), completed, len(captures), counts), flush=True)
        for record in captures:
            if record.get('complete') is False or record.get('remaining_raw', 0) not in (0, None):
                print('[ORACLE213_PARTIAL] token=%s size=%.3f direction_to_y=%s input=%s remaining=%s bins=%s' %
                      (record['token'], record['size_sol'], record['swap_for_y'],
                       record.get('requested_raw'), record.get('remaining_raw'),
                       record.get('bins_crossed')), flush=True)
        print('[REPORT]', OUT, flush=True)
    finally:
        meteora_dlmm.quote = old_quote
        bh_cls.refresh = old_refresh
        r.q87.c.rpc = old_rpc
        pd.MAX_PAIRS = old_cap
        freeze.freeze()
        print('[ORACLE213_RESTORED] cap=%d freeze=PASS signing=FALSE broadcast=FALSE' % old_cap)


def launch():
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle199_opportunity_freeze as freeze
    freeze.freeze()
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    h, k = vault.load(db, vault.HELIUS), vault.load(db, vault.SOLANA)
    if not h or not k:
        raise RuntimeError('ORACLE213_CREDENTIALS_MISSING')
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
        run_worker()
