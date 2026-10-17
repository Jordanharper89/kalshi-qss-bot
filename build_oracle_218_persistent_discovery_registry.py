"""ORACLE218: Persistent read-only universal/Mriya discovery registry."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
OLD = ROOT / 'ORACLE207_EXPANDED_RESEARCH.json'
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def full_mint(value):
    if not isinstance(value, str) or not 32 <= len(value) <= 44:
        return False
    n = 0
    for ch in value:
        if ch not in ALPHABET:
            return False
        n = n * 58 + ALPHABET.index(ch)
    length = (n.bit_length() + 7) // 8 + len(value) - len(value.lstrip('1'))
    return length == 32

def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path, timeout=20)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA busy_timeout=20000')
    c.executescript('''
    CREATE TABLE IF NOT EXISTS watches (
      mint TEXT PRIMARY KEY, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
      universal INTEGER NOT NULL DEFAULT 0, mriya INTEGER NOT NULL DEFAULT 0,
      identity_verified INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS sightings (
      id INTEGER PRIMARY KEY, mint TEXT NOT NULL, zone TEXT NOT NULL,
      observed_at TEXT NOT NULL, source TEXT NOT NULL, proof TEXT NOT NULL,
      UNIQUE(mint,zone,observed_at,source,proof));
    CREATE TABLE IF NOT EXISTS unresolved (
      alias TEXT PRIMARY KEY, reason TEXT NOT NULL, source TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assessments (
      id INTEGER PRIMARY KEY, mint TEXT NOT NULL, observed_at TEXT NOT NULL,
      direction TEXT NOT NULL, size_sol REAL NOT NULL, net_lamports INTEGER,
      status TEXT NOT NULL, source TEXT NOT NULL,
      UNIQUE(mint,observed_at,direction,size_sol,source));
    ''')
    return c

def add_sighting(c, item):
    mint, zone = item.get('mint'), item.get('zone')
    if not full_mint(mint) or zone not in ('UNIVERSAL', 'MRIYA'):
        raise ValueError('FULL_MINT_AND_ZONE_REQUIRED')
    observed, source, proof = (item.get(k) for k in ('observed_at','source','proof'))
    if not all(isinstance(v,str) and v.strip() for v in (observed,source,proof)):
        raise ValueError('PROVENANCE_REQUIRED')
    try:
        stamp = datetime.fromisoformat(observed.replace('Z','+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('TZ_REQUIRED')
    except (TypeError,ValueError) as exc:
        raise ValueError('VALID_TIMESTAMP_REQUIRED') from exc
    when = stamp.astimezone(timezone.utc).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    if stamp.timestamp() > datetime.now(timezone.utc).timestamp() + 300:
        raise ValueError('FUTURE_SIGHTING')
    c.execute('''INSERT INTO watches(mint,first_seen,last_seen,universal,mriya,identity_verified)
      VALUES(?,?,?,?,?,1) ON CONFLICT(mint) DO UPDATE SET
      last_seen=excluded.last_seen, universal=max(universal,excluded.universal),
      mriya=max(mriya,excluded.mriya)''',
      (mint,now,now,int(zone=='UNIVERSAL'),int(zone=='MRIYA')))
    c.execute('INSERT OR IGNORE INTO sightings(mint,zone,observed_at,source,proof) VALUES(?,?,?,?,?)',
              (mint,zone,when,source[:200],proof[:500]))

def import_old(c):
    if not OLD.exists():
        return 0
    data=json.loads(OLD.read_text(encoding='utf-8'))
    if data.get('build')!='ORACLE207' or data.get('broadcast') is not False:
        raise ValueError('UNTRUSTED_207_REPORT')
    aliases=set(str(x.get('token','')) for x in data.get('pairs',[]))
    for alias in aliases:
        if alias and not full_mint(alias):
            c.execute('INSERT OR IGNORE INTO unresolved VALUES(?,?,?)',
                      (alias,'TRUNCATED_IDENTITY','ORACLE207'))
    return len(aliases)

def counts(c):
    return dict(zip(('watches','universal','mriya','sightings','unresolved','assessments'),
        (c.execute('SELECT count(*) FROM watches').fetchone()[0],
         c.execute('SELECT count(*) FROM watches WHERE universal=1').fetchone()[0],
         c.execute('SELECT count(*) FROM watches WHERE mriya=1').fetchone()[0],
         c.execute('SELECT count(*) FROM sightings').fetchone()[0],
         c.execute('SELECT count(*) FROM unresolved').fetchone()[0],
         c.execute('SELECT count(*) FROM assessments').fetchone()[0])))

def test():
    c=connect(Path(':memory:'))
    mint='So11111111111111111111111111111111111111112'
    event={'mint':mint,'zone':'UNIVERSAL','observed_at':'2026-10-10T12:00:00Z',
           'source':'fixture','proof':'fixture-only'}
    add_sighting(c,event)
    add_sighting(c,event)
    add_sighting(c,dict(event,zone='MRIYA'))
    x=counts(c)
    assert x['watches']==1 and x['sightings']==2 and x['mriya']==1
    try:
        add_sighting(c,dict(event,mint='So111111111'))
        raise AssertionError('TRUNCATED_MINT_ACCEPTED')
    except ValueError:
        pass
    print('[ORACLE218_TEST_PASS] dual_zone_dedup=TRUE full_mints=TRUE')

def run(feed):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle199_opportunity_freeze as f
    f.freeze()
    c=connect(DB)
    with c:
        imported=import_old(c)
        if feed:
            with Path(feed).open(encoding='utf-8') as stream:
                for line in stream:
                    if line.strip():
                        add_sighting(c,json.loads(line))
    x=counts(c)
    print('[ORACLE218_REGISTRY]',json.dumps(x,sort_keys=True))
    print('[ORACLE218_LEGACY_ALIASES]',imported,'identity=UNRESOLVED')
    print('[ORACLE218_DB]',DB)
    print('[ORACLE218_SCOPE] HISTORY_PERSISTENT=TRUE MARKET_FEED_NOT_CONNECTED=TRUE '
          'PROFIT_CERTIFIED=FALSE SIGNING=FALSE BROADCAST=FALSE')
    f.freeze()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--run',action='store_true')
    p.add_argument('--feed',help='JSONL observations with verified provenance')
    a=p.parse_args()
    test() if a.test else run(a.feed)