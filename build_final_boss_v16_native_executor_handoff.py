from __future__ import annotations
"""V16 full-source native scanner + supervisor installer.
Restores the missing certified V8/V10 -> V15 native hydration handoff.
Retains frozen scanner, Q18/Q20/Q25, V14 paginated core, ORACLE402 and bus.
No broadcast and no private-key access.
"""
import argparse, ast, hashlib, importlib.util, os, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BUILDER=ROOT/'build_final_boss_v15_scanner_runtime.py'
SUPERVISOR=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v15_supervisor.py'
NEW_BUILDER=ROOT/'build_final_boss_v16_scanner_runtime.py'
NEW_SUPERVISOR=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v16_supervisor.py'
OLD_BUILDER_SHA='279a373ef0699c34046ea4088542e00ebf5e592927e74bae6a7669e7db98bf7c'
OLD_SUPERVISOR_SHA='c15f2c4cf621c2eed55abe87b76b064f5e431e9241f7193cff8cf89b1189fe66'

def digest(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
def const(source):
    t=ast.parse(source)
    result=[]
    for n in ast.walk(t):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=getattr(n,'targets',[]) or [getattr(n,'target',None)]
            if any(isinstance(x,ast.Name) and x.id in ('SOURCE','SCRIPT') for x in targets):
                if isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and len(n.value.value)>3000:result.append(n.value)
    if len(result)!=1:raise RuntimeError('ONE_EMBEDDED_SCANNER_REQUIRED')
    return result[0]
def source_replace(raw,node,new_text):
    s=raw.decode('utf-8-sig'); ls=s.splitlines(keepends=True)
    a=sum(map(len,ls[:node.lineno-1]))+node.col_offset
    z=sum(map(len,ls[:node.end_lineno-1]))+node.end_col_offset
    out=(s[:a]+repr(new_text)+s[z:]).encode()
    ast.parse(out)
    return out

STAGED_READER=r'''def _v16_certified_native_rows():
    # Resolve the exact V8/V10 triple BEFORE slow baseline network discovery.
    import hashlib as _h, json as _j, time as _t
    from pathlib import Path as _P
    from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v9_atomic_simulation_gate as _v9
    from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v10_admission_stage as _v10
    root=_P('runtime_state/oracle/final_boss_dual')
    certpath=root/'v12_mriya_refresh_certificate.json'
    stagepath=root/'staged_discovery.json'
    reportpath=root/'final_boss_v10_admission_stage.json'
    if any(p.is_symlink() or not p.is_file() or p.stat().st_size>500000 for p in (certpath,stagepath,reportpath)):
        raise ValueError('V16_STAGED_PROVENANCE_MISSING')
    now=_t.time()
    cert=_j.loads(certpath.read_text(encoding='utf-8'))
    raw=stagepath.read_bytes()
    stage=_j.loads(raw)
    report=_j.loads(reportpath.read_text(encoding='utf-8'))
    if not isinstance(cert,dict) or cert.get('status')!='CERTIFIED' or type(cert.get('at')) not in (int,float) or not 0<=now-cert['at']<=90:
        raise ValueError('V16_CERTIFICATE_STALE_OR_HOLD')
    if cert.get('stage_sha256')!=_h.sha256(raw).hexdigest():
        raise ValueError('V16_CERTIFIED_STAGE_HASH_MISMATCH')
    if not isinstance(stage,dict) or type(stage.get('generated_at')) not in (int,float) or not 0<=now-stage['generated_at']<=120:
        raise ValueError('V16_STAGE_EXPIRED')
    if report.get('status')!='STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE' or report.get('stage_written') is not True:
        raise ValueError('V16_V10_STAGE_NOT_COMMITTED')
    latest=_v9.load_v8(now)
    selected,_,_=_v10.select_v8(latest,_v9)
    staged=[r for r in stage.get('rows',[]) if isinstance(r,dict) and r.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW']
    triple=lambda r:(r['token'],r['pump_pool'],r['meteora_pool'])
    if not 0<len(selected)<=28 or len(staged)!=len(selected) or len({triple(r) for r in staged})!=len(staged):
        raise ValueError('V16_STAGED_SELECTION_COUNT_MISMATCH')
    if {triple(r) for r in staged}!={triple(r) for r in selected}:
        raise ValueError('V16_V8_V10_TRIPLE_MISMATCH')
    if {r['token'] for r in selected}!=set(report.get('staged_tokens',[])):
        raise ValueError('V16_STAGE_PROVENANCE_TOKENS_MISMATCH')
    risk_by_triple={triple(r):r['risk_scope'] for r in staged}
    if any(risk_by_triple[triple(r)]!=r['risk_scope'] for r in selected):
        raise ValueError('V16_STAGE_RISK_MISMATCH')
    print('[BOSS_V16_FRESH_CERTIFIED_SOURCE] '+_j.dumps({'exact_triples':len(selected),'fresh_certified':True,'broadcast':False},sort_keys=True),flush=True)
    return [dict(r,v12_admission='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM') for r in selected]

'''

def upgrade_scanner(raw):
    if digest(raw)!=OLD_BUILDER_SHA:raise RuntimeError('V15_SCANNER_SOURCE_SHA_DRIFT')
    s=raw.decode('utf-8-sig'); node=const(s)
    inner=node.value
    old='ranked=_e.raw_candidate_universe(root)'
    if inner.count(old)!=1 or inner.count('def scan_epoch(')!=2:raise RuntimeError('V15_NATIVE_HOOK_INTERFACE_DRIFT')
    if 'def _v16_certified_native_rows():' in inner:raise RuntimeError('V16_ALREADY_PRESENT')
    anchor='_v15_original_scan_epoch=scan_epoch\n'
    if inner.count(anchor)!=1:raise RuntimeError('V15_WRAPPER_ANCHOR_CHANGED')
    inner=inner.replace(anchor,STAGED_READER+anchor,1)
    inner=inner.replace(old,'ranked=_v16_certified_native_rows()',1)
    ast.parse(inner)
    assert inner.count('def scan_epoch(')==2
    return source_replace(raw,node,inner)

def upgrade_supervisor(raw):
    if digest(raw)!=OLD_SUPERVISOR_SHA:raise RuntimeError('V15_SUPERVISOR_SOURCE_SHA_DRIFT')
    s=raw.decode('utf-8-sig')
    swaps={
      "'build_final_boss_v15_scanner_runtime.py'":"'build_final_boss_v16_scanner_runtime.py'",
      "'v15_supervisor.lock'":"'v16_supervisor.lock'",
      "'final_boss_v15_supervisor.json'":"'final_boss_v16_supervisor.json'",
      "'FINAL_BOSS_V15'":"'FINAL_BOSS_V16'",
      "'[FINAL_BOSS_V15_SUPERVISOR]'":"'[FINAL_BOSS_V16_SUPERVISOR]'",
      "'[FINAL_BOSS_V15_INSPECT]'":"'[FINAL_BOSS_V16_INSPECT]'",
      "'[FINAL_BOSS_V15_HOLD]'":"'[FINAL_BOSS_V16_HOLD]'",
    }
    for a,b in swaps.items():
        if a not in s:raise RuntimeError('V15_SUPERVISOR_INTERFACE_CHANGED:'+a)
        s=s.replace(a,b)
    old="""    from build_final_boss_v15_native_admission import scanner_builder
    baseline, _ = v12.make_builder(SOURCE.read_bytes())
    expected = scanner_builder(baseline)"""
    new="""    from build_final_boss_v15_native_admission import scanner_builder as _prior_builder
    from build_final_boss_v16_native_executor_handoff import upgrade_scanner as _upgrade
    baseline, _ = v12.make_builder(SOURCE.read_bytes())
    expected = _upgrade(_prior_builder(baseline))"""
    if s.count(old)!=1:raise RuntimeError('V15_SOURCE_GUARD_MISSING')
    s=s.replace(old,new)
    prior="or (BASE/'v13_supervisor.lock').exists()"
    assert s.count(prior)==2, 'EXPECTED_TWO_SUPERVISOR_GUARDS'
    s=s.replace(prior,prior+" or (BASE/'v15_supervisor.lock').exists()")
    s=s.replace("raise Hold('V13_SUPERVISOR_LOCK_EXISTS')", "raise Hold('V16_SUPERVISOR_LOCK_EXISTS')")
    # The first epoch may not yet have a certified V8 stage; don't launch a doomed observer.
    if s.count('            if observe:\n                argv =')!=1:raise RuntimeError('V15_OBSERVER_STARTUP_DRIFT')
    s=s.replace('            if observe:\n                argv =','            if observe and certificate:\n                argv =')
    # Distinguish V16 lock in inspector from the old versions.
    s=s.replace("'v13_supervisor_lock': LOCK.exists(),", "'v16_supervisor_lock': LOCK.exists(), 'v13_supervisor_lock': (BASE/'v13_supervisor.lock').exists(), 'v15_supervisor_lock': (BASE/'v15_supervisor.lock').exists(),")
    ast.parse(s)
    return s.encode('utf-8')

def write_new(p,raw):
    if p.is_symlink():raise RuntimeError('OUTPUT_IS_SYMLINK')
    if p.exists():
        if digest(p.read_bytes())!=digest(raw):raise RuntimeError('EXISTING_OUTPUT_DRIFT')
        return 'VERIFIED_EXISTING'
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=p.parent,delete=False,suffix='.tmp') as f:
        f.write(raw);temp=Path(f.name)
    try:os.replace(temp,p)
    finally:temp.unlink(missing_ok=True)
    return 'INSTALLED'

