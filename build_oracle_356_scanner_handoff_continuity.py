"""ORACLE-356: full, fail-closed scanner bus -> pre-atomic bridge with upstream failure containment.

Never edits ORACLE-322 or ORACLE-352. No new WS/RPC client, wallet access,
transaction assembly, signing, or broadcasting. Uses existing ORACLE-352
producer's newline-delimited bus and single-bank parity records.
"""
from __future__ import annotations
import argparse
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import py_compile
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_356_scanner_handoff_continuity.py'
ORACLE352_INSTALLER = Path('build_oracle_352_scanner_bank_alignment.py')
ORACLE352_MODULE = ROOT / 'oracle_352_scanner_bank_alignment.py'
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_356_bridge_report.json')
INBOX = Path('runtime_state/oracle/final_boss_dual/oracle_356_atomic_presim_inbox.json')
LOCK = Path('runtime_state/oracle/final_boss_dual/oracle_355_bridge.lock')
SIZE_LAMPORTS = 10_000_000
TAG = re.compile(r'^\[(ORACLE352_(?:READY|HEARTBEAT|BANK_SUBMIT|BANK_PARITY|EXIT))\] (\{.*\})\s*$')
FP = re.compile(r'^[0-9a-f]{64}$')
PUBKEY = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
EXC = re.compile(r'^(?:[\w.]+\.)?([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception)|AssertionError|SystemExit|KeyboardInterrupt)(?::|$)')
FRAME = re.compile(r'\bFile "([^"]+)", line (\d+)')
ALLOW_DIRECTIONS = frozenset(('PUMP_TO_METEORA', 'METEORA_TO_PUMP'))

EXECUTION_AUTHORITY = False
SIGNING = False
BROADCAST = False


def install():
    ROOT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve()
    if source != TARGET.resolve():
        temp = TARGET.with_suffix('.py.tmp')
        shutil.copyfile(source, temp)
        os.replace(temp, TARGET)
    py_compile.compile(str(TARGET), doraise=True)
    print('[ORACLE356_INSTALL_PASS]', TARGET, 'sha256=' + hashlib.sha256(TARGET.read_bytes()).hexdigest())


def audit():
    if not ORACLE352_INSTALLER.is_file() or not ORACLE352_MODULE.is_file():
        raise RuntimeError('ORACLE352_PRODUCTION_MODULE_MISSING')
    p = subprocess.run([sys.executable, str(ORACLE352_INSTALLER), '--audit'],
                       capture_output=True, text=True, timeout=45, check=False)
    tokens = ('FROZEN_SCANNER_SHA_MATCH', 'SHADOW_ONLY', 'NO_NEW_WEBSOCKET',
              'SIGNING_FALSE', 'BROADCAST_FALSE')
    if p.returncode or any(t not in p.stdout for t in tokens):
        raise RuntimeError('ORACLE352_SCANNER_FREEZE_AUDIT_FAILED')
    print('[ORACLE356_AUDIT_PASS] ORACLE322_FROZEN ORACLE352_UNMODIFIED '
          'ONE_UPSTREAM_SESSION NO_NEW_WS NO_NEW_RPC NO_SIGN NO_BROADCAST')


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def event_decode(line):
    m = TAG.match(line.strip())
    if m is None:
        return None
    try:
        row = json.loads(m.group(2))
        return (m.group(1), row) if isinstance(row, dict) else None
    except (ValueError, TypeError):
        return None


def traceback_signature(lines):
    """Extract exception class and sanitized source basename/line only."""
    frames = []
    cls = 'UNCLASSIFIED_UPSTREAM_FAILURE'
    for line in lines:
        m = FRAME.search(line)
        if m:
            basename = m.group(1).replace('\\','/').split('/')[-1]
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,90}\.py', basename):
                basename = 'UNSAFE_PATH_REDACTED'
            frames.append({'file': basename, 'line': int(m.group(2))})
        match = EXC.match(line.strip())
        if match:
            cls = match.group(1)[:80]
    return {'exception_type': cls, 'frames': frames[-5:]}


