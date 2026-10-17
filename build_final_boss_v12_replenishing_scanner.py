from __future__ import annotations
"""COMPLETE V12 INSTALLER: original ORACLE322 preserved, certified next-epoch selector.
No frozen Q18/Q20/Q25 mutation. Bounded-epoch rotation only; no in-place socket rebinding.
"""
import argparse,hashlib,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODULE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v12_replenishment.py'
SOURCE=(
    'from __future__ import annotations\n'
    '"""Final Boss V12: guarded single-writer scanner epoch replenishment.\n'
    '\n'
    'Recreates a complete ORACLE-322 launcher with one isolated source change:\n'
    'V8/V10-certificate-prioritized select_rows at the next scanner epoch.\n'
    'The original scanner installer and Q18/Q20/Q25 are never replaced.\n'
    'Only ORACLE-322 publishes canonical scanner events; V11 observes them.\n'
    'No websocket is created here; no funded signing or broadcast method exists.\n'
    '"""\n'
    'import argparse\n'
    'import ast\n'
    'import hashlib\n'
    'import json\n'
    'import os\n'
    'import re\n'
    'import subprocess\n'
    'import sys\n'
    'import tempfile\n'
    'import threading\n'
    'import time\n'
    'from pathlib import Path\n'
    '\n'
    'ROOT=Path.cwd()\n'
    "BASE=ROOT/'runtime_state/oracle/final_boss_dual'\n"
    "ORIGINAL=ROOT/'build_oracle_322_scanner_isolated_discovery.py'\n"
    "DERIVED=ROOT/'build_final_boss_v12_scanner_runtime.py'\n"
    "STATUS=BASE/'final_boss_v12_replenishment.json'\n"
    "SUPERVISOR_LOCK=BASE/'v12_supervisor.lock'\n"
    "SCANNER_LOCK=BASE/'scanner.lock'\n"
    "SCANNER_STATUS=BASE/'scanner_status.json'\n"
    "V10_REPORT=BASE/'final_boss_v10_admission_stage.json'\n"
    "REFRESH_CERT=BASE/'v12_mriya_refresh_certificate.json'\n"
    "PACKAGE='qseries_v2.oracle_execution.solana_atomic_executor.'\n"
    "EXPECTED_INSTALLER_SHA='60c9a4d8acc4259a01f37c64332caea6139e49a84a719ada7e7fe4ec17bab57b'\n"
    "EXPECTED_INNER_SHA='e579d68ac26210ef98ba015180126782669144e81fc5eb2010f0d9586ced767c'\n"
    "ADDR=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')\n"
    'GRID=tuple(range(10_000_000,100_000_001,5_000_000))\n'
    '\n'
    'class Hold(RuntimeError):pass\n'
    '\n'
    'def hash_bytes(data):return hashlib.sha256(data).hexdigest()\n'
    "def normalized_bytes(data):return data.replace(b'\\r\\n',b'\\n')\n"
    'def hold_name(err):\n'
    '    s=str(err)\n'
    "    return s if isinstance(err,Hold) and re.fullmatch(r'[A-Z][A-Z0-9_]{3,100}',s) else type(err).__name__.upper()\n"
    '\n'
    'def read_json(path, limit=900000):\n'
    "    if not path.is_file() or path.is_symlink() or path.stat().st_size>limit:raise Hold('REPORT_MISSING_UNTRUSTED_OR_OVERSIZED')\n"
    "    x=json.loads(path.read_text(encoding='utf-8'))\n"
    "    if not isinstance(x,dict):raise Hold('REPORT_OBJECT_REQUIRED')\n"
    '    return x\n'
    '\n'
    'def source_from_original(raw):\n'
    "    if hash_bytes(normalized_bytes(raw))!=EXPECTED_INSTALLER_SHA:raise Hold('ORACLE322_ORIGINAL_INSTALLER_SHA_DRIFT')\n"
    "    tree=ast.parse(raw.decode('utf-8-sig'))\n"
    '    hits=[]\n'
    '    for n in ast.walk(tree):\n'
    '        if isinstance(n,(ast.Assign,ast.AnnAssign)):\n'
    '            targets=n.targets if isinstance(n,ast.Assign) else [n.target]\n'
    "            if not any(isinstance(t,ast.Name) and ('SOURCE' in t.id.upper() or 'SCRIPT' in t.id.upper()) for t in targets):continue\n"
    '            v=n.value\n'
    '            if isinstance(v,ast.Constant) and isinstance(v.value,str) and len(v.value)>3000:hits.append((v,v.value))\n'
    "    if len(hits)!=1:raise Hold('ORACLE322_EMBEDDED_SOURCE_NOT_UNIQUE')\n"
    '    node,inner=hits[0]\n'
    "    if hash_bytes(inner.encode('utf-8'))!=EXPECTED_INNER_SHA:raise Hold('ORACLE322_EMBEDDED_SOURCE_SHA_DRIFT')\n"
    '    tree_inner=ast.parse(inner)\n'
    '    funcs=[n for n in tree_inner.body if isinstance(n,ast.FunctionDef)]\n'
    '    fn={n.name:n for n in funcs}\n'
    "    if not {'select_rows','stage_discovery','connect','audit'}.issubset(fn):raise Hold('ORACLE322_SCANNER_INTERFACE_DRIFT')\n"
    "    if 'rank' not in ast.get_source_segment(inner,fn['select_rows']):raise Hold('ORACLE322_RANKING_INTERFACE_CHANGED')\n"
    '    return node,inner,fn\n'
    '\n'
    '# The wrapper is injected as a *complete new function* immediately after the original\n'
    '# select_rows. It retains the original function and delegates universal discovery to it.\n'
    '# The staged Mriya overlay is admitted only when both V8 and V10 agree at startup.\n'
    "WRAPPER = r'''\n"
    '_v12_original_select_rows = select_rows\n'
    '\n'
    'def select_rows(original):\n'
    '    global STAGED\n'
    '    import pathlib as _v12_pathlib\n'
    '    import time as _v12_time\n'
    '    import json as _v12_json\n'
    '    _v12_before = STAGED\n'
    '    try:\n'
    '        # Never allow unchecked historical V8 staged rows into the baseline.\n'
    "        STAGED = _v12_pathlib.Path('runtime_state/oracle/final_boss_dual/v12_ignored_legacy_stage.json')\n"
    '    except Exception:\n'
    '        STAGED = _v12_before\n'
    '    try:\n'
    '        _v12_baseline = _v12_original_select_rows(original)\n'
    '    finally:\n'
    '        STAGED = _v12_before\n'
    '    try:\n'
    '        from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v10_admission_stage as _v12_v10\n'
    '        from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v9_atomic_simulation_gate as _v12_v9\n'
    '        _v12_now = _v12_time.time()\n'
    '        _v12_raw=_v12_before.read_bytes()\n'
    "        _v12_doc = _v12_json.loads(_v12_raw.decode('utf-8'))\n"
    "        _v12_cert=_v12_json.loads(_v12_pathlib.Path('runtime_state/oracle/final_boss_dual/v12_mriya_refresh_certificate.json').read_text(encoding='utf-8'))\n"
    '        import hashlib as _v12_hashlib\n'
    "        if (not isinstance(_v12_cert,dict) or _v12_cert.get('status')!='CERTIFIED'\n"
    "                or _v12_cert.get('stage_sha256')!=_v12_hashlib.sha256(_v12_raw).hexdigest()\n"
    "                or not 0<=_v12_now-float(_v12_cert.get('at',0))<=90):\n"
    "            raise ValueError('V12_FRESH_STAGE_CERTIFICATE_NOT_VALID')\n"
    "        if not isinstance(_v12_doc,dict) or not 0 <= _v12_now-float(_v12_doc['generated_at']) <= 120:\n"
    "            raise ValueError('V12_STAGED_FEED_STALE')\n"
    '        _v12_source = _v12_v9.load_v8(_v12_now)\n'
    '        _v12_rows,_v12_alt,_v12_holds = _v12_v10.select_v8(_v12_source,_v12_v9)\n'
    "        _v12_stage=[r for r in _v12_doc.get('rows',[]) if isinstance(r,dict) and r.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW']\n"
    "        _v12_key=lambda x:(x['token'],x['pump_pool'],x['meteora_pool'])\n"
    '        if (not _v12_rows or len(_v12_rows)>28 or len(_v12_stage)!=len(_v12_rows)\n'
    '                or {_v12_key(r) for r in _v12_rows}!={_v12_key(r) for r in _v12_stage}):\n'
    "            raise ValueError('V12_FRESH_V8_STAGE_TRIPLE_MISMATCH')\n"
    '        _v12_added=[]\n'
    '        _v12_seen=set()\n'
    '        for _v12_r in _v12_rows:\n'
    '            _v12_t,_v12_p,_v12_d=_v12_key(_v12_r)\n'
    '            if (not all(isinstance(x,str) and 32<=len(x)<=44 for x in (_v12_t,_v12_p,_v12_d))\n'
    '                    or len({_v12_t,_v12_p,_v12_d})!=3 or _v12_t in _v12_seen):\n'
    "                raise ValueError('V12_INVALID_STAGED_EXACT_TRIPLE')\n"
    '            _v12_seen.add(_v12_t)\n'
    "            _v12_added.append(dict(_v12_r,rank=20,sources=['MRIYA'],v12_admission='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM'))\n"
    "        _v12_result=(_v12_added + [r for r in _v12_baseline if r.get('token') not in _v12_seen])[:112]\n"
    "        emit('BOSS_V12_DISCOVERY_SELECTION',dict(v8_selected=len(_v12_added),baseline_tokens=len(_v12_baseline),\n"
    "             final_candidates=len(_v12_result),new_distinct_tokens=sum(r['token'] not in {x['token'] for x in _v12_baseline} for r in _v12_added),\n"
    '             live_subscriptions_changed=False,simulation_authority=False))\n'
    '        return _v12_result\n'
    '    except Exception as _v12_exc:\n'
    '        # Never admit unverified V8 rows or bypass risk; universal discovery stays live.\n'
    "        emit('BOSS_V12_MRIYA_HOLD',dict(code=type(_v12_exc).__name__,\n"
    '             baseline_candidates=len(_v12_baseline),live_subscriptions_changed=False))\n'
    '        return _v12_baseline\n'
    "'''\n"
    '\n'
    'def inject_scanner(inner):\n'
    '    t=ast.parse(inner)\n'
    "    funcs=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='select_rows']\n"
    "    if len(funcs)!=1:raise Hold('SCANNER_SELECT_ROWS_COUNT_CHANGED')\n"
    '    f=funcs[0]\n'
    '    lines=inner.splitlines(keepends=True)\n'
    '    # insert AFTER original select_rows, BEFORE following helper declarations\n'
    "    lines.insert(f.end_lineno, '\\n'+WRAPPER.strip('\\n')+'\\n\\n')\n"
    "    modified=''.join(lines)\n"
    '    ast.parse(modified)\n'
    "    compile(modified,'<oracle322-v12-embedded-scanner>','exec')\n"
    '    # This must not modify Q25, Q20, Q18, main, the canonical bus, or 19-size pricing.\n'
    "    assert 'def select_rows(original)' in modified and modified.count('def select_rows(original)')==2\n"
    '    return modified\n'
    '\n'
    'def offset(lines,line,col):return sum(len(x) for x in lines[:line-1])+col\n'
    '\n'
    'def make_builder(original_bytes):\n'
    '    node,inner,fn=source_from_original(original_bytes)\n'
    '    new=inject_scanner(inner)\n'
    "    outer=original_bytes.decode('utf-8-sig')\n"
    '    lines=outer.splitlines(keepends=True)\n'
    '    a=offset(lines,node.lineno,node.col_offset);b=offset(lines,node.end_lineno,node.end_col_offset)\n'
    '    rebuilt=outer[:a]+repr(new)+outer[b:]\n'
    '    ast.parse(rebuilt)\n'
    "    compile(rebuilt,'<final_boss_v12_derived_builder>','exec')\n"
    '    # Ensure the only changed outer AST element is the embedded source constant.\n'
    '    baseline=ast.parse(outer);upgraded=ast.parse(rebuilt)\n'
    '    def scrub(tree):\n'
    '        for n in ast.walk(tree):\n'
    '            if isinstance(n,(ast.Assign,ast.AnnAssign)):\n'
    '                if isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and hash_bytes(n.value.value.encode()) in (EXPECTED_INNER_SHA,hash_bytes(new.encode())):\n'
    "                    n.value.value='<SCANNER_SOURCE>'\n"
    '        return ast.dump(tree,include_attributes=False)\n'
    "    if scrub(baseline)!=scrub(upgraded):raise Hold('ORACLE322_DERIVED_BUILDER_UNRELATED_CHANGE')\n"
    "    return rebuilt.encode('utf-8'),hash_bytes(new.encode())\n"
    '\n'
    'def save_atomic(path,data):\n'
    '    path.parent.mkdir(parents=True,exist_ok=True)\n'
    "    with tempfile.NamedTemporaryFile('wb',dir=path.parent,suffix='.tmp',delete=False) as fp:\n"
    '        fp.write(data);temp=Path(fp.name)\n'
    '    try:os.replace(temp,path)\n'
    '    finally:temp.unlink(missing_ok=True)\n'
    '\n'
    'def install():\n'
    "    if ORIGINAL.is_symlink() or not ORIGINAL.is_file():raise Hold('ORACLE322_ORIGINAL_MISSING')\n"
    '    upgraded,inner_sha=make_builder(ORIGINAL.read_bytes())\n'
    "    if DERIVED.is_symlink():raise Hold('V12_DERIVED_BUILDER_IS_LINK')\n"
    '    if DERIVED.exists():\n'
    "        if DERIVED.read_bytes()!=upgraded:raise Hold('V12_DERIVED_BUILDER_ALREADY_MODIFIED')\n"
    '    else:save_atomic(DERIVED,upgraded)\n'
    '    # Complete self-module is installed exactly; do not modify the scanner original.\n'
    "    target=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v12_replenishment.py'\n"
    '    source=Path(__file__).read_bytes()\n'
    "    if target.is_symlink():raise Hold('V12_MODULE_IS_LINK')\n"
    '    if target.exists():\n'
    "        if normalized_bytes(target.read_bytes())!=normalized_bytes(source):raise Hold('V12_INSTALLED_MODULE_DRIFT')\n"
    '    else:save_atomic(target,source)\n'
    "    print('[INSTALLED] FINAL_BOSS_V12_SCANNER_DERIVED_FULL_BUILDER')\n"
    "    print('[GENERATED]',DERIVED)\n"
    "    print('[EMBEDDED_SHA256]',inner_sha)\n"
    "    print('[PRESERVED] original ORACLE322 installer, Q18/Q20/Q25, bus, V9/V11/402')\n"
    "    print('[SCOPE] Single-socket bounded-epoch replenishment; no in-place WS rotation; no broadcast')\n"
    '\n'
    'def scanner_running():\n'
    '    if SCANNER_LOCK.exists():return True\n'
    '    try:\n'
    '        status=read_json(SCANNER_STATUS)\n'
    "        return status.get('status')=='RUNNING' and 0<=time.time()-SCANNER_STATUS.stat().st_mtime<=15\n"
    '    except Exception:return False\n'
    '\n'
    'def child_env(sign_sim=False):\n'
    '    e=os.environ.copy()\n'
    '    if not sign_sim:\n'
    '        for k in list(e):\n'
    "            if any(s in k.upper() for s in ('PRIVATE_KEY','MNEMONIC','KEYPAIR','SEED_PHRASE','SECRET')):e.pop(k,None)\n"
    '    return e\n'
    '\n'
    'def rpc_ready():\n'
    "    url=os.environ.get('SOLANA_RPC_URL','')\n"
    "    return url.startswith('https://') and 20<len(url)<1024\n"
    '\n'
    'def fresh_stage():\n'
    '    d=read_json(V10_REPORT)\n'
    "    if d.get('stage_written') is not True or d.get('status')!='STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE':\n"
    "        raise Hold('V10_STAGE_NOT_COMMITTED')\n"
    "    if d.get('scanner',{}).get('epoch') is None:raise Hold('V10_STAGE_EPOCH_MISSING')\n"
    '    return d\n'
    '\n'
    'def run_one(cmd,env):\n'
    '    return subprocess.call([sys.executable,*cmd],env=env,cwd=str(ROOT))\n'
    '\n'
    'def refresh():\n'
    "    if not rpc_ready():raise Hold('SOLANA_RPC_URL_REQUIRED_HIDDEN_KEY_NOT_ON_COMMAND_LINE')\n"
    '    env=child_env()\n'
    '    # Fail closed for Mriya admission, not for existing independent universal discovery.\n'
    '    # A quiet Mriya wallet must never kill the healthy universal scanning lane.\n'
    "    status='CERTIFIED';failed_at='NONE'\n"
    "    for mod,flag in [('final_boss_mriya_rpc_replenishment','--once'),\n"
    "                     ('final_boss_mriya_crossvenue_discovery','--once'),\n"
    "                     ('final_boss_v10_admission_stage','--stage')]:\n"
    "        if run_one(['-m',PACKAGE+mod,flag],env):\n"
    "            status='UNIVERSAL_ONLY';failed_at=mod;break\n"
    "    if status=='CERTIFIED':\n"
    '        try:\n'
    '            fresh_stage()\n'
    "            source=(BASE/'staged_discovery.json').read_bytes()\n"
    "            cert={'status':'CERTIFIED','at':time.time(),'stage_sha256':hash_bytes(source)}\n"
    '        except (OSError,ValueError,Hold):\n'
    "            status='UNIVERSAL_ONLY';failed_at='STAGE_CERTIFICATION'\n"
    "    if status!='CERTIFIED':\n"
    "        cert={'status':'HOLD_MRIYA_UNIVERSAL_CONTINUES','at':time.time(),\n"
    "              'reason_code':failed_at.split('.')[-1].upper()}\n"
    '    save_atomic(REFRESH_CERT,json.dumps(cert,sort_keys=True).encode())\n'
    "    print('[FINAL_BOSS_V12_DISCOVERY_REFRESH]',json.dumps({\n"
    "          'mriya':'CERTIFIED_FOR_NEXT_EPOCH' if status=='CERTIFIED' else 'HOLD_UNIVERSAL_DISCOVERY_ONLY',\n"
    "          'rpc_key_displayed':False,'broadcast':False},sort_keys=True),flush=True)\n"
    '    return cert\n'
    '\n'
    'def publish(obj):\n'
    '    o=dict(obj)\n'
    '    o.update(broadcast=False,funded_execution_authority=False,\n'
    '             original_scanner_installer_modified=False,derived_scanner_source_used=True,additional_websockets_by_supervisor=0,\n'
    '             size_grid_count=len(GRID),trade_sizes_simulated=[])\n'
    '    save_atomic(STATUS,json.dumps(o,sort_keys=True,indent=2).encode())\n'
    "    print('[FINAL_BOSS_V12_REPLENISHMENT]',json.dumps(o,sort_keys=True),flush=True)\n"
    '\n'
    'def await_new_scanner(previous_epoch,proc,timeout=55):\n'
    '    until=time.monotonic()+timeout\n'
    '    while time.monotonic()<until:\n'
    '        if proc.poll() is not None:return False\n'
    '        try:\n'
    '            s=read_json(SCANNER_STATUS)\n'
    "            if (s.get('status')=='RUNNING' and type(s.get('epoch')) is int\n"
    "                    and s['epoch']>previous_epoch and time.time()-SCANNER_STATUS.stat().st_mtime<=12):return True\n"
    '        except Exception:pass\n'
    '        time.sleep(.5)\n'
    '    return False\n'
    '\n'
    'def old_epoch():\n'
    '    try:\n'
    '        s=read_json(SCANNER_STATUS)\n'
    "        return s.get('epoch') if type(s.get('epoch')) is int else 0\n"
    '    except Exception:return 0\n'
    '\n'
    'def stage_ready_for_next_epoch():\n'
    '    try:\n'
    '        cert=read_json(REFRESH_CERT)\n'
    "        stage=BASE/'staged_discovery.json'\n"
    "        return (cert.get('status')=='CERTIFIED' and 0<=time.time()-cert['at']<=90\n"
    "                and hash_bytes(stage.read_bytes())==cert.get('stage_sha256'))\n"
    '    except Exception:return False\n'
    '\n'
    'def supervise(epochs,seconds,pairs,observe=False,signed_sim=False):\n'
    '    if not (epochs==0 or 1<=epochs<=100000) or not 150<=seconds<=3600 or not 1<=pairs<=28:\n'
    "        raise Hold('V12_EPOCH_PARAMETERS_OUT_OF_BOUNDS')\n"
    "    if signed_sim and not observe:raise Hold('SIGNED_SIM_REQUIRES_EXECUTOR_OBSERVATION')\n"
    "    if scanner_running():raise Hold('EXISTING_ORACLE322_SCANNER_ACTIVE_DO_NOT_DUPLICATE')\n"
    "    if not DERIVED.is_file() or DERIVED.is_symlink():raise Hold('V12_DERIVED_SCANNER_NOT_INSTALLED')\n"
    '    full,inner_sha=make_builder(ORIGINAL.read_bytes())\n'
    "    if DERIVED.read_bytes()!=full:raise Hold('V12_DERIVED_SCANNER_SHA_DRIFT')\n"
    '    BASE.mkdir(parents=True,exist_ok=True)\n'
    '    try:fd=os.open(SUPERVISOR_LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)\n'
    "    except FileExistsError:raise Hold('V12_SUPERVISOR_ALREADY_RUNNING') from None\n"
    '    current=0\n'
    '    try:\n'
    "        with os.fdopen(fd,'w') as f:f.write(str(os.getpid()))\n"
    '        while not epochs or current<epochs:\n'
    "            if scanner_running():raise Hold('V12_SCANNER_LOCK_ACTIVE_BEFORE_EPOCH')\n"
    '            prior=old_epoch()\n'
    '            # V10 needs the CURRENT running scanner, so refresh is done during the\n'
    '            # previous epoch. An older stage is never trusted for Mriya promotion.\n'
    '            certified_before=stage_ready_for_next_epoch()\n'
    "            scan=subprocess.Popen([sys.executable,str(DERIVED.name),'--launch','--seconds',str(seconds),'--pairs',str(pairs)],\n"
    '                cwd=str(ROOT),env=child_env(),stdin=subprocess.DEVNULL)\n'
    '            watcher=None;refresh_thread=None;refreshed={}\n'
    '            try:\n'
    '                if not await_new_scanner(prior,scan):\n'
    "                    raise Hold('V12_SCANNER_EPOCH_START_NOT_CONFIRMED')\n"
    '                current+=1\n'
    "                publish({'build':'FINAL_BOSS_V12','status':'RUNNING_BOUND_EPOCH',\n"
    "                         'epoch_iteration':current,'previous_scanner_epoch':prior,'scanner_epoch':old_epoch(),\n"
    "                         'selected_pair_capacity':pairs,'executor_observer_started':observe,\n"
    "                         'signed_sim_requested':signed_sim,'scanner_pid':scan.pid,\n"
    "                         'mriya_certificate_available_at_start':certified_before,\n"
    "                         'rotation_mode':'SINGLE_SOCKET_NEXT_EPOCH_ONLY'})\n"
    '                if observe:\n'
    "                    cmd=[sys.executable,'-m',PACKAGE+'final_boss_v11_native_bridge','--observe',\n"
    "                         '--seconds',str(max(1,min(180,seconds-55)))]\n"
    "                    if signed_sim:cmd.append('--signed-sim')\n"
    '                    watcher=subprocess.Popen(cmd,cwd=str(ROOT),env=child_env(sign_sim=signed_sim),stdin=subprocess.DEVNULL)\n'
    '                def prepare_next_epoch():\n'
    "                    try:refreshed['result']=refresh()\n"
    '                    except Exception as e:\n'
    "                        refreshed['error']=hold_name(e)\n"
    "                        save_atomic(REFRESH_CERT,json.dumps({'status':'HOLD_MRIYA_UNIVERSAL_CONTINUES',\n"
    "                                    'at':time.time(),'reason_code':hold_name(e)}).encode())\n"
    '                scan_started=time.monotonic()\n'
    '                while scan.poll() is None:\n'
    '                    # Refresh while the single original scanner remains healthy.\n'
    '                    # Certificate TTL=90 sec; start within ~65 sec of an epoch ending.\n'
    '                    if ((epochs==0 or current<epochs) and refresh_thread is None\n'
    '                            and time.monotonic()-scan_started >= max(5,seconds-65)):\n'
    '                        refresh_thread=threading.Thread(target=prepare_next_epoch,daemon=True)\n'
    '                        refresh_thread.start()\n'
    '                    time.sleep(.75)\n'
    '                rc=scan.wait()\n'
    "                if rc:raise Hold('V12_SCANNER_EPOCH_FAILED')\n"
    "                if SCANNER_LOCK.exists():raise Hold('V12_SCANNER_LOCK_REMAINS_AFTER_EPOCH')\n"
    '                if refresh_thread is not None:refresh_thread.join(timeout=35)\n'
    '                if refresh_thread is not None and refresh_thread.is_alive():\n'
    "                    raise Hold('V12_NEXT_EPOCH_REFRESH_STILL_RUNNING')\n"
    '                if watcher is not None:\n'
    '                    try:watcher.wait(timeout=15)\n'
    '                    except subprocess.TimeoutExpired:\n'
    '                        watcher.terminate();watcher.wait(timeout=10)\n'
    "                publish({'build':'FINAL_BOSS_V12','status':'EPOCH_COMPLETED',\n"
    "                         'epoch_iteration':current,'scanner_exit_code':rc,\n"
    "                         'executor_observer_exit_code':None if watcher is None else watcher.returncode,\n"
    "                         'next_epoch_mriya_certified':stage_ready_for_next_epoch(),\n"
    "                         'refresh_hold_code':refreshed.get('error'),\n"
    "                         'rotation_mode':'SINGLE_SOCKET_NEXT_EPOCH_ONLY'})\n"
    '            finally:\n'
    '                if scan.poll() is None:scan.wait()\n'
    '                if watcher is not None and watcher.poll() is None:\n'
    '                    watcher.terminate();watcher.wait(timeout=10)\n'
    '    except KeyboardInterrupt:\n'
    "        publish({'build':'FINAL_BOSS_V12','status':'OPERATOR_INTERRUPT_NO_FORCED_SCANNER_TERMINATION'})\n"
    '        return 130\n'
    '    finally:\n'
    '        try:SUPERVISOR_LOCK.unlink()\n'
    '        except OSError:pass\n'
    "    publish({'build':'FINAL_BOSS_V12','status':'FINISHED','epochs':current})\n"
    '    return 0\n'
    '\n'
    'def test():\n'
    '    assert len(GRID)==19 and GRID[0]==10000000 and GRID[-1]==100000000\n'
    "    sample='''from pathlib import Path\\nSTAGED=Path('file')\\ndef select_rows(original):\\n    grouped={}\\n    rank=2\\n    return original\\ndef stage_discovery():pass\\ndef connect():pass\\ndef audit():pass\\ndef main():pass\\n'''\n"
    '    patched=inject_scanner(sample)\n'
    '    # Full original-builder extraction and complete DERIVED builder assembly fixture.\n'
    "    giant_inner=sample + ('# original scanner source fixture\\n'*150)\n"
    "    fake_outer='SOURCE='+repr(giant_inner)+'\\n'\n"
    '    from unittest.mock import patch\n'
    "    with patch.dict(globals(),{'EXPECTED_INSTALLER_SHA':hash_bytes(fake_outer.encode()),\n"
    "                               'EXPECTED_INNER_SHA':hash_bytes(giant_inner.encode())}):\n"
    '        derived,inner_sha=make_builder(fake_outer.encode())\n'
    '        derived_ast=ast.parse(derived.decode())\n'
    '        bound=[n.value.value for n in derived_ast.body if isinstance(n,ast.Assign)\n'
    "               and any(isinstance(t,ast.Name) and t.id=='SOURCE' for t in n.targets)]\n"
    '        assert len(bound)==1 and bound[0]==inject_scanner(giant_inner)\n'
    '        assert inner_sha==hash_bytes(bound[0].encode())\n'
    "    assert patched.count('def select_rows(original)')==2\n"
    "    assert patched.index('def select_rows(original)')<patched.index('def stage_discovery()')\n"
    "    assert 'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW' in patched\n"
    "    assert 'final_boss_v10_admission_stage' in patched\n"
    "    assert 'live_subscriptions_changed=False' in patched\n"
    "    assert WRAPPER.count('accountSubscribe')==0 and WRAPPER.count('accountUnsubscribe')==0\n"
    "    assert WRAPPER.count('sendTransaction')==0 and WRAPPER.count('sendRawTransaction')==0\n"
    "    assert hash_bytes(b'test')==hashlib.sha256(b'test').hexdigest()\n"
    '    # Execute the actual injected selector against mocked V8/V10 certificates.\n'
    '    import builtins, types\n'
    '    from unittest.mock import patch\n'
    '    real_import=builtins.__import__\n'
    "    tok='A'*40; pum='B'*40; met='C'*40; old='D'*40\n"
    "    witness={'token':tok,'pump_pool':pum,'meteora_pool':met,'source':'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'}\n"
    "    v9=types.SimpleNamespace(load_v8=lambda t:{'prospects':[witness]})\n"
    '    v10=types.SimpleNamespace(select_v8=lambda rep,checker:([witness],0,{}))\n'
    '    fake=types.SimpleNamespace(final_boss_v9_atomic_simulation_gate=v9,final_boss_v10_admission_stage=v10)\n'
    '    def stub_import(name,globals=None,locals=None,fromlist=(),level=0):\n'
    "        if name=='qseries_v2.oracle_execution.solana_atomic_executor' and fromlist:return fake\n"
    '        return real_import(name,globals,locals,fromlist,level)\n'
    '    with tempfile.TemporaryDirectory() as tmp:\n'
    "        stage=Path(tmp)/'stage.json'\n"
    "        stage.write_text(json.dumps({'generated_at':time.time(), 'rows':[witness]}))\n"
    "        baseline=[{'token':tok,'pump_pool':old,'meteora_pool':met,'sources':['LIVE_TAPE'],'rank':1},\n"
    "                  {'token':old,'pump_pool':pum,'meteora_pool':met,'sources':['UNIVERSAL'],'rank':3}]\n"
    "        scope={'STAGED':stage,'emit':lambda k,v:None,'select_rows':lambda rows:list(rows)}\n"
    '        exec(WRAPPER,scope)\n'
    '        real_read_text=Path.read_text\n'
    '        def mocked_read_text(path,*args,**kwargs):\n'
    "            if path.name=='v12_mriya_refresh_certificate.json':\n"
    "                return json.dumps({'status':'CERTIFIED','at':time.time()-1,\n"
    "                    'stage_sha256':hash_bytes(stage.read_bytes())})\n"
    '            return real_read_text(path,*args,**kwargs)\n'
    "        with patch('builtins.__import__',side_effect=stub_import), patch.object(Path,'read_text',mocked_read_text):\n"
    "            got=scope['select_rows'](baseline)\n"
    "        assert len(got)==2 and got[0]['token']==tok and got[0]['pump_pool']==pum\n"
    "        assert got[0]['rank']==20 and got[1]['token']==old\n"
    "        assert scope['STAGED']==stage\n"
    "        stage.write_text(json.dumps({'generated_at':time.time()-200,'rows':[witness]}))\n"
    "        with patch('builtins.__import__',side_effect=stub_import), patch.object(Path,'read_text',mocked_read_text):\n"
    "            fallback=scope['select_rows'](baseline)\n"
    "        assert fallback==baseline and scope['STAGED']==stage\n"
    "    print('[PASS] FINAL_BOSS_V12 source-isolated full builder, V8/V10 stage match, original universal discovery, fail-closed, 19 sizes')\n"
    "    print('[BOUNDARY] Deterministic fixtures only; production scanner epoch and native simulation not claimed')\n"
    '\n'
    'def main():\n'
    "    p=argparse.ArgumentParser(description='Final Boss V12 single-socket bounded-epoch replenishment')\n"
    '    group=p.add_mutually_exclusive_group(required=True)\n'
    "    group.add_argument('--test',action='store_true')\n"
    "    group.add_argument('--install',action='store_true')\n"
    "    group.add_argument('--audit',action='store_true')\n"
    "    group.add_argument('--run',action='store_true')\n"
    "    group.add_argument('--prime',action='store_true',help='Refresh V8/V10 while existing scanner is live')\n"
    "    p.add_argument('--epochs',type=int,default=1,help='0 repeats continuously')\n"
    "    p.add_argument('--epoch-seconds',type=int,default=240)\n"
    "    p.add_argument('--pairs',type=int,default=28)\n"
    "    p.add_argument('--observe-executor',action='store_true')\n"
    "    p.add_argument('--signed-sim',action='store_true')\n"
    '    a=p.parse_args()\n'
    '    try:\n'
    '        if a.test:test();return 0\n'
    '        if a.install:install();return 0\n'
    '        if a.prime:\n'
    "            if not scanner_running():raise Hold('V12_PRIME_REQUIRES_RUNNING_ORACLE322')\n"
    '            refresh();return 0\n'
    '        if a.audit:\n'
    '            raw=ORIGINAL.read_bytes();full,inner=make_builder(raw)\n'
    "            print('[FINAL_BOSS_V12_AUDIT]',json.dumps({'source_guard':'PASS','derived_bytes':len(full),\n"
    "                  'derived_sha256':hash_bytes(full),'embedded_sha256':inner,\n"
    "                  'scanner_active':scanner_running(),'pairs_cap':28,'size_grid_count':19,\n"
    "                  'hot_rotation_live_in_place':False,'epoch_rotation_supported':True,\n"
    "                  'broadcast':False,'signed_sim_default':False},sort_keys=True));return 0\n"
    '        return supervise(a.epochs,a.epoch_seconds,a.pairs,a.observe_executor,a.signed_sim)\n'
    '    except Exception as ex:\n'
    "        print('[FINAL_BOSS_V12_HOLD]',hold_name(ex),flush=True)\n"
    '        return 2\n'
    "if __name__=='__main__':raise SystemExit(main())\n"
)
EXPECTED_MODULE_SHA='f17a4c5903dd22a02b293c802bc0ab3637209bbb70d63381f54cc6a292cda2ec'

