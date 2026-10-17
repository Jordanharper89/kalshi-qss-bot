
from pathlib import Path
import argparse, asyncio, json, os, shutil, subprocess, sys, unittest, uuid

PACKAGE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET='oracle_016_ws_first_guard.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_016_WS_FIRST_GUARD.json')
PARENT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')
VERSION='ORACLE_016_WS_FIRST_SCANNER_PRESERVED'
PROBE_ACCOUNT='J3SZrLFzgwDyGDLQCcGLpeuBA5bPGuuTKbhgmWKSsQK1'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC',
      'QSB_SOLANA_WALLET','SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL'}

def env_safe(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def classify_error(message):
    msg=str(message or '').lower()
    for pattern,label in (('429','RATE_LIMIT'),('rate limit','RATE_LIMIT'),
                          ('401','UNAUTHORIZED'),('403','FORBIDDEN'),
                          ('timeout','TIMEOUT'),('closed','CLOSED'),
                          ('refused','REFUSED'),('handshake','HANDSHAKE')):
        if pattern in msg: return label
    return 'UNKNOWN' if msg else 'NONE'

def counters_view(c):
    return {k:int(c.get(k,0) or 0) for k in ('acks','connections','reconnects',
             'rate_limit_disconnects','notifications','queue_drops','event_errors')}

async def ws_preflight(worker=None,seconds=6):
    if worker is None:
        from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
        worker=q19.persistent._worker
    c=dict(acks=0,connections=0,reconnects=0,rate_limit_disconnects=0,
           notifications=0,queue_drops=0,event_errors=0,last_ws_error=None)
    stop=asyncio.Event()
    q=asyncio.Queue(maxsize=8)
    task=asyncio.create_task(worker(0,[PROBE_ACCOUNT],q,c,stop))
    try:
        loop=asyncio.get_running_loop()
        deadline=loop.time()+seconds
        while loop.time()<deadline and not task.done():
            if c['acks']>=1:break
            await asyncio.sleep(.1)
        return {'acknowledged':c['acks']>=1,
                'stats':counters_view(c),
                'error_category':classify_error(c.get('last_ws_error'))}
    finally:
        stop.set();task.cancel()
        await asyncio.gather(task,return_exceptions=True)

def save(root,result):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tmp.replace(path)

def child(root,seconds,run_id):
    result={'version':VERSION,'run_id':run_id,'status':'HOLD',
            'rpc_requests':0,'simulations':0,'signing':False,'broadcast':False}
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        result['hold']='SECRET_IN_CHILD';save(root,result);return 2
    try:
        sys.path.insert(0,str(root))
        preflight=asyncio.run(ws_preflight())
        result['ws_preflight']=preflight
        if not preflight['acknowledged']:
            result['hold']='WS_SUBSCRIPTION_NOT_ACKNOWLEDGED_NO_RPC_HYDRATION'
            save(root,result);return 0
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_015_rpc_efficient_bootstrap as v15
        from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
        if v15.CANARY!=10_000_000:
            raise RuntimeError('EXACT_CANARY_DRIFT')
        original=q19.persistent._worker
        record={}
        async def observe_worker(index,addresses,q,c,stop):
            record['counters']=c
            record.setdefault('shard_sizes',[]).append(len(addresses))
            return await original(index,addresses,q,c,stop)
        q19.persistent._worker=observe_worker
        try:
            code=v15.child(root,seconds,run_id)
        finally:
            q19.persistent._worker=original
        report=json.loads((root/PARENT).read_text(encoding='utf-8'))
        if report.get('run_id')!=run_id:
            raise RuntimeError('STALE_V15_RESULT')
        c=record.get('counters') or {}
        result['scanner']=counters_view(c)
        result['scanner']['shard_sizes']=record.get('shard_sizes',[])
        result['scanner']['error_category']=classify_error(c.get('last_ws_error'))
        result['rpc_requests']=int(report.get('rpc_budget_used') or 0)
        result['rpc_by_method']=report.get('rpc_counts_measured') or {}
        result['simulations']=int(report.get('rpc_simulations_measured') or 0)
        result['ready']=int(report.get('ready') or 0)
        result['priced_events']=int(report.get('priced_events') or 0)
        result['evaluations']=report.get('evaluations') or {}
        result['attempt_count']=len(report.get('attempts') or [])
        result['holds']=report.get('holds') or []
        if result['rpc_requests']>80 or result['simulations']>1:
            raise RuntimeError('GUARD_LIMIT_BROKEN')
        if result['scanner']['acks']==0:
            result['hold']='FULL_SCANNER_NO_SUBSCRIPTION_ACK'
        elif result['priced_events']==0:
            result['hold']='FULL_SCANNER_NO_PRICED_EVENTS'
        else:
            result['status']='SCANNER_PRICING_OBSERVED_UNCERTIFIED'
        save(root,result)
        return code
    except Exception as exc:
        result['hold']='CHILD_'+type(exc).__name__
        save(root,result)
        return 2

class Tests(unittest.TestCase):
    def test_secrets_removed(self):
        self.assertEqual(env_safe({'PATH':'ok','QSB_SOLANA_PRIVATE_KEY':'secret'}),{'PATH':'ok'})
    def test_no_payload_logged(self):
        self.assertEqual(classify_error('403 key=private_value'),'FORBIDDEN')
    def test_hardened_status(self):
        self.assertEqual(classify_error('429 api-key=secret'),'RATE_LIMIT')
    def test_zero_events_not_ok(self):
        self.assertEqual(counters_view({})['notifications'],0)
    def test_ws_ack_without_rpc(self):
        async def worker(i,addrs,q,c,stop):
            c['acks']=1;c['connections']=1
            await stop.wait()
        result=asyncio.run(ws_preflight(worker,seconds=1))
        self.assertTrue(result['acknowledged'])
    def test_ws_unacked_holds(self):
        async def worker(i,addrs,q,c,stop):
            await stop.wait()
        result=asyncio.run(ws_preflight(worker,seconds=.15))
        self.assertFalse(result['acknowledged'])
    def test_readonly_probe(self):
        self.assertNotIn('sendTransaction',VERSION)
    def test_whitelist_retains_rpc_ws(self):
        self.assertEqual(env_safe({'SOLANA_RPC_URL':'x','SOLANA_WS_URL':'y'}),
                         {'SOLANA_RPC_URL':'x','SOLANA_WS_URL':'y'})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--probe',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--seconds',type=int,default=15)
    ap.add_argument('--run-id',default='')
    a=ap.parse_args();root=Path.cwd()
    if a.test:
        t=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if t.wasSuccessful() else 1
    if a.child:return child(root,a.seconds,a.run_id)
    if a.probe:
        if a.seconds<10 or a.seconds>20:
            print('[HOLD] PROBE_10_TO_20_SECONDS');return 2
        identifier=str(uuid.uuid4())
        cmd=[sys.executable,'-I',str(Path(__file__).resolve()),'--child',
             '--seconds',str(a.seconds),'--run-id',identifier]
        try:
            x=subprocess.run(cmd,cwd=root,env=env_safe(os.environ),
                             capture_output=True,text=True,timeout=a.seconds+100)
            r=json.loads((root/REPORT).read_text(encoding='utf-8'))
            if r.get('run_id')!=identifier:raise RuntimeError('STALE_REPORT')
            for key in ('status','hold','ws_preflight','scanner','ready',
                        'priced_events','evaluations','rpc_requests',
                        'rpc_by_method','simulations','holds'):
                if key in r:print('['+key.upper()+']',json.dumps(r[key]))
            print('[SCANNER_CODE] UNCHANGED [RPC_LIMIT] 80 [SIM_LIMIT] 1')
            print('[SIGNING] FALSE [BROADCAST] FALSE [REPORT]',root/REPORT)
            return x.returncode
        except Exception as exc:
            print('[HOLD] PARENT_'+type(exc).__name__);return 2
    dst=root/PACKAGE/TARGET
    if not dst.parent.is_dir():
        print('[FAIL] EXECUTOR_PACKAGE_MISSING');return 1
    if dst.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),dst)
    print('[PASS]',VERSION,dst)
    print('[MODE] ONE_WS_ACK_BEFORE_STARTUP; PRESERVE_ORIGINAL_SCANNER; GUARDED_V15')
    print('[SIGNING] FALSE [BROADCAST] FALSE [ALT_MUTATION] FALSE')
    return 0

if __name__=='__main__':raise SystemExit(main())