class Bridge:
    """Per-token latest-only admission, bound to 352 producer/cursor lineage."""
    def __init__(self, max_age_ms=1500, max_slot_gap=2, clock_ns=time.perf_counter_ns):
        self.clock_ns = clock_ns
        self.max_age_ns = int(max_age_ms * 1_000_000)
        self.max_slot_gap = int(max_slot_gap)
        self.epoch = None
        self.producer = None
        self.cursor = None
        self.last_cursor = None
        self.last_heartbeat_ns = None
        self.pending = {}
        self.latest = {}
        self.seen = OrderedDict()
        self.latest_inbox = {}
        self.inbox_deadlines = {}
        self.inbox_dirty = False
        self.history_429 = None
        self.bad_feed = None
        self.failed = False
        self.counts = dict(ready=0, bus_submitted=0, bank_verified=0,
                           positive_bank=0, negative_bank=0, preatomic=0,
                           duplicate=0, stale=0, superseded=0, identity=0,
                           no_event_id=0, slot_gap=0, non_parity=0,
                           ws_429=0, cursor_regression=0, epoch_change=0,
                           source_untrusted=0)
        self.latencies_ms = []
        self.last_reason = 'NOT_STARTED'
        self.upstream_exit_reason = None
        self.last_heartbeat = None
        self.heartbeat_samples = 0
        self.first_heartbeat = None
        self.last_heartbeat_at_ns = None
        self.bus_cursor_advanced = False
        self.bus_events_initial = None
        self.bus_events_final = None
        self.emitted_initial = None
        self.emitted_final = None

    def hold(self, reason, count=None):
        self.last_reason = reason
        if count:
            self.counts[count] += 1
        return None

    def invalidate(self, reason):
        self.pending.clear()
        self.latest.clear()
        self.latest_inbox.clear()
        self.inbox_deadlines.clear()
        self.inbox_dirty = True
        self.bad_feed = reason
        self.failed = True
        self.last_reason = reason

    def ready(self, row):
        epoch = row.get('epoch')
        producer = row.get('producer')
        cursor = row.get('cursor')
        if type(epoch) is not int or not isinstance(producer, str) or len(producer) < 8 or type(cursor) is not int:
            return self.hold('INVALID_PRODUCER_LINEAGE', 'identity')
        if self.epoch is not None and (epoch, producer) != (self.epoch, self.producer):
            self.counts['epoch_change'] += 1
            self.invalidate('EPOCH_OR_PRODUCER_CHANGED')
            return None
        self.epoch, self.producer, self.cursor = epoch, producer, cursor
        self.last_cursor = cursor
        self.counts['ready'] += 1
        self.last_reason = 'PRODUCER_READY'
        return None

    def heartbeat(self, row):
        if self.epoch is None:
            return self.hold('NO_PRODUCER_READY')
        if row.get('epoch') != self.epoch:
            self.counts['epoch_change'] += 1
            self.invalidate('EPOCH_OR_PRODUCER_CHANGED')
            return None
        cur = row.get('bus_cursor')
        if type(cur) is not int:
            return self.hold('HEARTBEAT_CURSOR_MISSING', 'identity')
        if cur < self.cursor:
            self.counts['cursor_regression'] += 1
            self.invalidate('BUS_CURSOR_REGRESSED')
            return None
        if self.cursor is not None and cur > self.cursor:
            self.bus_cursor_advanced = True
        self.cursor = cur
        self.last_heartbeat_ns = self.clock_ns()
        self.last_heartbeat_at_ns = self.last_heartbeat_ns
        self.heartbeat_samples += 1
        safe_keys = ('bus_cursor', 'scanner_admitted', 'scanner_emitted',
                     'scanner_positive_count', 'websocket_429_observed',
                     'bank_verified', 'queue_len')
        self.last_heartbeat = {k: row.get(k) for k in safe_keys if type(row.get(k)) in (int, bool)}
        if type(row.get('bus_events')) is int:
            if self.bus_events_initial is None:
                self.bus_events_initial = row['bus_events']
            self.bus_events_final = row['bus_events']
        if type(row.get('scanner_emitted')) is int:
            if self.emitted_initial is None:
                self.emitted_initial = row['scanner_emitted']
            self.emitted_final = row['scanner_emitted']
        observed = row.get('websocket_429_observed')
        if type(observed) is not int or observed < 0:
            return self.hold('WS_HEALTH_UNINSTRUMENTED', 'source_untrusted')
        if self.history_429 is None:
            self.history_429 = observed
            if observed:
                # Cannot prove old subscriptions recovered; no atomic promotion.
                self.bad_feed = 'WS_429_HISTORY_NOT_RECERTIFIED'
                self.counts['ws_429'] = observed
        elif observed > self.history_429:
            self.counts['ws_429'] += observed - self.history_429
            self.invalidate('WEBSOCKET_429_NEW_RATE_LIMIT')
        elif observed < self.history_429:
            self.invalidate('WS_429_COUNTER_RESET_OR_PRODUCER_RESTART')
        self.history_429 = observed

    def submit(self, row):
        if row.get('admitted') is not True or not isinstance(row.get('event_id'), (str, int)):
            return self.hold('NOT_ADMITTED_BUS_EVENT', 'no_event_id')
        if self.epoch is None or self.failed or self.bad_feed:
            return self.hold('FEED_NOT_TRUSTED', 'source_untrusted')
        eid = str(row['event_id'])
        token = row.get('token')
        direction = row.get('direction')
        age = row.get('age_ms')
        if not eid or not isinstance(token, str) or len(token) < 12 or direction not in ALLOW_DIRECTIONS:
            return self.hold('INVALID_EVENT_IDENTITY', 'identity')
        if type(age) not in (int, float) or not 0 <= age <= self.max_age_ns / 1e6:
            return self.hold('STALE_AT_SUBMISSION', 'stale')
        if eid in self.seen:
            return self.hold('DUPLICATE', 'duplicate')
        self.seen[eid] = None
        if len(self.seen) > 2048:
            self.seen.popitem(last=False)
        old = self.latest.get(token)
        if old and old in self.pending:
            del self.pending[old]
            self.counts['superseded'] += 1
        # A newer nomination invalidates any older positive ingress immediately.
        for full in list(self.latest_inbox):
            if full.startswith(token):
                self.latest_inbox.pop(full, None)
                self.inbox_deadlines.pop(full, None)
                self.inbox_dirty = True
        self.latest[token] = eid
        self.pending[eid] = (token, direction, self.epoch, self.producer, self.clock_ns())
        self.counts['bus_submitted'] += 1
        self.last_reason = 'AWAIT_SINGLE_BANK_VERIFICATION'
        # Explicitly don't hand an unverified scanner nomination to the executor.
        return None

    def parity(self, row):
        self.counts['bank_verified'] += 1
        eid = row.get('event_id')
        if row.get('admitted') is not True or not isinstance(eid, (str, int)):
            return self.hold('BANK_TELEMETRY_NOT_ADMITTED', 'no_event_id')
        eid = str(eid)
        existing = self.pending.pop(eid, None)
        if existing is None:
            return self.hold('SUPERSEDED_OR_UNKNOWN_SUBMISSION', 'superseded')
        token, direction, epoch, producer, born = existing
        if self.failed or self.bad_feed or epoch != self.epoch or producer != self.producer:
            return self.hold('FEED_NOT_TRUSTED', 'source_untrusted')
        full_token = row.get('token')
        if (not isinstance(full_token, str) or not full_token.startswith(token)
                or self.latest.get(token) != eid or row.get('direction') != direction):
            return self.hold('BANK_EVENT_IDENTITY_MISMATCH', 'identity')
        age = row.get('source_age_at_bank_end_ms')
        if type(age) not in (int, float) or age < 0 or age * 1e6 > self.max_age_ns:
            return self.hold('BANK_SOURCE_STALE', 'stale')
        elapsed_ns = max(0, self.clock_ns() - born)
        if elapsed_ns > self.max_age_ns:
            return self.hold('HANDOFF_STALE', 'stale')
        scan, bank, gap = (row.get('scanner_slot'), row.get('bank_slot'), row.get('bank_slot_gap'))
        if (any(type(x) is not int for x in (scan, bank, gap))
                or gap != bank-scan or not 0 <= gap <= self.max_slot_gap):
            return self.hold('SLOT_CONTEXT_GAP', 'slot_gap')
        gross = row.get('executor_same_bank_gross')
        scanner_bank = row.get('q18_same_bank_gross')
        if (row.get('single_context_verified') is not True
                or row.get('quote_model_result') != 'SAME_BANK_MODEL_PARITY'
                or type(gross) is not int or type(scanner_bank) is not int or gross != scanner_bank
                or not FP.fullmatch(str(row.get('account_fingerprint','')))):
            return self.hold('SINGLE_BANK_PARITY_FAILED', 'non_parity')
        if row.get('size_lamports') != SIZE_LAMPORTS:
            return self.hold('NOT_EXACT_0010_SOL', 'identity')
        if gross <= 0:
            return self.hold('NEGATIVE_SINGLE_BANK_GROSS', 'negative_bank')
        if not all(PUBKEY.fullmatch(str(row.get(k, ''))) for k in ('pump_pool', 'meteora_pool')):
            return self.hold('POOL_IDENTITY_MISSING', 'identity')
        # This does not assert trade profitability: fees and atomic simulation remain unverified.
        self.counts['positive_bank'] += 1
        accepted_ns = self.clock_ns()
        latency = (accepted_ns-born) / 1e6
        self.latencies_ms.append(round(latency,3))
        self.latencies_ms = self.latencies_ms[-128:]
        data = dict(schema='ORACLE356_PREATOMIC_V1', event_id=eid, token=full_token,
                    pump_pool=row.get('pump_pool'), meteora_pool=row.get('meteora_pool'),
                    direction=direction, size_lamports=SIZE_LAMPORTS,
                    epoch=self.epoch, producer=self.producer, scanner_slot=scan,
                    bank_slot=bank, account_fingerprint=row['account_fingerprint'],
                    verified_bank_gross_lamports=gross, source_age_ms=age,
                    handoff_elapsed_ms=round(latency,3),
                    status='AWAIT_NATIVE_ATOMIC_SIMULATION',
                    executable_profit_certified=False, fee_adjusted_profit_certified=False,
                    native_atomic_simulation_certified=False,
                    signing=False, broadcast=False, execution_authority=False)
        # One current candidate per token, no queued obsolete signals.
        remaining_ns = max(0, self.max_age_ns - int(age * 1e6))
        data['expires_at_unix_ms'] = int(time.time()*1000 + remaining_ns/1e6)
        self.latest_inbox[full_token] = data
        self.inbox_deadlines[full_token] = accepted_ns + remaining_ns
        self.inbox_dirty = True
        self.counts['preatomic'] += 1
        self.last_reason = 'PREATOMIC_CANDIDATE_READY_NOT_EXECUTABLE'
        return data

    def expire(self):
        now = self.clock_ns()
        for token, deadline in list(self.inbox_deadlines.items()):
            if now >= deadline:
                self.inbox_deadlines.pop(token, None)
                self.latest_inbox.pop(token, None)
                self.inbox_dirty = True
                self.counts['stale'] += 1
                self.last_reason = 'PREATOMIC_CANDIDATE_EXPIRED'

    def ingest(self, tag, row):
        if tag == 'ORACLE352_READY': return self.ready(row)
        if tag == 'ORACLE352_HEARTBEAT': return self.heartbeat(row)
        if tag == 'ORACLE352_BANK_SUBMIT': return self.submit(row)
        if tag == 'ORACLE352_BANK_PARITY': return self.parity(row)
        if tag == 'ORACLE352_EXIT':
            reason = row.get('reason')
            self.upstream_exit_reason = reason if isinstance(reason, str) and len(reason) < 120 and re.fullmatch(r'[A-Z0-9_]+', reason) else 'UNCLASSIFIED_EXIT_REASON'
            if reason == 'EPOCH_OR_PRODUCER_CHANGED':
                self.counts['epoch_change'] += 1
                self.invalidate('EPOCH_OR_PRODUCER_CHANGED')
        return None

    def summary(self, child_code=None, child_lines=0, failure=None):
        if self.epoch is None: status = 'HOLD_SCANNER_DID_NOT_READY'
        elif self.failed or self.bad_feed: status = 'HOLD_' + str(self.bad_feed)
        elif not self.counts['bus_submitted']: status = 'HOLD_NO_NEW_ADMITTED_SCANNER_EVENTS'
        elif not self.counts['preatomic']: status = 'HOLD_NO_FRESH_POSITIVE_BANK'
        else: status = 'PREATOMIC_INGRESS_CONNECTED_ATOMIC_PENDING'
        if child_code not in (None, 0) and not status.startswith('HOLD_'):
            status = 'HOLD_UPSTREAM_ABNORMAL_EXIT'
        return dict(status=status, last_reason=self.last_reason, counts=self.counts,
                    epoch=self.epoch, producer_prefix=(self.producer or '')[:12],
                    cursor=self.cursor, upstream_exit_code=child_code, child_lines=child_lines,
                    upstream_failure_signature=failure,
                    upstream_exit_reason=self.upstream_exit_reason,
                    heartbeat_samples=self.heartbeat_samples,
                    last_heartbeat=self.last_heartbeat,
                    bus_cursor_advanced=self.bus_cursor_advanced,
                    bus_events_change=None if self.bus_events_initial is None or self.bus_events_final is None else self.bus_events_final-self.bus_events_initial,
                    scanner_emitted_change=None if self.emitted_initial is None or self.emitted_final is None else self.emitted_final-self.emitted_initial,
                    candidate_count=len(self.latest_inbox),
                    ingress_latency_ms=self.latencies_ms[-30:],
                    preatomic_candidates=[dict(x, token=x['token'][:12], producer=x['producer'][:12])
                                         for x in self.latest_inbox.values()][-12:],
                    fee_adjusted_profit_certified=False,
                    native_atomic_simulation_certified=False,
                    first_funded_canary_lamports=SIZE_LAMPORTS,
                    execution_authority=False, signing=False, broadcast=False)


