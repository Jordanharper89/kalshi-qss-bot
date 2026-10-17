"""ORACLE224: Non-executing freshness gate for persistent Solana watch queue."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE224_FRESH_WS_QUEUE.json'
MAX_AGE_SECONDS = 90


def iso(value):
    v = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if v.tzinfo is None:
        raise ValueError('NAIVE_EVENT_TIMESTAMP')
    return v.astimezone(timezone.utc)


def classify(c, now):
    rows = c.execute('''SELECT q.mint,q.pump_pool,q.meteora_pool,q.last_event_id,
      q.status,e.source,e.kind,e.observed_at,e.admission,e.id
      FROM reprice_queue q LEFT JOIN watch_events e ON e.id=q.last_event_id
      ORDER BY q.queued_at DESC''').fetchall()
    result = {'WS_FRESH': [], 'DISCOVERY_ONLY': [], 'STALE': [],
              'BROKEN_LINEAGE': [], 'OTHER': []}
    for mint, pump, dlmm, eid, status, source, kind, observed, admission, joined in rows:
        item = {'mint': mint, 'pump_pool': pump, 'meteora_pool': dlmm,
                'event_id': eid, 'queue_status': status, 'source': source, 'kind': kind}
        if joined is None:
            group = 'BROKEN_LINEAGE'
        else:
            try:
                age = (now - iso(observed)).total_seconds()
                item['age_seconds'] = round(age, 3)
                if age < -5 or age > MAX_AGE_SECONDS:
                    group = 'STALE'
                elif source == 'UNIVERSAL_WS' and kind == 'POOL_UPDATE' and admission == 'FRESH_REPRICE':
                    group = 'WS_FRESH'
                elif source == 'UNIVERSAL_DISCOVERY' and kind == 'PAIR_DISCOVERED':
                    group = 'DISCOVERY_ONLY'
                else:
                    group = 'OTHER'
            except (TypeError, ValueError):
                group = 'BROKEN_LINEAGE'
        result[group].append(item)
    return result


def test():
    c = sqlite3.connect(':memory:')
    from build_oracle_221_persistent_watch_lifecycle import schema
    schema(c)
    now = datetime(2026, 10, 10, 18, tzinfo=timezone.utc)
    mint = 'So11111111111111111111111111111111111111112'
    pump = '11111111111111111111111111111111'
    c.execute('''INSERT INTO watch_events
        (mint,pump_pool,meteora_pool,source,source_event_id,observed_at,
         received_at,kind,admission) VALUES(?,?,?,?,?,?,?,?,?)''',
        (mint,pump,mint,'UNIVERSAL_WS','test1',now.isoformat(),now.isoformat(),
         'POOL_UPDATE','FRESH_REPRICE'))
    c.execute('INSERT INTO reprice_queue VALUES(?,?,?,?,?,?)',
              (mint,pump,mint,1,now.isoformat(),'PENDING_REVALIDATION'))
    assert len(classify(c,now)['WS_FRESH']) == 1
    assert len(classify(c,now+timedelta(seconds=91))['STALE']) == 1
    c.execute("UPDATE watch_events SET source='UNIVERSAL_DISCOVERY',kind='PAIR_DISCOVERED'")
    assert len(classify(c,now)['DISCOVERY_ONLY']) == 1
    assert c.execute('SELECT count(*) FROM reprice_queue').fetchone()[0] == 1
    print('[ORACLE224_TEST_PASS] fresh=TRUE stale=TRUE discovery_separate=TRUE queue_unchanged=TRUE')


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle199_opportunity_freeze as freeze
    freeze.freeze()
    if not DB.is_file():
        raise RuntimeError('ORACLE224_WATCH_DB_MISSING')
    c = sqlite3.connect('file:' + DB.resolve().as_posix() + '?mode=ro', uri=True)
    try:
        groups = classify(c,datetime.now(timezone.utc))
        counts = {name: len(items) for name,items in groups.items()}
        state = {'build':'ORACLE224','counts':counts,'groups':groups,
                 'watch_mode':'READ_ONLY','pricing_connected':False,
                 'profit_certified':False,'signing':False,'broadcast':False}
        ROOT.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(state,indent=2),encoding='utf-8')
        print('[ORACLE224_QUEUE]',json.dumps(counts,sort_keys=True))
        for item in groups['WS_FRESH']:
            print('[ORACLE224_WS_READY] token=%s event=%s age_s=%s' %
                  (item['mint'][:12],item['event_id'],item['age_seconds']))
        print('[ORACLE224_BOUNDARY] FRESH_EVENT_NOT_A_PRICE; REPRICE_NOT_CONNECTED; BROADCAST=FALSE')
        print('[REPORT]',REPORT)
    finally:
        c.close()
        freeze.freeze()


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test',action='store_true')
    mode.add_argument('--run',action='store_true')
    args=parser.parse_args()
    test() if args.test else run()