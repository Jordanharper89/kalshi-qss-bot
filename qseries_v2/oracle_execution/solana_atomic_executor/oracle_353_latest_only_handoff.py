"""ORACLE-353: shadow-only, fail-closed, latest-only ORACLE-352 handoff.

Complete installer: installs only this module; NEVER modifies frozen ORACLE-322 or 352.
No key reading, signing, broadcasting, or new websocket subscriptions.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unittest

MODULE_DIR = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = MODULE_DIR / 'oracle_353_latest_only_handoff.py'
UPSTREAM = Path('build_oracle_352_scanner_bank_alignment.py')
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_353_handoff_report.json')
CANARY_LAMPORTS = 10_000_000
EXECUTION_AUTHORITY = False
SIGNING = False
BROADCAST = False
TAGS = re.compile(r'^\[(ORACLE352_[A-Z_]+)\]\s*(\{.*\})\s*$')


def install():
    MODULE_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve()
    if source != TARGET.resolve():
        tmp = TARGET.with_suffix('.py.tmp')
        shutil.copyfile(source, tmp)
        os.replace(tmp, TARGET)
    import py_compile
    py_compile.compile(str(TARGET), doraise=True)
    sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print('[ORACLE353_INSTALL_PASS]', str(TARGET), 'sha256=' + sha)


def audit():
    if not UPSTREAM.is_file():
        raise RuntimeError('ORACLE352_FULL_INSTALLER_MISSING')
    if not (MODULE_DIR / 'oracle_352_scanner_bank_alignment.py').is_file():
        raise RuntimeError('ORACLE352_RUNTIME_MISSING')
    p = subprocess.run([sys.executable, str(UPSTREAM), '--audit'],
                       text=True, capture_output=True, timeout=35, check=False)
    required = ('FROZEN_SCANNER_SHA_MATCH', 'SHADOW_ONLY', 'NO_NEW_WEBSOCKET',
                'SIGNING_FALSE', 'BROADCAST_FALSE')
    if p.returncode or not all(s in p.stdout for s in required):
        raise RuntimeError('ORACLE352_SCANNER_FREEZE_AUDIT_FAILED')
    print('[ORACLE353_AUDIT_PASS] SCANNER_322_FROZEN ORACLE352_READ_ONLY '
          'NO_EXTRA_WS NO_SIGN NO_BROADCAST')


class Gate:
    def __init__(self, max_age_ms=850, max_slot_gap=2, clock=time.monotonic):
        self.clock = clock
        self.max_age_ms = int(max_age_ms)
        self.max_slot_gap = int(max_slot_gap)
        self.epoch = None
        self.producer = None
        self.cursor = None
        self.started = self.clock()
        self.last_cursor_advance = self.started
        self.feed_fault = None
        self.terminal = None
        self.pending = {}
        self.latest = {}
        self.seen = set()
        self.presim = []
        self.counts = dict(bus_submitted=0, bank_parity=0, telemetry=0,
                           stale=0, superseded=0, negative=0, parity_mismatch=0,
                           presim_ready=0, certified=0, ws_429=0,
                           epoch_changes=0, invalid=0)

    def reject(self, reason):
        if reason == 'STALE':
            self.counts['stale'] += 1
        elif reason == 'SUPERSEDED':
            self.counts['superseded'] += 1
        elif reason == 'BANK_NEGATIVE':
            self.counts['negative'] += 1
        elif reason == 'MODEL_DISAGREEMENT':
            self.counts['parity_mismatch'] += 1
        else:
            self.counts['invalid'] += 1
        return {'gate': 'HOLD_' + reason, 'signing': False, 'broadcast': False}

    def ready(self, row):
        epoch, producer = row.get('epoch'), row.get('producer')
        if not isinstance(epoch, int) or not isinstance(producer, str) or not producer:
            return self.reject('BAD_PRODUCER')
        if self.epoch is not None and (epoch, producer) != (self.epoch, self.producer):
            self.counts['epoch_changes'] += 1
            self.pending.clear()
            self.latest.clear()
            self.feed_fault = 'EPOCH_OR_PRODUCER_CHANGED'
            self.terminal = self.feed_fault
            return self.reject(self.feed_fault)
        self.epoch, self.producer = epoch, producer
        self.cursor = row.get('cursor')
        self.last_cursor_advance = self.clock()
        return {'gate': 'PRODUCER_BOUND', 'signing': False, 'broadcast': False}

    def heartbeat(self, row):
        if self.epoch is None:
            return self.reject('NO_READY')
        if row.get('epoch') != self.epoch:
            self.pending.clear()
            self.latest.clear()
            self.counts['epoch_changes'] += 1
            self.feed_fault = 'EPOCH_OR_PRODUCER_CHANGED'
            self.terminal = self.feed_fault
            return self.reject(self.feed_fault)
        old = self.cursor
        cur = row.get('bus_cursor')
        if type(cur) is int and (old is None or cur > old):
            self.cursor = cur
            self.last_cursor_advance = self.clock()
        if type(cur) is int and type(old) is int and cur < old:
            self.feed_fault = 'BUS_CURSOR_REGRESSED'
            self.terminal = self.feed_fault
        observed = row.get('websocket_429_observed', 0)
        if type(observed) is int and observed > 0:
            self.counts['ws_429'] = max(self.counts['ws_429'], observed)
            self.feed_fault = 'WEBSOCKET_429_UNRECOVERED'
            self.terminal = self.feed_fault
        if self.terminal:
            self.pending.clear()
            self.latest.clear()
            return self.reject(self.terminal)
        return None

    def submit(self, row):
        if not row.get('admitted') or not row.get('event_id'):
            self.counts['telemetry'] += 1
            return self.reject('TELEMETRY_ONLY')
        if self.epoch is None or self.feed_fault:
            return self.reject('FEED_UNTRUSTED')
        eid = str(row['event_id'])
        token = row.get('token')
        if not isinstance(token, str) or len(token) < 12 or eid in self.seen:
            return self.reject('DUPLICATE_OR_BAD_IDENTITY')
        age = row.get('age_ms')
        if not isinstance(age, (int, float)) or not 0 <= age <= self.max_age_ms:
            return self.reject('STALE')
        old = self.latest.get(token)
        if old and old in self.pending:
            del self.pending[old]
            self.counts['superseded'] += 1
        self.seen.add(eid)
        self.latest[token] = eid
        self.pending[eid] = {'token': token, 'direction': row.get('direction'),
                             'time': self.clock(), 'epoch': self.epoch,
                             'producer': self.producer}
        self.counts['bus_submitted'] += 1
        return {'gate': 'LATEST_ADMITTED_PENDING_BANK', 'signing': False, 'broadcast': False}

    def parity(self, row):
        self.counts['bank_parity'] += 1
        eid = row.get('event_id')
        if eid is None or not row.get('admitted'):
            return self.reject('TELEMETRY_ONLY')
        eid = str(eid)
        p = self.pending.pop(eid, None)
        if p is None:
            return self.reject('MISSING_OR_SUPERSEDED_SUBMIT')
        token = row.get('token')
        if (self.feed_fault or p['epoch'] != self.epoch or
                p['producer'] != self.producer):
            return self.reject('FEED_UNTRUSTED')
        if not isinstance(token, str) or not token.startswith(p['token']):
            return self.reject('TOKEN_MISMATCH')
        if self.latest.get(p['token']) != eid:
            return self.reject('SUPERSEDED')
        if row.get('direction') != p['direction']:
            return self.reject('DIRECTION_MISMATCH')
        age = row.get('source_age_at_bank_end_ms')
        if (not isinstance(age, (int, float)) or age < 0 or
                age > self.max_age_ms or
                (self.clock() - p['time']) * 1000 > self.max_age_ms):
            return self.reject('STALE')
        s, b, gap = row.get('scanner_slot'), row.get('bank_slot'), row.get('bank_slot_gap')
        if not all(type(x) is int for x in (s, b, gap)) or gap != b-s or not 0 <= gap <= self.max_slot_gap:
            return self.reject('SLOT_GAP')
        if (row.get('single_context_verified') is not True or
                row.get('quote_model_result') != 'SAME_BANK_MODEL_PARITY' or
                row.get('q18_same_bank_gross') != row.get('executor_same_bank_gross') or
                not re.fullmatch('[0-9a-f]{64}', str(row.get('account_fingerprint', '')))):
            return self.reject('MODEL_DISAGREEMENT')
        if row.get('size_lamports') != CANARY_LAMPORTS:
            return self.reject('WRONG_CANARY_SIZE')
        gross = row.get('executor_same_bank_gross')
        if type(gross) is not int or gross <= 0:
            return self.reject('BANK_NEGATIVE')
        self.counts['presim_ready'] += 1
        result = {'gate': 'BANK_POSITIVE_AWAIT_NATIVE_ATOMIC_SIM', 'event_id': eid,
                  'token_prefix': token[:12], 'size_lamports': CANARY_LAMPORTS,
                  'bank_slot': b, 'gross_lamports': gross,
                  'fingerprint': row['account_fingerprint'],
                  'signing': False, 'broadcast': False}
        self.presim.append(result)
        return result

    def ingest(self, tag, row):
        if tag == 'ORACLE352_READY':
            return self.ready(row)
        if tag == 'ORACLE352_HEARTBEAT':
            return self.heartbeat(row)
        if tag == 'ORACLE352_BANK_SUBMIT':
            return self.submit(row)
        if tag == 'ORACLE352_BANK_PARITY':
            return self.parity(row)
        if tag == 'ORACLE352_EXIT':
            if row.get('reason') == 'EPOCH_OR_PRODUCER_CHANGED':
                self.feed_fault = 'EPOCH_OR_PRODUCER_CHANGED'
                self.terminal = self.feed_fault
        return None

    def summary(self):
        return {'status': ('HOLD_' + self.feed_fault if self.feed_fault else
                       'NO_NEW_ADMITTED_BUS_EVENTS' if self.counts['bus_submitted'] == 0 else
                       'PRE_SIM_PENDING' if self.presim else 'NO_POSITIVE_BANK'),
                'epoch': self.epoch, 'producer_prefix': (self.producer or '')[:12],
                'cursor': self.cursor, 'counts': self.counts,
                'presim_candidates': self.presim[-20:],
                'fee_adjusted_profit_certified': False,
                'native_atomic_simulation_certified': False,
                'first_funded_canary_lamports': CANARY_LAMPORTS,
                'signing': False, 'broadcast': False, 'execution_authority': False}


def decode(line):
    match = TAGS.match(line.strip())
    if not match:
        return None
    try:
        data = json.loads(match.group(2))
        if isinstance(data, dict):
            return match.group(1), data
    except (ValueError, TypeError):
        pass
    return None


def report(gate):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT.with_suffix('.tmp')
    temp.write_text(json.dumps(gate.summary(), sort_keys=True, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, REPORT)


@contextlib.contextmanager
def single_instance():
    lockpath = Path('runtime_state/oracle/final_boss_dual/oracle_353_handoff.lock')
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    with lockpath.open('a+b') as fd:
        fd.seek(0)
        if fd.read(1) != b'1':
            fd.seek(0)
            fd.write(b'1')
            fd.flush()
        fd.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fd.seek(0)
            if os.name == 'nt':
                msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)


def run(args):
    audit()
    gate = Gate(args.max_age_ms, args.max_slot_gap)
    argv = [sys.executable, '-u', str(UPSTREAM), '--run',
            '--seconds', str(args.seconds), '--pairs', str(args.pairs),
            '--array-cap', str(args.array_cap), '--probes', '0',
            '--ttl-ms', str(args.ttl_ms), '--controls', '0']
    print('[ORACLE353_LIVE_START] UPSTREAM=ORACLE352 ONE_SCANNER_SESSION '
          'CONTROLS=0 PROBES=0 SIGNING_FALSE BROADCAST_FALSE', flush=True)
    code = 3
    with single_instance():
        with subprocess.Popen(argv, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                              bufsize=1) as child:
            try:
                for line in child.stdout:
                    event = decode(line)
                    if event:
                        tag, payload = event
                        result = gate.ingest(tag, payload)
                        if result and (tag in ('ORACLE352_BANK_PARITY', 'ORACLE352_READY') or
                                       result['gate'].startswith('HOLD_') and tag == 'ORACLE352_BANK_SUBMIT'):
                            print('[ORACLE353_HANDOFF]', json.dumps(result, sort_keys=True), flush=True)
                        if gate.terminal:
                            child.terminate()
                            break
                    elif '429' in line and ('websocket' in line.lower() or 'rate limit' in line.lower()):
                        gate.feed_fault = 'WEBSOCKET_429_UNRECOVERED'
                        gate.terminal = gate.feed_fault
                        child.terminate()
                        break
                try:
                    code = child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    code = child.wait()
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
    if gate.epoch is None and gate.feed_fault is None:
        gate.feed_fault = 'NO_SCANNER_READY'
    if code and not gate.feed_fault:
        gate.feed_fault = 'UPSTREAM_EXIT_' + str(code)
    report(gate)
    print('[ORACLE353_EXIT]', json.dumps(gate.summary(), sort_keys=True), flush=True)
    print('[ORACLE353_REPORT]', str(REPORT))
    return 2 if gate.feed_fault else 0


def tests():
    class T(unittest.TestCase):
        def setUp(self):
            self.now = [10.0]
            self.g = Gate(clock=lambda: self.now[0])
            self.g.ready({'epoch': 1, 'producer': 'abc', 'cursor': 2})
        def sub(self, eid='a', token='abcdefghijkl', age=4, admitted=True):
            return self.g.submit(dict(event_id=eid, token=token, direction='PUMP_TO_METEORA', age_ms=age, admitted=admitted))
        def bank(self, eid='a', gross=100000, **kw):
            row = dict(event_id=eid, admitted=True, token='abcdefghijklmnopqrst',
                       direction='PUMP_TO_METEORA', scanner_slot=100, bank_slot=100,
                       bank_slot_gap=0, source_age_at_bank_end_ms=200,
                       single_context_verified=True, quote_model_result='SAME_BANK_MODEL_PARITY',
                       q18_same_bank_gross=gross, executor_same_bank_gross=gross,
                       account_fingerprint='a'*64, size_lamports=CANARY_LAMPORTS)
            row.update(kw)
            return self.g.parity(row)
        def test_01_good_positive_is_presim_only(self):
            self.sub(); self.assertEqual(self.bank()['gate'], 'BANK_POSITIVE_AWAIT_NATIVE_ATOMIC_SIM')
            self.assertFalse(self.g.summary()['native_atomic_simulation_certified'])
        def test_02_negative_hold(self):
            self.sub(); self.assertEqual(self.bank(gross=-1)['gate'], 'HOLD_BANK_NEGATIVE')
        def test_03_telemetry_never_admits(self):
            self.sub(admitted=False); self.assertEqual(self.bank()['gate'], 'HOLD_MISSING_OR_SUPERSEDED_SUBMIT')
        def test_04_missing_id(self):
            self.assertEqual(self.sub(eid=None)['gate'], 'HOLD_TELEMETRY_ONLY')
        def test_05_late_source(self):
            self.sub(); self.assertEqual(self.bank(source_age_at_bank_end_ms=900)['gate'], 'HOLD_STALE')
        def test_06_delayed_handoff(self):
            self.sub(); self.now[0] += 1.; self.assertEqual(self.bank()['gate'], 'HOLD_STALE')
        def test_07_latest_wins(self):
            self.sub('a'); self.sub('b'); self.assertEqual(self.bank('a')['gate'], 'HOLD_MISSING_OR_SUPERSEDED_SUBMIT')
            self.assertEqual(self.bank('b')['gate'], 'BANK_POSITIVE_AWAIT_NATIVE_ATOMIC_SIM')
        def test_08_repeated_event(self):
            self.sub(); self.assertEqual(self.sub()['gate'], 'HOLD_DUPLICATE_OR_BAD_IDENTITY')
        def test_09_bad_model(self):
            self.sub(); self.assertEqual(self.bank(q18_same_bank_gross=99)['gate'], 'HOLD_MODEL_DISAGREEMENT')
        def test_10_bad_slot(self):
            self.sub(); self.assertEqual(self.bank(bank_slot=104, bank_slot_gap=4)['gate'], 'HOLD_SLOT_GAP')
        def test_11_canary_size(self):
            self.sub(); self.assertEqual(self.bank(size_lamports=9_000_000)['gate'], 'HOLD_WRONG_CANARY_SIZE')
        def test_12_epoch_invalidates(self):
            self.sub(); self.g.ready({'epoch':2,'producer':'def','cursor':0})
            self.assertEqual(self.bank()['gate'], 'HOLD_MISSING_OR_SUPERSEDED_SUBMIT')
            self.assertEqual(self.g.feed_fault, 'EPOCH_OR_PRODUCER_CHANGED')
        def test_13_ws429_invalidates(self):
            self.sub(); self.g.heartbeat({'epoch':1, 'bus_cursor':2,'websocket_429_observed':1})
            self.assertEqual(self.g.feed_fault, 'WEBSOCKET_429_UNRECOVERED')
            self.assertFalse(self.g.pending)
        def test_14_cursor_regression(self):
            self.g.heartbeat({'epoch':1,'bus_cursor':1,'websocket_429_observed':0})
            self.assertEqual(self.g.feed_fault, 'BUS_CURSOR_REGRESSED')
        def test_15_no_unknown_implicit_event(self):
            self.assertIsNone(decode('[NOPE] {"admitted":true}'))
        def test_16_good_decode(self):
            self.assertEqual(decode('[ORACLE352_READY] {"epoch":1}')[0], 'ORACLE352_READY')
        def test_17_same_bank_required(self):
            self.sub(); self.assertEqual(self.bank(single_context_verified=False)['gate'], 'HOLD_MODEL_DISAGREEMENT')
        def test_18_token_match(self):
            self.sub(); self.assertEqual(self.bank(token='differenttoken')['gate'], 'HOLD_TOKEN_MISMATCH')
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE353_TEST]', json.dumps({'passed': result.wasSuccessful(), 'tests': result.testsRun}))
    return 0 if result.wasSuccessful() else 1


def main():
    ap = argparse.ArgumentParser(description='ORACLE-353 latest-only shadow handoff')
    mode = ap.add_mutually_exclusive_group(required=True)
    for name in ('install', 'audit', 'test', 'run'):
        mode.add_argument('--' + name, action='store_true')
    ap.add_argument('--seconds', type=int, default=90)
    ap.add_argument('--pairs', type=int, default=28)
    ap.add_argument('--array-cap', type=int, default=60)
    ap.add_argument('--ttl-ms', type=int, default=2500)
    ap.add_argument('--max-age-ms', type=int, default=850)
    ap.add_argument('--max-slot-gap', type=int, default=2)
    args = ap.parse_args()
    if args.install: install()
    elif args.audit: audit()
    elif args.test: return tests()
    else:
        if not (1 <= args.seconds <= 3600 and 1 <= args.pairs <= 500 and
                1 <= args.array_cap <= 200 and 100 <= args.ttl_ms <= 10000 and
                100 <= args.max_age_ms <= 2500 and 0 <= args.max_slot_gap <= 20):
            ap.error('unsafe runtime limits')
        return run(args)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('[ORACLE353_HOLD]', type(exc).__name__)
        sys.exit(2)
