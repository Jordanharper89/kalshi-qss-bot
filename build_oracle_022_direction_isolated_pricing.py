from pathlib import Path
import argparse, importlib.util, inspect, json, os, shutil, subprocess, sys, threading, unittest, uuid
from types import SimpleNamespace
from unittest.mock import patch

PACKAGE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_022_direction_isolated_pricing.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_022_PRICING.json')
V21_REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_021_POOL_BOOTSTRAP.json')
ATOMIC_REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')
VERSION='ORACLE_022_DIRECTION_ISOLATED_EXACT_PRICING'
P2M='PUMP_TO_METEORA'
M2P='METEORA_TO_PUMP'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC',
      'SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL','QSB_SOLANA_WALLET'}
KNOWN=('DLMM_PARTIAL','DLMM_DIRECTION','TOKEN_NET_WORKER_DIED',
       'TOKEN_NET_WORKER','TOKEN_NET_RESPONSE_ORDER','FORWARD_TOKEN_NET_ZERO',
       'REVERSE_TOKEN_NET_ZERO','BIN_ARRAY','INSUFFICIENT_LIQUIDITY',
       'NO_LIQUIDITY','NOT_LOADED','POOL_NOT_FOUND')

def safe_env(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def reason(exc):
    message=str(exc).upper()
    symbol=next((x for x in KNOWN if x in message),'OTHER_REDACTED')
    return type(exc).__name__+':'+symbol

class Diagnostics:
    def __init__(self):
        self.lock=threading.Lock()
        self.calls=0
        self.passes={P2M:0,M2P:0}
        self.failures={}
    def begin(self):
        with self.lock:self.calls+=1
    def success(self,direction):
        with self.lock:self.passes[direction]+=1
    def fail(self,direction,stage,exc):
        label=direction+'/'+stage+'/'+reason(exc)
        with self.lock:self.failures[label]=self.failures.get(label,0)+1
    def snapshot(self):
        with self.lock:return {'events_quoted':self.calls,
                               'successful_directions':dict(self.passes),
                               'rejections_by_stage':dict(sorted(self.failures.items()))}

def split_exact(q18,snap,size_sol,diag):
    diag.begin()
    token=snap['token']
    start=int(round(float(size_sol)*1e9))
    if start!=10_000_000:raise RuntimeError('EXACT_CANARY_SIZE_REQUIRED')
    rows=[]
    stage='DLMM_BUY'
    try:
        buy=q18.core.dlmm_quote_snapshot(snap,start,q18.core.WSOL)
        stage='RECEIPT_NET'
        net_token=int(q18.token_net(token,int(buy['raw_out'])))
        if net_token<=0:raise RuntimeError('REVERSE_TOKEN_NET_ZERO')
        stage='PUMP_SELL'
        sell=q18.worker().sell(snap,net_token)
        end=int(sell['uiQuote']); min_end=int(sell['minQuote'])
        pnl=end-start; min_pnl=min_end-start
        rows.append({'token':token,'pump_pool':snap['pump_pool'],
                     'meteora':snap['meteora'],'start':start,'size_sol':float(size_sol),
                     'direction':M2P,'mq':buy,'gross_token':int(buy['raw_out']),
                     'net_token':net_token,'local_end':end,'local_min_end':min_end,
                     'local_net':pnl,'local_min_net':min_pnl,
                     'local_bps':pnl/start*10000.0,
                     'local_min_bps':min_pnl/start*10000.0,
                     'pump_model':'SAE003_PUMPSWAP_EXACT_QUOTE_IN'})
        diag.success(M2P)
    except Exception as exc:
        diag.fail(M2P,stage,exc)
    stage='PUMP_BUY'
    try:
        buy=q18.worker().buy(snap,start)
        gross=int(buy['baseOut'])
        stage='RECEIPT_NET'
        net_token=int(q18.token_net(token,gross))
        if net_token<=0:raise RuntimeError('FORWARD_TOKEN_NET_ZERO')
        stage='DLMM_SELL'
        sell=q18.core.dlmm_quote_snapshot(snap,net_token,token)
        end=int(sell['raw_out']); pnl=end-start
        rows.append({'token':token,'pump_pool':snap['pump_pool'],
                     'meteora':snap['meteora'],'start':start,'size_sol':float(size_sol),
                     'direction':P2M,'mq':sell,'pump_base_out_gross':gross,
                     'pump_base_out_net':net_token,'pump_max_quote':int(buy['maxQuote']),
                     'local_end':end,'local_net':pnl,'local_bps':pnl/start*10000.0,
                     'pump_model':'EXACT_PUMPSWAP_SDK'})
        diag.success(P2M)
    except Exception as exc:
        diag.fail(P2M,stage,exc)
    return sorted(rows,key=lambda x:x['local_net'],reverse=True)

def write_report(root,data):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tmp.replace(path)

def child(root,seconds,run_id):
    result={'build':VERSION,'run_id':run_id,'status':'HOLD',
            'signing':False,'broadcast':False,'canary_sent':False}
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        result['hold']='SECRET_ENVIRONMENT_REFUSED';write_report(root,result);return 2
    try:
        sys.path.insert(0,str(root))
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as atomic
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21
        if not atomic.VERSION.startswith('ORACLE_ATOMIC_CLOSEOUT_V20_'):
            raise RuntimeError('V20_CONTRACT_REQUIRED')
        if 'q18.exact_snapshot_opportunities' not in inspect.getsource(atomic.child):
            raise RuntimeError('V20_PRICER_SEAM_MISSING')
        diag=Diagnostics()
        previous=q18.exact_snapshot_opportunities
        def adapted(snap,size):return split_exact(q18,snap,size,diag)
        q18.exact_snapshot_opportunities=adapted
        try:
            code=v21.child(root,seconds,run_id)
        finally:
            q18.exact_snapshot_opportunities=previous
        result.update(diag.snapshot())
        for path,key in ((V21_REPORT,'discovery'),(ATOMIC_REPORT,'atomic')):
            p=root/path
            if not p.is_file():raise RuntimeError('REPORT_MISSING_'+key.upper())
            report=json.loads(p.read_text(encoding='utf-8'))
            if report.get('run_id')!=run_id:raise RuntimeError('STALE_'+key.upper()+'_REPORT')
            if key=='discovery':
                result.update(ready=report.get('ready',0),rpc_requests=report.get('rpc_requests',0),
                              scanner_status=report.get('scanner_status'),
                              scanner=report.get('scanner'),
                              identity_validation=report.get('identity_validation'))
            else:
                result.update(atomic_status=report.get('status'),
                              priced_events=report.get('priced_events',0),
                              evaluations=report.get('evaluations'),
                              best_quotes=report.get('best_quotes'),
                              local_check_pass=report.get('local_check_pass'),
                              local_rejections=report.get('local_check_reject'),
                              atomic_attempts=report.get('attempts'),
                              holds=report.get('holds'))
        passes=result['successful_directions']
        if not result.get('ready') or not result.get('priced_events'):
            result['status']='HOLD_NO_LIVE_PRICING'
        elif passes[P2M] and passes[M2P]:
            result['status']='BOTH_DIRECTIONS_PRICED_EXECUTION_UNCERTIFIED'
        elif passes[P2M]:
            result['status']='P2M_PRICED_M2P_HOLD'
        elif passes[M2P]:
            result['status']='M2P_PRICED_P2M_HOLD'
        else:
            result['status']='HOLD_ALL_EXACT_QUOTES_FAILED'
        write_report(root,result)
        return code
    except Exception as exc:
        result['hold']='V22_'+type(exc).__name__
        write_report(root,result)
        return 2

def parent(root,seconds):
    run_id=str(uuid.uuid4())
    cmd=[sys.executable,'-I',str(Path(__file__).resolve()),'--child',
         '--seconds',str(seconds),'--run-id',run_id]
    try:
        proc=subprocess.Popen(cmd,cwd=root,env=safe_env(os.environ),
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,bufsize=1)
        def relay():
            for line in proc.stdout:
                if line.startswith('[ORACLE017_PULSE]'):
                    print(line.rstrip(),flush=True)
        reader=threading.Thread(target=relay,daemon=True);reader.start()
        try:
            code=proc.wait(timeout=seconds+150)
        finally:
            if proc.poll() is None:proc.kill();proc.wait(timeout=5)
            reader.join(timeout=2)
        d=json.loads((root/REPORT).read_text(encoding='utf-8'))
        if d.get('run_id')!=run_id:raise RuntimeError('STALE_V22_REPORT')
        for k in ('status','hold','ready','rpc_requests','scanner_status',
                  'priced_events','evaluations','successful_directions',
                  'rejections_by_stage','best_quotes','local_check_pass',
                  'local_rejections','atomic_attempts','holds'):
            if k in d:print('['+k.upper()+']',json.dumps(d[k]),flush=True)
        print('[SCANNER] FROZEN [SIM_MAX] 1 [SIGNING] FALSE [BROADCAST] FALSE',flush=True)
        print('[REPORT]',root/REPORT,flush=True)
        return code
    except Exception as exc:
        print('[HOLD] V22_PARENT_'+type(exc).__name__,flush=True)
        return 2

class Tests(unittest.TestCase):
    def setUp(self):
        self.snap={'token':'TOK','pump_pool':'POOL','meteora':{'address':'DLMM'}}
        class Worker:
            def buy(self,snap,start):return {'baseOut':1200,'maxQuote':start}
            def sell(self,snap,amount):return {'uiQuote':9_700_000,'minQuote':9_600_000}
        def dlmm(snap,amount,mint):
            return {'raw_out':1500 if mint=='SOL' else 10_050_000,
                    'swap_for_y':mint=='TOK','bins_crossed':1,'arrays':[]}
        self.q=SimpleNamespace(core=SimpleNamespace(WSOL='SOL',dlmm_quote_snapshot=dlmm),
                               worker=lambda:Worker(),token_net=lambda token,gross:int(gross))
    def test_both_directions_have_exact_fields(self):
        d=Diagnostics();rows=split_exact(self.q,self.snap,.010,d)
        self.assertEqual({x['direction'] for x in rows},{M2P,P2M})
        self.assertEqual(rows[0]['pump_base_out_net'],1200)
        self.assertEqual(rows[0]['local_net'],50000)
        self.assertEqual(d.snapshot()['successful_directions'],{M2P:1,P2M:1})
    def test_reverse_failure_does_not_block_forward(self):
        fn=self.q.core.dlmm_quote_snapshot
        def broken(snap,amount,mint):
            if mint=='SOL':raise RuntimeError('DLMM_PARTIAL')
            return fn(snap,amount,mint)
        self.q.core.dlmm_quote_snapshot=broken
        d=Diagnostics();r=split_exact(self.q,self.snap,.010,d)
        self.assertEqual([x['direction'] for x in r],[P2M])
        self.assertIn('METEORA_TO_PUMP/DLMM_BUY/RuntimeError:DLMM_PARTIAL',d.failures)
    def test_forward_failure_does_not_block_reverse(self):
        fn=self.q.core.dlmm_quote_snapshot
        def broken(snap,amount,mint):
            if mint=='TOK':raise RuntimeError('DLMM_PARTIAL')
            return fn(snap,amount,mint)
        self.q.core.dlmm_quote_snapshot=broken
        r=split_exact(self.q,self.snap,.010,Diagnostics())
        self.assertEqual([x['direction'] for x in r],[M2P])
    def test_strict_size(self):
        with self.assertRaisesRegex(RuntimeError,'SIZE_REQUIRED'):
            split_exact(self.q,self.snap,.015,Diagnostics())
    def test_no_raw_secrets(self):
        self.assertEqual(reason(RuntimeError('API_KEY=secret')),'RuntimeError:OTHER_REDACTED')
    def test_failed_pump_buy_stays_rejected(self):
        class Bad:
            def buy(self,*a):raise RuntimeError('OH_NO')
            def sell(self,*a):return {'uiQuote':0,'minQuote':0}
        self.q.worker=lambda:Bad()
        d=Diagnostics();r=split_exact(self.q,self.snap,.010,d)
        self.assertFalse(any(x['direction']==P2M for x in r))
        self.assertTrue(any('/PUMP_BUY/' in k for k in d.failures))
    def test_environment_scrub(self):
        self.assertEqual(safe_env({'PATH':'ok','QSB_SOLANA_PRIVATE_KEY':'secret'}),{'PATH':'ok'})
    def test_parity_with_installed_exact_pricer(self):
        if importlib.util.find_spec('qseries_v2') is None:
            self.skipTest('Repository environment required')
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        with patch.object(q18.core,'dlmm_quote_snapshot',self.q.core.dlmm_quote_snapshot),\
             patch.object(q18,'worker',self.q.worker),\
             patch.object(q18,'token_net',self.q.token_net):
            baseline=q18.exact_snapshot_opportunities(self.snap,.010)
            split=split_exact(q18,self.snap,.010,Diagnostics())
        self.assertEqual(baseline,split)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--child',action='store_true')
    ap.add_argument('--seconds',type=int,default=60)
    ap.add_argument('--run-id',default='')
    args=ap.parse_args();root=Path.cwd()
    if args.test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        r=unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if r.wasSuccessful() else 1
    if args.child:return child(root,args.seconds,args.run_id)
    if args.run:
        if not 45<=args.seconds<=120:print('[HOLD] SESSION_45_TO_120_SECONDS');return 2
        return parent(root,args.seconds)
    dest=root/PACKAGE/NAME
    if not dest.parent.is_dir():print('[HOLD] CANONICAL_EXECUTOR_DIRECTORY_MISSING');return 2
    if dest.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),dest)
    print('[PASS]',VERSION,dest)
    print('[MODE] INDEPENDENT_DIRECTIONS; EXACT_SDK_MATH; STAGE_REJECTIONS; SCANNER_FROZEN')
    print('[SIGNING] FALSE [BROADCAST] FALSE [CANARY] UNSENT')
    return 0

if __name__=='__main__':raise SystemExit(main())