"""Oracle V1 native executor: real market validation / signed simulation only.

Uses existing Checkpoint-26 -> 25 -> 22 -> 21 -> 20 -> 19 -> 17 chain.
No live transaction broadcasting exists in the certified chain: --live fails closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.request
from unittest.mock import patch

ROOT = Path.cwd()
STATE = ROOT / 'runtime_state/oracle/V1'
BUS = STATE / 'opportunities.sqlite3'
REG = ROOT / 'runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json'
SHADOW = ROOT / 'runtime_state/oracle/oracle_live_execution/oracle_524/verified_candidate_registry.json'
R524 = SHADOW.with_name('handoff_report.json')
SCANNER = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py'
REPORT = STATE / 'executor_latest.json'
BLOCKED_METHODS = frozenset(('sendTransaction', 'sendRawTransaction', 'sendBundle',
                             'submitBundle', 'submitTransaction', 'requestAirdrop'))

class Hold(RuntimeError):
    pass

def read(path):
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise Hold('INVALID_JSON_' + path.name)
    return result

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_report(obj):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    t = REPORT.with_name(REPORT.name + '.' + str(os.getpid()) + '.tmp')
    try:
        t.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(t, REPORT)
    finally:
        t.unlink(missing_ok=True)

def method_in_json(body):
    if body is None:
        return False
    try:
        if isinstance(body, bytes): body = body.decode('utf-8')
        if isinstance(body, str): body = json.loads(body)
    except (UnicodeError, ValueError, TypeError):
        return False
    if isinstance(body, dict):
        return body.get('method') in BLOCKED_METHODS
    if isinstance(body, list):
        return any(method_in_json(x) for x in body)
    return False

def checked_rpc(old):
    def rpc(method, params):
        if method in BLOCKED_METHODS:
            raise Hold('V1_BROADCAST_RPC_BLOCKED')
        return old(method, params)
    return rpc

def checked_urlopen(old):
    def urlopen(url, *args, **kwargs):
        body = getattr(url, 'data', None)
        if body is None and args: body = args[0]
        if body is None: body = kwargs.get('data')
        if method_in_json(body):
            raise Hold('V1_BROADCAST_HTTP_BLOCKED')
        return old(url, *args, **kwargs)
    return urlopen

def checked_requests(old):
    def request(session, method, url, **kw):
        if method_in_json(kw.get('json')) or method_in_json(kw.get('data')):
            raise Hold('V1_BROADCAST_REQUEST_BLOCKED')
        return old(session, method, url, **kw)
    return request

def recent_nominations(now=None, max_records=20):
    now = time.time_ns() if now is None else now
    if not BUS.is_file(): return []
    try:
        db = sqlite3.connect(f'file:{BUS.as_posix()}?mode=ro', uri=True, timeout=1)
        try:
            rows = db.execute('SELECT json FROM opportunities WHERE expires_ns>? '
                              'ORDER BY gross_local_lamports DESC LIMIT ?',
                              (now, max_records)).fetchall()
        finally: db.close()
    except (sqlite3.Error, OSError) as exc:
        raise Hold('CANDIDATE_BUS_UNREADABLE_' + type(exc).__name__)
    found=[]
    for (raw,) in rows:
        c=json.loads(raw)
        if c.get('schema')=='ORACLE_V1_CANDIDATE_V1' and c.get('expires_ns',0)>now \
           and c.get('direction') in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
            found.append(c)
    return found

def state_for_native():
    # Share the scanner's exact pool metadata contract, not a separate guess.
    from .scanner import prepare_native
    return prepare_native()

def run(seconds):
    if os.getenv('QSB_LIVE_ARM','NO').upper() != 'NO':
        raise Hold('ARMING_NOT_PERMITTED_UNCERTIFIED_NATIVE_PATH')
    if not os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('SIGNER_REQUIRED_FOR_SIGVERIFY_SIM')
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_SOURCE_MISSING')
    native,wanted,cp17,q525=state_for_native()
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        checkpoint26_dlmm_output_ata_readiness as cp26,
        checkpoint21_signed_raw_transaction_simulation_cutover as cp21)
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    original_state=cp17.c12._expanded_state
    original_sim=cp21._signed_simulation_raw
    original_rpc=core.rpc
    original_url=urllib.request.urlopen
    try:
        import requests
    except ImportError:
        requests=None
    original_request = requests.sessions.Session.request if requests else None
    original_argv = list(sys.argv)
    frozen=(digest(SCANNER), digest(REG))
    ledger={'signed_sim_attempts':0,'signed_sim_successes':0,'signed_sim_failures':0,
            'exact_pairs':len(wanted),'nominations_observed_at_start':0}
    latest=recent_nominations()
    ledger['nominations_observed_at_start']=len(latest)
    # A nomination is an alert, never sufficient authorization to transact.
    ledger['matching_nominations_at_start'] = sum(
        (c['token'], c['meteora_pool']) in wanted for c in latest)

    def expanded():
        hydrated,registry,errors=q525.isolated_hydrate(native,original_state)
        actual={(str(p.token),str(p.meteora_pool)) for p in (hydrated.get('pairs') or [])}
        if errors or actual!=wanted:
            raise Hold('V1_NATIVE_REGISTRY_HYDRATION_DRIFT')
        return hydrated,registry,errors

    def monitored_sim(*args,**kwargs):
        ledger['signed_sim_attempts']+=1
        result=original_sim(*args,**kwargs)
        if not isinstance(result,dict) or result.get('err') is not None:
            ledger['signed_sim_failures']+=1
        else:
            ledger['signed_sim_successes']+=1
        return result

    print('[V1_EXECUTOR_START] exact_pairs=%d signed_sim_only=True broadcast=False canary=0.010_SOL' %
          len(wanted), flush=True)
    started=time.time()
    result={'status':'HOLD_UNCERTIFIED','broadcast':False,'execution_authority':False,
            'canary_size_sol':'0.010','fee_adjusted_net_profit_certified':False,
            'realized_profit_certified':False,'production_registry_unchanged':False,
            'frozen_scanner_unchanged':False}
    try:
        core.rpc=checked_rpc(original_rpc)
        urllib.request.urlopen=checked_urlopen(original_url)
        if requests:
            requests.sessions.Session.request=checked_requests(original_request)
        cp17.c12._expanded_state=expanded
        cp21._signed_simulation_raw=monitored_sim
        sys.argv=[original_argv[0],'--seconds',str(seconds)]
        rc=cp26.main()
        result['native_chain_return']=0 if rc is None else int(rc)
        if ledger['signed_sim_successes']:
            result['status']='SIMULATION_PASS_ECONOMICS_AND_LIVE_GATES_UNCERTIFIED'
        else:
            result['status']='HOLD_NO_SUCCESSFUL_SIGNED_TWO_LEG_SIMULATION'
    finally:
        cp17.c12._expanded_state=original_state
        cp21._signed_simulation_raw=original_sim
        core.rpc=original_rpc
        urllib.request.urlopen=original_url
        if requests: requests.sessions.Session.request=original_request
        sys.argv=original_argv
        result['production_registry_unchanged']=digest(REG)==frozen[1]
        result['frozen_scanner_unchanged']=digest(SCANNER)==frozen[0]
        if not result['production_registry_unchanged'] or not result['frozen_scanner_unchanged']:
            result['status']='HOLD_PROTECTED_FILES_CHANGED'
    result.update(ledger)
    result['elapsed_seconds']=round(time.time()-started,3)
    write_report(result)
    print('[V1_EXECUTOR_FINAL]',json.dumps(result,sort_keys=True),flush=True)
    return 0 if result['status'].startswith('SIMULATION_PASS_') and \
       result['production_registry_unchanged'] and result['frozen_scanner_unchanged'] else 2

def test():
    from unittest.mock import patch as mocked
    def good_rpc(method, params): return {'method': method}
    assert checked_rpc(good_rpc)('simulateTransaction',[])=={'method':'simulateTransaction'}
    try:
        checked_rpc(good_rpc)('sendTransaction',[])
        raise AssertionError('BROADCAST_NOT_BLOCKED')
    except Hold: pass
    assert method_in_json({'method':'sendTransaction'})
    assert method_in_json([{'method':'getBalance'}, {'method':'sendBundle'}])
    assert not method_in_json({'method':'simulateTransaction'})
    old_url=lambda *args,**kw: 42
    assert checked_urlopen(old_url)('https://example.invalid',b'{"method":"simulateTransaction"}')==42
    try:
        checked_urlopen(old_url)('https://example.invalid',b'{"method":"sendTransaction"}')
        raise AssertionError('HTTP_BROADCAST_NOT_BLOCKED')
    except Hold: pass
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        from .scanner import connect, publish, candidate
        f=Path(d)/'bus.sqlite3'
        with mocked.object(sys.modules[__name__], 'BUS', f):
            db=connect(f)
            good=candidate('A'*32,'B'*32,'C'*32,101,1,time.perf_counter_ns(),
                           {'direction':'PUMP_TO_METEORA','size_sol':0.010,
                            'local_net':1000},now_ns=time.time_ns())
            assert publish(db,good)
            assert len(recent_nominations())==1
            db.close()
    print('[PASS] V1_EXECUTOR shared_WAL freshness signed_sim_guard rpc_http_broadcast_block no_live_arm',flush=True)

def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--run',action='store_true')
    group.add_argument('--test',action='store_true')
    group.add_argument('--live',action='store_true')
    p.add_argument('--seconds',type=int,default=90)
    a=p.parse_args()
    try:
        if a.test: test(); return 0
        if a.live: raise Hold('LIVE_BROADCAST_NOT_CERTIFIED_OR_IMPLEMENTED_IN_V1')
        if not 10<=a.seconds<=600: raise Hold('INVALID_BOUNDED_SECONDS')
        return run(a.seconds)
    except Exception as exc:
        print('[V1_EXECUTOR_HOLD]',str(exc) if isinstance(exc,Hold) else type(exc).__name__,flush=True)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
