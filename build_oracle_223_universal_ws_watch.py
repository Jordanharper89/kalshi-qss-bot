"""ORACLE223: Read-only Solana WebSocket account updates to watch queue."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import build_oracle_221_persistent_watch_lifecycle as watch

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE223_WS_WATCH.json'


def targets(c, limit):
    rows = c.execute(
        'SELECT mint,pump_pool,meteora_pool FROM universal_routes '
        'ORDER BY last_seen DESC LIMIT ?', (limit,)
    ).fetchall()
    lookup = defaultdict(set)
    for route in rows:
        for address in (route[1], route[2]):
            lookup[address].add(tuple(route))
    return dict(lookup), len(rows)


def decode_notification(msg, subscriptions):
    if msg.get('method') != 'accountNotification':
        return None
    p = msg.get('params')
    if not isinstance(p, dict) or not isinstance(p.get('result'), dict):
        return None
    address = subscriptions.get(p.get('subscription'))
    result = p['result']
    slot = result.get('context', {}).get('slot')
    value = result.get('value')
    if not address or not isinstance(slot, int) or slot < 1:
        return None
    if not isinstance(value, dict):
        return None
    data = value.get('data')
    if not isinstance(data, list) or len(data) != 2 or data[1] != 'base64':
        return None
    try:
        raw = base64.b64decode(data[0], validate=True)
    except (ValueError, TypeError):
        return None
    return address, slot, hashlib.sha256(raw).hexdigest()


def test():
    key = '11111111111111111111111111111111'
    payload = {
        'method': 'accountNotification',
        'params': {
            'subscription': 7,
            'result': {
                'context': {'slot': 123},
                'value': {'data': ['YWJj', 'base64']}
            }
        }
    }
    result = decode_notification(payload, {7: key})
    assert result == (key, 123, hashlib.sha256(b'abc').hexdigest())
    assert decode_notification(payload, {}) is None

    c = sqlite3.connect(':memory:')
    c.execute(
        'CREATE TABLE universal_routes'
        '(mint,pump_pool,meteora_pool,last_seen)'
    )
    c.execute(
        'INSERT INTO universal_routes VALUES(?,?,?,?)',
        (key, key, key, 'a')
    )
    addresses, n = targets(c, 10)
    assert n == 1 and len(addresses) == 1

    print(
        '[ORACLE223_TEST_PASS] subscription_mapping=TRUE '
        'payload_hash=TRUE route_dedup=TRUE'
    )


async def observe(url, minutes, limit):
    try:
        import websockets
    except ImportError as exc:
        raise RuntimeError(
            'INSTALL_DEPENDENCY: python -m pip install websockets'
        ) from exc

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze
    )
    freeze.freeze()

    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE223_ARMED_REFUSED')

    c = sqlite3.connect(DB, timeout=20)
    watch.schema(c)
    address_routes, count = targets(c, limit)

    if not count:
        c.close()
        raise RuntimeError('ORACLE223_NO_REGISTERED_ROUTES')

    stats = Counter()
    subs = {}
    requests = {}
    end = asyncio.get_running_loop().time() + minutes * 60

    try:
        async with websockets.connect(
            url,
            max_size=8 * 1024 * 1024,
            ping_interval=20,
            open_timeout=15
        ) as ws:

            for i, address in enumerate(address_routes, 1):
                requests[i] = address
                await ws.send(json.dumps({
                    'jsonrpc': '2.0',
                    'id': i,
                    'method': 'accountSubscribe',
                    'params': [
                        address,
                        {
                            'encoding': 'base64',
                            'commitment': 'confirmed'
                        }
                    ]
                }))

            print(
                '[ORACLE223_SUBMITTED] routes=%d unique_accounts=%d'
                % (count, len(requests)),
                flush=True
            )

            while asyncio.get_running_loop().time() < end:
                try:
                    remaining = max(
                        .01,
                        end - asyncio.get_running_loop().time()
                    )
                    message = await asyncio.wait_for(
                        ws.recv(),
                        timeout=min(5, remaining)
                    )
                    msg = json.loads(message)
                except asyncio.TimeoutError:
                    continue

                if not isinstance(msg, dict):
                    continue

                if isinstance(msg.get('id'), int) and msg['id'] in requests:
                    if isinstance(msg.get('result'), int):
                        subs[msg['result']] = requests[msg['id']]
                        stats['subscriptions_acknowledged'] += 1
                    else:
                        stats['subscriptions_rejected'] += 1
                    continue

                event = decode_notification(msg, subs)
                if event is None:
                    stats['ignored_messages'] += 1
                    continue

                address, slot, digest = event
                stamp = datetime.now(timezone.utc)

                for route in address_routes.get(address, ()):
                    record = dict(zip(
                        ('mint', 'pump_pool', 'meteora_pool'),
                        route
                    ))

                    identity = (
                        address + '|' + str(slot) + '|' + digest +
                        '|' + '|'.join(route)
                    )

                    record.update(
                        source='UNIVERSAL_WS',
                        kind='POOL_UPDATE',
                        observed_at=stamp.isoformat(),
                        source_event_id=hashlib.sha256(
                            identity.encode()
                        ).hexdigest()
                    )

                    with c:
                        result = watch.ingest(c, record, stamp)

                    stats[result] += 1
                    stats['notifications_mapped'] += 1

    finally:
        out = {
            'build': 'ORACLE223',
            'scanned_routes': count,
            'unique_accounts': len(address_routes),
            'stats': dict(stats),
            'transport': 'wss_accountSubscribe',
            'replay_certified': False,
            'pool_ownership_certified': False,
            'price_certified': False,
            'mriya_connected': False,
            'signing': False,
            'broadcast': False
        }

        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(out, indent=2),
            encoding='utf-8'
        )
        c.close()
        freeze.freeze()

        print(
            '[ORACLE223_RESULT]',
            json.dumps(out, sort_keys=True),
            flush=True
        )
        print('[REPORT]', REPORT, flush=True)


def run(minutes, limit):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze
    )
    freeze.freeze()

    import build_oracle_182_secure_windows_credentials as vault
    key = vault.load(vault.api(), vault.HELIUS)

    if not key:
        raise RuntimeError('ORACLE223_HELIUS_CREDENTIAL_MISSING')

    env = os.environ.copy()
    env['SOLANA_WS_URL'] = (
        'wss://mainnet.helius-rpc.com/?api-key='
        + vault.quote(key, safe='')
    )
    env['QSB_LIVE_ARM'] = 'NO'
    env.pop('QSB_SOLANA_PRIVATE_KEY', None)

    return subprocess.call(
        [
            sys.executable,
            __file__,
            '--worker',
            '--minutes',
            str(minutes),
            '--limit',
            str(limit)
        ],
        env=env
    )


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    modes = ap.add_mutually_exclusive_group(required=True)

    for name in ('test', 'run', 'worker'):
        modes.add_argument('--' + name, action='store_true')

    ap.add_argument('--minutes', type=float, default=1)
    ap.add_argument('--limit', type=int, default=12)

    args = ap.parse_args()

    if not 0 < args.minutes <= 5 or not 0 < args.limit <= 100:
        ap.error('minutes: (0,5]; limit: 1..100')

    if args.test:
        test()
    elif args.run:
        sys.exit(run(args.minutes, args.limit))
    else:
        asyncio.run(
            observe(
                os.environ['SOLANA_WS_URL'],
                args.minutes,
                args.limit
            )
        )