"""ORACLE-146 full installer. Preserve original scanner; prepare native templates from its cache.
No private key handling, signing, simulation or broadcasting. Fail closed on identity.
"""
from pathlib import Path
import ast
import os
import subprocess
import sys
import tempfile

ROOT=Path.cwd()
Q25=ROOT/'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'
NATIVE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
TARGET=PKG/'oracle146_native_template_preparation.py'
HOOK='    o146.start(state,warmed)\n'
IMPORT='    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle146_native_template_preparation as o146\n'
MODULE=r'''"""Warm native templates from Q25 shared hydrated inventory. Never signs or broadcasts."""
import argparse
import json
import os
import threading
import time
from pathlib import Path

OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_146_NATIVE_TEMPLATES.json')
_STARTED=False
_LOCK=threading.Lock()

def public_wallet():
    # Do NOT call sim_identity: its fallback can be a third-party Mriya address.
    candidate=os.environ.get('QSB_SOLANA_WALLET','').strip()
    if not candidate:return None
    try:
        from solders.pubkey import Pubkey
        key=Pubkey.from_string(candidate)
        if not key.is_on_curve():return None
        return str(key)
    except Exception:
        return None

def prepare(state,warmed,native=None,wallet=None):
    result={'build':'ORACLE146','source':'Q25_SINGLE_HYDRATED_CACHE',
        'execution_authority':False,'signed':False,'simulated':False,'broadcast':False,
        'pair_count':len(state.get('pairs') or []),'ready_tokens':[],
        'holds':[], 'wallet_present':bool(wallet)}
    if not wallet:
        result['holds'].append('HOLD_PUBLIC_WALLET_NOT_AVAILABLE')
        return result
    if native is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as native
    if not callable(getattr(native,'prebuild_templates',None)) or not callable(getattr(native,'prebuild_meteora_templates',None)):
        result['holds'].append('HOLD_NATIVE_TEMPLATE_API_MISSING')
        return result
    try:
        native.prebuild_templates(state,wallet)
    except Exception as exc:
        result['holds'].append('HOLD_PUMP_PREBUILD_'+type(exc).__name__)
        return result
    result['pump_ready']=len(getattr(native,'READY_TOKENS',set()))
    if not result['pump_ready']:
        result['holds'].append('HOLD_NO_PUMP_TEMPLATES')
        return result
    try:
        native.prebuild_meteora_templates(state,wallet,warmed)
    except Exception as exc:
        result['holds'].append('HOLD_METEORA_PREBUILD_'+type(exc).__name__)
    templates=getattr(native,'TEMPLATES',{})
    meta=getattr(native,'METEORA_TEMPLATES',{})
    ready=set(getattr(native,'READY_TOKENS',set()))
    for pair in state.get('pairs') or []:
        token=str(pair.token)
        if token not in ready:continue
        p=templates.get(token)
        m=meta.get(token)
        if not isinstance(p,dict) or p.get('pump_pool')!=str(pair.pump_pool):
            result['holds'].append('HOLD_PUMP_IDENTITY_'+token[:12]);continue
        if not isinstance(m,dict):
            result['holds'].append('HOLD_METEORA_TEMPLATE_'+token[:12]);continue
        result['ready_tokens'].append(token[:12])
    result['ready_count']=len(result['ready_tokens'])
    if not result['ready_count']:result['holds'].append('HOLD_NO_COMPLETE_NATIVE_TEMPLATES')
    return result

def _worker(state,warmed):
    wallet=public_wallet()
    try:report=prepare(state,warmed,wallet=wallet)
    except Exception as exc:
        report={'build':'ORACLE146','holds':['HOLD_PREPARATION_'+type(exc).__name__],
                'execution_authority':False,'signed':False,'simulated':False,'broadcast':False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix('.tmp')
    temp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf8')
    os.replace(temp,OUT)
    print('[ORACLE146_NATIVE_TEMPLATES] ready=%s holds=%s report=%s'%(
        report.get('ready_count',0),report.get('holds',[]),OUT),flush=True)

def start(state,warmed):
    global _STARTED
    with _LOCK:
        if _STARTED:return
        _STARTED=True
    threading.Thread(target=_worker,args=(state,warmed),daemon=True,name='oracle146-native-template-prewarm').start()
    print('[ORACLE146] Q25 inventory -> native template prewarm; no signing/broadcast',flush=True)

def test():
    from types import SimpleNamespace
    class Native:
        TEMPLATES={};METEORA_TEMPLATES={};READY_TOKENS=set()
        @classmethod
        def prebuild_templates(cls,state,user):
            cls.TEMPLATES={'T':{'pump_pool':'P'}};cls.READY_TOKENS={'T'}
        @classmethod
        def prebuild_meteora_templates(cls,state,user,warmed):
            cls.METEORA_TEMPLATES={'T':{'id':'M'}}
    state={'pairs':[SimpleNamespace(token='T',pump_pool='P')]}
    assert 'HOLD_PUBLIC_WALLET_NOT_AVAILABLE' in prepare(state,[],Native,None)['holds']
    r=prepare(state,[],Native,'FIXTURE_PUBLIC_WALLET')
    assert r['ready_count']==1 and r['ready_tokens']==['T'] and not r['holds'],r
    assert r['broadcast'] is False and r['signed'] is False
    print('[TEST PASS] ORACLE146 Q25 identity-bound templates; wallet HOLD; no signing/broadcast')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');a=ap.parse_args()
    if a.test:test();return 0
    test();print('[MODE] Embedded Q25 prewarm; use oracle120_credentials.py --run');return 0
if __name__=='__main__':raise SystemExit(main())
'''

def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:
        f.write(raw);temp=Path(f.name)
    os.replace(temp,path)

def main():
    if not Q25.is_file() or not NATIVE.is_file():
        raise SystemExit('[HOLD] Q25 or native runtime missing; no changes')
    source=Q25.read_text(encoding='utf8')
    native=NATIVE.read_text(encoding='utf8')
    for x in (source,native,MODULE):ast.parse(x)
    for name in ('def prebuild_templates(', 'def prebuild_meteora_templates('):
        if name not in native:raise SystemExit('[HOLD] native API missing '+name)
    if 'EXECUTION_AUTHORITY=False' not in source:
        raise SystemExit('[HOLD] Q25 read-only guard missing')
    seam='    warmed=install_hot_math_and_prewarm(state)\n'
    if source.count(seam)!=1:raise SystemExit('[HOLD] Q25 warmup seam changed')
    if source.count(HOOK)==0:
        source=source.replace(seam,seam+IMPORT+HOOK,1)
    elif source.count(HOOK)!=1 or source.count(IMPORT)!=1:
        raise SystemExit('[HOLD] existing ORACLE146 hook ambiguous')
    ast.parse(source)
    oldq=Q25.read_bytes();oldm=TARGET.read_bytes() if TARGET.exists() else None
    try:
        put(TARGET,MODULE.encode('utf8'));put(Q25,source.encode('utf8'))
        check=subprocess.run([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle146_native_template_preparation','--test'],cwd=ROOT,capture_output=True,text=True,timeout=30)
        if check.returncode:raise RuntimeError((check.stdout+check.stderr)[-2000:])
        print(check.stdout.strip())
    except BaseException as exc:
        put(Q25,oldq)
        if oldm is None:TARGET.unlink(missing_ok=True)
        else:put(TARGET,oldm)
        raise SystemExit('[HOLD] ORACLE146 rollback: '+str(exc))
    print('[INSTALL PASS] ORACLE146 native template preparation using Q25 shared pairs')
    print('[RUN] python oracle120_credentials.py --run')
if __name__=='__main__':main()
