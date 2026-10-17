"""ORACLE-368: consolidated pre-atomic certification coordinator.

Complete replacement installer for Windows CMD / venv / python.
Scanner 322/351/352/360/363/364/365 remain unchanged.
Uses ORACLE-365 canonical SQLite event intake; single read-only local reader.
An optional native provider must expose prepare_unsigned(candidate)->dict.
Native provider should use verified local Meteora/PumpSwap builders, not start WS.
No private-key access, signing, sendTransaction, or real-money authority.

Certification stages:
  1 scanner health, producer/epoch and read-only intake
  2 freshness + latest-only exact-size nomination (10M..100M lamports)
  3 same-bank Q18/executor quote agreement, account readiness
  4 unsigned native v0 atomic packet and on-chain simulation (sigVerify=False)
  5 confirmed RPC fee and *estimated* net profitability check
A passing unsigned simulation is NOT realized profit or permission to trade.
"""
from __future__ import annotations

import argparse
import base64
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
import urllib.error
import urllib.request

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_368_source_boundary_repair.py')
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_368_atomic_certification_report.json')
INBOX = Path('runtime_state/oracle/final_boss_dual/oracle_368_preatomic_inbox.json')
CANARY = 10_000_000
MAX_TX_BYTES = 1232
MAX_RPC_CALLS = 8
MAX_SIM_SLOT_GAP = 2
MAX_CANDIDATE_AGE_MS = 1500
DEFAULT_PROVIDER = PKG + '.oracle_366_native_atomic_provider'
PUBKEY = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
HEX_64 = re.compile(r'^[0-9a-f]{64}$')


def installed():
    source = Path(__file__).resolve()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if source != TARGET.resolve():
        tmp = TARGET.with_name(TARGET.name + '.stage')
        tmp.write_bytes(source.read_bytes())
        compile(tmp.read_text(encoding='utf-8'), str(TARGET), 'exec')
        os.replace(tmp, TARGET)
    py_compile.compile(str(TARGET), doraise=True)
    if TARGET.read_bytes() != source.read_bytes():
        raise RuntimeError('INSTALLED_BYTES_DIFFER')
    print('[ORACLE366_INSTALL_PASS]', TARGET, 'sha256=' + hashlib.sha256(TARGET.read_bytes()).hexdigest(), flush=True)


def upstream():
    return importlib.import_module(PKG + '.oracle_365_sqlite_columnar_event_handoff')


def audit(require_installed=True):
    upstream().audit()  # ORACLE-322 freeze + ORACLE-352 source SHA + ORACLE-360 guard.
    if require_installed:
        if not TARGET.is_file() or TARGET.read_bytes() != Path(__file__).resolve().read_bytes():
            raise RuntimeError('ORACLE368_INSTALL_INTEGRITY_FAILURE')
        py_compile.compile(str(TARGET), doraise=True)
    print('[ORACLE366_AUDIT_PASS] FROZEN322 CERTIFIED352 GUARDED351 365_CANONICAL_BUS '
          'NO_EXTRA_WS ZERO_SIGNING ZERO_BROADCAST', flush=True)


def strict_positive(value):
    return type(value) is int and value > 0


def strict_nonnegative(value):
    return type(value) is int and value >= 0


def valid_pubkey(value):
    return isinstance(value, str) and bool(PUBKEY.fullmatch(value))


def valid_b64(value, min_bytes=1, max_bytes=1232):
    if not isinstance(value, str) or len(value) > max_bytes * 2:
        return None
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError):
        return None
    return raw if min_bytes <= len(raw) <= max_bytes else None



def unsigned_v0_witness(transaction_bytes, message_bytes):
    """Wire-level check: shortvec signatures, ALL ZERO, versioned v0 message."""
    if not transaction_bytes or not message_bytes:
        return False
    value = 0
    shift = 0
    cursor = 0
    for _ in range(3):
        if cursor >= len(transaction_bytes):
            return False
        byte = transaction_bytes[cursor]
        cursor += 1
        value |= (byte & 127) << shift
        if not byte & 128:
            break
        shift += 7
    else:
        return False
    if not 1 <= value <= 16:
        return False
    end = cursor + value * 64
    if end >= len(transaction_bytes):
        return False
    if any(transaction_bytes[cursor:end]):
        return False
    raw_message = transaction_bytes[end:]
    return (raw_message == message_bytes and len(raw_message) >= 4
            and raw_message[0] == 0x80)

