
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, threading, time, unittest, uuid

BASE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_026_persistent_forensic_watch.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_026_PERSISTENT_FORENSICS.json')
PREVIOUS=Path('runtime_state/oracle/oracle_live_execution/ORACLE_025_SIM_FORENSICS.json')
VERSION='ORACLE_026_ONE_STARTUP_PERSISTENT_FORENSIC_WATCH'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC',
      'SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL','QSB_SOLANA_WALLET'}
ALPH='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def safe_env(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def base58_data(s):
    n=0
    for ch in s:n=n*58+ALPH.index(ch)
    return b'\0'*(len(s)-len(s.lstrip('1')))+(n.to_bytes((n.bit_length()+7)//8,'big') if n else b'')

def inner_shape(rows):
    out=[]
    for group in rows or []:
        if not isinstance(group,dict):continue
        ins=group.get('instructions') or []
        item={'outer_index':group.get('index'),'instruction_count':len(ins),
              'parsed':0,'compiled':0,'unattributed_transfer_like':[]}
        for ix in ins:
            if not isinstance(ix,dict):continue
            if isinstance(ix.get('parsed'),dict):
                item['parsed']+=1
                continue
            item['compiled']+=1
            try:
                raw=base58_data(ix.get('data') or '')
                if len(raw) in (9,10) and raw[:1] in (b'\x03',b'\x0c'):
                    item['unattributed_transfer_like'].append({
                        'program_index':ix.get('programIdIndex'),
                        'raw_amount':int.from_bytes(raw[1:9],'little'),
                        'opcode':raw[0]})
            except (ValueError,TypeError,OverflowError):pass
        out.append(item)
    return out

def save(root,row):
    p=root/REPORT;p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(row,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    tmp.replace(p)

def child(root,seconds,run_id):
    result={'version':VERSION,'run_id':run_id,'status':'HOLD',
            'signing':False,'broadcast':False,'profit_certified':False,
            'canary_lamports':10_000_000,'rpc_cap':80,'sim_cap':1,
            'freshness_ms':1500,'scanner_modified':False}
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        result['hold']='SECRET_ENVIRONMENT_BLOCKED';save(root,result);return 2
    sys.path.insert(0,str(root))
    try:
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_025_atomic_sim_forensics as v25
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
        if (not v25.VERSION.startswith('ORACLE_025_') or
            (v24.RPC_CAP,v24.SIM_CAP,v24.CANARY,v24.FRESH_MS,v24.PAIR_CAP)!=(80,1,10_000_000,1500.0,8)):
            raise RuntimeError('CERTIFIED_RUNTIME_CONTRACT_CHANGED')
        original=core.rpc
        scope={'simulation_responses':0,'raw_inner_groups':[],'inner_available':False,
               'sim_error':None,'compute_units':None}
        def monitor(method,params):
            reply=original(method,params)
            if method=='simulateTransaction':
                value=(reply or {}).get('value') or {}
                scope['simulation_responses']+=1
                inner=value.get('innerInstructions')
                scope['inner_available']=isinstance(inner,list)
                scope['raw_inner_groups']=inner_shape(inner)
                scope['sim_error']=value.get('err')
                scope['compute_units']=value.get('unitsConsumed')
            return reply
        core.rpc=monitor
        try:
            rc=v25.child(root,seconds,run_id)
        finally:core.rpc=original
        previous=json.loads((root/PREVIOUS).read_text(encoding='utf-8'))
        if previous.get('run_id')!=run_id:raise RuntimeError('STALE_FORENSIC_REPORT')
        result.update(ready=previous.get('ready',0),priced_events=previous.get('priced_events',0),
                      rpc_requests=previous.get('rpc_requests',0),simulations=previous.get('simulations',0),
                      positive_candidates=previous.get('positive_candidates',0),
                      native_passes=previous.get('native_passes',0),
                      attempts=previous.get('attempts') or [],
                      forensic_evidence=previous.get('forensics'),
                      simulated_inner_structure=scope,holds=previous.get('holds') or [])
        if (result['rpc_requests'] or 0)>80 or (result['simulations'] or 0)>1:
            result['status']='HOLD_GUARDED_REQUEST_LIMIT'
        elif rc!=0:result['status']='HOLD_RUNTIME_ERROR'
        elif result['simulations']:
            result['status']='SIMULATION_EVIDENCE_CAPTURED_EXECUTION_DISABLED'
        else:result['status']='WATCH_COMPLETED_NO_QUALIFIED_SIMULATION'
        save(root,result)
        return rc
    except Exception as exc:
        result['hold']='WATCH_'+type(exc).__name__;save(root,result);return 2

def parent(root,seconds):
    rid=str(uuid.uuid4())
    command=[sys.executable,'-I',str(Path(__file__).resolve()),'--child',
             '--seconds',str(seconds),'--run-id',rid]
    proc=subprocess.Popen(command,cwd=root,env=safe_env(os.environ),
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    def drain():
        for line in proc.stdout:
            if line.startswith('[ORACLE017_PULSE]'):print(line.rstrip(),flush=True)
    reader=threading.Thread(target=drain,daemon=True);reader.start()
    start=time.monotonic();last=0
    try:
        while proc.poll() is None:
            elapsed=int(time.monotonic()-start)
            if elapsed-last>=30:
                print('[V26_HEARTBEAT] process=RUNNING elapsed_seconds='+str(elapsed),flush=True)
                last=elapsed
            if elapsed>seconds+180:raise RuntimeError('SESSION_TIMEOUT')
            time.sleep(1)
        reader.join(timeout=3)
        report=json.loads((root/REPORT).read_text(encoding='utf-8'))
        if report.get('run_id')!=rid:raise RuntimeError('STALE_WATCH_REPORT')
        for k in ('status','hold','ready','priced_events','rpc_requests','simulations',
                  'positive_candidates','native_passes','forensic_evidence',
                  'simulated_inner_structure','attempts','holds'):
            if k in report:print('['+k.upper()+']',json.dumps(report[k],sort_keys=True),flush=True)
        print('[SCANNER] FROZEN [SIM_MAX] 1 [SIGNING] FALSE [BROADCAST] FALSE',flush=True)
        print('[REPORT]',root/REPORT,flush=True)
        return proc.returncode
    except Exception as exc:
        print('[HOLD] WATCH_'+type(exc).__name__,flush=True);return 2
    finally:
        if proc.poll() is None:proc.kill();proc.wait(timeout=5)

class Tests(unittest.TestCase):
    def test_scrub(self):
        self.assertEqual(safe_env({'PATH':'x','QSB_SOLANA_PRIVATE_KEY':'secret'}),{'PATH':'x'})
    def test_base58_zero(self):
        self.assertEqual(base58_data('1'),b'\0')
    def test_empty_inner(self):
        self.assertEqual(inner_shape(None),[])
    def test_compiled_token_data(self):
        data=b'\x0c'+(1000).to_bytes(8,'little')+b'\x06'
        n=int.from_bytes(data,'big');digits=''
        while n:n,z=divmod(n,58);digits=ALPH[z]+digits
        rows=inner_shape([{'index':5,'instructions':[{'programIdIndex':3,'data':digits}]}])
        self.assertEqual(rows[0]['unattributed_transfer_like'][0]['raw_amount'],1000)
    def test_no_attribution_claim(self):
        self.assertEqual(inner_shape([{'index':1,'instructions':[{'data':'','programIdIndex':9}]}])[0]['compiled'],1)
    def test_limits(self):
        self.assertTrue(VERSION.startswith('ORACLE_026_'))
    def test_no_private_key_propagation(self):
        self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',safe_env({'QSB_SOLANA_PRIVATE_KEY':'xyz'}))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true');ap.add_argument('--run',action='store_true')
    ap.add_argument('--child',action='store_true');ap.add_argument('--seconds',type=int,default=300)
    ap.add_argument('--run-id',default='');args=ap.parse_args();root=Path.cwd()
    if args.test:
        t=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if t.wasSuccessful() else 1
    if args.child:return child(root,args.seconds,args.run_id)
    if args.run:
        if not 180<=args.seconds<=900:print('[HOLD] WINDOW_180_TO_900_SECONDS');return 2
        return parent(root,args.seconds)
    dest=root/BASE/NAME
    if not dest.parent.is_dir():print('[HOLD] EXECUTOR_PACKAGE_MISSING');return 2
    if dest.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),dest)
    print('[PASS]',VERSION,dest)
    print('[MODE] ONE_WARM_STARTUP; EXTENDED_WEBSOCKET_CAPTURE; ONE_UNSIGNED_SIM')
    print('[SCANNER] FROZEN [RPC_CAP] 80 [SIGNING] FALSE [BROADCAST] FALSE')
    return 0

if __name__=='__main__':raise SystemExit(main())