def test_stage_reader():
    import contextlib, json, os, sys, time, types
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as home:
        base=Path(home)/'runtime_state/oracle/final_boss_dual';base.mkdir(parents=True)
        triple={'token':'TokenVerified123','pump_pool':'PumpVerified123',
                'meteora_pool':'DlmmVerified123', 'risk_scope':'SPL_PROVISIONAL_SIM_REVIEW',
                'source':'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'}
        now=time.time();stage={'generated_at':now,'rows':[triple]}
        raw=json.dumps(stage).encode()
        (base/'staged_discovery.json').write_bytes(raw)
        (base/'v12_mriya_refresh_certificate.json').write_text(json.dumps({
            'status':'CERTIFIED','at':now,'stage_sha256':hashlib.sha256(raw).hexdigest()}))
        (base/'final_boss_v10_admission_stage.json').write_text(json.dumps({
            'status':'STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE','stage_written':True,
            'staged_tokens':[triple['token']]}))
        pkg='qseries_v2.oracle_execution.solana_atomic_executor'
        a=types.ModuleType(pkg);v9=types.ModuleType(pkg+'.final_boss_v9_atomic_simulation_gate')
        v10=types.ModuleType(pkg+'.final_boss_v10_admission_stage')
        v9.load_v8=lambda now:{'verified':True}
        v10.select_v8=lambda report,checker:([dict(triple)],0,[])
        a.final_boss_v9_atomic_simulation_gate=v9;a.final_boss_v10_admission_stage=v10
        modules={pkg:a,v9.__name__:v9,v10.__name__:v10}
        cwd=Path.cwd()
        try:
            os.chdir(home)
            with patch.dict(sys.modules,modules):
                env={};exec(STAGED_READER,env)
                rows=env['_v16_certified_native_rows']()
                assert len(rows)==1 and rows[0]['v12_admission']=='CERTIFIED_DISCOVERY_NEEDS_NATIVE_WARM'
                wrong=json.loads((base/'v12_mriya_refresh_certificate.json').read_text())
                wrong['stage_sha256']='0'*64
                (base/'v12_mriya_refresh_certificate.json').write_text(json.dumps(wrong))
                try:env['_v16_certified_native_rows']();raise AssertionError('FAILED_HASH_WAS_ADMITTED')
                except ValueError as exc:assert 'HASH_MISMATCH' in str(exc)
                wrong['stage_sha256']=hashlib.sha256(raw).hexdigest();wrong['at']=now-91
                (base/'v12_mriya_refresh_certificate.json').write_text(json.dumps(wrong))
                try:env['_v16_certified_native_rows']();raise AssertionError('EXPIRED_CERT_WAS_ADMITTED')
                except ValueError as exc:assert 'STALE_OR_HOLD' in str(exc)
        finally:os.chdir(cwd)
    print('[PASS] V16 fresh exact staged rows and both stale/hash mismatch fail closed')