class ExclusiveLock:
    def __enter__(self):
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        self.fd = open(LOCK, 'a+b')
        self.fd.seek(0)
        if self.fd.read(1) != b'1':
            self.fd.seek(0)
            self.fd.write(b'1')
            self.fd.flush()
        self.fd.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError):
            self.fd.close()
            raise RuntimeError('ORACLE356_ALREADY_RUNNING') from None
        return self

    def __exit__(self, *ignored):
        self.fd.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
        self.fd.close()


def preatomic_inbox(bridge):
    """Local read-only input contract for NEXT atomic-simulation module.

    No trade executable consumes this file in ORACLE-356. Atomic module must
    re-read fresh accounts, reprice, validate fees, and obtain separate authority.
    """
    return {'schema': 'ORACLE356_PREATOMIC_INBOX_V1', 'scanner_epoch': bridge.epoch,
            'producer': bridge.producer, 'expires_on_process_exit': True,
            'candidates': list(bridge.latest_inbox.values()), 'signing': False,
            'broadcast': False, 'execution_authority': False}


def _reader(pipe, output):
    """Bounded reader; the pipe is never a network subscription."""
    try:
        for line in pipe:
            try:
                output.put_nowait((time.perf_counter_ns(), line))
            except queue.Full:
                # We must not continue with potentially dropped bank updates.
                output.put(('OVERFLOW', ''))
                return
    finally:
        output.put(('EOF', ''))


