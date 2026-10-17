from __future__ import annotations
"""Complete V10 scanner discovery staging installer.

Writes ONLY the separate V10 admission module. It does not replace scanner 322,
the SDK, the single WebSocket, executor 402, V8, or V9.
"""
import argparse,hashlib,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
DEST=PACKAGE/'final_boss_v10_admission_stage.py'
SOURCE=r'''
from __future__ import annotations
"""V10: V8 native identities -> ORACLE-322's actual staged discovery contract.

This is a STANDBY admission to the scanner's NEXT epoch, NOT live subscriptions.
Never writes canonical bus, live scanner sockets, executor state, wallet state.
"""
import argparse, ast, collections, hashlib, importlib, json, os, re, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
STAGED=BASE/'staged_discovery.json'
OUT=BASE/'final_boss_v10_admission_stage.json'
SCANNER=ROOT/'build_oracle_322_scanner_isolated_discovery.py'
SCANNER_EMBEDDED_SHA='e579d68ac26210ef98ba015180126782669144e81fc5eb2010f0d9586ced767c'
V9_SHA='2d17b83e68d554320e993357b2037123d69c1b63341e41043e482d854d0b1e9f'
PKG='qseries_v2.oracle_execution.solana_atomic_executor.'
MAX_ROWS=112
MAX_AGE=90.0
LOCK=BASE/'v10_admission.lock'

class Hold(RuntimeError):pass

def digest(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
def module(name):return importlib.import_module(PKG+name)
def safe(exc):
    value=str(exc)
    return value if isinstance(exc,Hold) and re.fullmatch(r'[A-Z][A-Z0-9_]{2,90}',value) else type(exc).__name__.upper()

def read_json(path, limit=500_000):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>limit:
        raise Hold('JSON_SOURCE_MISSING_LINKED_OR_OVERSIZE')
    try:data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,ValueError):raise Hold('JSON_SOURCE_UNREADABLE') from None
    if not isinstance(data,dict):raise Hold('JSON_SOURCE_WRONG_TYPE')
    return data

def scanner_contract(path=SCANNER):
    if not path.is_file() or path.is_symlink():raise Hold('ORACLE322_INSTALLER_NOT_FOUND')
    try:
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        options=[]
        for node in ast.walk(tree):
            if not isinstance(node,(ast.Assign,ast.AnnAssign)):continue
            val=node.value
            if not isinstance(val,ast.Constant) or not isinstance(val.value,str) or len(val.value)<3000:continue
            names=[n.id for n in getattr(node,'targets',[]) if isinstance(n,ast.Name)]
            if isinstance(getattr(node,'target',None),ast.Name):names.append(node.target.id)
            if any('SOURCE' in n.upper() or 'SCRIPT' in n.upper() for n in names):options.append(val.value)
        if len(options)!=1:raise Hold('ORACLE322_EMBEDDED_SOURCE_AMBIGUOUS')
        source=options[0]
        if digest(source.encode())!=SCANNER_EMBEDDED_SHA:raise Hold('ORACLE322_SOURCE_HASH_DRIFT')
        inner=ast.parse(source)
        funcs={n.name:n for n in ast.walk(inner) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        if not {'select_rows','discovery','prepare','stage_discovery','heartbeat'}.issubset(funcs):
            raise Hold('ORACLE322_STAGING_FUNCTION_MISSING')
        text=ast.get_source_segment(source,funcs['select_rows']) or ''
        discovery=ast.get_source_segment(source,funcs['discovery']) or ''
        if not all(z in text for z in ('STAGED','read_text','grouped','latest_feed')):
            raise Hold('ORACLE322_STAGING_READER_NOT_CONFIRMED')
        if 'select_rows' not in discovery:raise Hold('ORACLE322_DISCOVERY_NOT_SELECTING_ROWS')
        # Source inspection, not a claim that the running process reloads its subscriptions.
        return {'embedded_sha256':digest(source.encode()),'staged_reader':True,
                'startup_discovery_binding':True,'running_subscription_reload':False}
    except (SyntaxError,UnicodeError,OSError) as exc:
        raise Hold('ORACLE322_SOURCE_PARSE_ERROR') from None

def select_v8(report, checker=None):
    """Choose ONE DLMM per token. Indexer liquidity is only ordering, never execution proof."""
    if checker is None:checker=module('final_boss_v9_atomic_simulation_gate')
    routes,holds=checker.candidates(report)
    by_token=collections.defaultdict(list)
    for row in report['prospects']:
        try:
            triple=checker.exact_triple(row)
            if triple not in routes:continue
            risk=checker.review_mint(row)
            if risk not in ('TOKEN2022_METADATA_ONLY_SIM_REVIEW','SPL_PROVISIONAL_SIM_REVIEW'):
                raise Hold('V8_RISK_NOT_PROVISIONAL_SIM_REVIEW')
            age=row.get('mriya_age_s')
            if type(age) not in (int,float) or not 0<=age<=180:
                raise Hold('MRIYA_WITNESS_AGE_INVALID')
            # Candidate source priority is stage-only; scanner must still hydrate actual SDK data.
            liquidity=row.get('meteora_liquidity_usd_indexer')
            liquidity=float(liquidity) if type(liquidity) in (int,float) and 0<=liquidity<=1e12 else -1.0
            by_token[triple[0]].append((liquidity,triple,risk,float(age)))
        except Exception:continue
    chosen=[];alternatives=0
    for token,opts in sorted(by_token.items()):
        opts.sort(key=lambda item:(-item[0],item[1][1],item[1][2]))
        _,(tok,pump,dlmm),risk,age=opts[0]
        alternatives+=len({x[1] for x in opts})-1
        chosen.append({'token':tok,'pump_pool':pump,'meteora_pool':dlmm,
                       'source':'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW',
                       'admission_scope':'NEXT_SCANNER_EPOCH_ONLY',
                       'risk_scope':risk,'mriya_age_s':age})
    if not chosen:raise Hold('NO_V8_ROUTES_ELIGIBLE_FOR_STAGING')
    if len(chosen)>28:raise Hold('STAGING_ADMISSION_CAPACITY_EXCEEDED')
    return chosen,alternatives,holds

def combine(old,chosen,now):
    rows=[]
    if old:
        t=old.get('generated_at')
        if type(t) not in (int,float) or not 0<=now-t<=600:
            # Scanner itself ignores expired STAGED; archive its exact bytes separately.
            # Replacing the expired cache does not remove an active subscription.
            rows=[]
        elif not isinstance(old.get('rows'),list) or len(old['rows'])>MAX_ROWS:
            raise Hold('EXISTING_STAGED_FEED_ROWS_INVALID')
        else:rows=old['rows']
    chosen_tokens={r['token'] for r in chosen}
    # Do not leave an older competing route for the SAME token: ORACLE-322's
    # token-oriented selection must never silently restore a different DLMM pool.
    rows=[r for r in rows if not (isinstance(r,dict) and (r.get('token') in chosen_tokens or
           r.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'))]
    used=set();combined=[]
    for r in chosen+rows:
        if not isinstance(r,dict):continue
        token=r.get('token');pump=r.get('pump_pool');dlmm=r.get('meteora_pool')
        if not all(isinstance(z,str) and re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{32,44}',z) for z in (token,pump)):
            # Old source rows without exact pool identity are not admitted by V10.
            continue
        # ORACLE-322 select_rows prioritizes tokens; do not promise multiple DLMM pools per token.
        key=(token,pump,dlmm if isinstance(dlmm,str) else '')
        if key in used:continue
        used.add(key);combined.append(r)
    if len(combined)>MAX_ROWS:raise Hold('STAGED_FEED_CAPACITY_PRESERVE_EXISTING_ROWS')
    return combined

def stage_doc(chosen,prior,now):
    rows=combine(prior,chosen,now)
    return {'generated_at':now,'rows':rows,'candidates':len(rows)}

def health():
    scan=module('oracle_344_scanner_align')
    conn=scan.bus()
    try:
        conn.execute('PRAGMA query_only=ON')
        stat=scan.validate_scanner(conn)
    finally:conn.close()
    if not isinstance(stat,dict) or stat.get('ok') is not True:
        raise Hold('CANONICAL_SCANNER_NOT_HEALTHY')
    return {'ok':True,'epoch':stat['epoch'],'producer_prefix':str(stat['producer'])[:12]}

def snapshot_bytes(path):
    if path.is_symlink():raise Hold('STAGED_FEED_SYMLINK_NOT_ALLOWED')
    if not path.exists():return None,None
    raw=path.read_bytes()
    if len(raw)>500_000:raise Hold('STAGED_FEED_TOO_LARGE')
    return raw,path.stat().st_mtime_ns

def save_atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,suffix='.tmp',delete=False) as fp:
        fp.write(raw);temp=Path(fp.name)
    try:os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)

def stage_write(doc,old_bytes,old_mtime):
    BASE.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(LOCK,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:raise Hold('V10_STAGE_WRITER_ALREADY_ACTIVE') from None
    backup=None
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(str(os.getpid()))
        before,mtime=snapshot_bytes(STAGED)
        if before!=old_bytes or mtime!=old_mtime:
            raise Hold('STAGED_FEED_CHANGED_DURING_PREPARATION')
        if old_bytes is not None:
            bak=BASE/('staged_pre_v10_'+hashlib.sha256(old_bytes).hexdigest()[:16]+'.bak')
            if bak.exists() and bak.read_bytes()!=old_bytes:raise Hold('STAGED_BACKUP_HASH_COLLISION')
            if not bak.exists():save_atomic(bak,old_bytes)
            backup=bak.name
        # Revalidate V8 witness and exact selected identities immediately before stage.
        checker=module('final_boss_v9_atomic_simulation_gate')
        fresh=checker.load_v8()
        ready,_,_=select_v8(fresh,checker)
        if {(z['token'],z['pump_pool'],z['meteora_pool']) for z in ready} != {
            (z['token'],z['pump_pool'],z['meteora_pool']) for z in doc['rows'] if z.get('source')=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'}:
            raise Hold('V8_SOURCE_CHANGED_DURING_STAGING')
        # Scanner remains unchanged. OS rename is the only stage mutation.
        save_atomic(STAGED,json.dumps(doc,sort_keys=True,indent=2).encode())
        return backup
    finally:
        try:LOCK.unlink()
        except OSError:pass

def run(apply=False):
    out={'build':'FINAL_BOSS_V10','status':'HOLD','mode':'STAGE_NEXT_EPOCH' if apply else 'AUDIT',
         'scanner_modified':False,'additional_websockets':0,'canonical_bus_writes':0,
         'signing':False,'broadcast':False,'live_subscription_rotation_applied':False,
         'funded_execution_authority':False,'stage_written':False,
         'next_epoch_native_hydration_certified':False}
    try:
        info=scanner_contract()
        v9=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v9_atomic_simulation_gate.py'
        if not v9.is_file() or digest(v9.read_bytes())!=V9_SHA:
            raise Hold('V9_MODULE_HASH_DRIFT')
        checker=module('final_boss_v9_atomic_simulation_gate')
        report=checker.load_v8()
        chosen,alternatives,risk_holds=select_v8(report,checker)
        out.update(scanner_contract=info,verified_v8_prospects=len(report['prospects']),
             reviewed_tokens=len(chosen),alternatives_not_promoted=alternatives,
             risk_holds=risk_holds,source_age_s=round(time.time()-report['observed_unix'],2),
             scanner=health())
        old_bytes,old_mtime=snapshot_bytes(STAGED)
        previous=json.loads(old_bytes.decode('utf-8')) if old_bytes is not None else None
        doc=stage_doc(chosen,previous,time.time())
        out.update(stage_candidates=len(doc['rows']),staged_tokens=[r['token'] for r in chosen],
                   old_staged_rows=len(previous.get('rows',[])) if isinstance(previous,dict) else 0)
        if apply:
            backup=stage_write(doc,old_bytes,old_mtime)
            out.update(stage_written=True,stage_backup=backup,
                       status='STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE',
                       stage_file='runtime_state/oracle/final_boss_dual/staged_discovery.json')
        else:out['status']='READY_TO_STAGE_NOT_LIVE'
    except Exception as exc:out['status']='HOLD_'+safe(exc)
    try:
        BASE.mkdir(parents=True,exist_ok=True)
        save_atomic(OUT,json.dumps(out,sort_keys=True,indent=2).encode())
    except OSError:pass
    print('[FINAL_BOSS_V10_ADMISSION]',json.dumps(out,sort_keys=True),flush=True)
    print('[REPORT]',OUT.relative_to(ROOT),flush=True)
    return 0 if out['status'] in ('READY_TO_STAGE_NOT_LIVE','STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE') else 2

def tests():
    from unittest.mock import patch
    class Mock:
        @staticmethod
        def exact_triple(r):
            if not r.get('onchain_pool_binding_verified'):raise Hold('BAD_POOL')
            return r['token'],r['pump_pool'],r['meteora_pool']
        @staticmethod
        def review_mint(r):return r['risk']
        @staticmethod
        def candidates(rep):
            return {Mock.exact_triple(r):{'risk':r['risk']} for r in rep['prospects'] if r.get('onchain_pool_binding_verified')},{}
    def mk(meteora,liq,risk='TOKEN2022_METADATA_ONLY_SIM_REVIEW'):
        return dict(token='a'*40,pump_pool='b'*40,meteora_pool=meteora,
                    meteora_liquidity_usd_indexer=liq,risk=risk,mriya_age_s=20,
                    onchain_pool_binding_verified=True)
    chosen,alts,holds=select_v8({'prospects':[mk('c'*40,500),mk('d'*40,300),mk('e'*40,200)]},Mock)
    assert len(chosen)==1 and chosen[0]['meteora_pool']=='c'*40 and alts==2
    assert chosen[0]['source']=='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW'
    now=1000.
    old={'generated_at':999.,'rows':[{'token':'f'*40,'pump_pool':'g'*40,'meteora_pool':'h'*40}]}
    doc=stage_doc(chosen,old,now)
    assert len(doc['rows'])==2 and doc['rows'][0]['token']=='a'*40
    assert stage_doc(chosen,old,now)==doc
    clash={'generated_at':999.,'rows':[dict(old['rows'][0],token='a'*40,meteora_pool='z'*40)]}
    assert len(stage_doc(chosen,clash,now)['rows'])==1
    expired=stage_doc(chosen,dict(old,generated_at=100.),now)
    assert len(expired['rows'])==1 and expired['rows'][0]['token']=='a'*40
    fake=("STAGED=1\ndef latest_feed():pass\ndef select_rows(original):\n grouped={}\n x=STAGED.read_text()\n return latest_feed()\ndef stage_discovery():pass\ndef discovery(root):return select_rows(root)\ndef prepare(root):pass\ndef heartbeat():pass\n")
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'builder.py';path.write_text('SOURCE='+repr(fake*60),encoding='utf-8')
        with patch.dict(globals(), {'SCANNER_EMBEDDED_SHA':digest((fake*60).encode())}):
            assert scanner_contract(path)['staged_reader']
    with tempfile.TemporaryDirectory() as folder:
        base=Path(folder);existing=base/'staged_discovery.json';lock=base/'v10.lock'
        existing.write_text(json.dumps(old),encoding='utf-8')
        oldbytes,oldmtime=snapshot_bytes(existing)
        Mock.load_v8=staticmethod(lambda: {'prospects':[mk('c'*40,500),mk('d'*40,300),mk('e'*40,200)]})
        with patch.dict(globals(),{'BASE':base,'STAGED':existing,'LOCK':lock,'module':lambda name:Mock}):
            name=stage_write(doc,oldbytes,oldmtime)
            assert name and (base/name).read_bytes()==oldbytes
            assert json.loads(existing.read_text())==doc
            assert not lock.exists()
            try:stage_write(doc,oldbytes,oldmtime)
            except Hold as exc:assert str(exc)=='STAGED_FEED_CHANGED_DURING_PREPARATION'
            else:raise AssertionError('stale stage source overwrite permitted')
    assert not any(k in repr(doc).lower() for k in ('private_key','api-key','mnemonic'))
    print('[PASS] FINAL_BOSS_V10 exact V8 triple, best route per token, 112-cap preservation, frozen scanner staging contract')
    print('[SCOPE] NEXT EPOCH ONLY; no live subscriptions, bus writes, signing, broadcast or claimed simulation')

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--audit',action='store_true');g.add_argument('--stage',action='store_true')
    a=p.parse_args()
    if a.test:tests();return 0
    return run(a.stage)
if __name__=='__main__':raise SystemExit(main())

'''

