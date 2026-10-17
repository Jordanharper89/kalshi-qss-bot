"""ORACLE-365: canonical scanner-bus positional-row handoff.

Complete installer. Windows CMD / active venv / python only.
Does not modify ORACLE-322/351/352/360/363/364, private keys, or execution authority.
Scanner new_events determines the cursor and which rows may be considered.
For positional tuples with an ID first, reads a matching full record from the same
read-only SQLite events table and requires byte/value equality before field mapping.
No RPC, WebSocket, signing, broadcasting or direct native executor invocation.
Staged candidates are non-executable pricing requests only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import nullcontext
import hashlib
import importlib
import json
import os
from pathlib import Path
import py_compile
import re
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_365_sqlite_columnar_event_handoff.py')
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_365_columnar_handoff_report.json')
INBOX = Path('runtime_state/oracle/final_boss_dual/oracle_365_atomic_reprice_inbox.json')
MAX_BATCH = 10000
MAX_IDS_PER_SQL = 500
SCHEMA_LABEL = 'ORACLE365_COLUMNAR_BUS_REPRICE_ONLY'


def core():
    return importlib.import_module(PKG + '.oracle_364_consolidated_event_handoff')


def install():
    src = Path(__file__).resolve()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if src != TARGET.resolve():
        temp = TARGET.with_name(TARGET.name + '.stage')
        temp.write_bytes(src.read_bytes())
        compile(temp.read_text(encoding='utf-8'), str(TARGET), 'exec')
        os.replace(temp, TARGET)
    py_compile.compile(str(TARGET), doraise=True)
    if TARGET.read_bytes() != src.read_bytes():
        raise RuntimeError('INSTALL_BYTES_MISMATCH')
    print('[ORACLE365_INSTALL_PASS]', TARGET, 'sha256=' + hashlib.sha256(TARGET.read_bytes()).hexdigest(), flush=True)


def audit():
    core().audit()  # ORACLE-352 certified source and ORACLE-360 repair must still pass.
    if not TARGET.is_file() or TARGET.read_bytes() != Path(__file__).resolve().read_bytes():
        raise RuntimeError('ORACLE365_INSTALLED_SOURCE_MISMATCH')
    py_compile.compile(str(TARGET), doraise=True)
    print('[ORACLE365_AUDIT_PASS] SCANNER322_FROZEN 352_CERTIFIED 360_GUARD '
          'ONE_QUERY_ONLY_SQLITE_READER NO_NEW_RPC_WS NO_KEY_NO_SIGN_NO_BROADCAST', flush=True)


def strict_id(v):
    if type(v) is int and v > 0:
        return v
    if type(v) is str and v.isascii() and v.isdecimal() and v[0] != '0':
        return int(v)
    return None


def _columns(conn):
    # The runtime owns the events table schema. SELECT * gives positional names in
    # their actual SELECT order; never guess positional column meanings.
    cursor = conn.execute('SELECT * FROM events LIMIT 0')
    names = [d[0] for d in (cursor.description or [])]
    if not names or 'id' not in names or len(set(names)) != len(names):
        raise RuntimeError('EVENT_TABLE_COLUMN_SCHEMA_UNSUPPORTED')
    if any(not isinstance(n, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', n)
           for n in names):
        raise RuntimeError('UNSAFE_EVENT_COLUMN_NAME')
    return names


def _shape(raw):
    if isinstance(raw, (list, tuple)):
        return 'positional_%d' % len(raw)
    if isinstance(raw, dict) or hasattr(raw, 'keys'):
        return 'mapping'
    return 'scalar_' + type(raw).__name__[:24]


def decode_batch(conn, original_rows, old_cursor, new_cursor, counters):
    """Read exact canonical bus rows only; never guess tuple field names.

    Only tuple rows whose first value is a valid event ID can be hydrated.
    Positional hydration requires exact equality to the same ID's full SQLite
    table row, preventing accidental reinterpretation of arbitrary tuples.
    """
    base = core()
    column_names = _columns(conn)
    counters['column_count'] = len(column_names)
    counters['sqlite_schema_read'] += 1
    keys = set()
    for raw in original_rows:
        counters['raw'] += 1
        counters['shape_' + _shape(raw)] += 1
        if isinstance(raw, (tuple, list)) and len(raw) > 2:
            eid = strict_id(raw[0])
            if eid is not None and old_cursor < eid <= new_cursor:
                keys.add(eid)
            else:
                counters['positional_unindexable'] += 1
    # Only gather IDs found in canonical scanner.new_events output. No replay.
    by_id = {}
    sorted_ids = sorted(keys)
    for start in range(0, len(sorted_ids), MAX_IDS_PER_SQL):
        chunk = sorted_ids[start:start + MAX_IDS_PER_SQL]
        marks = ','.join('?' for _ in chunk)
        sql = 'SELECT * FROM events WHERE id IN (' + marks + ')'
        cur = conn.execute(sql, chunk)
        if [d[0] for d in cur.description] != column_names:
            raise RuntimeError('EVENT_SCHEMA_CHANGED_MID_BATCH')
        for row in cur.fetchall():
            values = tuple(row)
            rowdict = dict(zip(column_names, values))
            rid = strict_id(rowdict.get('id'))
            if rid in keys:
                by_id[rid] = (values, rowdict)
    decoded = []
    for raw in original_rows:
        mapping = raw
        if isinstance(raw, (tuple, list)) and len(raw) > 2:
            rid = strict_id(raw[0])
            match = by_id.get(rid) if rid is not None else None
            if match is None or tuple(raw) != match[0]:
                counters['positional_row_mismatch'] += 1
                continue
            mapping = match[1]
            counters['columnar_exact_match'] += 1
        before = Counter()
        row = base.normalize_event(mapping, before)
        for reason, number in before.items():
            if reason != 'raw':
                counters['decode_' + reason] += number
        if row is not None:
            decoded.append(row)
    return decoded, column_names


def consume(scanner, conn, gate, counters, inbox):
    base = core()
    old = gate.cursor
    start = time.perf_counter_ns()
    rows, next_cursor = scanner.new_events(conn, old)
    latency = (time.perf_counter_ns() - start) / 1_000_000
    gate.poll_latencies_ms.append(round(latency, 3))
    gate.poll_latencies_ms = gate.poll_latencies_ms[-256:]
    if type(next_cursor) is not int or next_cursor < old:
        gate.fail('BUS_CURSOR_REGRESSION')
        return
    if not isinstance(rows, (tuple, list)) or len(rows) > MAX_BATCH:
        gate.fail('BAD_CANONICAL_BUS_BATCH')
        return
    if not rows and next_cursor > old:
        gate.fail('CURSOR_ADVANCED_WITHOUT_VISIBLE_ROWS')
        return
    if not rows:
        # Empty polls need no schema metadata query. This is the fast idle path.
        gate.expire()
        if gate.changed:
            if gate.latest and not gate.failed:
                base._base().atomic_json_write(inbox, gate.export())
            else:
                inbox.unlink(missing_ok=True)
            gate.changed = False
        return None
    try:
        decoded, names = decode_batch(conn, rows, old, next_cursor, counters)
    except (sqlite3.Error, RuntimeError, ValueError, TypeError):
        gate.fail('CANONICAL_EVENT_SCHEMA_UNVERIFIED')
        return
    gate.cursor = next_cursor
    for row in decoded:
        previous_counts = dict(gate.counts)
        staged = gate.accept(row)
        if staged:
            counters['staged'] += 1
            print('[ORACLE365_REPRICE_HANDOFF]', json.dumps({
                'event_id':staged['event_id'], 'token_prefix':staged['token'][:12],
                'direction':staged['direction'], 'size_lamports':staged['size_lamports'],
                'age_ms':staged['source_age_at_ingress_ms'],
                'bank_price_certified':False, 'signing':False, 'broadcast':False}), flush=True)
        else:
            counters['gate_reject'] += 1
            for reason, n in gate.counts.items():
                if n > previous_counts.get(reason, 0):
                    counters['gate_' + reason] += n - previous_counts.get(reason, 0)
        if gate.failed:
            break
    gate.expire()
    if gate.changed:
        if gate.latest and not gate.failed:
            base._base().atomic_json_write(inbox, gate.export())
        else:
            inbox.unlink(missing_ok=True)
        gate.changed = False
    return names


def run(seconds=180.0, ttl_ms=2500, max_age_ms=1500, poll_ms=5,
        scanner=None, preaudited=False, with_lock=True, report=REPORT, inbox=INBOX):
    if not (0.05 <= seconds <= 1800 and 5 <= poll_ms <= 100):
        raise ValueError('INVALID_RUNTIME_BOUNDS')
    if not preaudited:
        audit()
    base = core()
    if scanner is None:
        scanner = base._base().resolve_scanner_bus()
    gate = base._base().LocalIngress(ttl_ms=ttl_ms, max_age_ms=max_age_ms)
    counts = Counter()
    column_names = []
    lock = nullcontext()
    if with_lock:
        lockcls = importlib.import_module(PKG + '.oracle_359_lock_safe_handoff').ExclusiveLock
        lock = lockcls()
    inbox.unlink(missing_ok=True)
    conn = None
    try:
        with lock:
            conn = scanner.bus()
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            hb = scanner.validate_scanner(conn)
            cursor = int(conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            gate.attach(hb, cursor)
            column_names = _columns(conn)
            print('[ORACLE365_SCANNER_BOUND]', json.dumps({
                'epoch':gate.epoch, 'producer_prefix':gate.producer[:12],
                'cursor':gate.cursor, 'column_count':len(column_names),
                'read_only':True, 'extra_rpc_ws':False}),flush=True)
            deadline = time.monotonic() + seconds
            next_health = time.monotonic() + .25
            while time.monotonic() < deadline and not gate.failed:
                if time.monotonic() >= next_health:
                    gate.health(scanner.validate_scanner(conn))
                    next_health = time.monotonic() + .25
                    if gate.failed:
                        break
                result = consume(scanner, conn, gate, counts, inbox)
                if result is not None:
                    column_names = result
                time.sleep(poll_ms / 1000)
    except Exception as exc:
        # Errors from providers, DB, or lock must not expose API URL or secrets.
        gate.fail('SOURCE_OR_LOCK_' + type(exc).__name__)
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
        gate.latest.clear()
        gate.deadlines.clear()
        inbox.unlink(missing_ok=True)
        summary = gate.report()
        summary.update({
            'schema': SCHEMA_LABEL,
            'column_names':column_names, 'row_contract':dict(counts),
            'first_live_canary_lamports':10_000_000,
            'execution_stage':'PRE_ATOMIC_REPRICING_ONLY',
            'native_atomic_simulation_certified':False,
            'fee_adjusted_profit_certified':False,
            'private_key_used':False,'signing':False,'broadcast':False,
        })
        base._base().atomic_json_write(report, summary)
        print('[ORACLE365_EXIT]', json.dumps(summary,sort_keys=True),flush=True)
        print('[ORACLE365_REPORT]',report,flush=True)
    return 2 if gate.failed else 0


def tests():
    now = time.time_ns()
    event = {'id':8,'token':'A'*43,'pump_pool':'B'*43,'meteora_pool':'C'*43,
             'direction':'PUMP_TO_METEORA','size_lamports':10_000_000,
             'slot':1600,'created_ns':now,'scanner_gross':1100}
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory)/'bus.sqlite'
        conn = sqlite3.connect(str(db))
        columns = list(event)
        conn.execute('CREATE TABLE events (' + ','.join(
            x + (' INTEGER' if x in ('id','size_lamports','slot','created_ns','scanner_gross') else ' TEXT')
            for x in columns) + ')')
        conn.execute('INSERT INTO events VALUES ('+','.join('?' for _ in columns)+')',tuple(event.values()))
        conn.commit()
        conn.execute('PRAGMA query_only=ON')
        raw = conn.execute('SELECT * FROM events').fetchone()
        class Tests(unittest.TestCase):
            def test_valid_id(self):self.assertEqual(strict_id(42),42)
            def test_reject_boolean_id(self):self.assertIsNone(strict_id(True))
            def test_reject_float_id(self):self.assertIsNone(strict_id(1.0))
            def test_reject_zero_id(self):self.assertIsNone(strict_id(0))
            def test_reject_noncanonical_str_id(self):self.assertIsNone(strict_id('08'))
            def test_column_names(self):self.assertEqual(_columns(conn),columns)
            def test_positional_hydration(self):
                decoded, _=decode_batch(conn,[raw],7,8,Counter())
                self.assertEqual(decoded[0]['id'],8)
                self.assertEqual(decoded[0]['token'],event['token'])
            def test_wrong_position_rejected(self):
                corrupt=list(raw);corrupt[2]='WRONG'
                self.assertEqual(decode_batch(conn,[tuple(corrupt)],7,8,Counter())[0],[])
            def test_old_cursor_cannot_hydrate(self):
                self.assertEqual(decode_batch(conn,[raw],8,8,Counter())[0],[])
            def test_json_string(self):
                self.assertEqual(decode_batch(conn,[json.dumps(event)],7,8,Counter())[0][0]['id'],8)
            def test_unknown_record(self):
                self.assertEqual(decode_batch(conn,[('junk','abc','x')],7,8,Counter())[0],[])
            def test_no_synthetic_profit(self):
                x=dict(event);x.pop('scanner_gross')
                self.assertNotIn('scanner_gross',core().normalize_event(x,Counter()))
            def test_non_nomination_type_rejected(self):
                self.assertIsNone(core().normalize_event(dict(event,type='heartbeat'),Counter()))
            def test_key_not_used_by_bridge(self):
                self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',run.__code__.co_names)
            def test_metadata_only(self):
                gated=core()._base().LocalIngress()
                gated.attach({'epoch':3,'producer':'fixture_producer_123'},1)
                out=gated.accept(event)
                self.assertIsNotNone(out)
                self.assertFalse(out['execution_authority'])
            def test_newer_negative_invalidates(self):
                gated=core()._base().LocalIngress()
                gated.attach({'epoch':3,'producer':'fixture_producer_123'},1)
                gated.accept(event)
                x=dict(event,id=9,scanner_gross=-200)
                self.assertIsNone(gated.accept(x))
                self.assertFalse(gated.latest)
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        conn.close()
        if not result.wasSuccessful():return 1
        # Full SQLite bus path: scanner's canonical positional tuple -> repricing ingress.
        class Fixture:
            def bus(self):return sqlite3.connect(str(db))
            def validate_scanner(self, con):return {'epoch':3,'producer':'fixture_producer_123'}
            def new_events(self, con, cursor):
                rows=con.execute('SELECT * FROM events WHERE id>? ORDER BY id',(cursor,)).fetchall()
                return rows, rows[-1][0] if rows else cursor
        thread_errors=[]
        def delayed_insert():
            try:
                time.sleep(.03)
                c=sqlite3.connect(str(db))
                updated=dict(event,id=9,created_ns=time.time_ns())
                c.execute('INSERT INTO events VALUES ('+','.join('?' for _ in columns)+')',tuple(updated.values()))
                c.commit();c.close()
            except Exception as e:thread_errors.append(type(e).__name__)
        th=threading.Thread(target=delayed_insert)
        th.start()
        report=Path(directory)/'report.json';inbox=Path(directory)/'inbox.json'
        code=run(seconds=.18,poll_ms=5,scanner=Fixture(),preaudited=True,with_lock=False,report=report,inbox=inbox)
        th.join()
        actual=json.loads(report.read_text(encoding='utf-8'))
        if thread_errors or code != 0 or actual['ever_staged'] != 1 or actual['row_contract'].get('columnar_exact_match') != 1:
            raise AssertionError('COLUMNAR_SQLITE_E2E_FAIL:'+str(actual.get('row_contract')))
        if inbox.exists():raise AssertionError('STALE_INBOX_SURVIVED_SHUTDOWN')
        print('[ORACLE365_SQLITE_COLUMNAR_INTEGRATION_PASS] ONE_CANONICAL_ROW_STAGED NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)
    print('[ORACLE365_TEST_PASS]',result.testsRun,flush=True)
    return 0


def main():
    ap=argparse.ArgumentParser()
    for opt in ('install','test','audit','run','wallet-status'):
        ap.add_argument('--'+opt,action='store_true')
    ap.add_argument('--seconds',type=float,default=180)
    ap.add_argument('--ttl-ms',type=int,default=2500)
    ap.add_argument('--max-age-ms',type=int,default=1500)
    ap.add_argument('--poll-ms',type=int,default=5)
    args=ap.parse_args()
    if not any((args.install,args.test,args.audit,args.run,args.wallet_status)):
        ap.error('SELECT_MODE')
    if args.install:install()
    if args.test and tests():return 1
    if args.audit:audit()
    if args.wallet_status:
        print('[ORACLE365_WALLET_ENV]', 'PRESENT' if bool(os.environ.get('QSB_SOLANA_PRIVATE_KEY')) else 'NOT_SET',
              'KEY_NOT_PRINTED KEY_NOT_USED SIGNING_DISABLED BROADCAST_DISABLED',flush=True)
    if args.run:return run(args.seconds,args.ttl_ms,args.max_age_ms,args.poll_ms)
    return 0

if __name__=='__main__':sys.exit(main())
