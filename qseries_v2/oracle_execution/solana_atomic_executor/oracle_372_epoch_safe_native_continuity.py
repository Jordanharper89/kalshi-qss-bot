"""ORACLE-372: epoch-safe native UNSIGNED continuity, exact source diagnostics.

FULL installer. Extends the certified ORACLE-370 forward native provider and
ORACLE-368/366 source reader without modifying the frozen ORACLE-322 scanner.
Same producer, advanced epoch and fresh heartbeat allow a new source SESSION;
no stale event or in-flight packet survives session turnover. Changed producer
and stale heartbeat HOLD. PUMP_TO_METEORA only; reverse remains unverified.
Wallet PUBLIC key only, no private key, signing or transaction submission.
"""
from __future__ import annotations
import argparse,hashlib,importlib,json,os,re,sys,tempfile,time,traceback,threading,unittest
from collections import Counter
from pathlib import Path

ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
PKG='qseries_v2.oracle_execution.solana_atomic_executor'
TARGET=ROOT/'oracle_372_epoch_safe_native_continuity.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_372_epoch_safe_native_report.json')
PUBKEY=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
CODE=re.compile(r'^[A-Z][A-Z0-9_]{3,100}$')
EXECUTION_AUTHORITY=False
BROADCAST=False
SIGNING=False

class StopRun(RuntimeError):pass


def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:
        json.dump(value,f,indent=2,sort_keys=True,default=str)
        tmp=f.name
    os.replace(tmp,path)


def install():
    content=Path(__file__).resolve().read_bytes()
    compile(content.decode('utf-8'),str(TARGET),'exec')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile(dir=TARGET.parent,mode='wb',delete=False) as f:
            f.write(content);p=f.name
        os.replace(p,TARGET)
    assert TARGET.read_bytes()==content
    print('[ORACLE372_INSTALL_PASS]',TARGET,'sha256='+hashlib.sha256(content).hexdigest(),flush=True)


def modules():
    native=importlib.import_module(PKG+'.oracle_370_native_atomic_executor')
    core=importlib.import_module(PKG+'.oracle_368_source_boundary_repair')
    scan=importlib.import_module(PKG+'.oracle_344_scanner_align')
    return native,core,scan


def audit():
    native,core,scan=modules()
    native.audit()
    core.audit(require_installed=True)
    if TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise StopRun('ORACLE372_INSTALLED_SOURCE_MISMATCH')
    if (native.EXECUTION_AUTHORITY is not False or native.BROADCAST is not False
            or EXECUTION_AUTHORITY is not False or BROADCAST is not False or SIGNING is not False):
        raise StopRun('EXECUTION_FIREWALL_FAILURE')
    assert callable(native.NativeQ87Provider) and callable(native.verify_native_program_sequence)
    assert callable(core.live) and callable(scan.bus) and callable(scan.validate_scanner)
    print('[ORACLE372_AUDIT_PASS] 322_FROZEN 370_NATIVE_FORWARD 368_CANONICAL_READER '
          'EPOCH_REBIND_FAIL_CLOSED NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST',flush=True)


def read_heartbeat(scan):
    try:
        db=scan.bus()
        try:
            h=scan.validate_scanner(db)
        finally:
            db.close()
    except (OSError,RuntimeError,ValueError):
        raise StopRun('SCANNER_HEALTH_VALIDATION_FAILED') from None
    if (not isinstance(h,dict) or h.get('ok') is not True or
            not isinstance(h.get('producer'),str) or len(h['producer'])<8 or
            type(h.get('epoch')) is not int or h['epoch']<1 or
            type(h.get('age_s')) not in (int,float) or not 0<=h['age_s']<15):
        raise StopRun('SCANNER_HEARTBEAT_NOT_CERTIFIED')
    return h


def may_rebind(old_h,new_h):
    """New epoch is NOT itself authorization. Require fresh same producer + advance."""
    if not isinstance(old_h,dict) or not isinstance(new_h,dict):return False
    return (new_h.get('ok') is True and new_h.get('producer')==old_h.get('producer')
            and type(new_h.get('epoch')) is int and type(old_h.get('epoch')) is int
            and new_h['epoch']>old_h['epoch'] and
            type(new_h.get('age_s')) in (float,int) and 0<=new_h['age_s']<=2)


def safe_reason(exc):
    """Never print exception text unless it is a known uppercase internal hold code."""
    name=type(exc).__name__
    raw=str(exc)
    if name in ('Hold','StopRun') and CODE.fullmatch(raw):return raw
    tb=traceback.extract_tb(exc.__traceback__)
    src=tb[-1] if tb else None
    if src:
        base=Path(src.filename).name
        if re.fullmatch(r'[A-Za-z0-9_]+\.py',base):
            return 'PROVIDER_'+name+'_'+base.replace('.py','')+'_L'+str(src.lineno)
    return 'PROVIDER_'+name+'_LOCATION_UNKNOWN'