def norm(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()

def install():
    incoming=SOURCE.encode('utf-8')
    compile(SOURCE,'final_boss_v10_admission_stage.py','exec')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    if DEST.exists():
        if norm(DEST.read_bytes())!=norm(incoming):
            raise RuntimeError('HOLD_UNRECOGNIZED_EXISTING_V10_MODULE_NO_OVERWRITE')
        print('[PASS] V10_ALREADY_INSTALLED')
        return
    with tempfile.NamedTemporaryFile('wb',dir=PACKAGE,delete=False,suffix='.tmp') as out:
        out.write(incoming);temp=Path(out.name)
    try:os.replace(temp,DEST)
    finally:temp.unlink(missing_ok=True)
    if norm(DEST.read_bytes())!=norm(incoming):raise RuntimeError('V10_READBACK_MISMATCH')
    print('[INSTALLED]',DEST.relative_to(ROOT))
    print('[SHA256]',norm(incoming))
    print('[PRESERVED] scanner 322, single WebSocket, canonical events bus, Q18/Q20/Q25, executor 402, V8, V9')
    print('[BOUNDARY] NEXT SCANNER EPOCH STAGE ONLY; NOT LIVE ROTATION; NO SIGNING OR BROADCAST')

def test():
    compile(SOURCE,'final_boss_v10_admission_stage.py','exec')
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'project/qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v10_admission_stage.py'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(SOURCE,encoding='utf-8')
        pr=subprocess.run([sys.executable,str(path),'--test'],capture_output=True,text=True,timeout=40)
        if pr.returncode!=0:raise RuntimeError('V10_MODULE_TEST_FAIL_'+str(pr.returncode)+' '+pr.stderr[-300:])
        if '[PASS] FINAL_BOSS_V10' not in pr.stdout:raise RuntimeError('V10_PASS_MARKER_MISSING')
    for forbidden in ('sendTransaction', 'accountSubscribe', 'accountUnsubscribe', 'os.environ[\"QSB_SOLANA_PRIVATE_KEY\"]'):
        if forbidden in SOURCE:raise RuntimeError('V10_FORBIDDEN_EXECUTION_OR_WS_API_'+forbidden)
    print('[PASS] V10_INSTALLER full module tests, fail-closed source SHA, staging durability, no scanner or executor mutation')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--install',action='store_true')
    a=p.parse_args()
    if not(a.test or a.install):p.error('choose --test or --install')
    if a.test:test()
    if a.install:install()
if __name__=='__main__':main()
