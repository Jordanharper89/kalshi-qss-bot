"""ORACLE-386: full standalone, session-scoped same-bank gross quote parity witness.

Records the original native PumpSwap->Meteora pricing proof beside the original
scanner gross *hint*. Neither is overridden. ORACLE-322 is frozen; no new RPC,
websocket, signing, broadcasting, or private key access is introduced.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_386_same_bank_parity_witness.py')
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_386_same_bank_parity_witness.json')
CANARY=10_000_000
EXECUTION_AUTHORITY=SIGNING=BROADCAST=False
MAX_SAMPLES=120

class Hold(RuntimeError):pass


def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,delete=False) as f:
        json.dump(obj,f,sort_keys=True,indent=2);tmp=f.name
    os.replace(tmp,path)


def load(path):
    try:return json.loads(Path(path).read_text(encoding='utf8'))
    except (OSError,ValueError,TypeError):return {}


def deps():
    m385=importlib.import_module(PKG+'.oracle_385_scanner_source_unification')
    m370=importlib.import_module(PKG+'.oracle_370_native_atomic_executor')
    runtime=importlib.import_module(PKG+'.runtime')
    return m385,m370,runtime.q18


def safe_int(value):
    return value if type(value) is int else None


def quote_sample(rows,size,direction):
    if not isinstance(rows,(list,tuple)):return {'row_contract':'NON_SEQUENCE'}
    matches=[r for r in rows if isinstance(r,dict) and r.get('direction')==direction and
             safe_int(r.get('start'))==size]
    result={'row_contract':'MATCH' if len(matches)==1 else 'MISSING_OR_NONUNIQUE',
            'row_count':len(rows),'matching_rows':len(matches)}
    if len(matches)==1:
        row=matches[0]
        result['native_same_bank_gross_lamports']=safe_int(row.get('local_net'))
        result['native_same_bank_protected_lamports']=safe_int(row.get('local_min_net'))
        result['native_start_lamports']=safe_int(row.get('start'))
        result['direction']=direction
    return result


def classification(row):
    scanner=row.get('scanner_gross_hint_lamports')
    gross=row.get('native_same_bank_gross_lamports')
    reason=row.get('outcome_code')
    if scanner is not None and gross is not None:
        row['scanner_minus_native_lamports']=scanner-gross
        if scanner>0 and gross<=0:return 'SCANNER_POSITIVE_NATIVE_NONPOSITIVE'
        if scanner>0 and gross>0:return 'BOTH_GROSS_POSITIVE_NOT_NET_PROOF'
        return 'OTHER_GROSS_COMPARISON'
    if reason=='EXACT_NATIVE_GROSS_NONPOSITIVE':return 'NATIVE_GROSS_HOLD_NO_PRICE_WITNESS'
    if reason=='OK':return 'ORIGINAL_NATIVE_PROOF_RETURNED'
    return 'NO_COMPLETE_NATIVE_PRICE_WITNESS'


class NativeGrossWitness:
    """Read only observer of already-called native paths, restores hooks on all exits."""
    def __init__(self,native,q18,clock=None):
        self.native=native;self.q18=q18;self.clock=clock or time.monotonic
        self.local=threading.local();self.lock=threading.Lock();self.records=[]
        self.counts=Counter();self.old=None;self.started=self.clock()
    def __enter__(self):
        cls=self.native.NativeQ87Provider
        previous=(cls.prepare_unsigned,cls._bank,self.q18.exact_snapshot_opportunities)
        self.old=previous
        parent=self
        def prepare(provider,candidate):
            if not isinstance(candidate,dict):return previous[0](provider,candidate)
            ctx={'event_id':safe_int(candidate.get('event_id')),
                 'scanner_slot':safe_int(candidate.get('scanner_slot')),
                 'scanner_gross_hint_lamports':safe_int(candidate.get('scanner_gross_lamports_hint')),
                 'size_lamports':safe_int(candidate.get('size_lamports')),
                 'direction':candidate.get('direction') if candidate.get('direction') in
                    ('PUMP_TO_METEORA','METEORA_TO_PUMP') else 'UNKNOWN',
                 'token_prefix':str(candidate.get('token') or '')[:12],
                 'scanner_pump_pool_prefix':str(candidate.get('pump_pool') or '')[:12],
                 'scanner_dlmm_pool_prefix':str(candidate.get('meteora_pool') or '')[:12]}
            earlier=getattr(parent.local,'context',None)
            parent.local.context=ctx
            try:
                value=previous[0](provider,candidate)
                ctx['outcome_code']='OK'
                return value
            except Exception as exc:
                # Exception class and bounded symbolic reason only: no RPC URLs or secrets.
                name=str(exc)
                if len(name)>96 or not name.replace('_','').isalnum():name=type(exc).__name__
                ctx['outcome_code']=name
                raise
            finally:
                ctx['parity_class']=classification(ctx)
                with parent.lock:
                    parent.counts[ctx['parity_class']]+=1
                    parent.counts['events_observed']+=1
                    if len(parent.records)<MAX_SAMPLES or ctx['parity_class']=='SCANNER_POSITIVE_NATIVE_NONPOSITIVE':
                        parent.records.append(dict(ctx));parent.records=parent.records[-MAX_SAMPLES:]
                parent.local.context=earlier
        def bank(provider,token):
            value=previous[1](provider,token)
            ctx=getattr(parent.local,'context',None)
            if ctx is not None and isinstance(value,tuple) and len(value)>=4:
                ctx['bank_slot']=safe_int(value[0]);ctx['bank_accounts']=safe_int(value[1])
                snap=value[3]
                if isinstance(snap,dict):
                    ctx['bank_pump_pool_prefix']=str(snap.get('pump_pool',''))[:12]
                    met=snap.get('meteora') or {}
                    ctx['bank_dlmm_pool_prefix']=str(met.get('address',''))[:12] if isinstance(met,dict) else ''
                if type(ctx.get('scanner_slot')) is int and type(ctx.get('bank_slot')) is int:
                    ctx['slot_gap']=ctx['bank_slot']-ctx['scanner_slot']
            return value
        def quote(snapshot,size):
            rows=previous[2](snapshot,size)
            ctx=getattr(parent.local,'context',None)
            if ctx is not None and ctx.get('direction')=='PUMP_TO_METEORA':
                report=quote_sample(rows,ctx.get('size_lamports'),ctx['direction'])
                ctx.update(report)
            return rows
        cls.prepare_unsigned=prepare;cls._bank=bank;self.q18.exact_snapshot_opportunities=quote
        return self
    def __exit__(self,*args):
        if self.old:
            cls=self.native.NativeQ87Provider
            cls.prepare_unsigned,cls._bank,self.q18.exact_snapshot_opportunities=self.old
            self.old=None
        return False
    def report(self):
        with self.lock:
            records=[dict(x) for x in self.records];counts=dict(self.counts)
        compared=[r for r in records if type(r.get('scanner_minus_native_lamports')) is int]
        return {'events_total':counts.get('events_observed',0),'counts':counts,
                'sample_count':len(records),'paired_gross_comparisons_in_samples':len(compared),
                'witnesses':records,
                'fresh_source_and_native_gates_are_unmodified':True,
                'signing':False,'broadcast':False,'execution_authority':False}


def install():
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf8'),str(TARGET),'exec')
    if not (TARGET.parent/'oracle_385_scanner_source_unification.py').is_file():
        raise Hold('ORACLE385_NOT_INSTALLED')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:
            f.write(src);tmp=f.name
        os.replace(tmp,TARGET)
    if TARGET.read_bytes()!=src:raise Hold('ORACLE386_INSTALL_SOURCE_MISMATCH')
    print('[ORACLE386_INSTALL_PASS]',TARGET,flush=True)


def audit():
    import inspect
    if CANARY!=10_000_000 or (EXECUTION_AUTHORITY,SIGNING,BROADCAST)!=(False,False,False):
        raise Hold('NO_EXECUTION_AUTHORITY')
    text=inspect.getsource(NativeGrossWitness)
    if 'previous[0](provider,candidate)' not in text or 'previous[2](snapshot,size)' not in text:
        raise Hold('ORIGINAL_NATIVE_QUOTE_NOT_PRESERVED')
    if 'cls.prepare_unsigned,cls._bank,self.q18.exact_snapshot_opportunities=self.old' not in text:
        raise Hold('SOURCE_RESTORE_NOT_CERTIFIED')
    print('[ORACLE386_AUDIT_PASS] ORIGINAL_SAME_BANK_NATIVE_QUOTE_PRESERVED '
          'FROZEN322 NO_ADDITIONAL_RPC_WS NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)


def tests():
    class Native:
        class NativeQ87Provider:
            def _bank(self,token):return (200,4,'fake_fingerprint',{'pump_pool':'PUMPPOOL',
                                                          'meteora':{'address':'METEORAPOOL'}},12)
            def prepare_unsigned(self,candidate):
                slot,_,_,snap,_=self._bank(candidate['token'])
                out=Q.exact_snapshot_opportunities(snap,candidate['size_lamports']/1e9)
                assert slot>=candidate['scanner_slot']
                assert out[0]['local_net']<=0
                raise Hold('EXACT_NATIVE_GROSS_NONPOSITIVE')
    class Q:
        @staticmethod
        def exact_snapshot_opportunities(snap,size):
            return [{'start':10000000,'direction':'PUMP_TO_METEORA',
                     'local_net':-440,'local_min_net':-900}]
    def row():return {'event_id':12,'scanner_slot':199,'token':'TokenX','pump_pool':'PUMPPOOL',
                      'meteora_pool':'METEORAPOOL','direction':'PUMP_TO_METEORA',
                      'scanner_gross_lamports_hint':1234,'size_lamports':CANARY}
    orig_p=Native.NativeQ87Provider.prepare_unsigned
    orig_b=Native.NativeQ87Provider._bank
    orig_q=Q.exact_snapshot_opportunities
    class T(unittest.TestCase):
        def test_size(self):self.assertEqual(CANARY,10000000)
        def test_no_authority(self):self.assertFalse(EXECUTION_AUTHORITY or SIGNING or BROADCAST)
        def test_quote_match(self):
            x=quote_sample(Q.exact_snapshot_opportunities({},.01),CANARY,'PUMP_TO_METEORA')
            self.assertEqual(x['native_same_bank_gross_lamports'],-440)
        def test_quote_missing(self):
            self.assertEqual(quote_sample([],CANARY,'PUMP_TO_METEORA')['row_contract'],'MISSING_OR_NONUNIQUE')
        def test_refuses_float_start(self):
            self.assertEqual(quote_sample([{'start':1e7,'direction':'PUMP_TO_METEORA'}],CANARY,
                                          'PUMP_TO_METEORA')['matching_rows'],0)
        def test_classification(self):
            self.assertEqual(classification({'scanner_gross_hint_lamports':5,
                'native_same_bank_gross_lamports':-1}),'SCANNER_POSITIVE_NATIVE_NONPOSITIVE')
        def test_diff(self):
            x={'scanner_gross_hint_lamports':5,'native_same_bank_gross_lamports':-1};classification(x)
            self.assertEqual(x['scanner_minus_native_lamports'],6)
        def test_hooks_original_after_context(self):
            with NativeGrossWitness(Native,Q):pass
            self.assertIs(Native.NativeQ87Provider.prepare_unsigned,orig_p)
            self.assertIs(Native.NativeQ87Provider._bank,orig_b)
        def test_quote_restored(self):
            with NativeGrossWitness(Native,Q):pass
            self.assertIs(Q.exact_snapshot_opportunities,orig_q)
        def test_negative_gross_capture(self):
            with NativeGrossWitness(Native,Q) as o:
                with self.assertRaises(Hold):Native.NativeQ87Provider().prepare_unsigned(row())
                rep=o.report()
            self.assertEqual(rep['counts']['SCANNER_POSITIVE_NATIVE_NONPOSITIVE'],1)
            self.assertEqual(rep['witnesses'][0]['bank_slot'],200)
            self.assertEqual(rep['witnesses'][0]['slot_gap'],1)
        def test_propagates_original_holds(self):
            with NativeGrossWitness(Native,Q):
                with self.assertRaisesRegex(Hold,'EXACT_NATIVE_GROSS_NONPOSITIVE'):
                    Native.NativeQ87Provider().prepare_unsigned(row())
        def test_restores_on_exception(self):
            with self.assertRaises(Hold):
                with NativeGrossWitness(Native,Q):raise Hold('TEST')
            self.assertIs(Native.NativeQ87Provider.prepare_unsigned,orig_p)
        def test_nongross(self):
            self.assertEqual(classification({'outcome_code':'BANK_SLOT_DRIFT_REJECT'}),
                             'NO_COMPLETE_NATIVE_PRICE_WITNESS')
        def test_safe_int(self):
            self.assertIsNone(safe_int(1.0));self.assertIsNone(safe_int(True))
        def test_bounded_samples(self):self.assertEqual(MAX_SAMPLES,120)
        def test_secret_not_copied(self):
            x=NativeGrossWitness(Native,Q).report()
            self.assertNotIn('private',json.dumps(x).lower())
        def test_audit(self):audit()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE386_TEST_PASS]' if result.wasSuccessful() else '[ORACLE386_TEST_FAIL]',result.testsRun,flush=True)
    return 0 if result.wasSuccessful() else 1


def run(minutes,poll_ms,wallet):
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUNTIME_BOUNDS_INVALID')
    if not wallet or len(wallet)<32:raise Hold('PUBLIC_WALLET_REQUIRED')
    audit()
    m385,native,q18=deps()
    initial=m385.self_check() # mandatory exact certified scanner health; no bypass
    code=2;start=time.monotonic();witness=NativeGrossWitness(native,q18)
    status='READ_ONLY_HOLD'
    try:
        with witness:
            code=m385.run(minutes,poll_ms,wallet)
        status='READ_ONLY_COMPLETE' if code==0 else 'READ_ONLY_HOLD'
    finally:
        rep=witness.report()
        rep.update({'build':'ORACLE386','status':status,'duration_s':round(time.monotonic()-start,2),
                    'first_canary_lamports':CANARY,'scanner_precheck_epoch':initial.get('epoch'),
                    'scanner_source_precheck':'CERTIFIED_ORACLE385',
                    'trading_enabled':False,'private_key_used':False})
        dump(REPORT,rep)
        print('[ORACLE386_PRICE_PARITY_SUMMARY]',json.dumps({k:rep[k] for k in
               ('events_total','counts','paired_gross_comparisons_in_samples','sample_count')},sort_keys=True),flush=True)
        for x in rep['witnesses'][-8:]:
            print('[ORACLE386_PRICE_PARITY_WITNESS]',json.dumps(x,sort_keys=True),flush=True)
        print('[ORACLE386_REPORT]',REPORT,flush=True)
        print('[ORACLE386_STATUS]',status,flush=True)
    return code


def main():
    p=argparse.ArgumentParser()
    for x in ('install','test','audit','health-gate','inspect','run'):
        p.add_argument('--'+x,action='store_true')
    p.add_argument('--minutes',type=int,default=5)
    p.add_argument('--poll-ms',type=int,default=5)
    p.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    x=p.parse_args()
    if not any(getattr(x,a.replace('-','_')) for a in ('install','test','audit','health-gate','inspect','run')):
        p.error('ACTION_REQUIRED')
    if x.install:install()
    if x.test and tests():return 1
    if x.audit:audit()
    if x.health_gate:
        try:
            m385,_,_=deps()
            print('[ORACLE386_HEALTH_GATE_PASS]',json.dumps(m385.self_check(),sort_keys=True),flush=True)
        except Exception as exc:
            print('[ORACLE386_HEALTH_GATE_HOLD]',type(exc).__name__,flush=True);return 2
    if x.inspect:print('[ORACLE386_INSPECT]',json.dumps(load(REPORT),sort_keys=True),flush=True)
    if x.run:return run(x.minutes,x.poll_ms,x.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('[ORACLE386_HOLD]',type(exc).__name__,flush=True)
        raise SystemExit(2)