def make_worker(core,native,provider,rpc,accum):
    class Worker(core.LatestWorker):
        def loop(self):
            while True:
                with self.cv:
                    while not self.latest and not self.stop:self.cv.wait(.2)
                    if self.stop:return
                    token,item=self.latest.popitem()
                row,generation=item
                result={'stage':'HOLD','reason':'UNKNOWN'}
                try:
                    err=core.stage1_nomination(row)
                    if err:raise native.Hold(err)
                    proof=provider.prepare_unsigned(row)
                    if self.newer_or_invalid(token,generation):raise native.Hold('SUPERSEDED_BEFORE_SIM')
                    result=core.simulation_gate(row,proof,rpc)
                    if not isinstance(result,dict) or result.get('stage') not in ('HOLD','UNSIGNED_SIM_NET_ESTIMATE_PASS'):
                        raise native.Hold('SIMULATION_GATE_RETURN_INVALID')
                    if self.newer_or_invalid(token,generation):raise native.Hold('SUPERSEDED_AFTER_SIM')
                except Exception as exc:
                    result={'stage':'HOLD','reason':safe_reason(exc)}
                if self.newer_or_invalid(token,generation):
                    if result.get('reason') not in ('UNKNOWN','SOURCE_INVALIDATED'):
                        print('[ORACLE372_PRE_INVALIDATION_REASON]',
                              json.dumps({'reason':result['reason']}),flush=True)
                    result={'stage':'HOLD','reason':'SOURCE_INVALIDATED'}
                with self.cv:
                    self.results.append(result)
                    self.results=self.results[-80:]
                    self.counts[result.get('reason') or result.get('stage') or 'UNKNOWN']+=1
                # Hide wallet, RPC and token-account data; only stage/reason exposed.
                visible={k:v for k,v in result.items() if k in ('stage','reason','projected_net_lamports')}
                print('[ORACLE372_NATIVE_GATE]',json.dumps(visible,sort_keys=True),flush=True)
                accum[result.get('reason') or result.get('stage') or 'UNKNOWN']+=1
    return Worker


