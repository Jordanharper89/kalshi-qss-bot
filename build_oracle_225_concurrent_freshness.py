"""ORACLE225: Concurrent read-only watch freshness acceptance (no price claims)."""
import argparse
import json
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE225_CONCURRENT_FRESHNESS.json'
WATCHER = Path('build_oracle_223_universal_ws_watch.py')


def read_queue(path, now):
    from build_oracle_224_fresh_ws_queue_gate import classify
    uri = 'file:' + path.resolve().as_posix() + '?mode=ro'
    with sqlite3.connect(uri, uri=True, timeout=5) as conn:
        conn.execute('PRAGMA busy_timeout=5000')
        return classify(conn, now)


def accumulate(seen, groups):
    new = 0
    for event in groups['WS_FRESH']:
        identity = (event['mint'], event['pump_pool'],
                    event['meteora_pool'], event['event_id'])
        if identity not in seen:
            seen.add(identity)
            new += 1
    return new


def test():
    from build_oracle_224_fresh_ws_queue_gate import classify
    c = sqlite3.connect(':memory:')
    from build_oracle_221_persistent_watch_lifecycle import schema
    schema(c)
    now = datetime.now(timezone.utc)
    mint = 'So11111111111111111111111111111111111111112'
    pump = '11111111111111111111111111111111'
    c.execute('''INSERT INTO watch_events
      (mint,pump_pool,meteora_pool,source,source_event_id,observed_at,
       received_at,kind,admission) VALUES(?,?,?,?,?,?,?,?,?)''',
       (mint,pump,mint,'UNIVERSAL_WS','fixture',now.isoformat(),
        now.isoformat(),'POOL_UPDATE','FRESH_REPRICE'))
    c.execute('INSERT INTO reprice_queue VALUES(?,?,?,?,?,?)',
              (mint,pump,mint,1,now.isoformat(),'PENDING_REVALIDATION'))
    seen = set()
    groups = classify(c,now)
    assert accumulate(seen,groups) == 1
    assert accumulate(seen,groups) == 0
    assert c.execute('SELECT count(*) FROM reprice_queue').fetchone()[0] == 1
    print('[ORACLE225_TEST_PASS] simultaneous_freshness=TRUE dedup=TRUE read_only=TRUE')


def run(seconds, limit):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze)
    freeze.freeze()
    if not WATCHER.is_file() or not DB.is_file():
        raise RuntimeError('ORACLE225_DEPENDENCY_MISSING')
    command = [sys.executable, str(WATCHER), '--run', '--minutes',
               str(seconds / 60), '--limit', str(limit)]
    print('[ORACLE225_START] concurrent_ws=TRUE freshness_gate=TRUE', flush=True)
    proc = subprocess.Popen(command)
    seen = set()
    peaks = Counter()
    start = time.monotonic()
    watcher_exit = None
    try:
        while time.monotonic() - start < seconds + 12:
            groups = read_queue(DB, datetime.now(timezone.utc))
            for category, items in groups.items():
                peaks[category] = max(peaks[category], len(items))
            added = accumulate(seen, groups)
            if added:
                print('[ORACLE225_LIVE_FRESH] new=%d unique=%d current_fresh=%d' %
                      (added, len(seen), len(groups['WS_FRESH'])), flush=True)
            watcher_exit = proc.poll()
            if watcher_exit is not None:
                break
            time.sleep(2)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        watcher_exit = proc.returncode
        report = {
            'build': 'ORACLE225', 'watcher_exit': watcher_exit,
            'unique_live_fresh_events_seen': len(seen),
            'peak_queue_groups': dict(peaks),
            'meaning': 'Account update freshness only, not executable quotes',
            'pricing_connected': False, 'profit_certified': False,
            'mriya_connected': False, 'signing': False, 'broadcast': False
        }
        ROOT.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
        freeze.freeze()
        print('[ORACLE225_RESULT]', json.dumps(report, sort_keys=True), flush=True)
        print('[REPORT]', REPORT, flush=True)
    if watcher_exit != 0:
        raise RuntimeError('ORACLE225_WATCHER_FAILED')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--run', action='store_true')
    p.add_argument('--seconds', type=int, default=60)
    p.add_argument('--limit', type=int, default=12)
    args = p.parse_args()
    if args.test:
        test()
    else:
        if not 20 <= args.seconds <= 240 or not 1 <= args.limit <= 100:
            p.error('seconds=20..240 limit=1..100')
        run(args.seconds, args.limit)
