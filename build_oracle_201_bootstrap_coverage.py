"""ORACLE201 read-only pair admission evidence; existing executor is never edited."""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

STATE = Path('runtime_state/oracle/oracle_live_execution')
OUT = STATE / 'ORACLE201_BOOTSTRAP_COVERAGE.json'


def classify(tokens, ready, admitted, failed):
    rows = []
    for token in tokens:
        if token in admitted:
            status = 'ADMITTED'
        elif token not in ready:
            status = 'NOT_READY_TOKEN'
        elif token in failed:
            status = 'PUMP_WARM_FAILED'
        else:
            status = 'READY_NOT_ADMITTED_UNEXPLAINED'
        rows.append({'token': token[:12], 'status': status,
                     'warm_failure_type': failed.get(token)})
    return rows

def test():
    rows = classify(['A', 'B', 'C', 'D'], {'A', 'B', 'D'}, {'A'}, {'B': 'ValueError'})
    assert [x['status'] for x in rows] == [
        'ADMITTED', 'PUMP_WARM_FAILED', 'NOT_READY_TOKEN',
        'READY_NOT_ADMITTED_UNEXPLAINED']
    print('[TEST PASS] ORACLE201 admission partition and fail-closed classification')

def worker():
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE201_LIVE_ARM_REFUSED')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze,
        oracle186_direct_route_truth as d,
        runtime as r,
    )
    freeze.freeze()
    d.safety()
    old_rpc = r.q87.c.rpc
    old_prepare = r.q25.prepare_once
    old_worker = r.q18.worker
    observed = {'state': None}
    failed = {}

    def capture_prepare(*args, **kwargs):
        result = old_prepare(*args, **kwargs)
        observed['state'] = result[0]
        return result

    class WorkerProxy:
        def __init__(self, underlying):
            self._underlying = underlying
        def warm(self, pool):
            try:
                return self._underlying.warm(pool)
            except Exception as exc:
                failed[str(pool)] = type(exc).__name__
                raise

    def monitored_worker():
        return WorkerProxy(old_worker())

    pairs = []
    try:
        r.q87.c.rpc = d.restricted_rpc_factory(old_rpc)
        r.q25.prepare_once = capture_prepare
        r.q18.worker = monitored_worker
        pairs, _ = d.bootstrap()
        state = observed['state']
        if not isinstance(state, dict):
            raise RuntimeError('ORACLE201_STATE_NOT_CAPTURED')
        all_pairs = list(state.get('pairs') or [])
        ready = {str(x) for x in r.READY_TOKENS}
        admitted = {str(p.token) for p in pairs}
        failed_by_token = {str(p.token): failed[str(p.pump_pool)]
                           for p in all_pairs if str(p.pump_pool) in failed}
        tokens = list(dict.fromkeys(str(p.token) for p in all_pairs))
        rows = classify(tokens, ready, admitted, failed_by_token)
        counts = dict(Counter(x['status'] for x in rows))
        report = {
            'build': 'ORACLE201', 'status': 'READ_ONLY_ADMISSION_EVIDENCE',
            'state_pair_count': len(all_pairs),
            'unique_token_count': len(tokens),
            'ready_token_count': sum(t in ready for t in tokens),
            'admitted_pair_count': len(pairs),
            'counts': counts, 'rows': rows,
            'execution_authorized': False, 'broadcast': False,
            'profit_certified': False,
        }
        STATE.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('[ORACLE201_COVERAGE] discovered=%d ready=%d admitted=%d statuses=%s broadcast=FALSE' %
              (len(all_pairs), report['ready_token_count'], len(pairs), counts))
        for row in rows:
            print('[ORACLE201_PAIR] token=%s status=%s warm_error=%s' %
                  (row['token'], row['status'], row['warm_failure_type'] or 'NONE'))
        print('[REPORT]', OUT)
    finally:
        r.q18.worker = old_worker
        r.q25.prepare_once = old_prepare
        r.q87.c.rpc = old_rpc
        w = getattr(r.q18, '_worker', None)
        if w is not None:
            try:
                w.close()
                r.q18._worker = None
            except Exception:
                pass
        freeze.freeze()

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
        raise RuntimeError('ORACLE201_CREDENTIALS_MISSING')
    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = k
    env['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['SOLANA_WS_URL'] = 'wss://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['QSB_LIVE_ARM'] = 'NO'
    return subprocess.call([sys.executable, __file__, '--worker'], env=env)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', action='store_true')
    group.add_argument('--run', action='store_true')
    group.add_argument('--worker', action='store_true')
    a = parser.parse_args()
    if a.test:
        test()
    elif a.run:
        sys.exit(launch())
    else:
        worker()