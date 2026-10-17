"""ORACLE219: Full-identity universal discovery -> persistent research watch registry."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE219_UNIVERSAL_BRIDGE.json'
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def valid_key(value):
    if not isinstance(value, str) or not 32 <= len(value) <= 44:
        return False
    n = 0
    for char in value:
        if char not in ALPHABET:
            return False
        n = n * 58 + ALPHABET.index(char)
    return (n.bit_length() + 7) // 8 + len(value) - len(value.lstrip('1')) == 32


def normalize(rows):
    out, rejected = {}, 0
    for x in rows:
        if not isinstance(x, dict):
            rejected += 1
            continue
        mint, pump = x.get('token'), x.get('pump_pool')
        meta = x.get('meteora_meta') or {}
        dlmm = meta.get('address') if isinstance(meta, dict) else None
        if not all(valid_key(z) for z in (mint, pump, dlmm)):
            rejected += 1
            continue
        identity = (mint, pump, dlmm)
        out[identity] = {
            'mint': mint,
            'pump_pool': pump,
            'meteora_pool': dlmm
        }
    return list(out.values()), rejected


def install(c):
    c.execute('PRAGMA busy_timeout=20000')
    c.executescript('''
      CREATE TABLE IF NOT EXISTS watches (
        mint TEXT PRIMARY KEY,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        universal INTEGER NOT NULL DEFAULT 0,
        mriya INTEGER NOT NULL DEFAULT 0,
        identity_verified INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS universal_routes (
        mint TEXT NOT NULL,
        pump_pool TEXT NOT NULL,
        meteora_pool TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        observations INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(mint,pump_pool,meteora_pool));
      CREATE TABLE IF NOT EXISTS discovery_rounds (
        fingerprint TEXT PRIMARY KEY,
        observed_at TEXT NOT NULL,
        valid_routes INTEGER NOT NULL,
        rejected_routes INTEGER NOT NULL);
    ''')


def persist(c, routes, rejected, now):
    material = json.dumps(
        sorted(routes, key=lambda x: (
            x['mint'], x['pump_pool'], x['meteora_pool']
        )),
        sort_keys=True
    )
    fingerprint = hashlib.sha256(
        material.encode('utf-8')
    ).hexdigest()

    with c:
        for row in routes:
            mint = row['mint']
            pump = row['pump_pool']
            dlmm = row['meteora_pool']
            c.execute('''
              INSERT INTO watches
              (mint,first_seen,last_seen,universal,mriya,identity_verified)
              VALUES(?,?,?,1,0,1)
              ON CONFLICT(mint) DO UPDATE SET
              last_seen=excluded.last_seen,
              universal=1,identity_verified=1
            ''', (mint, now, now))
            c.execute('''
              INSERT INTO universal_routes
              (mint,pump_pool,meteora_pool,first_seen,last_seen,observations)
              VALUES(?,?,?,?,?,1)
              ON CONFLICT(mint,pump_pool,meteora_pool)
              DO UPDATE SET last_seen=excluded.last_seen,
              observations=observations+1
            ''', (mint, pump, dlmm, now, now))

        c.execute('''
          INSERT OR IGNORE INTO discovery_rounds
          VALUES(?,?,?,?)
        ''', (fingerprint, now, len(routes), rejected))

    return fingerprint


def test():
    mint = 'So11111111111111111111111111111111111111112'
    pump = '11111111111111111111111111111111'
    rows = [
        {
            'token': mint,
            'pump_pool': pump,
            'meteora_meta': {'address': mint}
        },
        {
            'token': 'SHORT',
            'pump_pool': pump,
            'meteora_meta': {'address': mint}
        }
    ]
    routes, bad = normalize(rows)
    assert len(routes) == 1 and bad == 1

    c = sqlite3.connect(':memory:')
    install(c)
    persist(c, routes, bad, '2026-10-10T18:00:00+00:00')
    persist(c, routes, bad, '2026-10-10T18:01:00+00:00')

    assert c.execute(
        'SELECT count(*) FROM watches'
    ).fetchone()[0] == 1
    assert c.execute(
        'SELECT observations FROM universal_routes'
    ).fetchone()[0] == 2
    assert c.execute(
        'SELECT count(*) FROM discovery_rounds'
    ).fetchone()[0] == 1

    print('[ORACLE219_TEST_PASS] full_identity=TRUE '
          'persistent_routes=TRUE unchanged_round_dedup=TRUE')


def worker():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as f
    )
    f.freeze()
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE219_ARMED_REFUSED')

    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
        live_account_stream as pd
    )

    engine = pd.prepare_pairs.__globals__['engine']
    candidates = engine.candidate_universe(Path.cwd())
    routes, rejected = normalize(candidates)

    if not routes:
        print('[ORACLE219_HOLD] no full-identity cross-venue routes; '
              'database unchanged')
        return 2

    now = datetime.now(timezone.utc).isoformat()
    c = sqlite3.connect(DB, timeout=20)
    install(c)
    fingerprint = persist(c, routes, rejected, now)

    unique = c.execute(
        'SELECT count(*) FROM watches WHERE universal=1'
    ).fetchone()[0]
    total = c.execute(
        'SELECT count(*) FROM universal_routes'
    ).fetchone()[0]

    report = {
        'build': 'ORACLE219',
        'observed_at': now,
        'valid_routes': len(routes),
        'rejected': rejected,
        'total_watched_mints': unique,
        'total_routes': total,
        'fingerprint': fingerprint,
        'profit_certified': False,
        'mriya_verified': False,
        'signing': False,
        'broadcast': False
    }
    REPORT.write_text(
        json.dumps(report, indent=2),
        encoding='utf-8'
    )
    print('[ORACLE219_UNIVERSAL] valid=%d rejected=%d '
          'watched_mints=%d persistent_routes=%d' %
          (len(routes), rejected, unique, total))
    print('[ORACLE219_RESEARCH] watch_only=TRUE '
          'profit_certified=FALSE mriya_verified=FALSE broadcast=FALSE')
    print('[REPORT]', REPORT)
    f.freeze()
    return 0


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as f
    )
    f.freeze()

    import build_oracle_182_secure_windows_credentials as vault

    h = vault.load(vault.api(), vault.HELIUS)
    if not h:
        raise RuntimeError('ORACLE219_HELIUS_CREDENTIAL_MISSING')

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
        [sys.executable, __file__, '--worker'],
        env=env
    )


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
        sys.exit(run())
    else:
        sys.exit(worker())