def write_atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False,suffix='.tmp') as fp:
        fp.write(raw);p=Path(fp.name)
    try:os.replace(p,path)
    finally:p.unlink(missing_ok=True)

def run(flags):
    want=SOURCE.encode('utf-8')
    if hashlib.sha256(want).hexdigest()!=EXPECTED_MODULE_SHA:
        print('[HOLD] V12 installer source SHA drift');return 2
    compile(SOURCE,str(MODULE),'exec')
    if flags=='--test':
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'v12_test.py';p.write_bytes(want)
            return subprocess.call([sys.executable,str(p),'--test'],cwd=str(ROOT))
    if not (ROOT/'build_oracle_322_scanner_isolated_discovery.py').is_file():
        print('[HOLD] ORACLE322 installer absent');return 2
    if MODULE.is_symlink():print('[HOLD] V12 module is a symlink');return 2
    if MODULE.exists():
        if MODULE.read_bytes().replace(b'\r\n',b'\n') != want:
            print('[HOLD] V12 installed module differs; refused overwrite');return 2
    else:write_atomic(MODULE,want)
    return subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.final_boss_v12_replenishment',flags],cwd=str(ROOT))

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--install',action='store_true');g.add_argument('--audit',action='store_true')
    a=p.parse_args()
    return run('--test' if a.test else '--install' if a.install else '--audit')
if __name__=='__main__':raise SystemExit(main())