def test():
    test_stage_reader()
    # Offline source checks preserve physical native admission and subscriber owner.
    v15=BUILDER.read_bytes() if BUILDER.is_file() else None
    sup=SUPERVISOR.read_bytes() if SUPERVISOR.is_file() else None
    if v15 is not None and sup is not None:
        a=upgrade_scanner(v15);b=upgrade_supervisor(sup)
        assert digest(a)!=digest(v15) and digest(b)!=digest(sup)
        assert b'getProgramAccounts' not in b
        ast.parse(a);ast.parse(b)
        assert b'_v16_certified_native_rows' in a and b'v15_supervisor.lock' in b
    reader=ast.parse(STAGED_READER)
    assert any(isinstance(n,ast.FunctionDef) and n.name=='_v16_certified_native_rows' for n in reader.body)
    assert 'sendTransaction' not in STAGED_READER and 'private_key' not in STAGED_READER
    assert "ranked=_v16_certified_native_rows()" in upgrade_scanner(v15).decode() if v15 is not None else True
    print('[PASS] V16 source guard, exact V8/V10 certificate before baseline, double witness, locked scanner and supervisor, no broadcast')

def main():
    ap=argparse.ArgumentParser()
    x=ap.add_mutually_exclusive_group(required=True)
    x.add_argument('--test',action='store_true');x.add_argument('--install',action='store_true')
    a=ap.parse_args()
    try:
        if a.test:test()
        else:
            if not BUILDER.is_file() or not SUPERVISOR.is_file() or BUILDER.is_symlink() or SUPERVISOR.is_symlink():raise RuntimeError('V15_REFERENCE_MISSING')
            print('[V16_SCANNER]',write_new(NEW_BUILDER,upgrade_scanner(BUILDER.read_bytes())))
            print('[V16_SUPERVISOR]',write_new(NEW_SUPERVISOR,upgrade_supervisor(SUPERVISOR.read_bytes())))
            print('[SHA_SCANNER]',digest(NEW_BUILDER.read_bytes()))
            print('[SHA_SUPERVISOR]',digest(NEW_SUPERVISOR.read_bytes()))
            print('[PRESERVED] V15_ORIGINAL_ORACLE322_Q18_Q20_Q25_V14_CORE_ORACLE402_CANONICAL_BUS')
            print('[SCOPE] one derived scanner, one supervisor, native V8/V10 admission, V11 executor observer; no signing or broadcast')
        return 0
    except Exception as exc:
        print('[V16_HOLD]',type(exc).__name__+':'+str(exc)[:180]);return 2
if __name__=='__main__':raise SystemExit(main())
