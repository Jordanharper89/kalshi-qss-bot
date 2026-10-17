
from pathlib import Path
import argparse, asyncio, json, math, os, shutil, subprocess, sys, unittest, uuid

VERSION='ORACLE_049_LIVE_OPPORTUNITY_LEDGER'
PKG=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_049_live_opportunity_ledger.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_049_OPPORTUNITIES.json')
CANARY=10_000_000

def finite(value):
    if type(value) not in (int,float):return None
    try:
        return float(value) if math.isfinite(float(value)) else None
    except (OverflowError,ValueError):return None

def safe_quote(quote):
    if not isinstance(quote,dict):return {}
    allowed=('fee','amount','gross','net','bps','lamport','raw_in','raw_out','input','output','min_out')
    return {str(k)[:48]:x for k,v in quote.items() if any(t in str(k).lower() for t in allowed)
            if (x:=finite(v)) is not None}

class Ledger:
    def __init__(self):self.rows={};self.errors={};self.evaluations=0;self.positives=0

    def add(self,direction,snapshot,quote):
        token=str(snapshot.get('token') or '') if isinstance(snapshot,dict) else ''
        if not token:return
        self.evaluations+=1
        net=finite(quote.get('local_net')) if isinstance(quote,dict) else None
        key=(token,direction)
        entry=self.rows.setdefault(key,{'token':token[:12],'direction':direction,
                                        'observations':0,'positive':0,'negative':0,'missing':0,
                                        'best_net':None,'last_net':None,'best_numeric_fields':{}})
        entry['observations']+=1;entry['last_net']=net
        if net is None:entry['missing']+=1;return
        if net>0:entry['positive']+=1;self.positives+=1
        else:entry['negative']+=1
        if entry['best_net'] is None or net>entry['best_net']:
            entry['best_net']=net;entry['best_numeric_fields']=safe_quote(quote)

    def error(self,direction,exc):
        key=direction+'_'+type(exc).__name__
        self.errors[key]=self.errors.get(key,0)+1

    def report(self):
        ranked=sorted(self.rows.values(),key=lambda x:(x['best_net'] is not None,x['best_net'] or 0),reverse=True)
        return {'evaluations':self.evaluations,'positive_quotes':self.positives,
                'quote_errors':self.errors,'directions':{x:sum(y['observations'] for y in self.rows.values()
                    if y['direction']==x) for x in ('PUMP_TO_METEORA','METEORA_TO_PUMP')},
                'ranked_pairs':ranked[:24]}

def write(root,runtime,ledger,rid,status):
    result={'revision':VERSION,'run_id':rid,'status':status,'live':runtime.report(),
            'quotes':ledger.report(),'native_execution_ready':False,'simulations':0,
            'signing':False,'broadcast':False,'canary_lamports':CANARY}
    path=root/REPORT;path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8');temp.replace(path)
    return result

async def observe(root,minutes,rid):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_047_final_live_replenishment as v47
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_024_fresh_candidate_revalidation as v24
    runtime=v47.Runtime(root,minutes,rid);ledger=Ledger()
    originals={}
    for name,direction in (('quote_p2m','PUMP_TO_METEORA'),('quote_m2p','METEORA_TO_PUMP')):
        fn=getattr(v24,name);originals[name]=fn
        def wrapped(*args,_fn=fn,_dir=direction,**kwargs):
            snap=args[1] if len(args)>1 else kwargs.get('snap',{})
            try:result=_fn(*args,**kwargs)
            except Exception as exc:
                ledger.error(_dir,exc)
                raise
            ledger.add(_dir,snap,result)
            return result
        setattr(v24,name,wrapped)

    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            report=write(root,runtime,ledger,rid,'OBSERVING')
            ranked=report['quotes']['ranked_pairs']
            best=ranked[0] if ranked else None
            print('[OPPORTUNITY] generations=%d active=%d quotes=%d positive=%d best_net=%s direction=%s errors=%s'%(
                runtime.generations,len(runtime.active),ledger.evaluations,ledger.positives,
                best['best_net'] if best else None,best['direction'] if best else None,
                json.dumps(ledger.errors,sort_keys=True)),flush=True)

    write(root,runtime,ledger,rid,'STARTING')
    beat=asyncio.create_task(heartbeat())
    try:
        await runtime.serve()
    finally:
        beat.cancel();await asyncio.gather(beat,return_exceptions=True)
        for name,fn in originals.items():setattr(v24,name,fn)
        write(root,runtime,ledger,rid,'ENDED')