def run_session(args, upstream_cmd=None, skip_audit=False,
                report_path=None, inbox_path=None, lock_required=True):
    """Exactly one ORACLE352 producer process. No wallet/RPC/WS client here."""
    if not skip_audit:
        audit()
    output_path = report_path if report_path is not None else REPORT
    inbox_file = inbox_path if inbox_path is not None else INBOX
    inbox_file.unlink(missing_ok=True)
    gate = Bridge(args.max_age_ms, args.max_slot_gap)
    cmd = upstream_cmd if upstream_cmd is not None else [
        sys.executable, '-u', str(ORACLE352_INSTALLER), '--run',
        '--seconds', str(args.seconds), '--pairs', str(args.pairs),
        '--array-cap', str(args.array_cap), '--ttl-ms', str(args.ttl_ms),
        '--probes', str(args.probes), '--controls', str(args.controls)]
    tag_prefix = 'ORACLE356_FIXTURE' if skip_audit else 'ORACLE356'
    print('[%s_START] ONE_ORACLE352_UPSTREAM CONTROLS=%d PROBES=%d '
          'NO_EXTRA_RPC_WS SIGNING_FALSE BROADCAST_FALSE' %
          (tag_prefix, args.controls, args.probes), flush=True)
    count_lines = 0
    returncode = None
    trace = []
    pipe_latency_ms = []
    traceback_seen = False
    safe_fault_markers = []
    child_eof = False
    lock = ExclusiveLock() if lock_required else None
    # In test fixtures no production lock is acquired; in production it is mandatory.
    from contextlib import nullcontext
    with lock if lock_required else nullcontext():
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, text=True, bufsize=1,
                              errors='replace') as proc:
            q = queue.Queue(maxsize=256)
            worker = threading.Thread(target=_reader, args=(proc.stdout, q), daemon=True)
            worker.start()
            deadline = time.monotonic() + args.seconds + 45
            try:
                while time.monotonic() < deadline:
                    try:
                        received_ns, line = q.get(timeout=.025)
                    except queue.Empty:
                        gate.expire()
                        if gate.inbox_dirty:
                            if gate.latest_inbox:
                                write_json(inbox_file, preatomic_inbox(gate))
                            else:
                                inbox_file.unlink(missing_ok=True)
                            gate.inbox_dirty = False
                        # Prevent a silent dead feed after a heartbeat; do not
                        # restart and compound RPC limits.
                        if (gate.last_heartbeat_at_ns is not None and
                            time.perf_counter_ns()-gate.last_heartbeat_at_ns > 20_000_000_000 and
                            proc.poll() is None):
                            gate.invalidate('SCANNER_HEARTBEAT_TIMEOUT')
                            break
                        if proc.poll() is not None and not worker.is_alive():
                            break
                        continue
                    if received_ns == 'EOF':
                        child_eof = True
                        break
                    if received_ns == 'OVERFLOW':
                        gate.invalidate('UPSTREAM_PIPE_BACKPRESSURE')
                        break
                    count_lines += 1
                    event = event_decode(line)
                    if event:
                        pipe_latency_ms.append(round(max(0, time.perf_counter_ns()-received_ns)/1e6,3))
                        pipe_latency_ms = pipe_latency_ms[-128:]
                        tag,row = event
                        item = gate.ingest(tag,row)
                        gate.expire()
                        if gate.inbox_dirty:
                            if gate.latest_inbox:
                                write_json(inbox_file, preatomic_inbox(gate))
                            else:
                                inbox_file.unlink(missing_ok=True)
                            gate.inbox_dirty = False
                        if tag == 'ORACLE352_READY':
                            print('[%s_SCANNER_BOUND]' % tag_prefix, json.dumps({
                                'epoch':gate.epoch,'cursor':gate.cursor,
                                'producer':(gate.producer or '')[:12]}), flush=True)
                        if item:
                            print('[%s_PREATOMIC]' % tag_prefix, json.dumps({
                                'event_id': str(item['event_id'])[:80],
                                'token':item['token'][:12],
                                'bank_slot':item['bank_slot'],
                                'gross_lamports':item['verified_bank_gross_lamports'],
                                'latency_ms':item['handoff_elapsed_ms'],
                                'signing':False,'broadcast':False}), flush=True)
                        if gate.failed:
                            break
                    else:
                        # Raw child text might contain secrets: never echo it or
                        # save it. Record only class/file/line from a traceback.
                        if 'Traceback (most recent call last)' in line:
                            traceback_seen = True
                        if (FRAME.search(line) or EXC.match(line.strip())):
                            trace.append(line.rstrip('\n')[:2000])
                            trace = trace[-30:]
                        # Explicitly fail closed on a new rate limit in stdout.
                        # This can be an RPC OR WS 429; never reconnect blindly.
                        if re.search(r'\b429\b',line) and re.search(r'(?i)\b(?:rpc|ws|websocket|rate.limit|http)\b',line):
                            safe_fault_markers.append('PROVIDER_429_LOG')
                            gate.invalidate('PROVIDER_429_STOP_NO_RESTART')
                            break
                else:
                    gate.invalidate('UPSTREAM_RUNTIME_DEADLINE')
            finally:
                if proc.poll() is None:
                    proc.terminate()
                try:
                    returncode = proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    returncode = proc.wait(timeout=8)
                worker.join(timeout=1)
    signature = traceback_signature(trace) if trace else None
    if returncode and not gate.failed:
        gate.bad_feed = 'UPSTREAM_EXIT_' + str(returncode)
    # The absence of a 352_EXIT record is not evidence of an orderly shutdown.
    # Use the actual subprocess returncode to report physical lifecycle.
    gate.expire()
    # Never leave a positive candidate or live-capable credential in memory or
    # on disk when its upstream producer exits. Only counts survive shutdown.
    gate.pending.clear()
    gate.latest.clear()
    gate.latest_inbox.clear()
    gate.inbox_deadlines.clear()
    inbox_file.unlink(missing_ok=True)
    out = gate.summary(returncode, count_lines, signature)
    if returncode and not out['status'].startswith('HOLD_'):
        out['status'] = 'HOLD_UPSTREAM_ABNORMAL_EXIT'
    out.update(pipe_delivery_ms=pipe_latency_ms[-30:],
               inbox_discarded_at_shutdown=True,
               traceback_observed=traceback_seen,
               upstream_fault_markers=safe_fault_markers[-4:],
               child_eof=child_eof,
               bridge_role='PRE_ATOMIC_ONLY_NOT_NATIVE_EXECUTOR')
    if signature:
        print('[%s_UPSTREAM_FAULT]' % tag_prefix,json.dumps(signature,sort_keys=True),flush=True)
    elif returncode:
        print('[%s_UPSTREAM_FAULT]' % tag_prefix,json.dumps({
            'exit_code':returncode,
            'oracle352_exit_reason':gate.upstream_exit_reason,
            'traceback_observed':traceback_seen,
            'classification':'NO_SAFE_TRACEBACK_CLASS_FOUND'}),flush=True)
    write_json(output_path,out)
    print('[%s_EXIT]' % tag_prefix,json.dumps(out,sort_keys=True),flush=True)
    print('[%s_REPORT]' % tag_prefix,str(output_path),flush=True)
    return 2 if out['status'].startswith('HOLD_') else 0