def stage1_nomination(candidate, now_ns=None):
    """Proof-of-source checks; candidate is still NOT a trade instruction."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if not isinstance(candidate, dict) or candidate.get('schema') != 'ORACLE363_ATOMIC_REPRICE_REQUEST_V1':
        return 'UNVERIFIED_INGRESS_SCHEMA'
    if any(candidate.get(k) is not False for k in
           ('execution_authority', 'signing', 'broadcast', 'native_atomic_simulation_certified')):
        return 'INGRESS_AUTHORITY_ESCALATION'
    if not all(strict_positive(candidate.get(k)) for k in
               ('event_id', 'scanner_epoch', 'scanner_slot', 'size_lamports')):
        return 'UNVERIFIED_SCANNER_IDENTITY'
    if not (10_000_000 <= candidate['size_lamports'] <= 100_000_000):
        return 'TRADE_SIZE_OUTSIDE_SCANNER_RANGE'
    if candidate.get('direction') not in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP'):
        return 'INVALID_SWAP_DIRECTION'
    if any(not valid_pubkey(candidate.get(k)) for k in ('token', 'pump_pool', 'meteora_pool')):
        return 'INVALID_PAIR_KEYS'
    if not isinstance(candidate.get('scanner_producer'), str) or len(candidate['scanner_producer']) < 8:
        return 'MISSING_SCANNER_PRODUCER'
    expires = candidate.get('expires_at_unix_ms')
    if not strict_positive(expires) or expires * 1_000_000 <= now_ns:
        return 'CANDIDATE_EXPIRED'
    age = candidate.get('source_age_at_ingress_ms')
    if type(age) not in (int, float) or not 0 <= age <= MAX_CANDIDATE_AGE_MS:
        return 'CANDIDATE_AGE_UNCERTIFIED'
    return None


def bank_native_gate(candidate, proof, now_ns=None):
    """Require actual same-bank economics and unsigned native transaction structure."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    issue = stage1_nomination(candidate, now_ns)
    if issue:
        return issue
    if not isinstance(proof, dict):
        return 'NATIVE_PROOF_MISSING'
    for k, source in (('event_id', 'event_id'), ('token', 'token'),
                      ('direction', 'direction'), ('size_lamports', 'size_lamports'),
                      ('pump_pool', 'pump_pool'), ('meteora_pool', 'meteora_pool')):
        if proof.get(k) != candidate.get(source):
            return 'NATIVE_PROOF_IDENTITY_MISMATCH'
    if not strict_positive(proof.get('bank_slot')) or not (
            candidate['scanner_slot'] <= proof['bank_slot'] <= candidate['scanner_slot'] + MAX_SIM_SLOT_GAP):
        return 'BANK_SLOT_MISSING_OR_UNFRESH'
    if not (isinstance(proof.get('bank_fingerprint'), str)
            and HEX_64.fullmatch(proof['bank_fingerprint'])):
        return 'BANK_FINGERPRINT_UNVERIFIED'
    if not strict_positive(proof.get('bank_account_count')):
        return 'BANK_ACCOUNTS_UNVERIFIED'
    if not strict_positive(proof.get('bank_timestamp_ns')):
        return 'BANK_TIME_UNVERIFIED'
    age_ms = (now_ns - proof['bank_timestamp_ns']) / 1_000_000
    if not 0 <= age_ms <= 850:
        return 'BANK_SNAPSHOT_STALE'
    scan = proof.get('q18_same_bank_gross_lamports')
    execution = proof.get('executor_same_bank_gross_lamports')
    if type(scan) is not int or type(execution) is not int or scan != execution or execution <= 0:
        return 'SAME_BANK_PARITY_OR_GROSS_FAILED'
    if proof.get('single_bank_context_verified') is not True:
        return 'ACCOUNT_CONTEXT_UNCERTIFIED'
    if proof.get('token_accounts_ready') is not True or proof.get('wsol_ready') is not True:
        return 'TOKEN_ACCOUNT_OR_WSOL_UNREADY'
    if proof.get('native_unsigned') is not True or proof.get('signing') is not False or proof.get('broadcast') is not False:
        return 'NATIVE_UNSIGNED_ONLY_REQUIRED'
    if proof.get('version') != 0 or proof.get('alt_resolved') is not True:
        return 'NATIVE_V0_ALT_NOT_READY'
    expected_legs = (['PUMP_BUY', 'DLMM_SELL'] if candidate['direction'] == 'PUMP_TO_METEORA'
                     else ['DLMM_BUY', 'PUMP_SELL'])
    if proof.get('legs') != expected_legs or proof.get('atomic_single_transaction') is not True:
        return 'TWO_LEG_ATOMIC_PROOF_MISSING'
    raw = valid_b64(proof.get('unsigned_transaction_b64'))
    message = valid_b64(proof.get('message_b64'))
    if raw is None or message is None:
        return 'NATIVE_MESSAGE_INVALID'
    if not strict_positive(proof.get('serialized_bytes')) or proof['serialized_bytes'] != len(raw):
        return 'NATIVE_BYTES_MISMATCH'
    if len(raw) > MAX_TX_BYTES:
        return 'NATIVE_PACKET_TOO_LARGE'
    if not unsigned_v0_witness(raw, message):
        return 'UNSIGNED_V0_WIRE_FORMAT_UNVERIFIED'
    for k in ('transfer_fee_lamports','rent_cost_lamports','tip_lamports','residue_lamports','adverse_buffer_lamports'):
        if not strict_nonnegative(proof.get(k)):
            return 'MISSING_COST_BOUND_' + k.upper()
    return None