def launch(minutes=3,poll_ms=5,ttl_ms=2500,max_age_ms=1500,wallet_pubkey=None):
    if not isinstance(wallet_pubkey,str) or not PUBKEY.fullmatch(wallet_pubkey):
        raise StopRun('VALID_PUBLIC_WALLET_ADDRESS_REQUIRED')
    if not 1<=minutes<=30 or not 5<=poll_ms<=100:
        raise StopRun('BOUNDED_RUNTIME_INVALID')
    if not (500<=ttl_ms<=10000 and 100<=max_age_ms<=ttl_ms):
        raise StopRun('FRESHNESS_BOUNDS_INVALID')
    native,core,scan=modules()
    audit()
    initial=read_heartbeat(scan)  # Before costly warm and RPC.
    producer=initial['producer']
    print('[ORACLE372_SOURCE_READY]',json.dumps({'producer_prefix':producer[:12],
          'epoch':initial['epoch'],'age_s':initial['age_s'],'new_ws':False}),flush=True)
    provider=native.NativeQ87Provider(wallet_pubkey)
    provider.prewarm()  # Q18/Q25/Q87 native forward builder; one warm per process.
    warm=read_heartbeat(scan)
    if warm['producer']!=producer:
        raise StopRun('PRODUCER_CHANGED_DURING_NATIVE_WARM')
    rpc=core.RpcReadOnly(provider.rpc_url,budget=40)
    native_counts=Counter();history=[]
    first=time.monotonic();deadline=first+minutes*60
    original=core.LatestWorker
    core.LatestWorker=make_worker(core,native,provider,rpc,native_counts)
    last_h=warm;outcome='HOLD_NO_LIVE_SESSION'
    try:
        while time.monotonic()<deadline:
            h=read_heartbeat(scan)
            if h['producer']!=producer:
                outcome='HOLD_SCANNER_PRODUCER_SWITCH';break
            remain=deadline-time.monotonic()
            if remain<1:break
            # New sessions preserve the warm native templates, not expired nominations.
            window=max(1,min(90,int(remain)))
            print('[ORACLE372_SESSION]',json.dumps({'epoch':h['epoch'],'seconds':window,
                  'producer_prefix':producer[:12],'new_websocket':False}),flush=True)
            code=core.live(seconds=window,poll_ms=poll_ms,ttl_ms=ttl_ms,
                           max_age_ms=max_age_ms,provider=provider,rpc=rpc,
                           report=Path('runtime_state/oracle/final_boss_dual/oracle_372_source_session_report.json'))
            p=Path('runtime_state/oracle/final_boss_dual/oracle_372_source_session_report.json')
            detail=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
            status=str(detail.get('status','MISSING_SESSION_REPORT'))
            history.append({'start_epoch':h['epoch'],'status':status,'code':code,
                 'event_contract':detail.get('event_contract',{}),
                 'native_gate_counts':detail.get('native_gate_counts',{})})
            save_json(REPORT,{'status':'RUNNING_NOT_TRADE_CERTIFIED','sessions':history,
                 'native_gate_counts':dict(native_counts),'wallet_pubkey_not_logged':True,
                 'signing':False,'broadcast':False,'private_key_used':False})
            if code==0:
                outcome='READ_ONLY_CERTIFICATION_SESSION_COMPLETED'
                continue
            if status!='HOLD_SCANNER_EPOCH_OR_PRODUCER_CHANGED':
                outcome='HOLD_'+status;break
            after=read_heartbeat(scan)
            if not may_rebind(h,after) or after['producer']!=producer:
                outcome='HOLD_EPOCH_REBIND_NOT_SAFE';break
            if len(history)>=16:
                outcome='HOLD_TOO_MANY_EPOCH_ROLLOVERS';break
            print('[ORACLE372_EPOCH_REBOUND]',json.dumps({'from_epoch':h['epoch'],
                   'to_epoch':after['epoch'],'same_producer':True,
                   'stale_candidates_dropped':True,'no_new_ws':True}),flush=True)
            last_h=after
            time.sleep(.05)
    finally:
        core.LatestWorker=original
    result={'status':outcome,'sessions':history,'native_gate_counts':dict(native_counts),
       'source_producer_prefix':producer[:12],'last_epoch':last_h['epoch'],
       'native_ready_tokens':len(provider.old.READY_TOKENS),
       'rpc_gate_calls':rpc.calls,'rpc_note':'Native Q87 account RPCs are separate from rpc_gate_calls',
       'signing':False,'broadcast':False,'execution_authority':False,'private_key_used':False,
       'first_funded_canary_lamports':10_000_000,'realized_profit_certified':False}
    save_json(REPORT,result)
    print('[ORACLE372_EXIT]',json.dumps({k:v for k,v in result.items() if k not in ('sessions',)},sort_keys=True),flush=True)
    print('[ORACLE372_REPORT]',REPORT,flush=True)
    return 0 if outcome=='READ_ONLY_CERTIFICATION_SESSION_COMPLETED' else 2