def run(args):
    return run_session(args)

def tests():
    class T(unittest.TestCase):
        def setUp(self):
            self.t = [10_000_000_000]
            self.b = Bridge(clock_ns=lambda: self.t[0])
            self.b.ready({'epoch': 1, 'producer': 'producer_12345678', 'cursor': 70})
            self.b.heartbeat({'epoch':1, 'bus_cursor':70, 'websocket_429_observed':0})
        def sub(self, eid='one', token='abcdefgh1234', **kw):
            x = dict(admitted=True, event_id=eid, token=token, direction='PUMP_TO_METEORA', age_ms=40)
            x.update(kw)
            return self.b.submit(x)
        def bank(self, eid='one', gross=100_000, **kw):
            x = dict(admitted=True, event_id=eid, token='abcdefgh1234567890',
                     direction='PUMP_TO_METEORA', source_age_at_bank_end_ms=100,
                     scanner_slot=100, bank_slot=101, bank_slot_gap=1,
                     single_context_verified=True, quote_model_result='SAME_BANK_MODEL_PARITY',
                     q18_same_bank_gross=gross, executor_same_bank_gross=gross,
                     account_fingerprint='a'*64, size_lamports=SIZE_LAMPORTS,
                     pump_pool='A'*44, meteora_pool='B'*44)
            x.update(kw)
            return self.b.parity(x)
        def test_01_valid_positive_boundary(self):
            self.sub(); r=self.bank(); self.assertEqual(r['status'], 'AWAIT_NATIVE_ATOMIC_SIMULATION')
            self.assertFalse(r['fee_adjusted_profit_certified'])
        def test_02_negative_rejected(self):
            self.sub(); self.assertIsNone(self.bank(gross=-1)); self.assertEqual(self.b.counts['negative_bank'],1)
        def test_03_no_telemetry(self):
            self.sub(admitted=False); self.assertIsNone(self.bank()); self.assertEqual(self.b.counts['preatomic'],0)
        def test_04_old_submission(self):
            self.sub(); self.t[0]+=1_600_000_000; self.assertIsNone(self.bank()); self.assertEqual(self.b.counts['stale'],1)
        def test_05_bank_source_age(self):
            self.sub(); self.assertIsNone(self.bank(source_age_at_bank_end_ms=1700))
        def test_06_slot_gap(self):
            self.sub(); self.assertIsNone(self.bank(bank_slot=103, bank_slot_gap=3))
        def test_07_snapshot_parity(self):
            self.sub(); self.assertIsNone(self.bank(q18_same_bank_gross=2))
        def test_08_fingerprint(self):
            self.sub(); self.assertIsNone(self.bank(account_fingerprint='wrong'))
        def test_09_exact_canary(self):
            self.sub(); self.assertIsNone(self.bank(size_lamports=9_000_000))
        def test_10_latest_wins(self):
            self.sub(); self.sub(eid='two'); self.assertIsNone(self.bank(eid='one'))
            self.assertIsNotNone(self.bank(eid='two'))
        def test_11_dedup(self):
            self.sub(); self.sub(); self.assertEqual(self.b.counts['duplicate'],1)
        def test_12_epoch_change(self):
            self.sub(); self.b.ready({'epoch':2,'producer':'producer_12345679','cursor':0})
            self.assertTrue(self.b.failed); self.assertIsNone(self.bank())
        def test_13_cursor_regression(self):
            self.b.heartbeat({'epoch':1,'bus_cursor':69,'websocket_429_observed':0})
            self.assertTrue(self.b.failed)
        def test_14_ws_429_increment(self):
            self.b.heartbeat({'epoch':1,'bus_cursor':71,'websocket_429_observed':1})
            self.assertTrue(self.b.failed)
        def test_15_ws_429_history(self):
            b=Bridge(); b.ready({'epoch':1,'producer':'producer_12345','cursor':0})
            b.heartbeat({'epoch':1,'bus_cursor':0,'websocket_429_observed':1})
            self.assertEqual(b.bad_feed,'WS_429_HISTORY_NOT_RECERTIFIED')
        def test_16_missing_event_id(self):
            self.sub(eid=None); self.assertEqual(self.b.counts['no_event_id'],1)
        def test_17_wrong_direction(self):
            self.sub(direction='UNKNOWN'); self.assertEqual(self.b.counts['identity'],1)
        def test_18_token_match(self):
            self.sub(); self.assertIsNone(self.bank(token='different1234567'))
        def test_19_decode(self):
            self.assertEqual(event_decode('[ORACLE352_READY] {"epoch":1}')[0], 'ORACLE352_READY')
            self.assertIsNone(event_decode('private_key=anything'))
        def test_20_traceback_secret_safe(self):
            z=traceback_signature(['  File "C:\\secret\\oracle_352.py", line 123, in xx',
                                    'ValueError: api-key=secrets'])
            self.assertNotIn('secrets', str(z)); self.assertEqual(z['exception_type'],'ValueError')
        def test_21_no_authority(self):
            self.sub(); row=self.bank(); self.assertFalse(row['execution_authority']); self.assertFalse(row['signing'])
        def test_22_bounded_seen(self):
            for i in range(2100): self.sub(eid=str(i), token='abcdefgh1234')
            self.assertLessEqual(len(self.b.seen),2048)
        def test_23_atomic_inbox_contract(self):
            self.sub(); self.bank(); r=preatomic_inbox(self.b)
            self.assertFalse(r['execution_authority']); self.assertEqual(len(r['candidates']),1)
        def test_24_no_future_replay(self):
            self.sub(); self.bank(); self.b.invalidate('EPOCH_CHANGED')
            self.assertFalse(self.b.latest_inbox)
        def test_25_missing_slot(self):
            self.sub(); self.assertIsNone(self.bank(scanner_slot=None))
        def test_27_newer_negative_invalidates_old_positive(self):
            self.sub(); self.bank(); self.assertEqual(len(self.b.latest_inbox),1)
            self.sub(eid='new'); self.assertFalse(self.b.latest_inbox)
            self.assertIsNone(self.bank(eid='new',gross=-100))
            self.assertFalse(self.b.latest_inbox)
        def test_29_missing_pool_rejected(self):
            self.sub(); self.assertIsNone(self.bank(pump_pool=None))
        def test_28_expired_presim_not_replayable(self):
            self.sub(); self.bank(); self.t[0]+=1_500_000_000
            self.b.expire(); self.assertFalse(self.b.latest_inbox)
        def test_30_heartbeat_counters(self):
            self.b.heartbeat({'epoch':1,'bus_cursor':71,'websocket_429_observed':0,
                              'scanner_emitted':9,'scanner_admitted':10})
            self.b.heartbeat({'epoch':1,'bus_cursor':71,'websocket_429_observed':0,
                              'scanner_emitted':10,'scanner_admitted':11})
            self.assertEqual(self.b.emitted_final-self.b.emitted_initial,1)
            self.assertTrue(self.b.bus_cursor_advanced)
        def test_31_exit_reason_recorded(self):
            self.b.ingest('ORACLE352_EXIT',{'reason':'UPSTREAM_FAILED'})
            self.assertEqual(self.b.upstream_exit_reason,'UPSTREAM_FAILED')
        def test_32_exit_reason_untrusted(self):
            self.b.ingest('ORACLE352_EXIT',{'reason':'credential=VERY_SECRET'})
            self.assertEqual(self.b.upstream_exit_reason,'UNCLASSIFIED_EXIT_REASON')
        def test_33_heartbeat_timeout_origin(self):
            self.assertEqual(self.b.heartbeat_samples,1)
            self.assertEqual(self.b.last_heartbeat_at_ns,self.t[0])
        def test_34_nonzero_returncode_cannot_pass(self):
            self.sub(); self.bank();
            result=self.b.summary(child_code=1)
            self.assertEqual(result['status'],'HOLD_UPSTREAM_ABNORMAL_EXIT')
        def test_26_strict_identity(self):
            self.sub(); self.assertIsNone(self.bank(direction='METEORA_TO_PUMP'))
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE356_TEST]', json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun}))
    return 0 if result.wasSuccessful() else 1



