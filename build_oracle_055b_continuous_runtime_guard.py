"""Complete ORACLE-055B installer. Does not change ORACLE-054, Q25, Q20, Q18 or Mriya."""
from pathlib import Path
from hashlib import sha256
import os
import tempfile

root = Path.cwd()
pkg = root / 'qseries_v2/oracle_execution/solana_atomic_executor'
source = pkg / 'oracle_054_reverse_native_handoff.py'
output = pkg / 'oracle_055_parity_simulation_guard.py'
testfile = root / 'test_oracle_055_parity_simulation_guard.py'
if not source.is_file():
    raise SystemExit('[HOLD] Missing ORACLE-054 original; nothing changed')
if not (root/'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py').is_file():
    raise SystemExit('[HOLD] Missing original Q18; nothing changed')
if output.exists() and 'ORACLE054_SHA256' not in output.read_text(encoding='utf-8',errors='replace'):
    raise SystemExit('[HOLD] Existing ORACLE-055 is unknown; nothing changed')
if testfile.exists() and 'test_01_source_lock' not in testfile.read_text(encoding='utf-8',errors='replace'):
    raise SystemExit('[HOLD] Existing ORACLE-055 test is unknown; nothing changed')
digest = sha256(source.read_bytes()).hexdigest()

code = r'''from __future__ import annotations
import argparse, contextlib, hashlib, importlib, json, os, re, runpy, sys, threading, time
from pathlib import Path
ORACLE054_SHA256 = "__SHA__"
PREV = Path(__file__).with_name('oracle_054_reverse_native_handoff.py')
REPORT = Path('runtime_state/oracle/oracle_live_execution/oracle_055_parity_simulation_guard.json')
MIN_SIZE_SOL = 0.010
EXECUTION_AUTHORITY = SIGNING = BROADCAST = False
DIRECTIONS = ('METEORA_TO_PUMP', 'PUMP_TO_METEORA')

def unchanged_source(path=PREV, expected=ORACLE054_SHA256):
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected

def safe(value):
    s = str(value)
    s = re.sub(r'(?i)(api-key|authorization|private_key|secret|token)=([^\s&]+)', r'\1=[REDACTED]', s)
    s = re.sub(r'(?:https?|wss?)://[^\s]+', '[URL_REDACTED]', s)
    return s[:350]

def state_digest(s):
    fields = ('token','pump_pool','pump_base_reserve','pump_quote_reserve','meteora','lb_bytes','arrays_raw')
    if not isinstance(s, dict) or any(k not in s for k in fields): return None
    def clean(v):
        if isinstance(v, bytes): return {'hash':hashlib.sha256(v).hexdigest(),'length':len(v)}
        if isinstance(v, dict): return {str(k):clean(v[k]) for k in sorted(v)}
        if isinstance(v, (list,tuple)): return [clean(x) for x in v]
        if isinstance(v, (str,int,float,bool)) or v is None: return v
        return {'unverified_type':type(v).__name__}
    raw=json.dumps({k:clean(s[k]) for k in fields},sort_keys=True,separators=(',',':'))
    return hashlib.sha256(raw.encode()).hexdigest()

def compare_quote(a,b):
    for k in ('token','direction','size_sol','pump_pool','meteora_pool'):
        if a.get(k)!=b.get(k): return 'NOT_COMPARABLE_ROUTE'
    if not a.get('state_sha256') or not b.get('state_sha256'): return 'HOLD_NO_IMMUTABLE_STATE_PROOF'
    if a['state_sha256']!=b['state_sha256']: return 'STATE_CHANGED_NOT_PRICE_PARITY_PROOF'
    try: return 'SAME_STATE_PRICER_PARITY' if abs(float(a['bps'])-float(b['bps']))<=.05 else 'SAME_STATE_PRICE_DIVERGENCE'
    except (KeyError,ValueError,TypeError): return 'HOLD_MISSING_PRICE_EVIDENCE'

def simulation_diagnostic(v):
    v = v.get('value',v) if isinstance(v,dict) else {}
    if not isinstance(v,dict): return {'category':'INVALID_SIMULATION_ENVELOPE','verified':False}
    err=v.get('err','MISSING_ERR_FIELD'); units=v.get('unitsConsumed'); logs=v.get('logs') or []
    e=str(err).lower(); lines=' '.join(str(x) for x in logs[-10:]).lower()
    if err is None and isinstance(units,int) and units>0: category='SIM_EXECUTED_NO_PROFIT_CERTIFICATION'
    elif 'blockhash' in e: category='BLOCKHASH_OR_FRESHNESS_REJECT'
    elif 'account' in e or 'account' in lines: category='ACCOUNT_OR_PROGRAM_REJECT'
    elif 'instructionerror' in e or 'custom program error' in lines: category='PROGRAM_INSTRUCTION_REJECT'
    elif not units: category='REJECTED_WITHOUT_REPORTED_COMPUTE'
    else: category='SIMULATION_REJECTED'
    return {'category':category,'verified':False,'err_summary':safe(err),
            'units_consumed':units if isinstance(units,int) else None,
            'log_tail':[safe(x) for x in logs[-4:] if isinstance(x,str)]}

def atomic_gate(r):
    required=('size_sol','direction','venue_order','source_fresh','accounts_reconciled','sim_err',
              'sim_units','fees_complete','residue_raw','net_lamports','atomic_two_legs','state_parity_verified')
    missing=[k for k in required if k not in r]
    if missing: return 'HOLD_MISSING_'+','.join(missing)
    try:
        if float(r['size_sol'])<MIN_SIZE_SOL: return 'HOLD_BELOW_010_CANARY_MINIMUM'
    except (TypeError,ValueError): return 'HOLD_INVALID_SIZE'
    if r['direction'] not in DIRECTIONS: return 'HOLD_UNKNOWN_DIRECTION'
    order=('METEORA','PUMPSWAP') if r['direction']==DIRECTIONS[0] else ('PUMPSWAP','METEORA')
    if tuple(r['venue_order'])!=order: return 'HOLD_REVERSED_NATIVE_LEG_ORDER'
    if r['sim_err'] is not None or not isinstance(r['sim_units'],int) or r['sim_units']<=0:
        return 'HOLD_FAILED_ATOMIC_SIMULATION'
    if not all(r[k] is True for k in ('source_fresh','accounts_reconciled','fees_complete',
                                      'atomic_two_legs','state_parity_verified')): return 'HOLD_INCOMPLETE_ATOMIC_PROOF'
    if r['residue_raw']!=0: return 'HOLD_INTERMEDIATE_TOKEN_RESIDUE'
    if not isinstance(r['net_lamports'],int) or r['net_lamports']<=0: return 'HOLD_NONPOSITIVE_NET_AFTER_ALL_FEES'
    return 'UNSIGNED_SIMULATION_EVIDENCE_ONLY_NO_BROADCAST'

class QuoteProbe:
    def __init__(self):
        self.rows=0; self.last={}; self.transitions={}; self.samples=[]; self.errors=[]; self.lock=threading.Lock()
    def observe(self,snap,size,rows):
        digest=state_digest(snap)
        if not isinstance(snap,dict): return
        slot=int(snap.get('source_slot') or 0); event=int(snap.get('source_event_ns') or 0)
        phase='EVENT_TAGGED' if slot>0 and event>0 else 'UNKNOWN_NOT_TRUSTED_AS_LIVE'
        with self.lock:
            for r in rows if isinstance(rows,(list,tuple)) else ():
                if not isinstance(r,dict): continue
                pool=r.get('meteora') if isinstance(r.get('meteora'),dict) else {}
                key=(str(r.get('token')),str(r.get('direction')),str(r.get('size_sol')))
                item={'token':key[0],'direction':key[1],'size_sol':r.get('size_sol'),
                      'pump_pool':r.get('pump_pool'),'meteora_pool':pool.get('address'),
                      'slot':slot,'phase':phase,'state_sha256':digest,'bps':r.get('local_bps')}
                self.rows+=1
                if key in self.last:
                    prev=self.last[key]; result=compare_quote(prev,item)
                    self.transitions[result]=self.transitions.get(result,0)+1
                    if result!='SAME_STATE_PRICER_PARITY' and len(self.samples)<20:
                        self.samples.append({'token':key[0][:12],'direction':key[1],
                          'previous_slot':prev['slot'],'slot':slot,'result':result,
                          'previous_bps':prev['bps'],'bps':item['bps']})
                self.last[key]=item
    def snapshot(self):
        with self.lock: return self.rows,dict(self.transitions),list(self.samples),list(self.errors)

class Monitor:
    def __init__(self,downstream):
        self.out=downstream; self.partial=''; self.lines=0; self.live=[]; self.startup=[]
        self.rejected=0; self.zero_units=0; self.rejections=[]; self.mriya=0; self.shards=set()
    def write(self,s):
        self.out.write(s); self.partial+=s
        while '\n' in self.partial:
            line,self.partial=self.partial.split('\n',1); self.consume(line[:4000])
        if len(self.partial)>8192: self.partial=''
        return len(s)
    def flush(self): self.out.flush()
    def isatty(self): return False
    @property
    def encoding(self): return getattr(self.out,'encoding','utf-8')
    def consume(self,line):
        self.lines+=1; low=line.lower()
        if 'mriya' in low: self.mriya+=1
        if 'websocket' in low or 'ws_shard' in low:
            m=re.search(r'(?:shards|ws_shards)=([0-9]+)',low)
            if m: self.shards.add(int(m.group(1)))
        if 'bps=' in low and any(x in low for x in ('exact','startup','hydrated')):
            m=re.search(r'bps=([+-]?[0-9.]+)',line)
            if m:
                target=self.live if any(x in low for x in ('exact_latest','exact_immutable')) else self.startup
                if len(target)<3000: target.append(float(m.group(1)))
        if any(x in low for x in ('rejected','sim_err','simulation error')):
            self.rejected+=1
            if re.search(r'(?:units|units_consumed|unitsconsumed)[=: ]+0\b',low): self.zero_units+=1
            if len(self.rejections)<20: self.rejections.append(safe(line))

def child_argv(seconds):
    if not isinstance(seconds,int) or isinstance(seconds,bool) or seconds<=0:
        raise ValueError('ORACLE055_SECONDS_MUST_BE_POSITIVE_INTEGER')
    return [str(PREV),'--run','--seconds',str(seconds),'--cycles','1']

def save_report(probe,mon,rc,failure=None,complete=False):
    rows,counts,samples,errors=probe.snapshot()
    data={'build':'ORACLE-055B','status':'HOLD_NO_EXECUTABLE_PROFIT_CERTIFICATION',
          'report_complete':bool(complete),'oracle_054_source_unchanged':unchanged_source(),
          'oracle_054_sha256':ORACLE054_SHA256,'single_original_scanner':True,
          'signing_added':False,'broadcast_added':False,'first_canary_sol':0.010,
          'quote_probe_rows':rows,'quote_state_transition_counts':counts,
          'quote_transition_samples':samples,'probe_errors':errors,
          'log_lines':mon.lines,'live_exact_log_rows':len(mon.live),
          'startup_or_unknown_price_rows':len(mon.startup),
          'startup_max_bps':max(mon.startup,default=None),'live_max_bps':max(mon.live,default=None),
          'simulation_rejection_lines':mon.rejected,'rejected_zero_unit_lines':mon.zero_units,
          'simulation_rejection_samples':list(mon.rejections),'mriya_log_lines':mon.mriya,
          'seen_websocket_shard_counts':sorted(mon.shards),
          'mriya_replenishment_certified':False,'native_correction_certified':False,
          'executable_profit_certified':False,'exit_code':rc,'failure':safe(failure) if failure else None}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    temp=REPORT.with_suffix('.json.tmp');temp.write_text(json.dumps(data,indent=2,sort_keys=True),encoding='utf-8')
    os.replace(temp,REPORT)
    return data

def run(seconds):
    if not unchanged_source(): raise RuntimeError('ORACLE054_SOURCE_DRIFT_REINSTALL_REQUIRED')
    argv=child_argv(seconds)
    q18=importlib.import_module('qseries_v2.oracle_execution.oracle_018_exact_sdk_hot_lane_cutover')
    original=q18.exact_snapshot_opportunities; probe=QuoteProbe(); mon=Monitor(sys.stdout)
    def measured(snap,size):
        rows=original(snap,size)
        try: probe.observe(snap,size,rows)
        except Exception as exc:
            with probe.lock:
                if len(probe.errors)<10: probe.errors.append(type(exc).__name__)
        return rows
    q18.exact_snapshot_opportunities=measured
    old_argv=sys.argv[:]; sys.argv=argv; stopped=threading.Event(); rc=0; failure=None
    def checkpoint():
        while not stopped.wait(60):
            try:
                save_report(probe,mon,None,complete=False)
                print('[ORACLE055_CHECKPOINT]',REPORT,flush=True)
            except Exception as exc: print('[ORACLE055_CHECKPOINT_ERROR]',type(exc).__name__,flush=True)
    thread=threading.Thread(target=checkpoint,daemon=True);thread.start()
    try:
        with contextlib.redirect_stdout(mon):
            try: runpy.run_module('qseries_v2.oracle_execution.solana_atomic_executor.oracle_054_reverse_native_handoff',run_name='__main__')
            except SystemExit as exc: rc=exc.code if isinstance(exc.code,int) else int(bool(exc.code))
    except BaseException as exc:
        rc=130 if isinstance(exc,KeyboardInterrupt) else 1
        failure=type(exc).__name__+':'+safe(exc)
        print('[ORACLE055_CHILD_STOP]',type(exc).__name__,flush=True)
    finally:
        stopped.set();thread.join(timeout=2);sys.argv=old_argv;q18.exact_snapshot_opportunities=original
        save_report(probe,mon,rc,failure,complete=True)
        print('[ORACLE055_REPORT]',REPORT,flush=True)
        print('[ORACLE055_HOLD] No executable profit certified; signing/broadcast unchanged',flush=True)
    return rc

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--audit',action='store_true')
    p.add_argument('--run',action='store_true');p.add_argument('--seconds',type=int,default=86400)
    a=p.parse_args(argv)
    if a.test:
        import unittest
        from test_oracle_055_parity_simulation_guard import Tests
        r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if r.wasSuccessful() else 1
    if a.audit:
        print('[ORACLE055_SOURCE]','PASS' if unchanged_source() else 'HOLD_SOURCE_DRIFT')
        print('[CHILD_SECONDS_ARG]',child_argv(86400)[3]);print('[SCANNER] ORIGINAL_Q25_Q20_Q18_PRESERVED')
        print('[MONEY] SIGNING_FALSE BROADCAST_FALSE PROFIT_NOT_CERTIFIED')
        return 0 if unchanged_source() else 1
    if a.run: return run(a.seconds)
    p.print_help();return 0
if __name__=='__main__': raise SystemExit(main())
'''.replace('__SHA__',digest)

