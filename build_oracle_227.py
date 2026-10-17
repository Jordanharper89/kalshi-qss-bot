from __future__ import annotations
import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

DEST = Path(
    'qseries_v2/oracle_execution/oracle_live_pricing/oracle227.py'
)
CACHE = Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE226_ACCOUNT_STATES.sqlite3'
)
REGISTRY = Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE218_DISCOVERY.sqlite3'
)
BUILD = 'ORACLE227_SYNCHRONIZED_SNAPSHOTS_V2'


def read_db(path):
    if not path.is_file():
        raise RuntimeError('HOLD_MISSING_DATABASE')
    return sqlite3.connect(
        path.resolve().as_uri() + '?mode=ro',
        uri=True
    )


def snapshot(
    mint, pump, dlmm, now=None,
    cache=CACHE, registry=REGISTRY,
    max_age_seconds=15, max_slot_skew=2
):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('NAIVE_NOW')

    with closing(read_db(registry)) as db:
        route = db.execute(
            'SELECT 1 FROM universal_routes '
            'WHERE mint=? AND pump_pool=? AND meteora_pool=?',
            (mint, pump, dlmm)
        ).fetchone()

    if not route:
        return {'ok': False, 'reason': 'ROUTE_NOT_REGISTERED'}

    rows = []
    with closing(read_db(cache)) as db:
        for address in (pump, dlmm):
            row = db.execute(
                'SELECT event_id,address,slot,owner,payload,'
                'digest,observed_at FROM account_states '
                'WHERE address=? '
                'ORDER BY slot DESC,received_at DESC LIMIT 1',
                (address,)
            ).fetchone()

            if row is None:
                return {
                    'ok': False,
                    'reason': 'MISSING_ACCOUNT_BYTES',
                    'address': address
                }

            rows.append(dict(zip(
                ('event_id', 'address', 'slot', 'owner',
                 'payload', 'digest', 'observed_at'),
                row
            )))

    for item in rows:
        dt = datetime.fromisoformat(item['observed_at'])
        if dt.tzinfo is None:
            return {'ok': False, 'reason': 'NAIVE_EVENT_TIME'}

        age = (now - dt).total_seconds()

        if age < -2 or age > max_age_seconds:
            return {
                'ok': False,
                'reason': 'STALE_ACCOUNT',
                'address': item['address']
            }

        if not item['payload']:
            return {'ok': False, 'reason': 'EMPTY_PAYLOAD'}

    if abs(rows[0]['slot'] - rows[1]['slot']) > max_slot_skew:
        return {'ok': False, 'reason': 'SLOT_SKEW'}

    return {
        'ok': True,
        'mint': mint,
        'pump': rows[0],
        'meteora': rows[1],
        'min_slot': min(x['slot'] for x in rows),
        'max_slot': max(x['slot'] for x in rows),
        'atomic_slot_certified': False,
        'execution_authority': False
    }


def install():
    source = Path(__file__).read_bytes()

    if DEST.exists() and DEST.read_bytes() != source:
        old = DEST.read_text(encoding='utf-8-sig')
        if ('ORACLE227_INSTALLED' not in old or
                'def snapshot(' not in old):
            raise RuntimeError(
                'REFUSE_UNRECOGNIZED_ORACLE227_OVERWRITE'
            )

    DEST.parent.mkdir(parents=True, exist_ok=True)
    init = DEST.parent / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

    DEST.write_bytes(source)
    print('[ORACLE227_INSTALLED]', DEST)


def test():
    with TemporaryDirectory() as td:
        folder = Path(td)
        cache = folder / 'cache.sqlite3'
        registry = folder / 'registry.sqlite3'
        now = datetime.now(timezone.utc).isoformat()

        with closing(sqlite3.connect(registry)) as db:
            db.execute(
                'CREATE TABLE universal_routes'
                '(mint,pump_pool,meteora_pool)'
            )
            db.execute(
                'INSERT INTO universal_routes VALUES(?,?,?)',
                ('mint', 'pump', 'dlmm')
            )
            db.commit()

        with closing(sqlite3.connect(cache)) as db:
            db.execute(
                'CREATE TABLE account_states'
                '(event_id,address,slot,owner,payload,'
                'digest,observed_at,received_at)'
            )
            db.executemany(
                'INSERT INTO account_states VALUES'
                '(?,?,?,?,?,?,?,?)',
                [
                    ('a', 'pump', 10, 'owner',
                     b'raw1', 'digest', now, now),
                    ('b', 'dlmm', 11, 'owner',
                     b'raw2', 'digest', now, now)
                ]
            )
            db.commit()

        result = snapshot(
            'mint', 'pump', 'dlmm',
            cache=cache, registry=registry
        )

        assert result['ok']
        assert result['pump']['payload'] == b'raw1'
        assert result['meteora']['payload'] == b'raw2'
        assert result['atomic_slot_certified'] is False

        with closing(sqlite3.connect(cache)) as db:
            db.execute(
                'UPDATE account_states SET slot=20 '
                'WHERE address=?', ('dlmm',)
            )
            db.commit()

        result = snapshot(
            'mint', 'pump', 'dlmm',
            cache=cache, registry=registry
        )
        assert result['reason'] == 'SLOT_SKEW'

    print(
        '[ORACLE227_TEST_PASS] '
        'windows_sqlite_handles_closed=TRUE '
        'dual_pool=TRUE '
        'byte_fidelity=TRUE '
        'slot_skew_rejection=TRUE'
    )


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()

    if args.install:
        install()
    if args.test:
        test()
    if not args.install and not args.test:
        ap.print_help()