class RateLimited(Exception):
    pass


class RpcReadOnly:
    """Bounded two-RPC witness only after native identity and size gates pass."""
    def __init__(self, url, budget=MAX_RPC_CALLS, transport=None):
        self.url = url
        self.budget = budget
        self.calls = 0
        self.transport = transport or self._transport
        self.stopped = False

    def _transport(self, method, params):
        body = json.dumps({'jsonrpc':'2.0', 'id':1, 'method':method, 'params':params}).encode()
        req = urllib.request.Request(self.url, body, {'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            if resp.status == 429:
                raise RateLimited()
            return json.loads(resp.read(2_000_000).decode('utf-8'))

    def rpc(self, method, params):
        if method not in ('simulateTransaction','getFeeForMessage'):
            raise ValueError('RPC_METHOD_NOT_ALLOWED')
        if self.stopped or self.calls >= self.budget:
            raise RateLimited('RPC_BUDGET_OR_STOP')
        if not isinstance(self.url, str) or not self.url.startswith('https://'):
            raise RuntimeError('HTTPS_RPC_MISSING')
        self.calls += 1
        try:
            data = self.transport(method, params)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                self.stopped = True
                raise RateLimited() from None
            raise RuntimeError('RPC_HTTP_ERROR_' + str(exc.code)) from None
        except RateLimited:
            self.stopped = True
            raise
        except (OSError, ValueError, TimeoutError):
            raise RuntimeError('RPC_TRANSPORT_FAILED') from None
        if not isinstance(data, dict):
            raise RuntimeError('RPC_MALFORMED_RESPONSE')
        if data.get('error'):
            # No response body/URL exposure, because it can include credentials.
            raise RuntimeError('RPC_RETURNED_ERROR')
        return data.get('result')


def simulation_gate(candidate, proof, rpc, now_ns=None):
    now_ns = time.time_ns() if now_ns is None else now_ns
    issue = bank_native_gate(candidate, proof, now_ns)
    if issue:
        return {'stage':'HOLD', 'reason':issue}
    try:
        fee_result = rpc.rpc('getFeeForMessage', [proof['message_b64'],
                          {'commitment':'processed', 'minContextSlot':proof['bank_slot']}])
        fee_slot = fee_result['context']['slot']
        fee = fee_result['value']
        if not strict_positive(fee_slot) or fee_slot < proof['bank_slot'] or not strict_positive(fee):
            return {'stage':'HOLD', 'reason':'RPC_TRANSACTION_FEE_UNVERIFIED'}
        sim_result = rpc.rpc('simulateTransaction', [proof['unsigned_transaction_b64'],
                          {'encoding':'base64', 'sigVerify':False, 'replaceRecentBlockhash':False,
                           'commitment':'processed', 'minContextSlot':proof['bank_slot']}])
        sim_slot = sim_result['context']['slot']
        value = sim_result['value']
        if not strict_positive(sim_slot) or sim_slot < proof['bank_slot'] or not isinstance(value,dict):
            return {'stage':'HOLD','reason':'SIMULATION_CONTEXT_UNVERIFIED'}
        if value.get('err') is not None:
            return {'stage':'HOLD','reason':'NATIVE_ATOMIC_SIMULATION_FAILED'}
        if not strict_positive(value.get('unitsConsumed')):
            return {'stage':'HOLD','reason':'SIMULATION_COMPUTE_UNVERIFIED'}
        extra = sum(proof[k] for k in ('transfer_fee_lamports','rent_cost_lamports',
                   'tip_lamports','residue_lamports','adverse_buffer_lamports'))
        projected = proof['executor_same_bank_gross_lamports'] - fee - extra
        if projected <= 0:
            return {'stage':'HOLD', 'reason':'FEE_ADJUSTED_PROFIT_NONPOSITIVE',
                    'projected_net_lamports':projected}
        if stage1_nomination(candidate, time.time_ns()) is not None:
            return {'stage':'HOLD','reason':'CANDIDATE_EXPIRED_POST_SIMULATION'}
        return {'stage':'UNSIGNED_SIM_NET_ESTIMATE_PASS',
                'reason':'NATIVE_SIM_SUCCEEDED_PROFIT_IS_ESTIMATE_NOT_REALIZED',
                'event_id':candidate['event_id'], 'token_prefix':candidate['token'][:12],
                'direction':candidate['direction'], 'size_lamports':candidate['size_lamports'],
                'bank_slot':proof['bank_slot'], 'fee_context_slot':fee_slot,
                'sim_context_slot':sim_slot, 'packet_bytes':proof['serialized_bytes'],
                'compute_units':value['unitsConsumed'], 'chain_fee_lamports':fee,
                'projected_net_lamports':projected, 'gross_bank_lamports':proof['executor_same_bank_gross_lamports'],
                'realized_profit_certified':False, 'execution_authority':False,
                'signing':False, 'broadcast':False,
                'first_funded_canary_lamports':CANARY}
    except RateLimited:
        rpc.stopped = True
        return {'stage':'HOLD', 'reason':'RPC_429_STOP_NO_RETRY'}
    except (TypeError, KeyError, AttributeError, IndexError, ValueError, RuntimeError):
        return {'stage':'HOLD', 'reason':'RPC_SIMULATION_OR_FEE_WITNESS_INVALID'}


class LatestWorker:
    def __init__(self, provider=None, rpc=None, clock_ns=time.time_ns):
        self.provider = provider
        self.rpc = rpc
        self.clock_ns = clock_ns
        self.cv = threading.Condition()
        self.latest = {}
        self.generations = {}
        self.stop = False
        self.invalidated = False
        self.counts = Counter()
        self.results = []
        self.thread = None

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self.loop, name='oracle366-latest-atomic', daemon=True)
            self.thread.start()

    def submit(self, row):
        with self.cv:
            token = row['token']
            if token in self.latest:
                self.counts['replaced'] += 1
            self.generations[token] = self.generations.get(token,0) + 1
            self.latest[token] = (dict(row), self.generations[token])
            self.counts['submitted'] += 1
            self.cv.notify()

    def newer_or_invalid(self, token, generation):
        with self.cv:
            return self.invalidated or self.generations.get(token) != generation

    def loop(self):
        while True:
            with self.cv:
                while not self.latest and not self.stop:
                    self.cv.wait(.2)
                if self.stop:
                    return
                token, item = self.latest.popitem()
            row, generation = item
            result = {'stage':'HOLD', 'reason':'NATIVE_ATOMIC_PROVIDER_NOT_CERTIFIED'}
            if stage1_nomination(row, self.clock_ns()) is not None:
                result = {'stage':'HOLD','reason':'CANDIDATE_UNVERIFIED_OR_STALE'}
            elif self.provider is not None and self.rpc is not None:
                try:
                    proof = self.provider.prepare_unsigned(dict(row))
                    if self.newer_or_invalid(token,generation):
                        result = {'stage':'HOLD','reason':'SUPERSEDED_BEFORE_SIMULATION'}
                    else:
                        result = simulation_gate(row, proof, self.rpc, self.clock_ns())
                except Exception:
                    result = {'stage':'HOLD','reason':'NATIVE_PROVIDER_FAILED'}
            if self.newer_or_invalid(token,generation):
                result = {'stage':'HOLD','reason':'SUPERSEDED_OR_SCANNER_UNHEALTHY'}
            with self.cv:
                self.results.append(result)
                self.results = self.results[-80:]
                self.counts[result['reason']] += 1
            print('[ORACLE366_GATE]',json.dumps({k:v for k,v in result.items()
                  if k in ('stage','reason','event_id','token_prefix','projected_net_lamports')}),flush=True)

    def reconcile(self, active_candidates):
        """Negative or expired newer nomination invalidates even in-flight quotes."""
        with self.cv:
            active = set(active_candidates)
            for token in list(self.generations):
                if token not in active:
                    self.generations[token] += 1
                    self.latest.pop(token, None)
                    self.counts['source_invalidations'] += 1
                    del self.generations[token]
            self.cv.notify_all()

    def close(self):
        with self.cv:
            self.stop = True
            self.invalidated = True
            self.latest.clear()
            self.cv.notify_all()
        if self.thread:
            self.thread.join(timeout=7)


def get_provider(module_name):
    if not module_name:
        return None
    if not re.fullmatch(r'qseries_v2\.oracle_execution\.solana_atomic_executor\.[A-Za-z_][A-Za-z0-9_]*',module_name):
        raise RuntimeError('NATIVE_PROVIDER_OUTSIDE_EXECUTOR_PACKAGE')
    module = importlib.import_module(module_name)
    if not callable(getattr(module,'prepare_unsigned',None)):
        raise RuntimeError('NATIVE_PROVIDER_MISSING_PREPARE_UNSIGNED')
    if getattr(module,'EXECUTION_AUTHORITY',True) is not False or getattr(module,'BROADCAST',True) is not False:
        raise RuntimeError('NATIVE_PROVIDER_NO_EXECUTION_FIREWALL')
    return module


def live(seconds=180, poll_ms=5, ttl_ms=2500, max_age_ms=1500, provider_module=None,
         report=REPORT, inbox=INBOX, scanner=None, preaudited=False, with_lock=True,
         provider=None, rpc=None):
    if not (1 <= seconds <= 1800 and 5 <= poll_ms <= 100):
        raise ValueError('INVALID_RUNTIME_BOUND')
    if not preaudited:
        audit()
    core = upstream()
    base = core.core()
    if scanner is None:
        # ORACLE-365.core() => ORACLE-364; ORACLE-364._base() => ORACLE-363.
        # The verified resolver lives on ORACLE-363, not ORACLE-365.
        source_module = base._base()
        scanner = source_module.resolve_scanner_bus()
    if not all(callable(getattr(scanner, n, None)) for n in ('bus','new_events','validate_scanner')):
        raise RuntimeError('SCANNER_BUS_CONTRACT_UNAVAILABLE')
    if provider is None:
        provider = get_provider(provider_module)
    if rpc is None and provider is not None:
        rpc = RpcReadOnly(os.environ.get('SOLANA_RPC_URL',''))
    worker = LatestWorker(provider, rpc)
    gate = base._base().LocalIngress(ttl_ms=ttl_ms,max_age_ms=max_age_ms,callback=worker.submit)
    counters = Counter()
    conn = None
    lock = nullcontext()
    if with_lock:
        lock = importlib.import_module(PKG + '.oracle_359_lock_safe_handoff').ExclusiveLock()
    inbox.unlink(missing_ok=True)
    worker.start()
    try:
        with lock:
            conn = scanner.bus()
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            hb = scanner.validate_scanner(conn)
            initial_cursor = int(conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            gate.attach(hb,initial_cursor)
            print('[ORACLE366_SCANNER_BOUND]',json.dumps({'epoch':gate.epoch,'cursor':gate.cursor,
                  'producer_prefix':gate.producer[:12],'provider_bound':provider is not None,
                  'read_only_sqlite':True,'new_ws':False,'signing':False,'broadcast':False}),flush=True)
            deadline = time.monotonic() + seconds
            check_at = time.monotonic()+.25
            while time.monotonic() < deadline and not gate.failed:
                if rpc is not None and rpc.stopped:
                    gate.fail('RPC_RATE_LIMIT_REQUIRES_REVALIDATION')
                    break
                if time.monotonic() >= check_at:
                    gate.health(scanner.validate_scanner(conn))
                    check_at = time.monotonic()+.25
                    if gate.failed:
                        break
                core.consume(scanner,conn,gate,counters,inbox)
                worker.reconcile(gate.latest)
                time.sleep(poll_ms/1000)
    except Exception as exc:
        # Source-level classification: do not print exception messages, URLs, environment or keys.
        # Preserve lock, integrity, and source-health failures; never auto-retry or bypass.
        import traceback
        frame_rows = traceback.extract_tb(exc.__traceback__)[-5:]
        safe_frames = [{'file':Path(f.filename).name[:90], 'line':f.lineno,
                        'function':f.name[:80]} for f in frame_rows]
        # Only stable all-capital codes can be emitted, not arbitrary exception content.
        raw_code = str(exc)
        safe_code = raw_code if re.fullmatch(r'[A-Z][A-Z0-9_]{2,90}', raw_code) else 'MESSAGE_REDACTED'
        print('[ORACLE368_SOURCE_FAILURE]', json.dumps({
            'type':type(exc).__name__, 'code':safe_code, 'frames':safe_frames,
            'lock_bypassed':False, 'signing':False, 'broadcast':False}), flush=True)
        gate.fail('SOURCE_LOCK_OR_SCHEMA_' + type(exc).__name__)
    finally:
        worker.close()
        if conn is not None:
            try:conn.close()
            except Exception:pass
        gate.latest.clear()
        gate.deadlines.clear()
        inbox.unlink(missing_ok=True)
        result = gate.report()
        result.update({'pipeline':'ORACLE368_SCANNER_TO_UNSIGNED_NATIVE_GATE',
                       'status': 'HOLD_' + gate.failure if gate.failed else
                       'NATIVE_SIM_NET_ESTIMATE_OBSERVED' if any(r['stage']=='UNSIGNED_SIM_NET_ESTIMATE_PASS'
                       for r in worker.results) else
                       'SCANNER_CANDIDATES_NO_NATIVE_CERTIFICATION' if gate.ever_staged else
                       'SCANNER_BOUND_NO_QUALIFIED_CANDIDATES',
                       'event_contract':dict(counters),'native_gate_counts':dict(worker.counts),
                       'native_gate_results':worker.results[-12:],
                       'provider_bound':provider is not None,
                       'rpc_calls':rpc.calls if rpc else 0,
                       'private_key_used':False,'first_funded_canary_lamports':CANARY,
                       'native_atomic_broadcast_certified':False,
                       'realized_profit_certified':False,
                       'execution_authority':False,'signing':False,'broadcast':False})
        report.parent.mkdir(parents=True,exist_ok=True)
        tmp = report.with_name(report.name+'.stage')
        tmp.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
        os.replace(tmp,report)
        print('[ORACLE366_EXIT]',json.dumps({k:v for k,v in result.items()
              if k in ('status','event_contract','native_gate_counts','rpc_calls','execution_authority','signing','broadcast')},sort_keys=True),flush=True)
        print('[ORACLE366_REPORT]',report,flush=True)
    return 2 if gate.failed else 0


def tests():
    now = time.time_ns()
    seed = {'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1','event_id':9,'scanner_epoch':3,
            'scanner_producer':'fixture_producer_123','scanner_slot':200,'size_lamports':CANARY,
            'token':'A'*43,'pump_pool':'B'*43,'meteora_pool':'C'*43,
            'direction':'PUMP_TO_METEORA','source_age_at_ingress_ms':5.0,
            'expires_at_unix_ms':(now//1_000_000)+500,
            'execution_authority':False,'signing':False,'broadcast':False,
            'native_atomic_simulation_certified':False}
    msg = bytes([0x80]) + b'MESSAGE_BODY_FOR_FIXTURE'
    packet = bytes([1]) + bytes(64) + msg
    witness = {'event_id':9,'token':'A'*43,'pump_pool':'B'*43,'meteora_pool':'C'*43,
               'direction':'PUMP_TO_METEORA','size_lamports':CANARY,
               'bank_slot':201, 'bank_account_count':4,'bank_timestamp_ns':now,
               'bank_fingerprint':'b'*64,
               'q18_same_bank_gross_lamports':90000,'executor_same_bank_gross_lamports':90000,
               'single_bank_context_verified':True,'token_accounts_ready':True,'wsol_ready':True,
               'native_unsigned':True,'signing':False,'broadcast':False,'version':0,
               'alt_resolved':True,'legs':['PUMP_BUY','DLMM_SELL'],'atomic_single_transaction':True,
               'unsigned_transaction_b64':base64.b64encode(packet).decode(),
               'message_b64':base64.b64encode(msg).decode(), 'serialized_bytes':len(packet),
               'transfer_fee_lamports':0,'rent_cost_lamports':0,'tip_lamports':0,
               'residue_lamports':0,'adverse_buffer_lamports':2000}
    def tr(method, params):
        if method=='getFeeForMessage':return {'result':{'context':{'slot':201},'value':5000}}
        return {'result':{'context':{'slot':201},'value':{'err':None,'unitsConsumed':250000}}}
    class Tests(unittest.TestCase):
        def test_candidate(self):self.assertIsNone(stage1_nomination(seed,now))
        def test_expiry(self):self.assertEqual(stage1_nomination(dict(seed,expires_at_unix_ms=1),now),'CANDIDATE_EXPIRED')
        def test_size(self):self.assertEqual(stage1_nomination(dict(seed,size_lamports=100_000_001),now),'TRADE_SIZE_OUTSIDE_SCANNER_RANGE')
        def test_authority(self):self.assertEqual(stage1_nomination(dict(seed,signing=True),now),'INGRESS_AUTHORITY_ESCALATION')
        def test_key(self):self.assertEqual(stage1_nomination(dict(seed,token='BAD'),now),'INVALID_PAIR_KEYS')
        def test_slot(self):self.assertEqual(bank_native_gate(seed,dict(witness,bank_slot=250),now),'BANK_SLOT_MISSING_OR_UNFRESH')
        def test_parity(self):self.assertEqual(bank_native_gate(seed,dict(witness,executor_same_bank_gross_lamports=500),now),'SAME_BANK_PARITY_OR_GROSS_FAILED')
        def test_negative(self):self.assertEqual(bank_native_gate(seed,dict(witness,executor_same_bank_gross_lamports=-1,q18_same_bank_gross_lamports=-1),now),'SAME_BANK_PARITY_OR_GROSS_FAILED')
        def test_accounts(self):self.assertEqual(bank_native_gate(seed,dict(witness,token_accounts_ready=False),now),'TOKEN_ACCOUNT_OR_WSOL_UNREADY')
        def test_bytes(self):self.assertEqual(bank_native_gate(seed,dict(witness,serialized_bytes=100),now),'NATIVE_BYTES_MISMATCH')
        def test_legs(self):self.assertEqual(bank_native_gate(seed,dict(witness,legs=['DLMM_BUY','PUMP_SELL']),now),'TWO_LEG_ATOMIC_PROOF_MISSING')
        def test_version(self):self.assertEqual(bank_native_gate(seed,dict(witness,version=1),now),'NATIVE_V0_ALT_NOT_READY')
        def test_cost_missing(self):self.assertEqual(bank_native_gate(seed,dict(witness,residue_lamports=None),now),'MISSING_COST_BOUND_RESIDUE_LAMPORTS')
        def test_bank_valid(self):self.assertIsNone(bank_native_gate(seed,witness,now))
        def test_rpc_methods(self):
            with self.assertRaises(ValueError):RpcReadOnly('https://fake',transport=tr).rpc('sendTransaction',[])
        def test_fee_net_pass_fixture(self):
            result=simulation_gate(seed,witness,RpcReadOnly('https://fixture',transport=tr),now)
            self.assertEqual(result['stage'],'UNSIGNED_SIM_NET_ESTIMATE_PASS')
            self.assertFalse(result['realized_profit_certified'])
        def test_fee_net_negative(self):
            p=dict(witness,adverse_buffer_lamports=90000)
            self.assertEqual(simulation_gate(seed,p,RpcReadOnly('https://fixture',transport=tr),now)['reason'],'FEE_ADJUSTED_PROFIT_NONPOSITIVE')
        def test_sim_error(self):
            def bad(m,p):
                d=tr(m,p)
                if m=='simulateTransaction':d['result']['value']['err']={'InstructionError':[1,{'Custom':1}]}
                return d
            self.assertEqual(simulation_gate(seed,witness,RpcReadOnly('https://fixture',transport=bad),now)['reason'],'NATIVE_ATOMIC_SIMULATION_FAILED')
        def test_rpc_429(self):
            def fail(m,p):raise urllib.error.HTTPError('https://fake',429,'',{},None)
            r=RpcReadOnly('https://fixture',transport=fail)
            self.assertEqual(simulation_gate(seed,witness,r,now)['reason'],'RPC_429_STOP_NO_RETRY')
            self.assertTrue(r.stopped)
        def test_worker_latest(self):
            w=LatestWorker(clock_ns=lambda:now);w.submit(seed);w.submit(dict(seed,event_id=10))
            self.assertEqual(w.counts['replaced'],1)
        def test_worker_no_network_by_default(self):
            w=LatestWorker(clock_ns=lambda:now);w.start();w.submit(seed)
            time.sleep(.025);w.close()
            self.assertEqual(w.results[0]['reason'],'NATIVE_ATOMIC_PROVIDER_NOT_CERTIFIED')
        def test_b64_bounds(self):self.assertIsNone(valid_b64(base64.b64encode(b'1'*1300).decode()))
        def test_unsigned_wire(self):self.assertTrue(unsigned_v0_witness(packet,msg))
        def test_signed_wire_rejected(self):
            signed=bytearray(packet); signed[1]=7
            self.assertEqual(bank_native_gate(seed,dict(witness,unsigned_transaction_b64=base64.b64encode(signed).decode()),now),'UNSIGNED_V0_WIRE_FORMAT_UNVERIFIED')
        def test_worker_reconcile_negative(self):
            w=LatestWorker();w.submit(seed);w.reconcile({})
            self.assertTrue(w.newer_or_invalid(seed['token'],1))
        def test_different_wire_message(self):
            self.assertEqual(bank_native_gate(seed,dict(witness,message_b64=base64.b64encode(b'BAD').decode()),now),'UNSIGNED_V0_WIRE_FORMAT_UNVERIFIED')
        def test_0_001_below_scanner_range(self):
            self.assertEqual(stage1_nomination(dict(seed,size_lamports=1_000_000),now),'TRADE_SIZE_OUTSIDE_SCANNER_RANGE')
        def test_0_100_window_valid(self):
            self.assertIsNone(stage1_nomination(dict(seed,size_lamports=100_000_000),now))
        def test_canary(self):self.assertEqual(CANARY,10_000_000)
        def test_no_key_access(self):
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',live.__code__.co_consts)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():return 1
    print('[ORACLE366_TEST_PASS]',result.testsRun,flush=True)
    return 0


def main():
    ap=argparse.ArgumentParser()
    for x in ('install','test','audit','run','wallet-status'):
        ap.add_argument('--'+x,action='store_true')
    ap.add_argument('--seconds',type=float,default=180)
    ap.add_argument('--ttl-ms',type=int,default=2500)
    ap.add_argument('--max-age-ms',type=int,default=1500)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--provider-module',default='')
    args=ap.parse_args()
    if not any((args.install,args.test,args.audit,args.run,args.wallet_status)):
        ap.error('SELECT_MODE')
    if args.install:installed()
    if args.test and tests():return 1
    if args.audit:audit()
    if args.wallet_status:
        print('[ORACLE366_WALLET]', 'PRESENT' if bool(os.environ.get('QSB_SOLANA_PRIVATE_KEY')) else 'NOT_SET',
              'KEY_NOT_PRINTED KEY_NOT_ACCESSED NO_SIGNING_NO_BROADCAST',flush=True)
    if args.run:
        return live(args.seconds,args.poll_ms,args.ttl_ms,args.max_age_ms,
                    provider_module=args.provider_module or None)
    return 0

if __name__=='__main__':sys.exit(main())
