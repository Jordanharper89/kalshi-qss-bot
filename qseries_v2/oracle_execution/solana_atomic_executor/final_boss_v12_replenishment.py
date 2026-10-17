from __future__ import annotations
"""Final Boss V12: guarded single-writer scanner epoch replenishment.

Recreates a complete ORACLE-322 launcher with one isolated source change:
V8/V10-certificate-prioritized select_rows at the next scanner epoch.
The original scanner installer and Q18/Q20/Q25 are never replaced.
Only ORACLE-322 publishes canonical scanner events; V11 observes them.
No websocket is created here; no funded signing or broadcast method exists.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT=Path.cwd()
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
ORIGINAL=ROOT/'build_oracle_322_scanner_isolated_discovery.py'
DERIVED=ROOT/'build_final_boss_v12_scanner_runtime.py'
STATUS=BASE/'final_boss_v12_replenishment.json'
SUPERVISOR_LOCK=BASE/'v12_supervisor.lock'
SCANNER_LOCK=BASE/'scanner.lock'
SCANNER_STATUS=BASE/'scanner_status.json'
V10_REPORT=BASE/'final_boss_v10_admission_stage.json'
REFRESH_CERT=BASE/'v12_mriya_refresh_certificate.json'
PACKAGE='qseries_v2.oracle_execution.solana_atomic_executor.'
EXPECTED_INSTALLER_SHA='60c9a4d8acc4259a01f37c64332caea6139e49a84a719ada7e7fe4ec17bab57b'
EXPECTED_INNER_SHA='e579d68ac26210ef98ba015180126782669144e81fc5eb2010f0d9586ced767c'
ADDR=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
GRID=tuple(range(10_000_000,100_000_001,5_000_000))

class Hold(RuntimeError):pass

def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def normalized_bytes(data):return data.replace(b'\r\n',b'\n')
def hold_name(err):
    s=str(err)
    return s if isinstance(err,Hold) and re.fullmatch(r'[A-Z][A-Z0-9_]{3,100}',s) else type(err).__name__.upper()

def read_json(path, limit=900000):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>limit:raise Hold('REPORT_MISSING_UNTRUSTED_OR_OVERSIZED')
    x=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(x,dict):raise Hold('REPORT_OBJECT_REQUIRED')
    return x

def source_from_original(raw):
    if hash_bytes(normalized_bytes(raw))!=EXPECTED_INSTALLER_SHA:raise Hold('ORACLE322_ORIGINAL_INSTALLER_SHA_DRIFT')
    tree=ast.parse(raw.decode('utf-8-sig'))
    hits=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            if not any(isinstance(t,ast.Name) and ('SOURCE' in t.id.upper() or 'SCRIPT' in t.id.upper()) for t in targets):continue
            v=n.value
            if isinstance(v,ast.Constant) and isinstance(v.value,str) and len(v.value)>3000:hits.append((v,v.value))
    if len(hits)!=1:raise Hold('ORACLE322_EMBEDDED_SOURCE_NOT_UNIQUE')
    node,inner=hits[0]
    if hash_bytes(inner.encode('utf-8'))!=EXPECTED_INNER_SHA:raise Hold('ORACLE322_EMBEDDED_SOURCE_SHA_DRIFT')
    tree_inner=ast.parse(inner)
    funcs=[n for n in tree_inner.body if isinstance(n,ast.FunctionDef)]
    fn={n.name:n for n in funcs}
    if not {'select_rows','stage_discovery','connect','audit'}.issubset(fn):raise Hold('ORACLE322_SCANNER_INTERFACE_DRIFT')
    if 'rank' not in ast.get_source_segment(inner,fn['select_rows']):raise Hold('ORACLE322_RANKING_INTERFACE_CHANGED')
    return node,inner,fn

# The wrapper is injected as a *complete new function* immediately after the original
# select_rows. It retains the original function and delegates universal discovery to it.
# The staged Mriya overlay is admitted only when both V8 and V10 agree at startup.
WRAPPER = r'''
_v12_original_select_rows = select_rows

def select_rows(original):
    global STAGED
    import pathlib as _v12_pathlib
    import time as _v12_time
    import json as _v12_json
    _v12_before = STAGED
    try:
        # Never allow unchecked historical V8 staged rows into the baseline.
        STAGED = _v12_pathlib.Path('runtime_state/oracle/final_boss_dual/v12_ignored_legacy_stage.json')
    except Exception:
        STAGED = _v12_before
    try:
        _v12_baseline = _v12_original_select_rows(original)
    finally:
        STAGED = _v12_before
    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v10_admission_stage as _v12_v10
        from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v9_atomic_simulation_gate as _v12_v9
        _v12_now = _v12_time.time()
        _v12_raw=_v12_before.read_bytes()
        _v12_doc = _v12_json.loads(_v12_raw.decode('utf-8'))
        _v12_cert=_v12_json.loads(_v12_pathlib.Path('runtime_state/oracle/final_boss_dual/v12_mriya_refresh_certificate.json').read_text(encoding='utf-8'))
        import hashlib as _v12_hashlib
        if (not isinstance(_v12_cert,dict) or _v12_cert.get('status')!='CERTIFIED'
                or _v12_cert.get('stage_sha256')!=_v12_hashlib.sha256(_v12_raw).hexdigest()
                or not 0<=_v12_now-float(_v12_cert.get('at',0))<=90):
            raise ValueError('V12_FRESH_STAGE_CERTIFICATE_NOT_VALID')
        if not isinstance(_v12_doc,dict) or not 0 <= _v12_now-float(_v12_doc['generated_at']) <= 120:
            raise ValueError('V12_STAGED_FEED_STALE')
        _v12_source = _v12_v9.load_v8(_v12_now)
        _v12_rows,_v12_alt,_v12_holds = _v12_v10.select_v8(_v12_source,_v12_v9)
        _v12_stage=[r for r in _v12_doc.get('rows',[]) if isinstance(r,dict) and r.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW']
        _v12_key=lambda x:(x['token'],x['pump_pool'],x['meteora_pool'])
        if (not _v12_rows or len(_v12_rows)>28 or len(_v12_stage)!=len(_v12_rows)
                or {_v12_key(r) for r in _v12_rows}!={_v12_key(r) for r in _v12_stage}):
            raise ValueError('V12_FRESH_V8_STAGE_TRIPLE_MISMATCH')
        _v12_added=[]
        _v12_seen=set()
        for _v12_r in _v12_rows:
            _v12_t,_v12_p,_v12_d=_v12_key(_v12_r)
            if (not all(isinstance(x,str) and 32<=len(x)<=44 for x in (_v12_t,_v12_p,_v12_d))
                    or len({_v12_t,_v12_p,_v12_d})!=3 or _v12_t in _v12_seen):
                raise ValueError('V12_INVALID_STAGED_EXACT_TRIPLE')
            _v12_seen.add(_v12_t)
            _v12_added.append(dict(_v12_r,rank=20,sources=['MRIYA'],v12_admission='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM'))
        _v12_result=(_v12_added + [r for r in _v12_baseline if r.get('token') not in _v12_seen])[:112]
        emit('BOSS_V12_DISCOVERY_SELECTION',dict(v8_selected=len(_v12_added),baseline_tokens=len(_v12_baseline),
             final_candidates=len(_v12_result),new_distinct_tokens=sum(r['token'] not in {x['token'] for x in _v12_baseline} for r in _v12_added),
             live_subscriptions_changed=False,simulation_authority=False))
        return _v12_result
    except Exception as _v12_exc:
        # Never admit unverified V8 rows or bypass risk; universal discovery stays live.
        emit('BOSS_V12_MRIYA_HOLD',dict(code=type(_v12_exc).__name__,
             baseline_candidates=len(_v12_baseline),live_subscriptions_changed=False))
        return _v12_baseline
'''

def inject_scanner(inner):
    t=ast.parse(inner)
    funcs=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='select_rows']
    if len(funcs)!=1:raise Hold('SCANNER_SELECT_ROWS_COUNT_CHANGED')
    f=funcs[0]
    lines=inner.splitlines(keepends=True)
    # insert AFTER original select_rows, BEFORE following helper declarations
    lines.insert(f.end_lineno, '\n'+WRAPPER.strip('\n')+'\n\n')
    modified=''.join(lines)
    ast.parse(modified)
    compile(modified,'<oracle322-v12-embedded-scanner>','exec')
    # This must not modify Q25, Q20, Q18, main, the canonical bus, or 19-size pricing.
    assert 'def select_rows(original)' in modified and modified.count('def select_rows(original)')==2
    return modified

def offset(lines,line,col):return sum(len(x) for x in lines[:line-1])+col

def make_builder(original_bytes):
    node,inner,fn=source_from_original(original_bytes)
    new=inject_scanner(inner)
    outer=original_bytes.decode('utf-8-sig')
    lines=outer.splitlines(keepends=True)
    a=offset(lines,node.lineno,node.col_offset);b=offset(lines,node.end_lineno,node.end_col_offset)
    rebuilt=outer[:a]+repr(new)+outer[b:]
    ast.parse(rebuilt)
    compile(rebuilt,'<final_boss_v12_derived_builder>','exec')
    # Ensure the only changed outer AST element is the embedded source constant.
    baseline=ast.parse(outer);upgraded=ast.parse(rebuilt)
    def scrub(tree):
        for n in ast.walk(tree):
            if isinstance(n,(ast.Assign,ast.AnnAssign)):
                if isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and hash_bytes(n.value.value.encode()) in (EXPECTED_INNER_SHA,hash_bytes(new.encode())):
                    n.value.value='<SCANNER_SOURCE>'
        return ast.dump(tree,include_attributes=False)
    if scrub(baseline)!=scrub(upgraded):raise Hold('ORACLE322_DERIVED_BUILDER_UNRELATED_CHANGE')
    return rebuilt.encode('utf-8'),hash_bytes(new.encode())

def save_atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,suffix='.tmp',delete=False) as fp:
        fp.write(data);temp=Path(fp.name)
    try:os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)

def install():
    if ORIGINAL.is_symlink() or not ORIGINAL.is_file():raise Hold('ORACLE322_ORIGINAL_MISSING')
    upgraded,inner_sha=make_builder(ORIGINAL.read_bytes())
    if DERIVED.is_symlink():raise Hold('V12_DERIVED_BUILDER_IS_LINK')
    if DERIVED.exists():
        if DERIVED.read_bytes()!=upgraded:raise Hold('V12_DERIVED_BUILDER_ALREADY_MODIFIED')
    else:save_atomic(DERIVED,upgraded)
    # Complete self-module is installed exactly; do not modify the scanner original.
    target=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v12_replenishment.py'
    source=Path(__file__).read_bytes()
    if target.is_symlink():raise Hold('V12_MODULE_IS_LINK')
    if target.exists():
        if normalized_bytes(target.read_bytes())!=normalized_bytes(source):raise Hold('V12_INSTALLED_MODULE_DRIFT')
    else:save_atomic(target,source)
    print('[INSTALLED] FINAL_BOSS_V12_SCANNER_DERIVED_FULL_BUILDER')
    print('[GENERATED]',DERIVED)
    print('[EMBEDDED_SHA256]',inner_sha)
    print('[PRESERVED] original ORACLE322 installer, Q18/Q20/Q25, bus, V9/V11/402')
    print('[SCOPE] Single-socket bounded-epoch replenishment; no in-place WS rotation; no broadcast')

def scanner_running():
    if SCANNER_LOCK.exists():return True
    try:
        status=read_json(SCANNER_STATUS)
        return status.get('status')=='RUNNING' and 0<=time.time()-SCANNER_STATUS.stat().st_mtime<=15
    except Exception:return False

def child_env(sign_sim=False):
    e=os.environ.copy()
    if not sign_sim:
        for k in list(e):
            if any(s in k.upper() for s in ('PRIVATE_KEY','MNEMONIC','KEYPAIR','SEED_PHRASE','SECRET')):e.pop(k,None)
    return e

def rpc_ready():
    url=os.environ.get('SOLANA_RPC_URL','')
    return url.startswith('https://') and 20<len(url)<1024

def fresh_stage():
    d=read_json(V10_REPORT)
    if d.get('stage_written') is not True or d.get('status')!='STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE':
        raise Hold('V10_STAGE_NOT_COMMITTED')
    if d.get('scanner',{}).get('epoch') is None:raise Hold('V10_STAGE_EPOCH_MISSING')
    return d

def run_one(cmd,env):
    return subprocess.call([sys.executable,*cmd],env=env,cwd=str(ROOT))

def refresh():
    if not rpc_ready():raise Hold('SOLANA_RPC_URL_REQUIRED_HIDDEN_KEY_NOT_ON_COMMAND_LINE')
    env=child_env()
    # Fail closed for Mriya admission, not for existing independent universal discovery.
    # A quiet Mriya wallet must never kill the healthy universal scanning lane.
    status='CERTIFIED';failed_at='NONE'
    for mod,flag in [('final_boss_mriya_rpc_replenishment','--once'),
                     ('final_boss_mriya_crossvenue_discovery','--once'),
                     ('final_boss_v10_admission_stage','--stage')]:
        if run_one(['-m',PACKAGE+mod,flag],env):
            status='UNIVERSAL_ONLY';failed_at=mod;break
    if status=='CERTIFIED':
        try:
            fresh_stage()
            source=(BASE/'staged_discovery.json').read_bytes()
            cert={'status':'CERTIFIED','at':time.time(),'stage_sha256':hash_bytes(source)}
        except (OSError,ValueError,Hold):
            status='UNIVERSAL_ONLY';failed_at='STAGE_CERTIFICATION'
    if status!='CERTIFIED':
        cert={'status':'HOLD_MRIYA_UNIVERSAL_CONTINUES','at':time.time(),
              'reason_code':failed_at.split('.')[-1].upper()}
    save_atomic(REFRESH_CERT,json.dumps(cert,sort_keys=True).encode())
    print('[FINAL_BOSS_V12_DISCOVERY_REFRESH]',json.dumps({
          'mriya':'CERTIFIED_FOR_NEXT_EPOCH' if status=='CERTIFIED' else 'HOLD_UNIVERSAL_DISCOVERY_ONLY',
          'rpc_key_displayed':False,'broadcast':False},sort_keys=True),flush=True)
    return cert

def publish(obj):
    o=dict(obj)
    o.update(broadcast=False,funded_execution_authority=False,
             original_scanner_installer_modified=False,derived_scanner_source_used=True,additional_websockets_by_supervisor=0,
             size_grid_count=len(GRID),trade_sizes_simulated=[])
    save_atomic(STATUS,json.dumps(o,sort_keys=True,indent=2).encode())
    print('[FINAL_BOSS_V12_REPLENISHMENT]',json.dumps(o,sort_keys=True),flush=True)

def await_new_scanner(previous_epoch,proc,timeout=55):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if proc.poll() is not None:return False
        try:
            s=read_json(SCANNER_STATUS)
            if (s.get('status')=='RUNNING' and type(s.get('epoch')) is int
                    and s['epoch']>previous_epoch and time.time()-SCANNER_STATUS.stat().st_mtime<=12):return True
        except Exception:pass
        time.sleep(.5)
    return False

def old_epoch():
    try:
        s=read_json(SCANNER_STATUS)
        return s.get('epoch') if type(s.get('epoch')) is int else 0
    except Exception:return 0

def stage_ready_for_next_epoch():
    try:
        cert=read_json(REFRESH_CERT)
        stage=BASE/'staged_discovery.json'
        return (cert.get('status')=='CERTIFIED' and 0<=time.time()-cert['at']<=90
                and hash_bytes(stage.read_bytes())==cert.get('stage_sha256'))
    except Exception:return False

def supervise(epochs,seconds,pairs,observe=False,signed_sim=False):
    if not (epochs==0 or 1<=epochs<=100000) or not 150<=seconds<=3600 or not 1<=pairs<=28:
        raise Hold('V12_EPOCH_PARAMETERS_OUT_OF_BOUNDS')
    if signed_sim and not observe:raise Hold('SIGNED_SIM_REQUIRES_EXECUTOR_OBSERVATION')
    if scanner_running():raise Hold('EXISTING_ORACLE322_SCANNER_ACTIVE_DO_NOT_DUPLICATE')
    if not DERIVED.is_file() or DERIVED.is_symlink():raise Hold('V12_DERIVED_SCANNER_NOT_INSTALLED')
    full,inner_sha=make_builder(ORIGINAL.read_bytes())
    if DERIVED.read_bytes()!=full:raise Hold('V12_DERIVED_SCANNER_SHA_DRIFT')
    BASE.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(SUPERVISOR_LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise Hold('V12_SUPERVISOR_ALREADY_RUNNING') from None
    current=0
    try:
        with os.fdopen(fd,'w') as f:f.write(str(os.getpid()))
        while not epochs or current<epochs:
            if scanner_running():raise Hold('V12_SCANNER_LOCK_ACTIVE_BEFORE_EPOCH')
            prior=old_epoch()
            # V10 needs the CURRENT running scanner, so refresh is done during the
            # previous epoch. An older stage is never trusted for Mriya promotion.
            certified_before=stage_ready_for_next_epoch()
            scan=subprocess.Popen([sys.executable,str(DERIVED.name),'--launch','--seconds',str(seconds),'--pairs',str(pairs)],
                cwd=str(ROOT),env=child_env(),stdin=subprocess.DEVNULL)
            watcher=None;refresh_thread=None;refreshed={}
            try:
                if not await_new_scanner(prior,scan):
                    raise Hold('V12_SCANNER_EPOCH_START_NOT_CONFIRMED')
                current+=1
                publish({'build':'FINAL_BOSS_V12','status':'RUNNING_BOUND_EPOCH',
                         'epoch_iteration':current,'previous_scanner_epoch':prior,'scanner_epoch':old_epoch(),
                         'selected_pair_capacity':pairs,'executor_observer_started':observe,
                         'signed_sim_requested':signed_sim,'scanner_pid':scan.pid,
                         'mriya_certificate_available_at_start':certified_before,
                         'rotation_mode':'SINGLE_SOCKET_NEXT_EPOCH_ONLY'})
                if observe:
                    cmd=[sys.executable,'-m',PACKAGE+'final_boss_v11_native_bridge','--observe',
                         '--seconds',str(max(1,min(180,seconds-55)))]
                    if signed_sim:cmd.append('--signed-sim')
                    watcher=subprocess.Popen(cmd,cwd=str(ROOT),env=child_env(sign_sim=signed_sim),stdin=subprocess.DEVNULL)
                def prepare_next_epoch():
                    try:refreshed['result']=refresh()
                    except Exception as e:
                        refreshed['error']=hold_name(e)
                        save_atomic(REFRESH_CERT,json.dumps({'status':'HOLD_MRIYA_UNIVERSAL_CONTINUES',
                                    'at':time.time(),'reason_code':hold_name(e)}).encode())
                scan_started=time.monotonic()
                while scan.poll() is None:
                    # Refresh while the single original scanner remains healthy.
                    # Certificate TTL=90 sec; start within ~65 sec of an epoch ending.
                    if ((epochs==0 or current<epochs) and refresh_thread is None
                            and time.monotonic()-scan_started >= max(5,seconds-65)):
                        refresh_thread=threading.Thread(target=prepare_next_epoch,daemon=True)
                        refresh_thread.start()
                    time.sleep(.75)
                rc=scan.wait()
                if rc:raise Hold('V12_SCANNER_EPOCH_FAILED')
                if SCANNER_LOCK.exists():raise Hold('V12_SCANNER_LOCK_REMAINS_AFTER_EPOCH')
                if refresh_thread is not None:refresh_thread.join(timeout=35)
                if refresh_thread is not None and refresh_thread.is_alive():
                    raise Hold('V12_NEXT_EPOCH_REFRESH_STILL_RUNNING')
                if watcher is not None:
                    try:watcher.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        watcher.terminate();watcher.wait(timeout=10)
                publish({'build':'FINAL_BOSS_V12','status':'EPOCH_COMPLETED',
                         'epoch_iteration':current,'scanner_exit_code':rc,
                         'executor_observer_exit_code':None if watcher is None else watcher.returncode,
                         'next_epoch_mriya_certified':stage_ready_for_next_epoch(),
                         'refresh_hold_code':refreshed.get('error'),
                         'rotation_mode':'SINGLE_SOCKET_NEXT_EPOCH_ONLY'})
            finally:
                if scan.poll() is None:scan.wait()
                if watcher is not None and watcher.poll() is None:
                    watcher.terminate();watcher.wait(timeout=10)
    except KeyboardInterrupt:
        publish({'build':'FINAL_BOSS_V12','status':'OPERATOR_INTERRUPT_NO_FORCED_SCANNER_TERMINATION'})
        return 130
    finally:
        try:SUPERVISOR_LOCK.unlink()
        except OSError:pass
    publish({'build':'FINAL_BOSS_V12','status':'FINISHED','epochs':current})
    return 0

def test():
    assert len(GRID)==19 and GRID[0]==10000000 and GRID[-1]==100000000
    sample='''from pathlib import Path\nSTAGED=Path('file')\ndef select_rows(original):\n    grouped={}\n    rank=2\n    return original\ndef stage_discovery():pass\ndef connect():pass\ndef audit():pass\ndef main():pass\n'''
    patched=inject_scanner(sample)
    # Full original-builder extraction and complete DERIVED builder assembly fixture.
    giant_inner=sample + ('# original scanner source fixture\n'*150)
    fake_outer='SOURCE='+repr(giant_inner)+'\n'
    from unittest.mock import patch
    with patch.dict(globals(),{'EXPECTED_INSTALLER_SHA':hash_bytes(fake_outer.encode()),
                               'EXPECTED_INNER_SHA':hash_bytes(giant_inner.encode())}):
        derived,inner_sha=make_builder(fake_outer.encode())
        derived_ast=ast.parse(derived.decode())
        bound=[n.value.value for n in derived_ast.body if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='SOURCE' for t in n.targets)]
        assert len(bound)==1 and bound[0]==inject_scanner(giant_inner)
        assert inner_sha==hash_bytes(bound[0].encode())
    assert patched.count('def select_rows(original)')==2
    assert patched.index('def select_rows(original)')<patched.index('def stage_discovery()')
    assert 'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW' in patched
    assert 'final_boss_v10_admission_stage' in patched
    assert 'live_subscriptions_changed=False' in patched
    assert WRAPPER.count('accountSubscribe')==0 and WRAPPER.count('accountUnsubscribe')==0
    assert WRAPPER.count('sendTransaction')==0 and WRAPPER.count('sendRawTransaction')==0
    assert hash_bytes(b'test')==hashlib.sha256(b'test').hexdigest()
    # Execute the actual injected selector against mocked V8/V10 certificates.
    import builtins, types
    from unittest.mock import patch
    real_import=builtins.__import__
    tok='A'*40; pum='B'*40; met='C'*40; old='D'*40
    witness={'token':tok,'pump_pool':pum,'meteora_pool':met,'source':'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'}
    v9=types.SimpleNamespace(load_v8=lambda t:{'prospects':[witness]})
    v10=types.SimpleNamespace(select_v8=lambda rep,checker:([witness],0,{}))
    fake=types.SimpleNamespace(final_boss_v9_atomic_simulation_gate=v9,final_boss_v10_admission_stage=v10)
    def stub_import(name,globals=None,locals=None,fromlist=(),level=0):
        if name=='qseries_v2.oracle_execution.solana_atomic_executor' and fromlist:return fake
        return real_import(name,globals,locals,fromlist,level)
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp)/'stage.json'
        stage.write_text(json.dumps({'generated_at':time.time(), 'rows':[witness]}))
        baseline=[{'token':tok,'pump_pool':old,'meteora_pool':met,'sources':['LIVE_TAPE'],'rank':1},
                  {'token':old,'pump_pool':pum,'meteora_pool':met,'sources':['UNIVERSAL'],'rank':3}]
        scope={'STAGED':stage,'emit':lambda k,v:None,'select_rows':lambda rows:list(rows)}
        exec(WRAPPER,scope)
        real_read_text=Path.read_text
        def mocked_read_text(path,*args,**kwargs):
            if path.name=='v12_mriya_refresh_certificate.json':
                return json.dumps({'status':'CERTIFIED','at':time.time()-1,
                    'stage_sha256':hash_bytes(stage.read_bytes())})
            return real_read_text(path,*args,**kwargs)
        with patch('builtins.__import__',side_effect=stub_import), patch.object(Path,'read_text',mocked_read_text):
            got=scope['select_rows'](baseline)
        assert len(got)==2 and got[0]['token']==tok and got[0]['pump_pool']==pum
        assert got[0]['rank']==20 and got[1]['token']==old
        assert scope['STAGED']==stage
        stage.write_text(json.dumps({'generated_at':time.time()-200,'rows':[witness]}))
        with patch('builtins.__import__',side_effect=stub_import), patch.object(Path,'read_text',mocked_read_text):
            fallback=scope['select_rows'](baseline)
        assert fallback==baseline and scope['STAGED']==stage
    print('[PASS] FINAL_BOSS_V12 source-isolated full builder, V8/V10 stage match, original universal discovery, fail-closed, 19 sizes')
    print('[BOUNDARY] Deterministic fixtures only; production scanner epoch and native simulation not claimed')

def main():
    p=argparse.ArgumentParser(description='Final Boss V12 single-socket bounded-epoch replenishment')
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--test',action='store_true')
    group.add_argument('--install',action='store_true')
    group.add_argument('--audit',action='store_true')
    group.add_argument('--run',action='store_true')
    group.add_argument('--prime',action='store_true',help='Refresh V8/V10 while existing scanner is live')
    p.add_argument('--epochs',type=int,default=1,help='0 repeats continuously')
    p.add_argument('--epoch-seconds',type=int,default=240)
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--observe-executor',action='store_true')
    p.add_argument('--signed-sim',action='store_true')
    a=p.parse_args()
    try:
        if a.test:test();return 0
        if a.install:install();return 0
        if a.prime:
            if not scanner_running():raise Hold('V12_PRIME_REQUIRES_RUNNING_ORACLE322')
            refresh();return 0
        if a.audit:
            raw=ORIGINAL.read_bytes();full,inner=make_builder(raw)
            print('[FINAL_BOSS_V12_AUDIT]',json.dumps({'source_guard':'PASS','derived_bytes':len(full),
                  'derived_sha256':hash_bytes(full),'embedded_sha256':inner,
                  'scanner_active':scanner_running(),'pairs_cap':28,'size_grid_count':19,
                  'hot_rotation_live_in_place':False,'epoch_rotation_supported':True,
                  'broadcast':False,'signed_sim_default':False},sort_keys=True));return 0
        return supervise(a.epochs,a.epoch_seconds,a.pairs,a.observe_executor,a.signed_sim)
    except Exception as ex:
        print('[FINAL_BOSS_V12_HOLD]',hold_name(ex),flush=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
