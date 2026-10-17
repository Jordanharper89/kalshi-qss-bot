"""ORACLE220: Resolve universal cross-venue identities; preserve watch history."""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import build_oracle_219_universal_registry_bridge as bridge

REPORT = bridge.ROOT / 'ORACLE220_UNIVERSAL_RESOLUTION.json'


def resolve(rows, resolver):
    accepted, rejects = {}, Counter()
    for row in rows:
        if not isinstance(row, dict):
            rejects['BAD_ROW'] += 1
            continue
        token, pump = row.get('token'), row.get('pump_pool')
        if not bridge.valid_key(token):
            rejects['BAD_MINT'] += 1
            continue
        if not bridge.valid_key(pump):
            rejects['BAD_PUMP_POOL'] += 1
            continue
        meta = row.get('meteora_meta')
        if not isinstance(meta, dict) or not bridge.valid_key(meta.get('address')):
            try:
                meta = resolver(token)
            except Exception as exc:
                rejects['DLMM_LOOKUP_' + type(exc).__name__[:32]] += 1
                continue
        if not isinstance(meta, dict) or not bridge.valid_key(meta.get('address')):
            rejects['NO_VALID_DLMM_ADDRESS'] += 1
            continue
        dlmm = meta['address']
        accepted[(token, pump, dlmm)] = dict(mint=token, pump_pool=pump,
                                              meteora_pool=dlmm)
    return list(accepted.values()), dict(rejects)


def test():
    mint = 'So11111111111111111111111111111111111111112'
    pool = '11111111111111111111111111111111'
    rows = [dict(token=mint, pump_pool=pool),
            dict(token=mint, pump_pool=pool, meteora_meta={'address':mint}),
            dict(token='SHORT', pump_pool=pool)]
    calls = []
    def resolver(token):
        calls.append(token)
        return {'address':mint}
    routes, bad = resolve(rows, resolver)
    assert len(routes) == 1 and bad == {'BAD_MINT':1} and calls == [mint]
    c = sqlite3.connect(':memory:')
    bridge.install(c)
    bridge.persist(c, routes, 1, '2026-10-10T00:00:00+00:00')
    assert c.execute('SELECT count(*) FROM universal_routes').fetchone()[0] == 1
    routes, bad = resolve([dict(token=mint, pump_pool=pool)],
                          lambda token: (_ for _ in ()).throw(ValueError('secret')))
    assert not routes and bad == {'DLMM_LOOKUP_ValueError':1}
    print('[ORACLE220_TEST_PASS] fallback_resolution=TRUE dedup=TRUE '
          'no_exception_detail=TRUE')


def worker():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze)
    freeze.freeze()
    if os.getenv('QSB_LIVE_ARM','').upper() == 'YES':
        raise RuntimeError('ORACLE220_ARMED_REFUSED')
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
        live_account_stream as pd)
    g = pd.prepare_pairs.__globals__
    engine, core = g['engine'], g['c']
    candidates = list(engine.candidate_universe(Path.cwd()))
    routes, rejects = resolve(candidates, core.discover_dlmm)
    bridge.ROOT.mkdir(parents=True, exist_ok=True)
    if routes:
        c = sqlite3.connect(bridge.DB, timeout=20)
        try:
            bridge.install(c)
            now = datetime.now(timezone.utc).isoformat()
            fingerprint = bridge.persist(c, routes, sum(rejects.values()), now)
            mints = c.execute('SELECT count(*) FROM watches WHERE universal=1').fetchone()[0]
            persistent = c.execute('SELECT count(*) FROM universal_routes').fetchone()[0]
        finally:
            c.close()
    else:
        fingerprint, mints, persistent = None, 0, 0
    report = dict(build='ORACLE220', raw_candidates=len(candidates),
                  accepted_routes=len(routes), rejects=rejects,
                  watched_mints=mints, persistent_routes=persistent,
                  fingerprint=fingerprint, source='candidate_universe+discover_dlmm',
                  pool_ownership_verified=False, profitability_verified=False,
                  mriya_feed_connected=False, signing=False, broadcast=False)
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE220_DISCOVERY] candidates=%d valid=%d rejected=%s' %
          (len(candidates), len(routes), rejects))
    print('[ORACLE220_REGISTRY] watched_mints=%d routes=%d' % (mints, persistent))
    print('[ORACLE220_SCOPE] history_retained=TRUE mriya=NOT_CONNECTED '
          'profit=NOT_CERTIFIED signing=FALSE broadcast=FALSE')
    print('[REPORT]', REPORT)
    freeze.freeze()
    return 0 if routes else 2


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze)
    freeze.freeze()
    import build_oracle_182_secure_windows_credentials as vault
    h = vault.load(vault.api(), vault.HELIUS)
    if not h:
        raise RuntimeError('ORACLE220_HELIUS_CREDENTIAL_MISSING')
    env = os.environ.copy()
    env['SOLANA_RPC_URL'] = ('https://mainnet.helius-rpc.com/?api-key='
                             + vault.quote(h, safe=''))
    env['SOLANA_WS_URL'] = ('wss://mainnet.helius-rpc.com/?api-key='
                            + vault.quote(h, safe=''))
    env['QSB_LIVE_ARM'] = 'NO'
    env.pop('QSB_SOLANA_PRIVATE_KEY', None)
    return subprocess.call([sys.executable, __file__, '--worker'], env=env)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    for value in ('test','run','worker'):
        mode.add_argument('--'+value, action='store_true')
    a = ap.parse_args()
    if a.test:
        test()
    else:
        sys.exit(run() if a.run else worker())