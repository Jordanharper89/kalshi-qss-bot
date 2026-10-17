from __future__ import annotations
"""ORACLE-399: canonical execution owner, fail-closed until native SDK bridge is certified.

No scanner edits, no scanner/WebSocket/RPC duplication. An in-repo native bridge
must supply fresh canonical candidates and the actual PumpSwap/Meteora SDK
transaction construction, wallet signing, final freshness and reconciliation.
"""
import argparse
import ast
import base64
import hashlib
import importlib
import json
import math
import os
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PACKAGE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
ROOT = Path(__file__).resolve().parents[3] if Path(__file__).resolve().parent.name == 'solana_atomic_executor' else Path.cwd()
TARGET = ROOT / PACKAGE / 'oracle_399_final_boss_execution_owner.py'
STATE = ROOT / 'runtime_state/oracle/final_boss_dual'
FREEZE = STATE / 'ORACLE322_FROZEN_SOURCE_HASHES.json'
FROZEN_NAMES = ('build_oracle_322_scanner_isolated_discovery.py',
                'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py',
                'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py',
                'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py')
JOURNAL = STATE / 'oracle_399_transaction_journal.sqlite3'
REPORT = STATE / 'oracle_399_execution_owner.json'
SIZES = tuple(range(10_000_000, 100_000_001, 5_000_000))
PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
ORDER = {'PUMP_TO_METEORA': (PUMP, DLMM), 'METEORA_TO_PUMP': (DLMM, PUMP)}
BRIDGE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_399_native_sdk_bridge'
REQUIRED = ('next_candidate', 'prepare', 'sign', 'simulation_net_lamports', 'revalidate', 'reconcile', 'certification')

class Hold(RuntimeError):
    pass

def integer(v):
    return type(v) is int and v >= 0

