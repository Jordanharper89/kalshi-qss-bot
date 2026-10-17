"""ORACLE221: durable watch lifecycle and read-only repricing queue."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE221_WATCH_LIFECYCLE.json'
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def valid_key(v):
    if not isinstance(v, str) or not 32 <= len(v) <= 44:
        return False
    n = 0
    for ch in v:
        if ch not in ALPHABET:
            return False
        n = n * 58 + ALPHABET.index(ch)
    return (n.bit_length() + 7)//8 + len(v) - len(v.lstrip('1')) == 32


def schema(c):
    c.execute('PRAGMA busy_timeout=20000')
    c.executescript('''
    CREATE TABLE IF NOT EXISTS watch_events (
      id INTEGER PRIMARY KEY, mint TEXT NOT NULL, pump_pool TEXT NOT NULL,
      meteora_pool TEXT NOT NULL, source TEXT NOT NULL,
      source_event_id TEXT NOT NULL, observed_at TEXT NOT NULL,
      received_at TEXT NOT NULL, kind TEXT NOT NULL,
      admission TEXT NOT NULL,
      UNIQUE(source,source_event_id));
    CREATE INDEX IF NOT EXISTS watch_events_route ON
      watch_events(mint,pump_pool,meteora_pool,observed_at);
    CREATE TABLE IF NOT EXISTS reprice_queue (
      mint TEXT NOT NULL, pump_pool TEXT NOT NULL,
      meteora_pool TEXT NOT NULL, last_event_id INTEGER NOT NULL,
      queued_at TEXT NOT NULL, status TEXT NOT NULL,
      PRIMARY KEY(mint,pump_pool,meteora_pool));
    ''')


def parse_time(s):
    if not isinstance(s, str):
        raise ValueError('TIME_REQUIRED')
    x = datetime.fromisoformat(s.replace('Z','+00:00'))
    if x.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    return x.astimezone(timezone.utc)


def ingest(c, row, now, max_age=90):
    keys = ('mint','pump_pool','meteora_pool')
    if not isinstance(row, dict) or not all(valid_key(row.get(k)) for k in keys):
        raise ValueError('COMPLETE_ROUTE_REQUIRED')
    source = row.get('source')
    eid = row.get('source_event_id')
    kind = row.get('kind')
    if source not in ('UNIVERSAL_WS','UNIVERSAL_DISCOVERY','MRIYA_VERIFIED'):
        raise ValueError('SOURCE_NOT_ADMITTED')
    if not isinstance(eid,str) or not 1 <= len(eid) <= 180:
        raise ValueError('EVENT_ID_REQUIRED')
    if kind not in ('POOL_UPDATE','PAIR_DISCOVERED','VERIFIED_TRANSACTION'):
        raise ValueError('EVENT_KIND_INVALID')
    if (source == 'MRIYA_VERIFIED') != (kind == 'VERIFIED_TRANSACTION'):
        raise ValueError('MRIYA_PROOF_BOUNDARY')
    if source == 'MRIYA_VERIFIED':
        # Unverified imports cannot assert on-chain verification.
        raise ValueError('MRIYA_VERIFICATION_CONNECTOR_NOT_INSTALLED')
    observed = parse_time(row.get('observed_at'))
    age = (now-observed).total_seconds()
    if age < -5:
        raise ValueError('FUTURE_EVENT')
    route = tuple(row[k] for k in keys)
    known = c.execute('''SELECT 1 FROM universal_routes WHERE
      mint=? AND pump_pool=? AND meteora_pool=?''',route).fetchone()
    if not known:
        raise ValueError('ROUTE_NOT_IN_DISCOVERY_REGISTRY')
    fresh = 0 <= age <= max_age
    admission = 'FRESH_REPRICE' if fresh else 'STALE_HISTORY_ONLY'
    before = c.total_changes
    c.execute('''INSERT OR IGNORE INTO watch_events
      (mint,pump_pool,meteora_pool,source,source_event_id,observed_at,
       received_at,kind,admission) VALUES(?,?,?,?,?,?,?,?,?)''',
       (*route,source,eid,observed.isoformat(),now.isoformat(),kind,admission))
    inserted = c.total_changes > before
    if inserted and fresh:
        event_id = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute('''INSERT INTO reprice_queue VALUES(?,?,?,?,?,?)
          ON CONFLICT(mint,pump_pool,meteora_pool) DO UPDATE SET
          last_event_id=excluded.last_event_id, queued_at=excluded.queued_at,
          status='PENDING_REVALIDATION' ''',
          (*route,event_id,now.isoformat(),'PENDING_REVALIDATION'))
    return admission if inserted else 'DUPLICATE'


def test():
    c=sqlite3.connect(':memory:')
    schema(c)
    c.execute('''CREATE TABLE universal_routes
      (mint TEXT,pump_pool TEXT,meteora_pool TEXT)''')
    mint='So11111111111111111111111111111111111111112'
    pump='11111111111111111111111111111111'
    route=(mint,pump,mint)
    c.execute('INSERT INTO universal_routes VALUES(?,?,?)',route)
    now=datetime(2026,10,10,18,tzinfo=timezone.utc)
    row=dict(zip(('mint','pump_pool','meteora_pool'),route))
    row.update(source='UNIVERSAL_WS',source_event_id='evt1',kind='POOL_UPDATE',
               observed_at=now.isoformat())
    assert ingest(c,row,now)=='FRESH_REPRICE'
    assert ingest(c,row,now)=='DUPLICATE'
    old=dict(row,source_event_id='evt2',observed_at=(now-timedelta(hours=3)).isoformat())
    assert ingest(c,old,now)=='STALE_HISTORY_ONLY'
    assert c.execute('SELECT count(*) FROM reprice_queue').fetchone()[0]==1
    try:
        ingest(c,dict(row,source='MRIYA_VERIFIED',kind='VERIFIED_TRANSACTION'),now)
        raise AssertionError('unverified Mriya accepted')
    except ValueError as e:
        assert str(e)=='MRIYA_VERIFICATION_CONNECTOR_NOT_INSTALLED'
    print('[ORACLE221_TEST_PASS] history=TRUE fresh_queue=TRUE dedup=TRUE mriya_guard=TRUE')


def run(feed):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle199_opportunity_freeze as freeze
    freeze.freeze()
    if not DB.exists():
        raise RuntimeError('ORACLE218_DB_MISSING')
    c=sqlite3.connect(DB,timeout=20)
    try:
        schema(c)
        now=datetime.now(timezone.utc)
        stats={}
        if feed:
            with Path(feed).open(encoding='utf-8') as f:
                with c:
                    for line in f:
                        if not line.strip():
                            continue
                        result=ingest(c,json.loads(line),now)
                        stats[result]=stats.get(result,0)+1
        watches=c.execute('SELECT count(*) FROM watches').fetchone()[0]
        routes=c.execute('SELECT count(*) FROM universal_routes').fetchone()[0]
        events=c.execute('SELECT count(*) FROM watch_events').fetchone()[0]
        pending=c.execute("SELECT count(*) FROM reprice_queue WHERE status='PENDING_REVALIDATION'").fetchone()[0]
        report=dict(build='ORACLE221',watched_mints=watches,routes=routes,
                    historical_events=events,pending_revalidation=pending,
                    ingested=stats,ws_connector_active=False,mriya_connector_active=False,
                    profit_certified=False,signing=False,broadcast=False)
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('[ORACLE221_WATCH] mints=%d routes=%d events=%d pending=%d'%(watches,routes,events,pending))
        print('[ORACLE221_INGEST]',stats)
        print('[ORACLE221_SCOPE] feed_adapter=NOT_CONNECTED reprice_execution=NOT_CONNECTED mriya=NOT_CONNECTED')
        print('[REPORT]',REPORT)
    finally:
        c.close()
        freeze.freeze()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test',action='store_true')
    mode.add_argument('--run',action='store_true')
    p.add_argument('--feed',help='JSONL events from a separately verified read-only feed')
    args=p.parse_args()
    test() if args.test else run(args.feed)