def integration_tests():
    """End-to-end child/pipe/bridge contract with NO RPC or trading."""
    import tempfile
    from types import SimpleNamespace
    args=SimpleNamespace(seconds=2,pairs=1,array_cap=1,ttl_ms=2500,
                         probes=3,controls=1,max_age_ms=1500,max_slot_gap=2)
    # Only deterministic fake payload; neither the installed runtime nor
    # native signer executes in the fixture.
    base={'epoch':3,'cursor':90,'producer':'fixtureproducer123456789'}
    submit={'event_id':'fixture01','admitted':True,'token':'abcdefgh1234',
            'direction':'PUMP_TO_METEORA','age_ms':10}
    bank={'event_id':'fixture01','admitted':True,'token':'abcdefgh123456789',
          'direction':'PUMP_TO_METEORA','source_age_at_bank_end_ms':30,
          'scanner_slot':100,'bank_slot':101,'bank_slot_gap':1,
          'single_context_verified':True,'quote_model_result':'SAME_BANK_MODEL_PARITY',
          'q18_same_bank_gross':1200,'executor_same_bank_gross':1200,
          'account_fingerprint':'a'*64,'size_lamports':SIZE_LAMPORTS,
          'pump_pool':'A'*44,'meteora_pool':'B'*44}
    hb={'epoch':3,'bus_cursor':90,'websocket_429_observed':0}
    program=('import sys,json\n'
             'rows='+repr([('ORACLE352_READY',base),('ORACLE352_HEARTBEAT',hb),
                          ('ORACLE352_BANK_SUBMIT',submit),('ORACLE352_BANK_PARITY',bank)])+'\n'
             'for tag,row in rows: print("["+tag+"] "+json.dumps(row),flush=True)\n'
             'sys.exit(1)\n')
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        cmd=[sys.executable,'-u','-c',program]
        status=run_session(args,upstream_cmd=cmd,skip_audit=True,
                           report_path=root/'result.json',inbox_path=root/'inbox.json',
                           lock_required=False)
        report=json.loads((root/'result.json').read_text())
        assert status==2 and report['counts']['preatomic']==1,report
        assert report['status']=='HOLD_UPSTREAM_EXIT_1',report
        assert report['inbox_discarded_at_shutdown'] and not (root/'inbox.json').exists(),report
        assert report['candidate_count']==0 and not report['preatomic_candidates'],report
        traceback_program=('import sys\n' +
            'print('+repr('[ORACLE352_READY] '+json.dumps(base))+',flush=True)\n' +
            'print('+repr('Traceback (most recent call last):')+',flush=True)\n' +
            'print('+repr('  File "oracle_352_scanner_bank_alignment.py", line 404, in run')+',flush=True)\n' +
            'print('+repr('RuntimeError: api-key=SENSITIVE')+',flush=True)\n' +
            'sys.exit(1)\n')
        status=run_session(args,upstream_cmd=[sys.executable,'-u','-c',traceback_program],
                           skip_audit=True,report_path=root/'fail.json',
                           inbox_path=root/'fail_inbox.json',lock_required=False)
        failure=json.loads((root/'fail.json').read_text())
        assert status==2 and failure['upstream_exit_code']==1,failure
        assert failure['upstream_failure_signature']['exception_type']=='RuntimeError',failure
        assert 'SENSITIVE' not in (root/'fail.json').read_text(),failure
        assert failure['upstream_failure_signature']['frames'][-1]['line']==404,failure
    print('[ORACLE356_FIXTURE_PASS] 2 END_TO_END_PRODUCER_CASES NO_RPC NO_WS NO_REPLAY')

