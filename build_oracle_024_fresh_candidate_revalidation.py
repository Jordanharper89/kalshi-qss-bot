
from pathlib import Path
import argparse, asyncio, base64, json, os, shutil, subprocess, sys, threading, time, types, unittest, uuid

BASE=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_024_fresh_candidate_revalidation.py'
OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_024_FRESH_CANDIDATES.json')
VERSION='ORACLE_024_FRESH_P2M_REVALIDATION'
CANARY=10_000_000
FRESH_MS=1500.0
PAIR_CAP=8
RPC_CAP=80
SIM_CAP=1
P2M='PUMP_TO_METEORA'
M2P='METEORA_TO_PUMP'
SAFE={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','COMSPEC','QSB_SOLANA_WALLET','SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL'}

def scrub(e):
    return {k:v for k,v in e.items() if k.upper() in SAFE}

def age_ms(received):
    return (time.perf_counter_ns()-int(received))/1e6

def hold_reason(e):
    msg=str(e).upper()
    for name in ('PROTECTED_MARGIN','NO_PROTECTED_SURPLUS','QUOTE_REPLAY_MISMATCH','TRAVERSED_ARRAY','NATIVE_MIN_OUTPUT','PUMP_EXACT','SWAP2','BIN_DIRECTION','COMPILE','STALE','ALT','RPC_REQUEST_BUDGET','TOKEN_NET_WORKER','DLMM_PARTIAL','NO_LIQUIDITY'):
        if name in msg:return name
    return type(e).__name__+'_REDACTED'

def latest_row(lane,token,row):
    with lane.cv:
        newer=lane.latest.get(token)
        if newer is not None and int(newer[3])>int(row[3]):
            return lane.latest.pop(token)
    return row

def is_fresh(lane,token,row):
    return age_ms(row[2])<=FRESH_MS and not lane.newer_waiting(token,row[3])

def record_quote(rep,token,slot,direction,net):
    rep['evaluations'][direction]+=1
    label=rep['best_quotes'].get(direction)
    if label is None or int(net)>int(label['quote_lamports']):
        rep['best_quotes'][direction]={'token':str(token),'slot':int(slot),'quote_lamports':int(net)}
    key=str(token)+'/'+direction
    r=rep['pair_quotes'].setdefault(key,{'count':0,'positives':0,'best':None})
    r['count']+=1
    r['positives']+=int(net>0)
    r['best']=int(net) if r['best'] is None else max(r['best'],int(net))

def quote_p2m(q18,snap):
    token=str(snap['token']);start=CANARY
    buy=q18.worker().buy(snap,start)
    gross=int(buy['baseOut'])
    net=int(q18.token_net(token,gross))
    if not 0<net<=gross:raise RuntimeError('BAD_FORWARD_RECEIPT_NET')
    m=q18.core.dlmm_quote_snapshot(snap,net,token)
    end=int(m['raw_out']);pnl=end-start
    return {'token':token,'pump_pool':snap['pump_pool'],'meteora':snap['meteora'],
            'start':start,'size_sol':.01,'direction':P2M,'mq':m,
            'pump_base_out_gross':gross,'pump_base_out_net':net,
            'pump_max_quote':int(buy['maxQuote']),
            'local_end':end,'local_net':pnl,'local_bps':pnl/start*10000,
            'pump_model':'EXACT_PUMPSWAP_SDK'}

def quote_m2p(q18,snap):
    token=str(snap['token']);start=CANARY
    m=q18.core.dlmm_quote_snapshot(snap,start,q18.core.WSOL)
    net=int(q18.token_net(token,int(m['raw_out'])))
    if net<=0:raise RuntimeError('BAD_REVERSE_RECEIPT_NET')
    sell=q18.worker().sell(snap,net)
    end=int(sell['uiQuote']);minimum=int(sell['minQuote']);pnl=end-start
    return {'token':token,'start':start,'direction':M2P,'local_net':pnl,
            'local_min_net':minimum-start,'local_end':end,'local_bps':pnl/start*10000}

def save(root,rep):
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n',encoding='utf-8');tmp.replace(p)

def child(root,seconds,run_id):
    r={'build':VERSION,'run_id':run_id,'status':'HOLD','ready':0,
       'rpc_requests':0,'simulations':0,'evaluations':{P2M:0,M2P:0},'best_quotes':{},
       'pair_quotes':{},'native_passes':0,'positive_candidates':0,'rechecks':0,
       'holds':[],'attempts':[],'rejects':{},'signing':False,'broadcast':False,'canary_sent':False}
    if any('PRIVATE_KEY' in x.upper() or 'SECRET_KEY' in x.upper() for x in os.environ):
        r['holds'].append('PRIVATE_KEY_ENV_REFUSED');save(root,r);return 2
    sys.path.insert(0,str(root))
    from solders.pubkey import Pubkey
    from meteora_dlmm import quote as dlmm_quote
    from meteora_dlmm.decode import array_index_of
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine,live_account_stream as pd
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as v20
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_015_rpc_efficient_bootstrap as v15
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21
    if not v20.VERSION.startswith('ORACLE_ATOMIC_CLOSEOUT_V20_'):
        r['holds'].append('V20_REQUIRED');save(root,r);return 2
    wallet=os.environ.get('QSB_SOLANA_WALLET','').strip()
    Pubkey.from_string(wallet)
    original_rpc=core.rpc;original_account=core.account
    original_pool=engine.exact_pool_ok;original_pairs=pd.MAX_PAIRS
    original_keypair=core.keypair;original_signed=core.signed_tx;original_send=core.send
    guard=v15.Guard(original_rpc,RPC_CAP)
    core.rpc=guard;core.keypair=core.signed_tx=core.send=v20.deny
    registered={};validated=set()
    def identity(token,pool):
        try:ok=v21.derived_pool(token,core)==pool
        except (ValueError,TypeError,KeyError):ok=False
        if ok:registered[pool]=token
        return (ok,'PDA_MATCH' if ok else 'PDA_MISMATCH')
    def account(address):
        raw,owner=original_account(address)
        if address in registered:
            v21.attest(raw,owner,registered[address],core)
            validated.add(address)
        return raw,owner
    engine.exact_pool_ok=identity;core.account=account;pd.MAX_PAIRS=PAIR_CAP
    lane=None
    ticket={'simulated':False,'compiled':0,'checks':0,'alt':None}
    def reject(reason):r['rejects'][reason]=r['rejects'].get(reason,0)+1
    try:
        state,_=v15.prepare_pairs_only(root)
        if len(state['pairs'])<1:raise RuntimeError('NO_VERIFIED_PAIR')
        if len(validated)!=len(state['pairs']):raise RuntimeError('POOL_OWNER_ATTESTATION_INCOMPLETE')
        q25.bind_cached_state(state)
        warmed=rt.install_proven_hot_math(state)
        rt.USER=wallet
        rt.prebuild_templates(state,wallet)
        rt.prebuild_meteora_templates(state,wallet,warmed)
        ready=set(rt.READY_TOKENS)
        r['ready']=len(ready)
        if not ready:raise RuntimeError('NO_READY_EXECUTION_PAIRS')
        for pair in state['pairs']:
            if str(pair.token) in ready:q18.worker().warm(str(pair.pump_pool))
        lane=q20.LatestStateLane()
        def price(self,token,original):
            row=latest_row(self,token,original)
            for recheck in range(3):
                if age_ms(row[2])>FRESH_MS:
                    reject('SNAPSHOT_AGE_EXCEEDED');return
                snap,slot,received,generation=row
                try:
                    forward=quote_p2m(q18,snap)
                    record_quote(r,token,slot,P2M,forward['local_net'])
                except Exception as ex:
                    reject('P2M_'+hold_reason(ex));forward=None
                if (forward and forward['local_net']>0 and not ticket['simulated']
                    and ticket['checks']<24):
                    r['positive_candidates']+=1;ticket['checks']+=1
                    try:
                        fee=max(v20.FEE_BUFFER,int(state.get('landing') or 0))
                        ixs,bounds=v20.build_bound(rt,wallet,snap,forward,dlmm_quote,array_index_of,fee)
                        r['native_passes']+=1
                        if not is_fresh(self,token,row):
                            reject('FRESHER_SNAPSHOT_REQUIRED')
                            newer=latest_row(self,token,row)
                            if newer is not row and recheck<2:
                                row=newer;r['rechecks']+=1;continue
                            return
                        attempt={'token':str(token),'slot':int(slot),'bounds':bounds,'status':'HOLD'}
                        try:
                            if ticket['compiled']>=2:
                                raise RuntimeError('COMPILE_ATTEMPT_LIMIT')
                            if ticket['alt'] is None:ticket['alt']=v20.verify_alt(core)
                            blockhash=core.rpc('getLatestBlockhash',[{'commitment':'processed'}])['value']['blockhash']
                            ticket['compiled']+=1
                            built=rt.q87.compile_candidate(wallet,ixs,[[ticket['alt']]],blockhash)
                            if not built.get('ok'):raise RuntimeError('ATOMIC_COMPILE_REJECTED')
                            raw=bytes(built['unsigned']);attempt['tx_bytes']=len(raw)
                            if len(raw)>1232 or raw[:65]!=bytes([1])+bytes(64) or raw[65:66]!=bytes([128]):
                                raise RuntimeError('UNSIGNED_ATOMIC_V0_INVALID')
                            if not is_fresh(self,token,row):
                                reject('STALE_BEFORE_SIMULATION')
                                raise RuntimeError('STALE_BEFORE_SIMULATION')
                            ticket['simulated']=True
                            response=core.rpc('simulateTransaction',[
                                base64.b64encode(raw).decode(),
                                {'encoding':'base64','sigVerify':False,'replaceRecentBlockhash':True,'commitment':'processed'}])['value']
                            attempt['error']=response.get('err')
                            attempt['compute_units']=response.get('unitsConsumed')
                            attempt['status']='UNSIGNED_SIM_PASS_ECONOMICS_HOLD' if response.get('err') is None else 'SIMULATION_REJECTED'
                            attempt['logs_tail']=list(response.get('logs') or [])[-5:]
                        except Exception as ex:
                            attempt['reason']=hold_reason(ex)
                        r['attempts'].append(attempt)
                    except Exception as ex:
                        reject('NATIVE_'+hold_reason(ex))
                try:
                    reverse=quote_m2p(q18,snap)
                    record_quote(r,token,slot,M2P,reverse['local_net'])
                except Exception as ex:reject('M2P_'+hold_reason(ex))
                return
        lane._price=types.MethodType(price,lane);lane.start()
        pairs=list(state['pairs']);p=q19.persistent;shards=p.m._shards(state['addresses'])
        counts={k:0 for k in ('acks','connections','notifications','priced_events','reconnects','rate_limit_disconnects','event_errors','queue_drops')}
        counts.update(last_ws_error=None,lat=[],best=None)
        async def observe():
            queue=asyncio.Queue(maxsize=4096);stop=asyncio.Event()
            tasks=[asyncio.create_task(p._worker(i,s,queue,counts,stop)) for i,s in enumerate(shards)]
            start=time.monotonic()
            try:
                while time.monotonic()-start<seconds:
                    try:ev=await asyncio.wait_for(queue.get(),timeout=.2)
                    except asyncio.TimeoutError:continue
                    binding=state['preg'].get(ev.get('address'))
                    if binding is None:continue
                    i,kind=binding;pair=pairs[i]
                    if str(pair.token) not in ready:continue
                    try:
                        changed=p.m.pd.apply_account_event(pair,kind,ev['address'],ev['raw'],ev['slot'],ev['received_ns'])
                        if changed:
                            counts['priced_events']+=1
                            lane.submit(str(pair.token),rt.immutable_snapshot(pair),ev['slot'],ev['received_ns'])
                    except Exception:counts['event_errors']+=1
            finally:
                stop.set()
                for task in tasks:task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
        asyncio.run(observe())
        lane.close();lane=None
        r.update(scanner=counts,priced_events=counts['priced_events'],rpc_requests=guard.total,
                 rpc_methods=dict(guard.methods),simulations=guard.simulations,
                 verified_pools=len(validated),shard_sizes=[len(x) for x in shards])
        if any(x.get('status')=='UNSIGNED_SIM_PASS_ECONOMICS_HOLD' for x in r['attempts']):
            r['status']='UNSIGNED_SIM_PASS_NET_PROFIT_UNCERTIFIED'
        elif r['evaluations'][P2M] and r['evaluations'][M2P]:
            r['status']='TWO_DIRECTIONS_ACTIVE_NO_SIM_PASS'
        if not ticket['simulated']:r['holds'].append('NO_SUCCESSFUL_ATOMIC_SIMULATION')
        r['holds']+=['ACTUAL_FEES_RESIDUE_AND_TRANSFER_HOOKS_NOT_CERTIFIED','NO_REALIZED_PROFIT']
    except Exception as ex:r['holds'].append('ENGINE_'+hold_reason(ex))
    finally:
        if lane is not None:
            try:lane.close()
            except Exception:pass
        r['rpc_requests']=guard.total;r['rpc_methods']=dict(guard.methods);r['simulations']=guard.simulations
        core.rpc=original_rpc;core.account=original_account
        core.keypair=original_keypair;core.signed_tx=original_signed;core.send=original_send
        engine.exact_pool_ok=original_pool;pd.MAX_PAIRS=original_pairs
        save(root,r)
    return 0

class Tests(unittest.TestCase):
    def test_environment(self):
        self.assertEqual(scrub({'PATH':'yes','QSB_SOLANA_PRIVATE_KEY':'secret'}),{'PATH':'yes'})
    def test_freshness(self):
        now=time.perf_counter_ns();self.assertLess(age_ms(now),FRESH_MS)
        self.assertGreater(age_ms(now-3_000_000_000),FRESH_MS)
    def test_latest_state(self):
        l=types.SimpleNamespace(cv=threading.Condition(),latest={'x':('new',3,4,2)})
        self.assertEqual(latest_row(l,'x',('old',1,2,1))[0],'new')
        self.assertNotIn('x',l.latest)
    def test_no_newer(self):
        l=types.SimpleNamespace(cv=threading.Condition(),latest={})
        x=('old',1,2,1);self.assertIs(latest_row(l,'x',x),x)
    def test_candidate_ledger(self):
        r={'evaluations':{P2M:0,M2P:0},'best_quotes':{},'pair_quotes':{}}
        record_quote(r,'T',5,P2M,100);record_quote(r,'T',6,P2M,-1)
        self.assertEqual(r['pair_quotes']['T/'+P2M]['positives'],1)
        self.assertEqual(r['best_quotes'][P2M]['quote_lamports'],100)
    def test_redaction(self):
        self.assertNotIn('secret',hold_reason(RuntimeError('api-key=secret')))
    def test_fixed_gates(self):
        self.assertEqual((CANARY,FRESH_MS,PAIR_CAP,RPC_CAP,SIM_CAP),(10_000_000,1500.,8,80,1))
    def test_forward_is_exact_amount_and_p2m(self):
        class Worker:
            def buy(self,snap,start):
                return {'baseOut':2000,'maxQuote':start}
        fake=types.SimpleNamespace(
            worker=lambda:Worker(),
            token_net=lambda token,gross:gross-1,
            core=types.SimpleNamespace(dlmm_quote_snapshot=lambda snap,amt,mint:{'raw_out':10_100_000,'swap_for_y':True,'bins_crossed':1}))
        q=quote_p2m(fake,{'token':'T','pump_pool':'P','meteora':{'address':'M'}})
        self.assertEqual(q['pump_base_out_net'],1999)
        self.assertEqual(q['local_net'],100000)
        self.assertEqual((q['start'],q['direction']),(CANARY,P2M))
    def test_reverse_is_separate(self):
        class Worker:
            def sell(self,snap,amount):return {'uiQuote':9_900_000,'minQuote':9_800_000}
        fake=types.SimpleNamespace(worker=lambda:Worker(),token_net=lambda token,gross:gross,
            core=types.SimpleNamespace(WSOL='SOL',dlmm_quote_snapshot=lambda snap,amt,mint:{'raw_out':500}))
        r=quote_m2p(fake,{'token':'T'})
        self.assertEqual(r['local_net'],-100000)
        self.assertEqual(r['direction'],M2P)
    def test_source_no_orders(self):
        import inspect
        source=inspect.getsource(child)
        self.assertNotIn('sendTransaction',source)
        self.assertNotIn('sign_transaction',source)

def parent(root,seconds):
    rid=str(uuid.uuid4())
    command=[sys.executable,'-I',str(Path(__file__).resolve()),'--child','--seconds',str(seconds),'--run-id',rid]
    proc=subprocess.run(command,cwd=root,env=scrub(os.environ),capture_output=True,text=True,timeout=seconds+160)
    rep=json.loads((root/OUT).read_text(encoding='utf-8'))
    if rep.get('run_id')!=rid:raise RuntimeError('STALE_V24_REPORT')
    for key in ('status','ready','verified_pools','shard_sizes','priced_events','evaluations',
                'best_quotes','pair_quotes','positive_candidates','native_passes','rechecks',
                'rejects','rpc_requests','rpc_methods','simulations','attempts','holds'):
        if key in rep:print('['+key.upper()+']',json.dumps(rep[key],sort_keys=True),flush=True)
    print('[SCANNER] ORIGINAL [FRESHNESS_MS] 1500 [RPC_MAX] 80 [SIM_MAX] 1 [SIGNING] FALSE [BROADCAST] FALSE')
    print('[REPORT]',root/OUT)
    return proc.returncode

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true');ap.add_argument('--run',action='store_true')
    ap.add_argument('--child',action='store_true');ap.add_argument('--seconds',type=int,default=60)
    ap.add_argument('--run-id',default='')
    a=ap.parse_args();root=Path.cwd()
    if a.test:
        t=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if t.wasSuccessful() else 1
    if a.child:return child(root,a.seconds,a.run_id)
    if a.run:
        if not 45<=a.seconds<=90:print('[HOLD] DURATION_45_TO_90');return 2
        return parent(root,a.seconds)
    dest=root/BASE/NAME
    if not dest.parent.is_dir():print('[HOLD] EXECUTOR_PACKAGE_MISSING');return 2
    if dest.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),dest)
    print('[PASS]',VERSION,dest)
    print('[MODE] EIGHT_PAIRS; P2M_FIRST; REPRICE_NEWEST_SNAPSHOT; NO_FRESHNESS_BYPASS')
    print('[LIMITS] 80_RPC; 1_UNSIGNED_SIM; 0.010_SOL; SIGNING_FALSE; BROADCAST_FALSE')
    return 0

if __name__=='__main__':raise SystemExit(main())
