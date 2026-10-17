"""ORACLE-362: direct local scanner-bus -> atomic REPRICING ingress.

One read-only sqlite bus connection; no additional RPC/WS client, no wallet access,
no native transaction construction, signing, broadcasting, or execution authority.
The staging payload is NOT an authorization or an executable price. It is deleted
on shutdown; consumers must independently revalidate accounts and simulate.

Run from the Windows CMD repository root, with the project's active venv.
"""
from __future__ import annotations

import argparse
from collections import Counter, OrderedDict
from contextlib import nullcontext
import hashlib
import importlib
import json
import os
from pathlib import Path
import py_compile
import statistics
import subprocess
import sys
import tempfile
import time
import unittest

PACKAGE = 'qseries_v2.oracle_execution.solana_atomic_executor'
ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_362_verified_scanner_bus_binding.py'
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_362_bus_ingress_report.json')
INBOX = Path('runtime_state/oracle/final_boss_dual/oracle_362_atomic_reprice_inbox.json')
INSTALLER_352 = Path('build_oracle_352_scanner_bank_alignment.py')
INSTALLER_360 = Path('build_oracle_360_integrity_bus_recovery.py')
MODULE_351 = ROOT / 'oracle_351_fast_bank_parity.py'
MODULE_352 = ROOT / 'oracle_352_scanner_bank_alignment.py'
MIN_SIZE = 10_000_000
MAX_SIZE = 100_000_000
FIRST_FUNDED_CANARY_LAMPORTS = 10_000_000
DIRECTIONS = frozenset(('PUMP_TO_METEORA', 'METEORA_TO_PUMP'))
B58 = frozenset('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
EXECUTION_AUTHORITY = False
SIGNING = False
BROADCAST = False


def atomic_json_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    try:
        tmp.write_text(json.dumps(obj, separators=(',', ':'), sort_keys=True) + '\n', encoding='utf-8')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install():
    ROOT.mkdir(parents=True, exist_ok=True)
    original = Path(__file__).resolve()
    if original != TARGET.resolve():
        staged = TARGET.with_name(TARGET.name + '.tmp')
        staged.write_bytes(original.read_bytes())
        py_compile.compile(str(staged), doraise=True)
        os.replace(staged, TARGET)
    py_compile.compile(str(TARGET), doraise=True)
    if TARGET.read_bytes() != original.read_bytes():
        raise RuntimeError('INSTALL_BYTE_MISMATCH')
    print('[ORACLE362_INSTALL_PASS]', TARGET, 'sha256=' + sha256(TARGET), flush=True)


def _checked_audit(cmd, expected):
    p = subprocess.run([sys.executable, *cmd], capture_output=True, text=True,
                       timeout=90, check=False)
    if p.returncode != 0 or expected not in p.stdout:
        raise RuntimeError('AUDIT_FAILED_' + expected)


def audit():
    if not all(f.is_file() for f in (INSTALLER_352, INSTALLER_360, MODULE_351, MODULE_352)):
        raise RuntimeError('CERTIFIED_SCANNER_DEPENDENCY_MISSING')
    _checked_audit((str(INSTALLER_352), '--audit'), 'FROZEN_SCANNER_SHA_MATCH')
    _checked_audit((str(INSTALLER_360), '--audit'), 'ORACLE360_AUDIT_PASS')
    if 'ORACLE360_KEEP_LATEST_STRICT_V1' not in MODULE_351.read_text(encoding='utf-8'):
        raise RuntimeError('ORACLE351_BUS_GUARD_MISSING')
    py_compile.compile(str(MODULE_352), doraise=True)
    py_compile.compile(str(MODULE_351), doraise=True)
    resolve_scanner_bus()
    print('[ORACLE362_AUDIT_PASS] 322_FROZEN 352_ORIGINAL_AUDIT 351_GUARD '
          'ONE_LOCAL_DB_READER NO_EXTRA_RPC_WS NO_SIGN_NO_BROADCAST', flush=True)


def valid_pubkey(v):
    return isinstance(v, str) and 32 <= len(v) <= 44 and all(c in B58 for c in v)


def exact_int(x, positive=False):
    if type(x) is int:
        n = x
    elif type(x) is str and x and x.isascii() and x.isdecimal() and (x == '0' or x[0] != '0'):
        n = int(x)
    else:
        raise ValueError('NONCANONICAL_INT')
    if positive and n <= 0:
        raise ValueError('NONPOSITIVE_INT')
    return n


def gross_hint(n):
    """No guessed profitability: accept only explicit integral scanner gross fields."""
    for key in ('gross_lamports', 'scanner_gross', 'local_net'):
        if key in n:
            try:
                return exact_int(n[key])
            except (TypeError, ValueError):
                return 'INVALID'
    return None


class LocalIngress:
    """Bounded newest-per-token staging; NOT a bank-verified or trade-ready gate."""
    def __init__(self, ttl_ms=2500, max_age_ms=1500, clock_ns=time.time_ns,
                 mono_ns=time.perf_counter_ns, callback=None):
        if not (500 <= ttl_ms <= 5000 and 50 <= max_age_ms <= ttl_ms):
            raise ValueError('INVALID_FRESHNESS_BOUNDS')
        self.ttl_ns = int(ttl_ms * 1_000_000)
        self.max_age_ns = int(max_age_ms * 1_000_000)
        self.clock_ns = clock_ns
        self.mono_ns = mono_ns
        self.callback = callback
        self.producer = None
        self.epoch = None
        self.cursor = None
        self.latest = {}
        self.deadlines = {}
        self.recent_ids = OrderedDict()
        self.counts = Counter()
        self.failed = False
        self.failure = None
        self.changed = False
        self.history_429 = None
        self.provider_health = 'WS_429_COUNTER_NOT_EXPOSED'
        self.published_ages_ms = []
        self.poll_latencies_ms = []
        self.ever_staged = 0
        self.last_signal_slot = None

    def fail(self, reason):
        self.failed = True
        self.failure = reason
        self.latest.clear()
        self.deadlines.clear()
        self.changed = True
        self.counts['hold'] += 1

    def attach(self, hb, cursor):
        if type(hb) is not dict:
            raise RuntimeError('BAD_SCANNER_HEALTH')
        epoch = exact_int(hb.get('epoch'), positive=True)
        producer = hb.get('producer')
        if not isinstance(producer, str) or len(producer) < 8:
            raise RuntimeError('BAD_SCANNER_PRODUCER')
        cur = exact_int(cursor)
        if cur < 0:
            raise RuntimeError('INVALID_SCANNER_CURSOR')
        self.epoch, self.producer, self.cursor = epoch, producer, cur
        self.counts['attached'] += 1
        self.health(hb)

    def health(self, hb):
        if self.failed:
            return
        try:
            epoch = exact_int(hb['epoch'], positive=True)
            if epoch != self.epoch or hb.get('producer') != self.producer:
                self.fail('SCANNER_EPOCH_OR_PRODUCER_CHANGED')
                return
            counter = hb.get('websocket_429_observed')
            if counter is not None:
                counter = exact_int(counter)
                if counter < 0:
                    self.fail('INVALID_429_COUNTER')
                    return
                if self.history_429 is None:
                    self.history_429 = counter
                    self.provider_health = ('WS_429_HISTORY_REQUIRES_REVALIDATION'
                                            if counter else 'NO_WS_429_AT_ATTACH')
                elif counter > self.history_429:
                    self.fail('NEW_429_PROVIDER_RATE_LIMIT')
                    return
                elif counter < self.history_429:
                    self.fail('WS_429_COUNTER_RESET')
                    return
                self.history_429 = counter
            self.counts['health_checks'] += 1
        except (KeyError, TypeError, ValueError):
            self.fail('BAD_SCANNER_HEALTH')

    def _decode(self, raw):
        if isinstance(raw, dict):
            return raw
        if hasattr(raw, 'keys'):
            return {k: raw[k] for k in raw.keys()}
        return None

    def accept(self, raw):
        if self.failed or self.epoch is None:
            return None
        n = self._decode(raw)
        if not n:
            self.counts['invalid_schema'] += 1
            return None
        try:
            eid = exact_int(n['id'], positive=True)
            created = exact_int(n['created_ns'], positive=True)
            slot = exact_int(n['slot'], positive=True)
            size = exact_int(n['size_lamports'], positive=True)
            token = n['token']
            pump = n['pump_pool']
            meteora = n['meteora_pool']
            direction = n['direction']
        except (KeyError, TypeError, ValueError):
            self.counts['invalid_schema'] += 1
            return None
        if not (valid_pubkey(token) and valid_pubkey(pump) and valid_pubkey(meteora)
                and direction in DIRECTIONS and MIN_SIZE <= size <= MAX_SIZE):
            self.counts['invalid_identity_or_size'] += 1
            return None
        now = self.clock_ns()
        age_ns = now - created
        if age_ns < 0 or age_ns > self.max_age_ns:
            self.counts['stale_or_future'] += 1
            return None
        if eid in self.recent_ids:
            self.counts['duplicate'] += 1
            return None
        # Already-observed older event must never replace a newer event.
        old = self.latest.get(token)
        if old is not None and eid <= old['event_id']:
            self.counts['superseded'] += 1
            return None
        hint = gross_hint(n)
        if hint == 'INVALID' or (isinstance(hint, int) and hint <= 0):
            self.counts['nonpositive_or_invalid_gross'] += 1
            # A newer negative nomination must also invalidate an older positive.
            if old is not None:
                self.latest.pop(token, None)
                self.deadlines.pop(token, None)
                self.changed = True
            self.recent_ids[eid] = None
            return None
        self.recent_ids[eid] = None
        if len(self.recent_ids) > 4096:
            self.recent_ids.popitem(last=False)
        self.counts['replaced'] += int(old is not None)
        expires_in_ns = min(self.ttl_ns, self.max_age_ns) - age_ns
        if expires_in_ns <= 0:
            self.counts['stale_or_future'] += 1
            return None
        row = {
            'schema': 'ORACLE362_ATOMIC_REPRICE_REQUEST_V1',
            'event_id': eid, 'scanner_epoch': self.epoch,
            'scanner_producer': self.producer, 'scanner_slot': slot,
            'token': token, 'pump_pool': pump, 'meteora_pool': meteora,
            'direction': direction, 'size_lamports': size,
            'scanner_gross_lamports_hint': hint,
            'scanner_gross_proven': False,
            'identity_vetted_by_352': False,
            'fresh_bank_pricing_certified': False,
            'fee_adjusted_profit_certified': False,
            'native_atomic_simulation_certified': False,
            'stage': 'REPRICE_AND_VET_REQUIRED',
            'not_trade_ready': True,
            'first_funded_canary_lamports': FIRST_FUNDED_CANARY_LAMPORTS,
            'execution_authority': False, 'signing': False, 'broadcast': False,
            'source_age_at_ingress_ms': round(age_ns / 1e6, 3),
            'expires_at_unix_ms': int((now + expires_in_ns) // 1_000_000),
        }
        self.latest[token] = row
        self.deadlines[token] = self.mono_ns() + expires_in_ns
        self.changed = True
        self.ever_staged += 1
        self.counts['ingressed'] += 1
        self.published_ages_ms.append(round(age_ns / 1e6, 3))
        self.published_ages_ms = self.published_ages_ms[-256:]
        self.last_signal_slot = slot
        if self.callback:
            try:
                # Actual in-process callback boundary for the NEXT price/sim worker.
                self.callback(dict(row))
            except Exception:
                self.fail('ATOMIC_REPRICE_CALLBACK_FAILED')
                return None
        return row

    def expire(self):
        now = self.mono_ns()
        for token, deadline in list(self.deadlines.items()):
            if now >= deadline:
                self.deadlines.pop(token, None)
                self.latest.pop(token, None)
                self.changed = True
                self.counts['expired'] += 1

    def export(self):
        return {'schema': 'ORACLE362_ATOMIC_REPRICE_INBOX_V1',
                'scanner_epoch': self.epoch, 'producer': self.producer,
                'provider_health': self.provider_health,
                'health_uncertified_for_execution': True,
                'only_valid_while_producer_live': True,
                'first_funded_canary_lamports': FIRST_FUNDED_CANARY_LAMPORTS,
                'candidates': list(self.latest.values()),
                'execution_authority': False, 'signing': False, 'broadcast': False}

    def report(self):
        ages = self.published_ages_ms
        lat = self.poll_latencies_ms
        return {'status': ('HOLD_' + self.failure if self.failed else
                           'SCANNER_TO_ATOMIC_REPRICE_INGRESS_OBSERVED' if self.ever_staged else
                           'SCANNER_BOUND_NO_FRESH_REPRICE_EVENTS'),
                'scanner_epoch': self.epoch,
                'producer_prefix': (self.producer or '')[:12], 'cursor': self.cursor,
                'counts': dict(self.counts),
                'provider_health': self.provider_health,
                'nomination_sizes_lamports': [MIN_SIZE, MAX_SIZE],
                'first_funded_canary_lamports': FIRST_FUNDED_CANARY_LAMPORTS,
                'ever_staged': self.ever_staged,
                'current_candidates': len(self.latest),
                'latest_token_prefixes': [t[:12] for t in self.latest.keys()],
                'last_signal_slot': self.last_signal_slot,
                'source_age_ms_min': min(ages) if ages else None,
                'source_age_ms_p50': statistics.median(ages) if ages else None,
                'source_age_ms_max': max(ages) if ages else None,
                'local_poll_ms_p50': statistics.median(lat) if lat else None,
                'local_poll_ms_max': max(lat) if lat else None,
                'scope': 'REPRICE_INGRESS_ONLY_NOT_ATOMIC_EXECUTION',
                'fresh_bank_pricing_certified': False,
                'fee_adjusted_profit_certified': False,
                'native_atomic_simulation_certified': False,
                'execution_authority': False, 'signing': False, 'broadcast': False,
                'inbox_discarded_at_shutdown': True}


def process_new_events(scanner, conn, gate, inbox_path):
    old_cursor = gate.cursor
    started = time.perf_counter_ns()
    rows, cursor = scanner.new_events(conn, old_cursor)
    elapsed = (time.perf_counter_ns() - started) / 1e6
    gate.poll_latencies_ms.append(round(elapsed, 3))
    gate.poll_latencies_ms = gate.poll_latencies_ms[-256:]
    if type(cursor) is not int or cursor < old_cursor:
        gate.fail('SCANNER_BUS_CURSOR_REGRESSION')
        return
    if not isinstance(rows, (list, tuple)) or len(rows) > 10000:
        gate.fail('BAD_SCANNER_BUS_BATCH')
        return
    gate.cursor = cursor
    # Decoded, canonicalized, coalesced by the existing ORACLE-360 guard.
    # This is not an ORACLE-352 identity/bank verification certificate.
    guard = importlib.import_module(PACKAGE + '.oracle_351_fast_bank_parity')
    nominations = guard.keep_latest(rows)
    gate.counts['raw_events_seen'] += len(rows)
    gate.counts['coalesced_events_seen'] += len(nominations)
    # If two different sizes target the same token, newest event wins.
    for n in nominations:
        row = gate.accept(n)
        if row:
            print('[ORACLE362_REPRICE_HANDOFF]', json.dumps({
                'event_id': row['event_id'], 'token': row['token'][:12],
                'direction': row['direction'], 'size_lamports': row['size_lamports'],
                'age_ms': row['source_age_at_ingress_ms'], 'price_certified': False,
                'signing': False, 'broadcast': False}), flush=True)
    gate.expire()
    if gate.changed:
        if gate.latest and not gate.failed:
            atomic_json_write(inbox_path, gate.export())
        else:
            inbox_path.unlink(missing_ok=True)
        gate.changed = False


def resolve_scanner_bus():
    """Bind the *actual* ORACLE352 -> ORACLE351 -> frozen scanner object graph.

    ORACLE352 uses old351.keep_latest and ORACLE351 calls scan.bus(),
    scan.validate_scanner(), and scan.new_events(). ORACLE352 exports no .scan.
    Require the same ORACLE351 module object in both imports to avoid drift.
    """
    parent = importlib.import_module(PACKAGE + '.oracle_352_scanner_bank_alignment')
    old351 = importlib.import_module(PACKAGE + '.oracle_351_fast_bank_parity')
    if getattr(parent, 'old351', None) is not old351:
        raise RuntimeError('ORACLE352_351_SOURCE_GRAPH_MISMATCH')
    scanner = getattr(old351, 'scan', None)
    if scanner is None or not all(callable(getattr(scanner, name, None))
                                  for name in ('bus', 'validate_scanner', 'new_events')):
        raise RuntimeError('ORACLE351_SCANNER_BUS_API_UNAVAILABLE')
    return scanner


def live_session(seconds=90, ttl_ms=2500, max_age_ms=1500, poll_ms=10,
                 scanner=None, report_path=REPORT, inbox_path=INBOX,
                 lock_required=True, pre_audited=False):
    if not 5 <= seconds <= 1800 or not 5 <= poll_ms <= 100:
        raise ValueError('INVALID_RUNTIME_BOUNDS')
    if not pre_audited:
        audit()
    if scanner is None:
        scanner = resolve_scanner_bus()
    from contextlib import nullcontext
    lock = nullcontext()
    if lock_required:
        bridge = importlib.import_module(PACKAGE + '.oracle_359_lock_safe_handoff')
        lock = bridge.ExclusiveLock()
    gate = LocalIngress(ttl_ms=ttl_ms, max_age_ms=max_age_ms)
    inbox_path.unlink(missing_ok=True)
    conn = None
    try:
        with lock:
            conn = scanner.bus()
            # Enforce that this connection cannot mutate the scanner bus.
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            hb = scanner.validate_scanner(conn)
            # Start from the current scanner cursor: NEVER replay old opportunities.
            initial_cursor = conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]
            gate.attach(hb, initial_cursor)
            print('[ORACLE362_SCANNER_BOUND]', json.dumps({
                'epoch': gate.epoch, 'producer': gate.producer[:12],
                'cursor': gate.cursor, 'mode': 'LOCAL_DB_NO_EXTRA_WS_RPC'}), flush=True)
            deadline = time.monotonic() + seconds
            next_health = time.monotonic() + .25
            while time.monotonic() < deadline and not gate.failed:
                if time.monotonic() >= next_health:
                    gate.health(scanner.validate_scanner(conn))
                    next_health = time.monotonic() + .25
                    if gate.failed:
                        break
                process_new_events(scanner, conn, gate, inbox_path)
                if gate.failed:
                    break
                gate.expire()
                if gate.changed:
                    if gate.latest:
                        atomic_json_write(inbox_path, gate.export())
                    else:
                        inbox_path.unlink(missing_ok=True)
                    gate.changed = False
                time.sleep(poll_ms / 1000)
    except Exception as exc:
        # Do not print arbitrary exception strings: may include RPC URL credentials.
        gate.fail('SOURCE_OR_LOCK_' + type(exc).__name__)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        gate.latest.clear()
        gate.deadlines.clear()
        inbox_path.unlink(missing_ok=True)
        summary = gate.report()
        atomic_json_write(report_path, summary)
        print('[ORACLE362_EXIT]', json.dumps(summary, sort_keys=True), flush=True)
        print('[ORACLE362_REPORT]', report_path, flush=True)
    return 2 if gate.failed else 0


def tests():
    NOW = 1_800_000_000_000_000_000
    TOKEN='A'*43
    PUMP='B'*43
    MET='C'*43
    def event(eid=5, age_ms=40, size=10_000_000, **kw):
        x=dict(id=eid, created_ns=NOW-int(age_ms*1e6),slot=800,
               token=TOKEN,pump_pool=PUMP,meteora_pool=MET,
               direction='PUMP_TO_METEORA',size_lamports=size,
               gross_lamports=4500)
        x.update(kw)
        return x
    def make(callback=None):
        o=LocalIngress(clock_ns=lambda:NOW,mono_ns=lambda:4_000_000_000, callback=callback)
        o.attach(dict(epoch=2,producer='fixture_producer_ABC'),10)
        return o
    class Cases(unittest.TestCase):
        def test_01_valid_nomination(self): self.assertEqual(make().accept(event())['event_id'],5)
        def test_02_size_floor(self): self.assertIsNotNone(make().accept(event(size=MIN_SIZE)))
        def test_03_size_ceiling(self): self.assertIsNotNone(make().accept(event(size=MAX_SIZE)))
        def test_04_low_size_rejected(self): self.assertIsNone(make().accept(event(size=MIN_SIZE-1)))
        def test_05_high_size_rejected(self): self.assertIsNone(make().accept(event(size=MAX_SIZE+1)))
        def test_06_stale(self): self.assertIsNone(make().accept(event(age_ms=2000)))
        def test_07_future(self): self.assertIsNone(make().accept(event(age_ms=-1)))
        def test_08_float_id(self): self.assertIsNone(make().accept(event(id=5.5)))
        def test_09_bool_size(self): self.assertIsNone(make().accept(event(size_lamports=True)))
        def test_10_wrong_pubkey(self): self.assertIsNone(make().accept(event(token='bad')))
        def test_11_direction(self): self.assertIsNone(make().accept(event(direction='NONE')))
        def test_12_nonpositive_gross(self): self.assertIsNone(make().accept(event(gross_lamports=-1)))
        def test_13_missing_gross_not_profit_claim(self):
            r=event(); del r['gross_lamports']; x=make().accept(r)
            self.assertIsNone(x['scanner_gross_lamports_hint']); self.assertFalse(x['fee_adjusted_profit_certified'])
        def test_14_size_preserved(self): self.assertEqual(make().accept(event(size=50_000_000))['size_lamports'],50_000_000)
        def test_15_newer_event_supersedes(self):
            g=make(); g.accept(event()); g.accept(event(eid=6,size=20_000_000))
            self.assertEqual(g.latest[TOKEN]['size_lamports'],20_000_000)
        def test_16_older_event_cannot_supersede(self):
            g=make(); g.accept(event(eid=7)); g.accept(event(eid=6))
            self.assertEqual(g.latest[TOKEN]['event_id'],7)
        def test_17_newer_negative_invalidates(self):
            g=make(); g.accept(event()); g.accept(event(eid=6,gross_lamports=-1))
            self.assertFalse(g.latest)
        def test_18_duplicate(self):
            g=make(); g.accept(event()); g.accept(event()); self.assertEqual(g.counts['duplicate'],1)
        def test_19_epoch_change_failclosed(self):
            g=make(); g.accept(event()); g.health(dict(epoch=3,producer='fixture_producer_ABC'))
            self.assertTrue(g.failed); self.assertFalse(g.latest)
        def test_20_new_429_failclosed(self):
            g=make(); g.health(dict(epoch=2,producer='fixture_producer_ABC',websocket_429_observed=3))
            g.health(dict(epoch=2,producer='fixture_producer_ABC',websocket_429_observed=4))
            self.assertEqual(g.failure,'NEW_429_PROVIDER_RATE_LIMIT')
        def test_21_history_429_not_cleared(self):
            g=make(); g.health(dict(epoch=2,producer='fixture_producer_ABC',websocket_429_observed=7))
            self.assertEqual(g.provider_health,'WS_429_HISTORY_REQUIRES_REVALIDATION')
        def test_22_callback_invoked(self):
            rows=[]; g=make(rows.append);g.accept(event());self.assertEqual(rows[0]['event_id'],5)
        def test_23_callback_failure_cannot_execute(self):
            def fail(x):raise RuntimeError('fixture')
            g=make(fail);self.assertIsNone(g.accept(event()));self.assertTrue(g.failed)
        def test_24_cursor_regression(self):
            class Fake:
                def new_events(self,c,cur):return [],cur-1
            g=make()
            with tempfile.TemporaryDirectory() as td:
                process_new_events(Fake(),None,g,Path(td)/'inbox.json')
            self.assertEqual(g.failure,'SCANNER_BUS_CURSOR_REGRESSION')
        def test_25_no_authority(self):
            r=make().accept(event())
            self.assertFalse(r['execution_authority']);self.assertFalse(r['signing']);self.assertFalse(r['broadcast'])
        def test_26_expire(self):
            now=[100];g=LocalIngress(clock_ns=lambda:NOW,mono_ns=lambda:now[0]);g.attach(dict(epoch=2,producer='fixture_producer_ABC'),0)
            g.accept(event()); now[0]+=1_500_000_000;g.expire();self.assertFalse(g.latest)
        def test_27_export_is_not_trade(self):
            g=make();g.accept(event());self.assertTrue(g.export()['health_uncertified_for_execution'])
        def test_28_pubkey_invalid_zero(self):self.assertFalse(valid_pubkey('0'*43))
        def test_29_bad_batch_failclosed(self):
            class Bad:
                def new_events(self,c,cur):return {'events':[]},cur
            g=make()
            with tempfile.TemporaryDirectory() as td:process_new_events(Bad(),None,g,Path(td)/'inbox.json')
            self.assertTrue(g.failed)
        def test_30_integrity_size_limit(self):
            self.assertEqual(FIRST_FUNDED_CANARY_LAMPORTS,10_000_000)
        def test_31_callback_copy(self):
            calls=[];g=make(calls.append);g.accept(event());calls[0]['token']='altered';self.assertEqual(g.latest[TOKEN]['token'],TOKEN)
        def test_32_local_db_to_inbox_fixture(self):
            import sqlite3
            from types import ModuleType
            conn=sqlite3.connect(':memory:')
            conn.execute('CREATE TABLE events (id INTEGER PRIMARY KEY)')
            conn.execute('INSERT INTO events VALUES (5)')
            data=event(created_ns=time.time_ns()-20_000_000)
            g=LocalIngress()
            g.attach({'epoch':2,'producer':'fixture_producer_ABC'},4)
            class FakeScanner:
                def new_events(self,conn,cursor):return [data],5
            module=ModuleType(PACKAGE+'.oracle_351_fast_bank_parity')
            module.keep_latest=lambda rows:list(rows)
            old=sys.modules.get(module.__name__)
            sys.modules[module.__name__]=module
            try:
                with tempfile.TemporaryDirectory() as td:
                    path=Path(td)/'inbox.json'
                    process_new_events(FakeScanner(),conn,g,path)
                    self.assertTrue(path.exists())
                    inbox=json.loads(path.read_text())
                    self.assertEqual(inbox['candidates'][0]['size_lamports'],10_000_000)
                    self.assertFalse(inbox['candidates'][0]['native_atomic_simulation_certified'])
                    self.assertEqual(g.cursor,5)
                    self.assertEqual(g.counts['raw_events_seen'],1)
            finally:
                conn.close()
                if old is None:sys.modules.pop(module.__name__,None)
                else:sys.modules[module.__name__]=old
        def test_33_process_source_cannot_trade(self):
            g=make();self.assertEqual(g.export()['first_funded_canary_lamports'],10_000_000)
            self.assertFalse(g.export()['execution_authority'])
        def test_34_actual_source_graph_without_parent_scan(self):
            from types import SimpleNamespace
            from unittest.mock import patch
            scanner=SimpleNamespace(bus=lambda:None,validate_scanner=lambda c:{},
                                    new_events=lambda c,k:([],k))
            child=SimpleNamespace(scan=scanner)
            parent=SimpleNamespace(old351=child)  # No parent.scan: exact regression
            with patch('importlib.import_module',side_effect=lambda name:
                       parent if name.endswith('oracle_352_scanner_bank_alignment') else child):
                self.assertIs(resolve_scanner_bus(),scanner)
        def test_35_wrong_scanner_graph_rejected(self):
            from types import SimpleNamespace
            from unittest.mock import patch
            child=SimpleNamespace(scan=SimpleNamespace())
            parent=SimpleNamespace(old351=SimpleNamespace(scan=child.scan))
            with patch('importlib.import_module',side_effect=lambda name:
                       parent if name.endswith('oracle_352_scanner_bank_alignment') else child):
                with self.assertRaisesRegex(RuntimeError,'SOURCE_GRAPH_MISMATCH'):
                    resolve_scanner_bus()
        def test_36_missing_required_method_fails_closed(self):
            from types import SimpleNamespace
            from unittest.mock import patch
            child=SimpleNamespace(scan=SimpleNamespace(bus=lambda:None))
            parent=SimpleNamespace(old351=child)
            with patch('importlib.import_module',side_effect=lambda name:
                       parent if name.endswith('oracle_352_scanner_bank_alignment') else child):
                with self.assertRaisesRegex(RuntimeError,'SCANNER_BUS_API_UNAVAILABLE'):
                    resolve_scanner_bus()
        def test_37_parent_scan_cannot_override_351(self):
            from types import SimpleNamespace
            from unittest.mock import patch
            real=SimpleNamespace(bus=lambda:None,validate_scanner=lambda c:{},
                                 new_events=lambda c,k:([],k))
            child=SimpleNamespace(scan=real)
            parent=SimpleNamespace(old351=child,scan='WRONG_SCANNER')
            with patch('importlib.import_module',side_effect=lambda name:
                       parent if name.endswith('oracle_352_scanner_bank_alignment') else child):
                self.assertIs(resolve_scanner_bus(),real)
        def test_38_direct_bus_live_smoke(self):
            # Exercises live_session(scanner=None), module resolver, real SQLite
            # cursor setup, scan.new_events(), coalescing, and temp inbox.
            import sqlite3
            from types import SimpleNamespace
            from unittest.mock import patch
            connect_count=[]
            class FakeScan:
                def bus(self):
                    c=sqlite3.connect(':memory:')
                    c.execute('CREATE TABLE events (id INTEGER PRIMARY KEY)')
                    c.execute('INSERT INTO events VALUES(4)')
                    connect_count.append(1)
                    return c
                def validate_scanner(self, conn):
                    return dict(epoch=2,producer='fixture_producer_ABC',websocket_429_observed=0)
                def new_events(self, conn, cursor):
                    if cursor<5:
                        x=event(eid=5, created_ns=time.time_ns()-20_000_000)
                        return [x],5
                    return [],cursor
            fake=FakeScan()
            child=SimpleNamespace(scan=fake,keep_latest=lambda rows:rows)
            parent=SimpleNamespace(old351=child)
            def imports(name):
                if name.endswith('oracle_352_scanner_bank_alignment'):return parent
                if name.endswith('oracle_351_fast_bank_parity'):return child
                raise AssertionError('UNEXPECTED_IMPORT_'+name)
            with tempfile.TemporaryDirectory() as td:
                rp=Path(td)/'report.json';ip=Path(td)/'inbox.json'
                # Fast forward the clock only after the first real bus read.
                # No RPC, WebSockets, signer, or fake positive P&L certification.
                tick=[0]
                orig_mono=time.monotonic
                def elapsed():
                    tick[0]+=0.8
                    return tick[0]
                with patch('importlib.import_module',side_effect=imports), \
                     patch.object(time,'monotonic',side_effect=elapsed), \
                     patch.object(time,'sleep',return_value=None):
                    result=live_session(seconds=5,ttl_ms=2500,max_age_ms=1500,
                                      poll_ms=10,scanner=None,report_path=rp,
                                      inbox_path=ip,lock_required=False,pre_audited=True)
                self.assertEqual(result,0)
                output=json.loads(rp.read_text(encoding='utf-8'))
                self.assertEqual(output['ever_staged'],1)
                self.assertEqual(len(connect_count),1)
                self.assertEqual(output['counts']['ingressed'],1)
                self.assertFalse(ip.exists())
                self.assertFalse(output['native_atomic_simulation_certified'])
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    if not result.wasSuccessful():
        return 1
    print('[ORACLE362_TEST_PASS]', result.testsRun, flush=True)
    return 0


def main():
    ap=argparse.ArgumentParser()
    for flag in ('install','test','audit','run'):
        ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--seconds',type=int,default=90)
    ap.add_argument('--ttl-ms',type=int,default=2500)
    ap.add_argument('--max-age-ms',type=int,default=1500)
    ap.add_argument('--poll-ms',type=int,default=10)
    args=ap.parse_args()
    if not any((args.install,args.test,args.audit,args.run)):
        ap.error('SELECT_MODE')
    if args.test and tests():return 1
    if args.install:install()
    if args.audit:audit()
    if args.run:
        print('[ORACLE362_START] SCANNER322_READ_ONLY LOCAL_BUS_POLL_10MS NO_RPC_WS '
              'SIZES_010_TO_100 REPRICE_STAGE_ONLY NO_SIGN_NO_BROADCAST',flush=True)
        try:
            return live_session(args.seconds,args.ttl_ms,args.max_age_ms,args.poll_ms)
        except (RuntimeError, ImportError, AttributeError) as exc:
            # Only print our own literal classifications; never print raw
            # exception messages that might contain authenticated RPC URLs.
            known = frozenset(('ORACLE352_351_SOURCE_GRAPH_MISMATCH',
                               'ORACLE351_SCANNER_BUS_API_UNAVAILABLE'))
            message = str(exc) if str(exc) in known else 'AUDIT_OR_SCANNER_SOURCE_UNAVAILABLE'
            print('[ORACLE362_HOLD]',message,'exception_type='+type(exc).__name__,flush=True)
            return 2
    return 0

if __name__=='__main__':
    sys.exit(main())
