"""ORACLE-364: complete, self-installing scanner -> pre-atomic repricing bridge.

Windows CMD, active venv. Scanner 322, 351, 352, 360, 363 left intact.
Read-only local bus, NO RPC/WS clients, NO secret access, NO signing/broadcast.

The inbox is a *request for independent bank repricing*, NOT an execution order.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import py_compile
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_364_consolidated_event_handoff.py')
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_364_handoff_report.json')
INBOX = Path('runtime_state/oracle/final_boss_dual/oracle_364_atomic_reprice_inbox.json')
ALLOWED_EVENT_TYPES = frozenset(('nomination','candidate','opportunity','signal','scanner_nomination','trade_opportunity'))
REQUIRED = frozenset(('id','created_ns','slot','size_lamports','token','pump_pool','meteora_pool','direction'))
MAX_JSON_CHARS = 16_384


def _base():
    return importlib.import_module(PKG + '.oracle_363_verified_scanner_bus_binding')


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def install():
    src = Path(__file__).resolve()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if src != TARGET.resolve():
        tmp = TARGET.with_name(TARGET.name + '.installtmp')
        tmp.write_bytes(src.read_bytes())
        compile(tmp.read_text(encoding='utf-8'), str(TARGET), 'exec')
        os.replace(tmp, TARGET)
    py_compile.compile(str(TARGET), doraise=True)
    if TARGET.read_bytes() != src.read_bytes():
        raise RuntimeError('INSTALL_BYTES_MISMATCH')
    print('[ORACLE364_INSTALL_PASS]', TARGET, 'sha256=' + _sha(TARGET), flush=True)


def audit():
    # Base audit includes unmodified ORACLE-352 certified SHA and ORACLE-360 guard.
    base = _base()
    base.audit()
    if not TARGET.is_file():
        raise RuntimeError('ORACLE364_NOT_INSTALLED')
    py_compile.compile(str(TARGET), doraise=True)
    if _sha(TARGET) != _sha(Path(__file__)):
        raise RuntimeError('ORACLE364_INSTALLED_BYTES_DIFFER')
    scanner = base.resolve_scanner_bus()
    for name in ('bus', 'validate_scanner', 'new_events'):
        if not callable(getattr(scanner, name, None)):
            raise RuntimeError('SCANNER_BUS_METHOD_MISSING_' + name)
    print('[ORACLE364_AUDIT_PASS] 322_FROZEN 352_CERTIFIED 351_GUARD 363_REUSED '
          'ONE_READ_ONLY_DB NO_NEW_RPC_WS NO_KEY NO_SIGN_NO_BROADCAST', flush=True)


def _strict_id(value):
    if type(value) is int and value > 0:
        return value
    if type(value) is str and value.isascii() and value.isdecimal() and value[0] != '0':
        return int(value)
    return None


def _decode_json(raw, counts):
    if isinstance(raw, (bytes, bytearray)):
        if len(raw) > MAX_JSON_CHARS:
            counts['oversize'] += 1
            return None
        try:
            raw = bytes(raw).decode('utf-8')
        except UnicodeError:
            counts['bad_utf8'] += 1
            return None
    if isinstance(raw, str):
        if len(raw) > MAX_JSON_CHARS:
            counts['oversize'] += 1
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            counts['invalid_json'] += 1
            return None
    return raw


def normalize_event(raw, counts):
    """Decode only explicit nomination objects, never fabricate missing economics.

    Supports a JSON string event and an (event_id, JSON) scanner-bus envelope.
    A mismatched envelope / internal event ID is fatal to that event.
    """
    counts['raw'] += 1
    envelope_id = None
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        envelope_id = _strict_id(raw[0])
        if envelope_id is None:
            counts['invalid_envelope_id'] += 1
            return None
        raw = raw[1]
        counts['tuple_envelope'] += 1
    raw = _decode_json(raw, counts)
    if raw is None:
        return None
    if not isinstance(raw, dict) and hasattr(raw, 'keys'):
        try:
            raw = {k: raw[k] for k in raw.keys()}
        except (TypeError, KeyError, IndexError):
            counts['bad_mapping'] += 1
            return None
    if not isinstance(raw, dict):
        counts['non_nomination_record'] += 1
        return None
    # Descend only explicitly recognized single-event payload containers.
    outer = raw
    for level in range(3):
        tags = [outer.get(k) for k in ('type', 'event_type', 'kind') if k in outer]
        if tags and not all(isinstance(t, str) and t.lower() in ALLOWED_EVENT_TYPES for t in tags):
            counts['non_nomination_type'] += 1
            return None
        if REQUIRED.issubset(outer):
            break
        nested = None
        for k in ('nomination','payload','payload_json','event','data'):
            if k in outer:
                nested = _decode_json(outer[k], counts)
                break
        if isinstance(nested, dict):
            inner = dict(nested)
            for k in ('id',):
                if k not in inner and k in outer:
                    inner[k] = outer[k]
            outer = inner
            counts['nested_envelope'] += 1
        else:
            break
    if not REQUIRED.issubset(outer):
        counts['missing_nomination_fields'] += 1
        return None
    eid = _strict_id(outer['id'])
    if eid is None or (envelope_id is not None and eid != envelope_id):
        counts['id_mismatch'] += 1
        return None
    # Never promote an unknown event category into a trading nomination.
    # Stage stays non-executable; all base ingress rules remain enforced.
    counts['decoded_nomination'] += 1
    return outer


def _safe_publish(base, gate, inbox):
    gate.expire()
    if gate.changed:
        if gate.latest and not gate.failed:
            base.atomic_json_write(inbox, gate.export())
        else:
            inbox.unlink(missing_ok=True)
        gate.changed = False


def consume_batch(scanner, conn, gate, stats, inbox):
    start = time.perf_counter_ns()
    rows, next_cursor = scanner.new_events(conn, gate.cursor)
    gate.poll_latencies_ms.append(round((time.perf_counter_ns()-start)/1e6, 3))
    if len(gate.poll_latencies_ms) > 256:
        gate.poll_latencies_ms = gate.poll_latencies_ms[-256:]
    if type(next_cursor) is not int or next_cursor < gate.cursor:
        gate.fail('BUS_CURSOR_REGRESSION')
        return
    if not isinstance(rows, (list,tuple)) or len(rows) > 10000:
        gate.fail('UNEXPECTED_BUS_BATCH')
        return
    gate.cursor = next_cursor
    for raw in rows:
        row = normalize_event(raw, stats)
        if row is None:
            continue
        prev = dict(gate.counts)
        staged = gate.accept(row)
        if staged:
            stats['repricing_handoff'] += 1
            # Only identifiers and metadata; no keys or account data in output.
            print('[ORACLE364_REPRICE_HANDOFF]', json.dumps({
                'event_id':staged['event_id'], 'token_prefix':staged['token'][:12],
                'size_lamports':staged['size_lamports'], 'direction':staged['direction'],
                'source_age_ms':staged['source_age_at_ingress_ms'],
                'bank_pricing_certified':False, 'signing':False, 'broadcast':False}), flush=True)
        else:
            changed = [k for k in gate.counts if gate.counts[k] > prev.get(k, 0)]
            stats['ingress_rejected'] += 1
            for reason in changed:
                stats['hold_' + reason] += 1
        if gate.failed:
            break
    _safe_publish(_base(), gate, inbox)


def run(seconds=180, ttl_ms=2500, max_age_ms=1500, poll_ms=10,
        scanner=None, audit_first=True, use_lock=True,
        report_path=REPORT, inbox_path=INBOX):
    if not .05 <= seconds <= 1800 or not 5 <= poll_ms <= 100:
        raise ValueError('BAD_RUNTIME_BOUNDS')
    if audit_first:
        audit()
    base = _base()
    if scanner is None:
        scanner = base.resolve_scanner_bus()
    from contextlib import nullcontext
    lock = nullcontext()
    if use_lock:
        bridge = importlib.import_module(PKG + '.oracle_359_lock_safe_handoff')
        lock = bridge.ExclusiveLock()
    gate = base.LocalIngress(ttl_ms=ttl_ms,max_age_ms=max_age_ms)
    stats = Counter()
    conn = None
    inbox_path.unlink(missing_ok=True)
    try:
        with lock:
            conn = scanner.bus()
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            hb = scanner.validate_scanner(conn)
            cursor = conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]
            gate.attach(hb, int(cursor))
            print('[ORACLE364_SCANNER_BOUND]', json.dumps({
                'epoch':gate.epoch, 'producer_prefix':gate.producer[:12],
                'cursor':gate.cursor, 'read_only':True, 'additional_rpc_ws':False}), flush=True)
            deadline = time.monotonic()+seconds
            next_health = time.monotonic()+.25
            while time.monotonic() < deadline and not gate.failed:
                if time.monotonic() >= next_health:
                    gate.health(scanner.validate_scanner(conn))
                    next_health = time.monotonic()+.25
                    if gate.failed:break
                consume_batch(scanner, conn, gate, stats, inbox_path)
                _safe_publish(base, gate, inbox_path)
                time.sleep(poll_ms/1000)
    except Exception as exc:
        # No arbitrary exception text: exception may contain an RPC endpoint/key.
        gate.fail('SOURCE_OR_LOCK_' + type(exc).__name__)
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
        gate.latest.clear()
        gate.deadlines.clear()
        inbox_path.unlink(missing_ok=True)
        result = gate.report()
        result['raw_event_contract'] = dict(stats)
        result['execution_stage'] = 'SCANNER_TO_PRE_ATOMIC_REPRICE_ONLY'
        result['private_key_used'] = False
        result['first_live_canary_lamports'] = 10_000_000
        result['native_atomic_certified'] = False
        result['signing'] = False
        result['broadcast'] = False
        base.atomic_json_write(report_path, result)
        print('[ORACLE364_EXIT]', json.dumps(result, sort_keys=True), flush=True)
        print('[ORACLE364_REPORT]', report_path, flush=True)
    return 2 if gate.failed else 0


def tests():
    now = time.time_ns()
    token = 'A'*43
    pump = 'B'*43
    met = 'C'*43
    def obj(eid=8, **kw):
        d = dict(id=eid, token=token, pump_pool=pump, meteora_pool=met,
                 direction='PUMP_TO_METEORA', size_lamports=10_000_000,
                 slot=1500, created_ns=now, scanner_gross=9000)
        d.update(kw)
        return d
    def decode(x):
        return normalize_event(x, Counter())
    class T(unittest.TestCase):
        def test_direct_mapping(self): self.assertEqual(decode(obj())['id'],8)
        def test_json_text(self): self.assertEqual(decode(json.dumps(obj()))['id'],8)
        def test_json_bytes(self): self.assertEqual(decode(json.dumps(obj()).encode())['id'],8)
        def test_tuple_envelope(self): self.assertEqual(decode((8,json.dumps(obj())))['id'],8)
        def test_envelope_missing_id(self):
            d=obj(); d.pop('id'); self.assertEqual(decode({'id':8,'payload':d})['id'],8)
        def test_envelope_with_json_payload(self):
            d=obj(); d.pop('id'); self.assertEqual(decode({'id':8,'payload_json':json.dumps(d)})['id'],8)
        def test_envelope_conflicting_id(self): self.assertIsNone(decode((9,json.dumps(obj()))))
        def test_type_telemetry_reject(self): self.assertIsNone(decode(dict(obj(),type='telemetry')))
        def test_type_nomination_accept(self): self.assertIsNotNone(decode(dict(obj(),type='nomination')))
        def test_unknown_type_reject(self): self.assertIsNone(decode(dict(obj(),type='random_type')))
        def test_non_json_string(self): self.assertIsNone(decode('some text'))
        def test_json_list_not_event(self): self.assertIsNone(decode('[1,2,3]'))
        def test_missing_fields(self): self.assertIsNone(decode({'id':8}))
        def test_bounded_json(self): self.assertIsNone(decode('A'*(MAX_JSON_CHARS+1)))
        def test_bool_id(self): self.assertIsNone(decode(dict(obj(),id=True)))
        def test_nonstrict_id(self): self.assertIsNone(decode(dict(obj(),id=8.5)))
        def test_slot_preserved(self): self.assertEqual(decode(obj(slot=2000))['slot'],2000)
        def test_size_preserved(self): self.assertEqual(decode(obj(size_lamports=100_000_000))['size_lamports'],100_000_000)
        def test_no_synthetic_gross(self):
            d=obj();d.pop('scanner_gross');self.assertNotIn('scanner_gross',decode(d))
        def test_negative_rejected_by_existing_gate(self):
            base=_base();gate=base.LocalIngress();gate.attach({'epoch':3,'producer':'fixture_producer_123'},1)
            self.assertIsNone(gate.accept(decode(obj(scanner_gross=-1))))
        def test_stale_rejected_by_existing_gate(self):
            base=_base();gate=base.LocalIngress(max_age_ms=1500);gate.attach({'epoch':3,'producer':'fixture_producer_123'},1)
            self.assertIsNone(gate.accept(decode(obj(created_ns=now-8_000_000_000))))
        def test_unsupported_size_rejected_by_existing_gate(self):
            base=_base();gate=base.LocalIngress();gate.attach({'epoch':3,'producer':'fixture_producer_123'},1)
            self.assertIsNone(gate.accept(decode(obj(size_lamports=101_000_000))))
        def test_staged_is_not_executable(self):
            base=_base();gate=base.LocalIngress();gate.attach({'epoch':3,'producer':'fixture_producer_123'},1)
            row=gate.accept(decode(obj()))
            self.assertFalse(row['execution_authority']);self.assertFalse(row['signing']);self.assertFalse(row['broadcast'])
            self.assertFalse(row['fresh_bank_pricing_certified'])
        def test_latest_only(self):
            base=_base();gate=base.LocalIngress();gate.attach({'epoch':3,'producer':'fixture_producer_123'},1)
            gate.accept(decode(obj(eid=8)));gate.accept(decode(obj(eid=9,size_lamports=20_000_000)))
            self.assertEqual(gate.latest[token]['event_id'],9)
        def test_new_429_fails_closed(self):
            base=_base();gate=base.LocalIngress();gate.attach({'epoch':3,'producer':'fixture_producer_123', 'websocket_429_observed':2},1)
            gate.health({'epoch':3,'producer':'fixture_producer_123','websocket_429_observed':3})
            self.assertTrue(gate.failed)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    out=unittest.TextTestRunner(verbosity=1).run(suite)
    if not out.wasSuccessful():return 1
    print('[ORACLE364_TEST_PASS]', out.testsRun, flush=True)
    # This is a real SQLite file + actual production processing loop fixture.
    with tempfile.TemporaryDirectory() as td:
        dbp = Path(td)/'bus.sqlite'
        cp=sqlite3.connect(str(dbp))
        cp.execute('CREATE TABLE events (id INTEGER PRIMARY KEY,payload TEXT)')
        cp.execute('INSERT INTO events VALUES (?,?)',(4,'{}'))
        cp.commit();cp.close()
        class FixtureScanner:
            def bus(self):return sqlite3.connect(str(dbp))
            def validate_scanner(self, conn):return {'epoch':3,'producer':'fixture_producer_123'}
            def new_events(self, conn, cursor):
                rows=conn.execute('SELECT id,payload FROM events WHERE id>? ORDER BY id',(cursor,)).fetchall()
                return rows, (rows[-1][0] if rows else cursor)
        def writer():
            time.sleep(.04)
            c=sqlite3.connect(str(dbp));c.execute('INSERT INTO events VALUES (?,?)',(8,json.dumps(obj(eid=8,created_ns=time.time_ns()))));c.commit();c.close()
        th=threading.Thread(target=writer);th.start()
        rp=Path(td)/'out.json';ip=Path(td)/'inbox.json'
        code=run(seconds=.2,poll_ms=5,scanner=FixtureScanner(),audit_first=False,use_lock=False,report_path=rp,inbox_path=ip)
        th.join()
        summary=json.loads(rp.read_text(encoding='utf-8'))
        assert code==0 and summary['ever_staged']==1, summary
        assert not ip.exists(), 'INBOX_MUST_BE_ERASED_AT_EXIT'
        print('[ORACLE364_SQLITE_LIVE_PATH_FIXTURE_PASS] STAGED_1 NO_KEY NO_SIGN_NO_BROADCAST',flush=True)
    return 0


def main():
    p=argparse.ArgumentParser()
    for flag in ('install','test','audit','run','wallet-status'):p.add_argument('--'+flag,action='store_true')
    p.add_argument('--seconds',type=float,default=180)
    p.add_argument('--ttl-ms',type=int,default=2500)
    p.add_argument('--max-age-ms',type=int,default=1500)
    p.add_argument('--poll-ms',type=int,default=10)
    a=p.parse_args()
    if not (a.install or a.test or a.audit or a.run or a.wallet_status):p.error('SELECT_MODE')
    if a.install:install()
    if a.test and tests():return 1
    if a.audit:audit()
    if a.wallet_status:
        print('[ORACLE364_WALLET_ENV]', 'PRESENT' if bool(os.environ.get('QSB_SOLANA_PRIVATE_KEY')) else 'NOT_SET',
              'KEY_NOT_PRINTED KEY_NOT_USED EXECUTION_DISABLED', flush=True)
    if a.run:return run(a.seconds,a.ttl_ms,a.max_age_ms,a.poll_ms)
    return 0


if __name__ == '__main__':
    sys.exit(main())