tests = r'''import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_055_parity_simulation_guard as m
class Tests(unittest.TestCase):
    def good(self):
        return {'size_sol':.010,'direction':'METEORA_TO_PUMP','venue_order':['METEORA','PUMPSWAP'],
                'source_fresh':True,'accounts_reconciled':True,'sim_err':None,'sim_units':1000,
                'fees_complete':True,'residue_raw':0,'net_lamports':100,'atomic_two_legs':True,
                'state_parity_verified':True}
    def row(self):
        return {'token':'t','direction':'METEORA_TO_PUMP','size_sol':.010,'pump_pool':'p',
                'meteora_pool':'m','bps':99,'state_sha256':'a'}
    def test_01_source_lock(self): self.assertTrue(m.unchanged_source())
    def test_02_child_seconds_integer(self): self.assertEqual(m.child_argv(86400)[3],'86400')
    def test_03_fractional_child_rejected(self):
        with self.assertRaises(ValueError): m.child_argv(86400.0)
    def test_04_child_one_scanner(self): self.assertEqual(m.child_argv(86400)[-2:],['--cycles','1'])
    def test_05_state_hash_reproducible(self):
        s=dict(token='t',pump_pool='p',pump_base_reserve=3,pump_quote_reserve=4,
               meteora={'address':'m'},lb_bytes=b'a',arrays_raw=((1,2,b'b'),))
        self.assertEqual(m.state_digest(s),m.state_digest(dict(reversed(list(s.items())))))
    def test_06_missing_state_unknown(self): self.assertIsNone(m.state_digest({'token':'t'}))
    def test_07_state_change(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,state_sha256='b')),'STATE_CHANGED_NOT_PRICE_PARITY_PROOF')
    def test_08_same_state_divergence(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,bps=-10)),'SAME_STATE_PRICE_DIVERGENCE')
    def test_09_same_state_parity(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,bps=99.01)),'SAME_STATE_PRICER_PARITY')
    def test_10_minimum_canary(self):
        r=self.good();r['size_sol']=.005;self.assertEqual(m.atomic_gate(r),'HOLD_BELOW_010_CANARY_MINIMUM')
    def test_11_reverse_order(self):
        r=self.good();r['venue_order']=['PUMPSWAP','METEORA'];self.assertEqual(m.atomic_gate(r),'HOLD_REVERSED_NATIVE_LEG_ORDER')
    def test_12_sim_rejected(self):
        r=self.good();r['sim_units']=0;r['sim_err']={'InstructionError':[0,1]}
        self.assertEqual(m.atomic_gate(r),'HOLD_FAILED_ATOMIC_SIMULATION')
    def test_13_fee_and_residue(self):
        r=self.good();r['residue_raw']=1;self.assertEqual(m.atomic_gate(r),'HOLD_INTERMEDIATE_TOKEN_RESIDUE')
        r=self.good();r['fees_complete']=False;self.assertEqual(m.atomic_gate(r),'HOLD_INCOMPLETE_ATOMIC_PROOF')
    def test_14_unsigned_only(self):
        self.assertEqual(m.atomic_gate(self.good()),'UNSIGNED_SIMULATION_EVIDENCE_ONLY_NO_BROADCAST')
        self.assertFalse(m.EXECUTION_AUTHORITY or m.BROADCAST or m.SIGNING)
    def test_15_redaction(self): self.assertNotIn('SUPERSECRET',m.safe('https://x/?api-key=SUPERSECRET'))
    def test_16_sim_envelope(self):
        self.assertFalse(m.simulation_diagnostic({'value':{'err':'InstructionError','unitsConsumed':0}})['verified'])
    def test_17_source_drift(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_text('changed');self.assertFalse(m.unchanged_source(p,'deadbeef'))
    def test_18_no_evidence(self): self.assertTrue(m.atomic_gate({}).startswith('HOLD_MISSING_'))
if __name__=='__main__': unittest.main(verbosity=2)
'''

pkg.mkdir(parents=True,exist_ok=True)
for path, content in ((output,code),(testfile,tests)):
    stage=path.with_suffix(path.suffix+'.tmp')
    stage.write_text(content,encoding='utf-8')
    compile(content,str(stage),'exec')
    os.replace(stage,path)
print('[PASS] ORACLE-055B installed full monitor and tests')
print('[PRESERVED] ORACLE-054 sha256='+digest[:16])
print('[FIXED] child --seconds is integer; --cycles=1')
print('[CHECKPOINT] JSON report updated during continuous runtime every 60 seconds')
print('[MONEY] ORACLE-054 unchanged; no new signing or broadcasting')