def source_hashes():
    if not FREEZE.is_file():
        raise Hold('FREEZE_MANIFEST_NOT_FOUND')
    hashes = json.loads(FREEZE.read_text(encoding='utf-8'))
    if not isinstance(hashes, dict) or set(hashes) != set(FROZEN_NAMES):
        raise Hold('SCANNER_FOUR_FILE_FREEZE_MALFORMED')
    for name, expected in hashes.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise Hold('FROZEN_SOURCE_MISSING:' + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise Hold('FROZEN_SOURCE_CHANGED:' + name)
    return hashes

def status():
    result = {'module': 'ORACLE399', 'scope': 'ONE_EXECUTION_OWNER',
              'scanner_modified': False, 'extra_websocket': False,
              'size_min_sol': 0.010, 'size_max_sol': 0.100,
              'sizes': len(SIZES), 'signing': False, 'broadcast': False}
    try:
        result['source_hashes_verified'] = len(source_hashes())
    except (Hold, ValueError, OSError) as exc:
        result['hold'] = str(exc)
    source = ROOT / PACKAGE
    result['native_sources_present'] = {name: bool(list(source.glob('oracle_' + str(name).zfill(3) + '_*.py')))
                                        for name in (54, 77, 370, 374, 378, 379, 380, 382)}
    result['native_bridge_present'] = (source / 'oracle_399_native_sdk_bridge.py').is_file()
    result['native_interfaces'] = {}
    for number in (54, 77, 370, 374, 378, 379, 380, 382):
        found = []
        for path in list(source.glob('oracle_' + str(number).zfill(3) + '_*.py'))[:3]:
            try:
                syntax = ast.parse(path.read_text(encoding='utf-8-sig'))
                functions = [x.name for x in syntax.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
                found.append({'source':path.name,'functions':functions[:80]})
            except (OSError,SyntaxError):
                found.append({'source':path.name,'status':'SOURCE_UNREADABLE'})
        result['native_interfaces'][str(number)] = found
    result['legacy_fixed_canary_found'] = False
    for path in source.glob('oracle_382_*.py'):
        if 'FIRST_FUNDED_CANARY!=10_000_000' in path.read_text(encoding='utf-8', errors='replace'):
            result['legacy_fixed_canary_found'] = True
    result['status'] = ('HOLD_FREEZE' if result.get('hold') else
                        'HOLD_NATIVE_BRIDGE' if not result['native_bridge_present'] else
                        'READY_FOR_NATIVE_BRIDGE_TEST_NOT_LIVE_CERTIFIED')
    return result

def validate_candidate(c):
    if not isinstance(c, dict): raise Hold('CANDIDATE_NOT_MAPPING')
    size = c.get('size_lamports')
    if size not in SIZES or type(size) is not int: raise Hold('SIZE_NOT_ON_19_STEP_GRID')
    if c.get('direction') not in ORDER: raise Hold('DIRECTION_INVALID')
    for key in ('token', 'pump_pool', 'meteora_pool'):
        if not isinstance(c.get(key), str) or not 32 <= len(c[key]) <= 44:
            raise Hold('MISSING_FULL_' + key.upper())
    for key in ('source_epoch', 'snapshot_slot'):
        if not integer(c.get(key)) or c[key] < 1: raise Hold('CANONICAL_' + key.upper() + '_INVALID')
    if not integer(c.get('gross_lamports')) or c['gross_lamports'] <= 0:
        raise Hold('NO_POSITIVE_GROSS_QUOTE')
    if c.get('scanner_validator') != 'PASS': raise Hold('SCANNER_HEALTH_NOT_CERTIFIED')
    if c.get('canonical_pool_match') is not True: raise Hold('CANONICAL_NATIVE_POOL_MISMATCH')
    age = c.get('age_ms')
    if isinstance(age, bool) or not isinstance(age, (int, float)) or not math.isfinite(age) or not 0 <= age <= 750:
        raise Hold('SCANNER_SNAPSHOT_STALE')
    return c

def validate_plan(c, p):
    if not isinstance(p, dict): raise Hold('NATIVE_PLAN_NOT_MAPPING')
    for key in ('token', 'pump_pool', 'meteora_pool', 'direction', 'source_epoch', 'snapshot_slot'):
        if p.get(key) != c.get(key): raise Hold('NATIVE_SNAPSHOT_BINDING_' + key.upper())
    if p.get('size_lamports') != c['size_lamports']: raise Hold('NATIVE_SIZE_DRIFT')
    if list(p.get('swap_programs', [])) != list(ORDER[c['direction']]):
        raise Hold('NATIVE_TWO_LEG_PROGRAM_ORDER_INVALID')
    if p.get('version') != 'v0' or p.get('alt_resolved') is not True:
        raise Hold('VERSIONED_ALT_NOT_VERIFIED')
    if p.get('token_programs_verified') is not True or p.get('all_accounts_verified') is not True:
        raise Hold('TOKEN_PROGRAM_OR_ACCOUNT_META_FAILURE')
    if p.get('evaluated_sizes_lamports') != list(SIZES) or p.get('selection_policy') != 'MAX_PROTECTED_NET_LAMPORTS':
        raise Hold('NATIVE_19_SIZE_PROTECTED_RANKING_UNVERIFIED')
    if p.get('full_input_consumed') is not True or p.get('min_out_protected') is not True:
        raise Hold('PARTIAL_FILL_OR_SLIPPAGE_UNPROTECTED')
    if not integer(p.get('protected_min_return_lamports')): raise Hold('NATIVE_MIN_RETURN_MISSING')
    if not integer(p.get('last_valid_block_height')): raise Hold('BLOCKHASH_EXPIRY_NOT_BOUND')
    if not isinstance(p.get('blockhash'), str): raise Hold('BLOCKHASH_MISSING')
    for key in ('tip_lamports', 'rent_lamports', 'other_cost_lamports'):
        if not integer(p.get(key)): raise Hold('COST_COMPONENT_UNKNOWN_' + key.upper())
    return p

class Rpc:
    def __init__(self, url, wait=time.sleep):
        if not url.startswith(('https://', 'http://127.0.0.1:', 'http://localhost:')):
            raise Hold('RPC_URL_NOT_ALLOWED')
        self.url, self.wait = url, wait
        self.calls = 0

    def call(self, method, params=None, *, submit=False):
        allowed = {'getLatestBlockhash', 'getBlockHeight', 'getFeeForMessage',
                   'simulateTransaction', 'getSignatureStatuses', 'getTransaction',
                   'sendTransaction'}
        if method not in allowed or (method == 'sendTransaction') != submit:
            raise Hold('RPC_METHOD_OR_SUBMISSION_BOUNDARY_INVALID')
        body = json.dumps({'jsonrpc':'2.0', 'id':self.calls+1,
                           'method':method, 'params':params or []}).encode()
        req = urllib.request.Request(self.url, body,
                                     {'Content-Type':'application/json'}, method='POST')
        self.calls += 1
        for attempt in range(3 if not submit else 1):
            try:
                with urllib.request.urlopen(req, timeout=12) as rsp:
                    result = json.loads(rsp.read(3_000_000).decode())
                if result.get('error'):
                    err = result['error']
                    if err.get('code') == 429 and not submit and attempt < 2:
                        self.wait((2, 5)[attempt]); continue
                    raise Hold('RPC_' + method + '_ERROR_' + str(err.get('code')))
                if 'result' not in result: raise Hold('RPC_RESULT_MISSING')
                return result['result']
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and not submit and attempt < 2:
                    self.wait((2, 5)[attempt]); continue
                raise Hold('RPC_HTTP_' + str(exc.code)) from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                raise Hold('RPC_TRANSPORT_' + type(exc).__name__) from None
        raise Hold('RPC_RETRIES_EXHAUSTED')

def signed_message(signed, plan):
    try:
        from solders.message import MessageV0, to_bytes_versioned
        from solders.transaction import VersionedTransaction
        tx = VersionedTransaction.from_bytes(signed)
        if not isinstance(tx.message, MessageV0): raise Hold('SIGNED_PACKET_NOT_V0')
        if len(signed) > 1232: raise Hold('TX_PACKET_EXCEEDS_1232_BYTES')
        tx.verify_and_hash_message()  # real Ed25519 signature check
        message = to_bytes_versioned(tx.message)
        if hashlib.sha256(message).hexdigest() != plan.get('message_sha256'):
            raise Hold('NATIVE_SIGNED_MESSAGE_DRIFT')
        if str(tx.message.recent_blockhash) != plan['blockhash']:
            raise Hold('NATIVE_BLOCKHASH_DRIFT')
        keys = [str(k) for k in tx.message.account_keys]
        programs = [keys[ix.program_id_index] if ix.program_id_index < len(keys) else 'ALT_PROGRAM_UNRESOLVED'
                    for ix in tx.message.instructions]
        swaps = [name for name in programs if name in (PUMP, DLMM)]
        if tuple(swaps) != ORDER[plan['direction']]:
            raise Hold('ACTUAL_SIGNED_SWAP_INSTRUCTION_ORDER_INVALID')
        return tx, message
    except ImportError:
        raise Hold('SOLDERS_NOT_INSTALLED') from None
    except Hold:
        raise
    except Exception as exc:
        raise Hold('SIGNED_PACKET_DECODE_OR_SIGNATURE_FAILED_' + type(exc).__name__) from None

def protected_profit(candidate, plan, cluster_fee, simulated_net):
    if not integer(cluster_fee) or not isinstance(simulated_net, int):
        raise Hold('FEE_OR_SIM_DELTA_UNVERIFIED')
    expenses = sum(plan[k] for k in ('tip_lamports','rent_lamports','other_cost_lamports'))
    min_net = plan['protected_min_return_lamports'] - candidate['size_lamports'] - cluster_fee - expenses
    after_sim = simulated_net - cluster_fee - expenses
    if min_net <= 0 or after_sim <= 0: raise Hold('NO_PROTECTED_FEE_POSITIVE_PROFIT')
    return min(min_net, after_sim)

def journal():
    STATE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(JOURNAL, timeout=3)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS transmissions (digest TEXT PRIMARY KEY, signature TEXT NOT NULL, status TEXT NOT NULL, updated_utc INTEGER NOT NULL)')
    db.commit()
    return db

def atomic_claim(db, digest, sig):
    try:
        db.execute('INSERT INTO transmissions VALUES (?,?,?,?)', (digest, sig, 'PREPARED', int(time.time())))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def state(db, digest, value):
    db.execute('UPDATE transmissions SET status=?, updated_utc=? WHERE digest=?',
               (value, int(time.time()), digest)); db.commit()

def execute_once(bridge, rpc, *, live=False, clock=time.monotonic):
    source_hashes()
    candidate = validate_candidate(bridge.next_candidate())
    latest = rpc.call('getLatestBlockhash', [{'commitment':'processed', 'minContextSlot':candidate['snapshot_slot']}])
    value = latest.get('value', {})
    if latest.get('context', {}).get('slot', 0) < candidate['snapshot_slot'] or not value.get('blockhash'):
        raise Hold('BLOCKHASH_BEHIND_CANONICAL_SNAPSHOT')
    plan = validate_plan(candidate, bridge.prepare(candidate, value))
    if plan['blockhash'] != value['blockhash'] or plan['last_valid_block_height'] != value['lastValidBlockHeight']:
        raise Hold('NATIVE_BLOCKHASH_LIFETIME_MISMATCH')
    # Signing is an in-process native-bridge operation; key never crosses RPC or appears in logs.
    signed = bridge.sign(plan)
    if not isinstance(signed, bytes): raise Hold('BRIDGE_SIGNER_MUST_RETURN_BYTES')
    tx, message = signed_message(signed, plan)
    fee = rpc.call('getFeeForMessage', [base64.b64encode(message).decode(),
                                        {'commitment':'processed','minContextSlot':candidate['snapshot_slot']}])
    cluster_fee = fee.get('value') if isinstance(fee, dict) else None
    if not integer(cluster_fee): raise Hold('RPC_MESSAGE_FEE_UNAVAILABLE')
    sim = rpc.call('simulateTransaction', [base64.b64encode(signed).decode(),
                    {'encoding':'base64','sigVerify':True,'replaceRecentBlockhash':False,
                     'minContextSlot':candidate['snapshot_slot'],'commitment':'processed'}])
    sv = sim.get('value') if isinstance(sim, dict) else None
    if not isinstance(sv, dict) or sv.get('err') is not None: raise Hold('SIGNED_SIMULATION_FAILED')
    if sim.get('context', {}).get('slot', 0) < candidate['snapshot_slot']:
        raise Hold('SIM_BANK_BEHIND_SNAPSHOT')
    if not integer(sv.get('unitsConsumed')) or sv['unitsConsumed'] > 1_400_000:
        raise Hold('SIM_COMPUTE_LIMIT_INVALID')
    sim_delta = bridge.simulation_net_lamports(candidate, plan, sim)
    net = protected_profit(candidate, plan, cluster_fee, sim_delta)
    latest_state = bridge.revalidate(candidate, plan)
    if not isinstance(latest_state, dict) or latest_state.get('fresh') is not True:
        raise Hold('FINAL_CANONICAL_SNAPSHOT_STALE')
    for key in ('token','pump_pool','meteora_pool','direction','source_epoch'):
        if latest_state.get(key) != candidate[key]: raise Hold('FINAL_' + key.upper() + '_MISMATCH')
    if latest_state.get('native_pool_ready') is not True or latest_state.get('wallet_funded') is not True:
        raise Hold('FINAL_POOL_OR_WALLET_NOT_READY')
    if rpc.call('getBlockHeight', [{'commitment':'processed'}]) >= plan['last_valid_block_height']:
        raise Hold('SIGNED_PACKET_BLOCKHASH_EXPIRED')
    result = {'status':'SIGNED_ATOMIC_SIM_PASS' if not live else 'SUBMISSION_PENDING',
              'direction':candidate['direction'], 'size_sol':candidate['size_lamports']/1e9,
              'fee_lamports':cluster_fee, 'protected_net_lamports':net,
              'sim_units':sv['unitsConsumed'], 'signing':True, 'broadcast':False}
    if not live: return result
    # Separate native integration certification; passing interface tests is insufficient.
    cert = bridge.certification()
    bridge_source = ROOT / PACKAGE / 'oracle_399_native_sdk_bridge.py'
    if not isinstance(cert, dict) or not bridge_source.is_file():
        raise Hold('NATIVE_BRIDGE_CERTIFICATION_UNAVAILABLE')
    if cert.get('source_sha256') != hashlib.sha256(bridge_source.read_bytes()).hexdigest():
        raise Hold('NATIVE_BRIDGE_CERTIFICATION_SOURCE_MISMATCH')
    if not all(cert.get(k) is True for k in ('dual_leg_v0_verified', 'signed_sim_verified',
                                               'dynamic_19_sizes_verified', 'reconciliation_verified')):
        raise Hold('NATIVE_BRIDGE_PHYSICAL_TESTS_INCOMPLETE')
    source_hashes()  # re-check freeze immediately before possible submission
    if os.environ.get('QSB_LIVE_ARM') != 'YES': raise Hold('LIVE_ARM_NOT_EXPLICIT')
    if os.environ.get('QSB_ORACLE399_LIVE_APPROVED') != 'YES': raise Hold('ORACLE399_LIVE_NOT_CERTIFIED')
    # Write-ahead idempotency: no blind retry on uncertain send status.
    digest = hashlib.sha256(signed).hexdigest()
    sig = str(tx.signatures[0])
    with journal() as db:
        if not atomic_claim(db, digest, sig): raise Hold('DUPLICATE_SIGNED_TRANSACTION_IN_JOURNAL')
        state(db, digest, 'SENDING_UNCERTAIN')
        try:
            returned = rpc.call('sendTransaction', [base64.b64encode(signed).decode(),
               {'encoding':'base64','skipPreflight':False,'preflightCommitment':'processed',
                'maxRetries':0,'minContextSlot':candidate['snapshot_slot']}], submit=True)
        except Hold:
            state(db, digest, 'UNKNOWN_MUST_RECONCILE_SIGNATURE')
            raise
        if returned != sig:
            state(db, digest, 'UNKNOWN_SIGNATURE_MISMATCH')
            raise Hold('RPC_RETURNED_DIFFERENT_SIGNATURE')
        state(db, digest, 'SENT')
        end = clock() + 50
        while clock() < end:
            observed = rpc.call('getSignatureStatuses', [[sig], {'searchTransactionHistory':True}])
            record = (observed.get('value') or [None])[0]
            if isinstance(record, dict) and record.get('err') is not None:
                state(db, digest, 'CHAIN_FAILED'); raise Hold('CHAIN_TRANSACTION_FAILED_FEE_MAY_BE_CHARGED')
            if isinstance(record, dict) and record.get('confirmationStatus') in ('confirmed','finalized'):
                receipt = rpc.call('getTransaction', [sig, {'encoding':'json','commitment':'confirmed',
                                                           'maxSupportedTransactionVersion':0}])
                if not isinstance(receipt, dict) or not isinstance(receipt.get('meta'), dict):
                    state(db, digest, 'CONFIRMED_RECEIPT_UNAVAILABLE')
                    raise Hold('CONFIRMED_BUT_RECEIPT_UNAVAILABLE')
                if receipt['meta'].get('err') is not None:
                    state(db, digest, 'CHAIN_FAILED'); raise Hold('CHAIN_RECEIPT_FAILED')
                proof = bridge.reconcile(candidate, plan, receipt)
                if not isinstance(proof, dict) or proof.get('balances_reconciled') is not True:
                    state(db, digest, 'CONFIRMED_RECONCILIATION_HOLD')
                    raise Hold('ONCHAIN_WSOL_TOKEN_OR_RESIDUE_UNRECONCILED')
                actual = proof.get('realized_net_lamports')
                if type(actual) is not int:
                    state(db, digest, 'CONFIRMED_PROFIT_UNVERIFIED')
                    raise Hold('ONCHAIN_REALIZED_PNL_UNVERIFIED')
                state(db, digest, 'RECONCILED_PROFIT' if actual > 0 else 'RECONCILED_NONPROFIT')
                result.update(status='CHAIN_CONFIRMED_RECONCILED', broadcast=True, signature=sig,
                              realized_net_lamports=actual, realized_profit_certified=actual > 0)
                return result
            time.sleep(1)
        state(db, digest, 'UNKNOWN_PENDING_CONFIRMATION')
        raise Hold('TX_CONFIRMATION_TIMEOUT_RECONCILE_BEFORE_RESEND')

def load_bridge():
    path = ROOT / PACKAGE / 'oracle_399_native_sdk_bridge.py'
    if not path.is_file(): raise Hold('NATIVE_SDK_BRIDGE_MISSING_LOCAL_SOURCE_REQUIRED')
    module = importlib.import_module(BRIDGE)
    missing = [name for name in REQUIRED if not callable(getattr(module, name, None))]
    if missing: raise Hold('NATIVE_SDK_BRIDGE_CONTRACT_MISSING_' + ','.join(missing))
    return module

def tests():
    c = {'size_lamports':25_000_000, 'direction':'METEORA_TO_PUMP',
         'token':'a'*40, 'pump_pool':'b'*40, 'meteora_pool':'c'*40,
         'source_epoch':5, 'snapshot_slot':200, 'gross_lamports':100_000,
         'scanner_validator':'PASS','canonical_pool_match':True,'age_ms':20}
    p = dict(c, version='v0', swap_programs=list(ORDER[c['direction']]),
             alt_resolved=True, token_programs_verified=True, all_accounts_verified=True,
             full_input_consumed=True, min_out_protected=True,
             evaluated_sizes_lamports=list(SIZES), selection_policy='MAX_PROTECTED_NET_LAMPORTS',
             blockhash='h'*40,
             last_valid_block_height=333, protected_min_return_lamports=25_150_000,
             tip_lamports=0, rent_lamports=0, other_cost_lamports=0)
    assert len(SIZES)==19 and SIZES[0]==10_000_000 and SIZES[-1]==100_000_000
    validate_candidate(c); validate_plan(c,p)
    assert protected_profit(c,p,10_000,130_000)==120_000
    for key,value,expected in [('size_lamports',101_000_000,'SIZE_NOT_ON_19_STEP_GRID'),
                               ('age_ms',751,'SCANNER_SNAPSHOT_STALE'),
                               ('canonical_pool_match',False,'CANONICAL_NATIVE_POOL_MISMATCH')]:
        bad = dict(c, **{key:value})
        try: validate_candidate(bad); raise AssertionError('accepted bad '+key)
        except Hold as exc: assert expected in str(exc)
    try: protected_profit(c,p,151_000,130_000); raise AssertionError('negative protected')
    except Hold: pass
    p2=dict(p, swap_programs=[PUMP, DLMM])
    try: validate_plan(c,p2); raise AssertionError('wrong direction')
    except Hold: pass
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE transmissions (digest TEXT PRIMARY KEY, signature TEXT NOT NULL, status TEXT NOT NULL, updated_utc INTEGER NOT NULL)')
        assert atomic_claim(db,'packetsha','signature')
        assert not atomic_claim(db,'packetsha','signature')
    print('[PASS] ORACLE399 19 sizes, bidirectional identity, native-v0 proof, fee-positive economics, idempotency')
    print('[SCOPE] Deterministic contract tests; no live signer or SDK integration certified')

def main():
    a=argparse.ArgumentParser()
    g=a.add_mutually_exclusive_group(required=True)
    for item in ('test','install','audit','preflight','live'):
        g.add_argument('--'+item,action='store_true')
    args=a.parse_args()
    try:
        if args.test: tests(); return 0
        if args.install:
            TARGET.parent.mkdir(parents=True, exist_ok=True)
            current = Path(__file__).resolve()
            if current != TARGET.resolve():
                if TARGET.exists() and TARGET.read_bytes() != current.read_bytes():
                    raise Hold('DIFFERENT_ORACLE399_INSTALLED_SOURCE_NO_OVERWRITE')
                shutil.copy2(current, TARGET)
            tests()
            print('[INSTALLED]',TARGET.relative_to(ROOT))
            return 0
        if args.audit:
            result = status(); STATE.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print('[ORACLE399_AUDIT]',json.dumps(result,sort_keys=True))
            print('[REPORT]',REPORT.relative_to(ROOT))
            return 0
        bridge=load_bridge()
        rpc_url = os.environ.get('SOLANA_RPC_URL','')
        if not rpc_url: raise Hold('SOLANA_RPC_URL_NOT_CONFIGURED')
        result=execute_once(bridge,Rpc(rpc_url),live=args.live)
        print('[ORACLE399_RESULT]',json.dumps(result,sort_keys=True))
        return 0
    except (Hold,ValueError,KeyError) as exc:
        print('[ORACLE399_HOLD]',str(exc))
        return 2
    except Exception as exc:
        # Never echo arbitrary wallet/SDK exception strings: they may include secret material.
        print('[ORACLE399_HOLD] NATIVE_OR_RPC_EXCEPTION_' + type(exc).__name__)
        return 2

if __name__=='__main__':
    sys.exit(main())