def tests():
    class Cases(unittest.TestCase):
        def test_same_producer_new_epoch(self):
            self.assertTrue(may_rebind({'producer':'a','epoch':2},{'ok':True,'producer':'a','epoch':3,'age_s':.1}))
        def test_no_producer_switch(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':2},{'ok':True,'producer':'b','epoch':3,'age_s':.1}))
        def test_no_stale_heartbeat(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':2},{'ok':True,'producer':'a','epoch':3,'age_s':17}))
        def test_no_same_epoch(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':3},{'ok':True,'producer':'a','epoch':3,'age_s':0}))
        def test_no_decreasing_epoch(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':3},{'ok':True,'producer':'a','epoch':2,'age_s':0}))
        def test_no_negative_age(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':2},{'ok':True,'producer':'a','epoch':3,'age_s':-1}))
        def test_no_bool_epoch(self):
            self.assertFalse(may_rebind({'producer':'a','epoch':2},{'ok':True,'producer':'a','epoch':True,'age_s':0}))
        def test_no_missing_record(self):
            self.assertFalse(may_rebind({},{}))
        def test_controlled_hold(self):
            self.assertEqual(safe_reason(StopRun('SCANNER_NOT_HEALTHY')),'SCANNER_NOT_HEALTHY')
        def test_no_credentials_in_generic_exception(self):
            try:raise RuntimeError('password=SECRET_API_KEY_DO_NOT_SHOW')
            except Exception as exc:
                s=safe_reason(exc)
                self.assertNotIn('SECRET',s)
                self.assertIn('RuntimeError',s)
        def test_no_private_key_io(self):
            s=Path(__file__).read_text(encoding='utf-8')
            self.assertNotIn('sendTransaction',s.split('def tests():')[0])
            self.assertNotIn('sign_message(',s.split('def tests():')[0])
            self.assertNotIn('getpass(',s.split('def tests():')[0])
        def test_epoch_rebind_session_integration(self):
            from unittest.mock import patch
            from types import SimpleNamespace
            import io,contextlib
            hb=[{'ok':True,'producer':'p'*32,'epoch':1,'age_s':.1},
                {'ok':True,'producer':'p'*32,'epoch':1,'age_s':.1},
                {'ok':True,'producer':'p'*32,'epoch':1,'age_s':.1},
                {'ok':True,'producer':'p'*32,'epoch':2,'age_s':.1},
                {'ok':True,'producer':'p'*32,'epoch':2,'age_s':.1}]
            calls=[]
            class P:
                def __init__(self,wallet):
                    self.wallet=wallet;self.rpc_url='https://example.invalid';self.old=SimpleNamespace(READY_TOKENS={'T'})
                def prewarm(self):pass
            class R:
                calls=0
                def __init__(self,*args,**kwargs):pass
            class N:
                EXECUTION_AUTHORITY=False;BROADCAST=False;NativeQ87Provider=P
            class C:
                LatestWorker=object
                RpcReadOnly=R
                def live(self,**kwargs):
                    calls.append(kwargs)
                    state=('HOLD_SCANNER_EPOCH_OR_PRODUCER_CHANGED' if len(calls)==1 else 'HOLD_RPC_RATE_LIMIT_REQUIRES_REVALIDATION')
                    save_json(kwargs['report'],{'status':state,'event_contract':{},'native_gate_counts':{}})
                    return 2
            c=C()
            with tempfile.TemporaryDirectory() as tmp:
                with patch.dict(globals(),{'modules':lambda:(N,c,object()),
                         'audit':lambda:None,'read_heartbeat':lambda sc:hb.pop(0),
                         'REPORT':Path(tmp)/'res.json'}), contextlib.redirect_stdout(io.StringIO()):
                    result=launch(minutes=1,wallet_pubkey='A'*43)
                self.assertEqual(result,2)
                self.assertEqual(len(calls),2)
                self.assertIs(c.LatestWorker,object)
                rep=json.loads((Path(tmp)/'res.json').read_text())
                self.assertEqual(len(rep['sessions']),2)
                self.assertFalse(rep['broadcast'])
        def test_audit_full_contract_with_stubbed_modules(self):
            from unittest.mock import patch
            from types import SimpleNamespace
            class N:
                EXECUTION_AUTHORITY=False
                BROADCAST=False
                NativeQ87Provider=type('Provider',(),{})
                verify_native_program_sequence=staticmethod(lambda:None)
                @staticmethod
                def audit():pass
            class C:
                @staticmethod
                def audit(require_installed=False):
                    if not require_installed:raise RuntimeError('NOT_STRICT')
                @staticmethod
                def live():pass
            sc=SimpleNamespace(bus=lambda:None,validate_scanner=lambda db:None)
            with patch.dict(globals(),{'modules':lambda:(N,C,sc),
                     'TARGET':Path(__file__).resolve()}):
                audit()
        def test_audit_rejects_missing_scanner_contract(self):
            from unittest.mock import patch
            from types import SimpleNamespace
            class N:
                EXECUTION_AUTHORITY=False
                BROADCAST=False
                NativeQ87Provider=type('Provider',(),{})
                verify_native_program_sequence=staticmethod(lambda:None)
                @staticmethod
                def audit():pass
            class C:
                @staticmethod
                def audit(require_installed=False):pass
                @staticmethod
                def live():pass
            with patch.dict(globals(),{'modules':lambda:(N,C,SimpleNamespace()),
                     'TARGET':Path(__file__).resolve()}):
                with self.assertRaises(AttributeError):audit()
        def test_target_compiles(self):
            compile(Path(__file__).read_text(encoding='utf-8'),__file__,'exec')
    res=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    print('[ORACLE372_TEST_PASS]' if res.wasSuccessful() else '[ORACLE372_TEST_FAIL]',res.testsRun,flush=True)
    return res.wasSuccessful()


def main():
    ap=argparse.ArgumentParser()
    for name in ('install','test','audit','run'):ap.add_argument('--'+name,action='store_true')
    ap.add_argument('--minutes',type=int,default=3)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--ttl-ms',type=int,default=2500)
    ap.add_argument('--max-age-ms',type=int,default=1500)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET_PUBKEY',''))
    args=ap.parse_args()
    if not any((args.install,args.test,args.audit,args.run)):ap.error('SELECT_ACTION')
    if args.install:install()
    if args.test and not tests():return 1
    if args.audit:audit()
    if args.run:
        wallet=args.wallet_pubkey or input('Solana wallet PUBLIC address (never private key): ').strip()
        return launch(args.minutes,args.poll_ms,args.ttl_ms,args.max_age_ms,wallet)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except StopRun as exc:
        print('[ORACLE372_HOLD]',safe_reason(exc),flush=True);raise SystemExit(2)
