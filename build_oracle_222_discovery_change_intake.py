"""ORACLE222: Incremental universal discovery intake, never fabricated WS ticks."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import build_oracle_219_universal_registry_bridge as bridge
import build_oracle_220_universal_discovery_resolution as discovery
import build_oracle_221_persistent_watch_lifecycle as lifecycle

ROOT = bridge.ROOT
DB = bridge.DB
REPORT = ROOT / 'ORACLE222_DISCOVERY_CHANGE_INTAKE.json'


def refresh(c, candidates, resolver, now):
    routes, rejected = discovery.resolve(candidates, resolver)
    existing = set(c.execute(
        'SELECT mint,pump_pool,meteora_pool FROM universal_routes'
    ))
    new_routes = [
        r for r in routes
        if (r['mint'], r['pump_pool'], r['meteora_pool']) not in existing
    ]
    stats = {
        'new_routes': len(new_routes),
        'observations': 0,
        'duplicates': 0,
        'rejected': rejected,
        'resolved': len(routes)
    }
    with c:
        if routes:
            bridge.persist(
                c, routes, sum(rejected.values()), now.isoformat()
            )
        for r in new_routes:
            route = (
                r['mint'], r['pump_pool'], r['meteora_pool']
            )
            event_id = 'discovery:' + hashlib.sha256(
                '|'.join(route).encode()
            ).hexdigest()
            event = dict(
                r,
                source='UNIVERSAL_DISCOVERY',
                source_event_id=event_id,
                kind='PAIR_DISCOVERED',
                observed_at=now.isoformat()
            )
            result = lifecycle.ingest(c, event, now)
            key = 'duplicates' if result == 'DUPLICATE' else 'observations'
            stats[key] += 1
    return stats


def test():
    c = sqlite3.connect(':memory:')
    bridge.install(c)
    lifecycle.schema(c)

    m = 'So11111111111111111111111111111111111111112'
    p = '11111111111111111111111111111111'
    candidates = [{'token': m, 'pump_pool': p}]
    now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
    resolver = lambda _: {'address': m}

    a = refresh(c, candidates, resolver, now)
    b = refresh(c, candidates, resolver, now)

    assert a['new_routes'] == 1
    assert a['observations'] == 1
    assert b['new_routes'] == 0
    assert b['observations'] == 0
    assert c.execute(
        'SELECT count(*) FROM watch_events'
    ).fetchone()[0] == 1
    assert c.execute(
        'SELECT count(*) FROM reprice_queue'
    ).fetchone()[0] == 1
    assert c.execute(
        'SELECT count(*) FROM watches'
    ).fetchone()[0] == 1

    print(
        '[ORACLE222_TEST_PASS] fresh_discovery=TRUE '
        'unchanged_no_event=TRUE history=TRUE'
    )


def worker():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze
    )
    freeze.freeze()

    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE222_ARMED_REFUSED')
    if not DB.is_file():
        raise RuntimeError('ORACLE218_DB_MISSING')

    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
        live_account_stream as pd
    )
    g = pd.prepare_pairs.__globals__
    rows = list(g['engine'].candidate_universe(Path.cwd()))

    c = sqlite3.connect(DB, timeout=20)
    try:
        bridge.install(c)
        lifecycle.schema(c)
        stats = refresh(
            c, rows, g['c'].discover_dlmm,
            datetime.now(timezone.utc)
        )
        stats['persistent_routes'] = c.execute(
            'SELECT count(*) FROM universal_routes'
        ).fetchone()[0]
        stats['persistent_mints'] = c.execute(
            'SELECT count(*) FROM watches'
        ).fetchone()[0]
        stats['pending'] = c.execute(
            "SELECT count(*) FROM reprice_queue "
            "WHERE status='PENDING_REVALIDATION'"
        ).fetchone()[0]
        stats['discovery_rows'] = len(rows)
    finally:
        c.close()

    ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        'build': 'ORACLE222',
        **stats,
        'scope': 'DISCOVERY_CHANGE_ONLY',
        'ws_prices_connected': False,
        'mriya_verified': False,
        'profit_certified': False,
        'signing': False,
        'broadcast': False
    }
    REPORT.write_text(
        json.dumps(report, indent=2), encoding='utf-8'
    )

    print('[ORACLE222_INTAKE]', json.dumps(stats, sort_keys=True))
    print(
        '[ORACLE222_SCOPE] new_routes_only=TRUE '
        'ws=NOT_CONNECTED mriya=NOT_CONNECTED broadcast=FALSE'
    )
    print('[REPORT]', REPORT)
    freeze.freeze()
    return 0


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze
    )
    freeze.freeze()

    import build_oracle_182_secure_windows_credentials as vault
    h = vault.load(vault.api(), vault.HELIUS)
    if not h:
        raise RuntimeError('ORACLE222_HELIUS_CREDENTIAL_MISSING')

    env = os.environ.copy()
    env['SOLANA_RPC_URL'] = (
        'https://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['SOLANA_WS_URL'] = (
        'wss://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['QSB_LIVE_ARM'] = 'NO'
    env.pop('QSB_SOLANA_PRIVATE_KEY', None)

    return subprocess.call(
        [sys.executable, __file__, '--worker'], env=env
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    modes = p.add_mutually_exclusive_group(required=True)
    for name in ('test', 'run', 'worker'):
        modes.add_argument('--' + name, action='store_true')
    a = p.parse_args()

    if a.test:
        test()
    else:
        sys.exit(run() if a.run else worker())