def main():
    p = argparse.ArgumentParser(description='ORACLE-356 full scanner-to-preatomic bridge with abnormal-exit and heartbeat gating')
    mode = p.add_mutually_exclusive_group(required=True)
    for m in ('install','test','audit','run'):
        mode.add_argument('--'+m,action='store_true')
    p.add_argument('--seconds',type=int,default=90)
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--array-cap',type=int,default=60)
    p.add_argument('--ttl-ms',type=int,default=2500)
    p.add_argument('--max-age-ms',type=int,default=1500)
    p.add_argument('--max-slot-gap',type=int,default=2)
    # 352 succeeded with 3/12; 0/0 failed. Never use unverified zero option.
    p.add_argument('--controls',type=int,default=3)
    p.add_argument('--probes',type=int,default=12)
    args = p.parse_args()
    if args.install: install(); return 0
    if args.test:
        r=tests()
        if r == 0: integration_tests()
        return r
    if args.audit: audit(); return 0
    if not (5<=args.seconds<=3600 and 1<=args.pairs<=100 and
            1<=args.array_cap<=100 and 100<=args.ttl_ms<=10000 and
            100<=args.max_age_ms<=2500 and 0<=args.max_slot_gap<=5 and
            1<=args.controls<=3 and 1<=args.probes<=12):
        p.error('invalid or unsupported runtime limits')
    return run(args)


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        # No exception messages: they might contain transport credentials.
        print('[ORACLE356_HOLD]', type(exc).__name__, flush=True)
        sys.exit(2)
