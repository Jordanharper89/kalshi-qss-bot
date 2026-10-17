
from __future__ import annotations
import argparse, base64, hashlib, sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

DEST = Path('qseries_v2/oracle_execution/oracle_live_pricing/oracle226.py')
REGISTRY = Path('runtime_state/oracle/oracle_live_execution/ORACLE218_DISCOVERY.sqlite3')
CACHE = Path('runtime_state/oracle/oracle_live_execution/ORACLE226_ACCOUNT_STATES.sqlite3')
MARKER = 'ORACLE226_CANONICAL_RAW_ACCOUNT_STATE_V2'

def stamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('TIMESTAMP_MUST_BE_UTC_AWARE')
    return dt.astimezone(timezone.utc)

def routes(registry=REGISTRY):
    if not registry.is_file():
        raise RuntimeError('HOLD_NO_ORACLE218_REGISTRY')
    with closing(sqlite3.connect(registry.resolve().as_uri()+'?mode=ro', uri=True)) as c:
        rows = c.execute('SELECT mint,pump_pool,meteora_pool FROM universal_routes').fetchall()
    return {pool for mint,pump,dlmm in rows for pool in (pump,dlmm)}

def initialize(cache=CACHE):
    cache.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(cache, timeout=10)) as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('''CREATE TABLE IF NOT EXISTS account_states(
          event_id TEXT PRIMARY KEY, address TEXT NOT NULL, slot INTEGER NOT NULL,
          owner TEXT NOT NULL, payload BLOB NOT NULL, digest TEXT NOT NULL,
          observed_at TEXT NOT NULL, received_at TEXT NOT NULL)''')
        c.execute('CREATE INDEX IF NOT EXISTS state_lookup ON account_states(address,slot DESC)')
        c.commit()

def ingest(address, slot, owner, data64, observed_at, registry=REGISTRY, cache=CACHE):
    if address not in routes(registry):
        raise ValueError('UNREGISTERED_POOL')
    if type(slot) is not int or slot <= 0:
        raise ValueError('INVALID_SLOT')
    if not isinstance(owner,str) or not 32 <= len(owner) <= 44:
        raise ValueError('OWNER_REQUIRED')
    when = stamp(observed_at)
    now = datetime.now(timezone.utc)
    if abs((now-when).total_seconds()) > 30:
        raise ValueError('STALE_OR_FUTURE_EVENT')
    raw = base64.b64decode(data64, validate=True)
    if not 1 <= len(raw) <= 1048576:
        raise ValueError('INVALID_ACCOUNT_PAYLOAD_LENGTH')
    digest = hashlib.sha256(raw).hexdigest()
    eid = hashlib.sha256(f'{address}|{slot}|{digest}'.encode()).hexdigest()
    initialize(cache)
    with closing(sqlite3.connect(cache, timeout=10)) as c:
        c.execute('''INSERT OR IGNORE INTO account_states VALUES(?,?,?,?,?,?,?,?)''',
                  (eid,address,slot,owner,raw,digest,when.isoformat(),now.isoformat()))
        c.commit()
    return {'event_id':eid,'address':address,'slot':slot,'digest':digest,'bytes':len(raw)}

def install():
    source = Path(__file__).read_bytes()
    if DEST.exists() and DEST.read_bytes() != source:
        old = DEST.read_text(encoding='utf-8-sig')
        if 'ORACLE226_INSTALLED' not in old or 'def ingest(' not in old:
            raise RuntimeError('REFUSE_UNRECOGNIZED_ORACLE226_OVERWRITE')
    DEST.parent.mkdir(parents=True, exist_ok=True)
    init = DEST.parent/'__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')
    DEST.write_bytes(source)
    print('[ORACLE226_INSTALLED]', DEST)

def test():
    with TemporaryDirectory() as td:
        r=Path(td)/'registry.sqlite3'
        c=Path(td)/'cache.sqlite3'
        with closing(sqlite3.connect(r)) as db:
            db.execute('CREATE TABLE universal_routes(mint,pump_pool,meteora_pool)')
            db.execute('INSERT INTO universal_routes VALUES(?,?,?)',('mint','pump','dlmm'))
            db.commit()
        ts=datetime.now(timezone.utc).isoformat()
        obj=ingest('pump',1,'1'*32,base64.b64encode(b'abc').decode(),ts,r,c)
        assert obj['bytes']==3
        assert ingest('pump',1,'1'*32,'YWJj',ts,r,c)['event_id']==obj['event_id']
        with closing(sqlite3.connect(c)) as db:
            assert db.execute('SELECT count(*) FROM account_states').fetchone()[0]==1
        try:
            ingest('unknown',1,'1'*32,'YWJj',ts,r,c)
        except ValueError:
            pass
        else:
            raise AssertionError('UNREGISTERED_ACCOUNT_ACCEPTED')
    print('[ORACLE226_TEST_PASS] windows_sqlite_handles_closed=TRUE raw_bytes_retained=TRUE dedup=TRUE')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--install',action='store_true')
    ap.add_argument('--test',action='store_true')
    a=ap.parse_args()
    if a.install: install()
    if a.test: test()
    if not a.install and not a.test: ap.print_help()