def child(root,minutes,rid):
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        print('[HOLD] SECRET_ENVIRONMENT_REFUSED');return 2
    try:asyncio.run(observe(root,minutes,rid));return 0
    except KeyboardInterrupt:return 130
    except Exception as exc:
        print('[HOLD]',type(exc).__name__);return 2

def parent(root,minutes):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_047_final_live_replenishment as v47
    rid=str(uuid.uuid4())
    cmd=[sys.executable,'-I','-u',str(Path(__file__).resolve()),'--child','--minutes',str(minutes),'--run-id',rid]
    env=v47.scrub(os.environ);env['PYTHONIOENCODING']='utf-8'
    p=subprocess.Popen(cmd,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                       text=True,encoding='utf-8',errors='replace',bufsize=1)
    try:
        for line in p.stdout:
            if line.startswith(('[GENERATION]','[PRICING]','[OPPORTUNITY]','[HOLD]')):
                print(line.rstrip(),flush=True)
        p.wait()
    except KeyboardInterrupt:
        p.terminate()
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:p.kill();p.wait()

    path=root/REPORT
    if path.is_file():
        result=json.loads(path.read_text(encoding='utf-8'))
        if result.get('run_id')==rid:
            live=result['live'];quotes=result['quotes']
            print('[RESULT] generations=%s active=%s rotations=%s quotes=%s positive=%s rpc=%s'%(
                live['generations'],live['active_pairs'],live['rotation_commits'],
                quotes['evaluations'],quotes['positive_quotes'],live['rpc_requests']))
            print('[TOP_QUOTES]',json.dumps(quotes['ranked_pairs'][:5],sort_keys=True))
            print('[REPORT]',path)
    print('[SIGNING] FALSE [BROADCAST] FALSE')
    return p.returncode if p.returncode is not None else 2

class Tests(unittest.TestCase):
    def test_positive_negative(self):
        x=Ledger();s={'token':'ABC'}
        x.add('PUMP_TO_METEORA',s,{'local_net':-3});x.add('PUMP_TO_METEORA',s,{'local_net':2})
        self.assertEqual(x.positives,1);self.assertEqual(x.report()['ranked_pairs'][0]['best_net'],2)

    def test_missing_net(self):
        x=Ledger();x.add('METEORA_TO_PUMP',{'token':'ABC'},{});self.assertEqual(x.report()['ranked_pairs'][0]['missing'],1)

    def test_no_private_fields(self):
        self.assertEqual(safe_quote({'local_net':3,'private_key':'secret','raw_in':10}),{'local_net':3.0,'raw_in':10.0})

    def test_nonfinite(self):
        self.assertIsNone(finite(float('inf')))

    def test_error(self):
        x=Ledger();x.error('P2M',ValueError());self.assertEqual(x.errors['P2M_ValueError'],1)

    def test_canary(self):
        self.assertEqual(CANARY,10_000_000)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--live',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--minutes',type=int,default=5)
    ap.add_argument('--run-id',default='')
    a=ap.parse_args()
    root=Path.cwd()

    if a.test:
        ran=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if ran.wasSuccessful() else 1
    if a.child:
        sys.path.insert(0,str(root.resolve()))
        return child(root,a.minutes,a.run_id)
    if a.live:
        if a.minutes<0:return 2
        return parent(root,a.minutes)

    target=root/PKG/NAME
    if not target.parent.is_dir():
        print('[HOLD] EXECUTOR_PACKAGE_MISSING')
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)

    print('[PASS]',VERSION)
    print('[MODE] ORACLE_047_LIVE_QUOTES_WITH_NUMERIC_OPPORTUNITY_LEDGER')
    print('[SCANNER] FROZEN [SIGNING] FALSE [BROADCAST] FALSE')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
