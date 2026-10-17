from pathlib import Path
import argparse, asyncio, json, os, shutil, subprocess, sys, threading, time, unittest, uuid

VERSION='ORACLE_047_FINAL_LIVE_MRIYA_REPLENISHMENT'
PKG=Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME='oracle_047_final_live_replenishment.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_047_LIVE.json')
CAP=8; REFRESH=90; RPC_WINDOW=300; RPC_CAP=250; CANARY=10_000_000
SAFE={'PATH','PATHEXT','SYSTEMROOT','WINDIR','SYSTEMDRIVE','TEMP','TMP','COMSPEC','SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL','QSB_SOLANA_WALLET'}

def scrub(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def persist(root,row):
    path=root/REPORT;path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(row,indent=2,sort_keys=True)+'\n',encoding='utf-8');tmp.replace(path)

class Budget:
    def __init__(self,rpc):
        self.rpc=rpc;self.lock=threading.Lock();self.window=time.monotonic();self.used=0;self.total=0;self.methods={};self.denied=0
    def __call__(self,method,params):
        if not isinstance(method,str) or not (method.startswith('get') or method=='simulateTransaction') or method=='simulateTransaction':
            raise RuntimeError('EXECUTION_RPC_DISABLED')
        with self.lock:
            now=time.monotonic()
            if now-self.window>=RPC_WINDOW:self.window=now;self.used=0
            if self.used>=RPC_CAP:
                self.denied+=1;raise RuntimeError('RPC_WINDOW_CAP_EXHAUSTED')
            self.used+=1;self.total+=1;self.methods[method]=self.methods.get(method,0)+1
        return self.rpc(method,params)

def choose_victim(active,seen):
    if not active:return None
    # Never evict a pair observed in the last 90 seconds.
    eligible=[token for token in active if time.monotonic()-seen.get(token,0)>90]
    return min(eligible,key=lambda t:seen.get(t,0)) if eligible else None

class Runtime:
    def __init__(self,root,minutes,run_id):
        self.root=root;self.minutes=minutes;self.run_id=run_id
        self.active={};self.last_seen={};self.routes={};self.events=0;self.quotes=0
        self.rotations=0;self.discoveries=0;self.generations=0;self.acks=0;self.holds={}
        self.status='STARTING';self.guard=None;self.transport=None;self.worker=None
        self.landing=0;self.originals=[]
    def hold(self,code):self.holds[code]=self.holds.get(code,0)+1
    def report(self):
        return {'revision':VERSION,'run_id':self.run_id,'status':self.status,
                'generations':self.generations,'discovered_rows':self.discoveries,
                'active_pairs':len(self.active),'active_tokens':list(self.active),
                'rotation_commits':self.rotations,'ws_notifications':self.events,
                'priced_events':self.quotes,'subscription_acks':self.acks,
                'holds':dict(self.holds),'rpc_requests':self.guard.total if self.guard else 0,
                'rpc_methods':self.guard.methods if self.guard else {},
                'rpc_window_denied':self.guard.denied if self.guard else 0,
                'execution_authority':False,'native_templates_certified':False,
                'signing':False,'broadcast':False,'simulations':0,
                'canary_lamports':CANARY,'scanner_source_modified':False}
    def refresh_hydrate(self,initial):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine,live_account_stream as pd
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_036_live_worker_handoff as v36
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        self.worker.refresh();generation,rows=v36.worker_snapshot(self.worker)
        selected,rejected=v36.admission(rows,v36.inventory_rows(self.root),32)
        pairs=[];local_holds={}
        remaining=[x for x in selected if x['token'] not in self.active]
        amount=max(0,CAP-len(self.active)) if initial else 2
        # Fresh hydration, owner attestation, and exact PDA validation.
        for row in remaining[:amount]:
            token,pool=row['token'],row['pump_pool']
            try:
                if v21.derived_pool(token,core)!=pool:raise RuntimeError('POOL_PDA_MISMATCH')
                old_universe=engine.candidate_universe;old_cap=pd.MAX_PAIRS;old_account=core.account
                inspected=set()
                def checked(address):
                    data,owner=old_account(address)
                    if address==pool:
                        v21.attest(data,owner,token,core);inspected.add(address)
                    return data,owner
                try:
                    engine.candidate_universe=lambda path:[row]
                    pd.MAX_PAIRS=1;core.account=checked
                    hydrated,landing=pd.prepare_pairs(self.root)
                finally:
                    engine.candidate_universe=old_universe;pd.MAX_PAIRS=old_cap;core.account=old_account
                if len(hydrated)!=1 or pool not in inspected:raise RuntimeError('ATTESTATION_INCOMPLETE')
                pairs.append(hydrated[0]);self.landing=int(landing)
            except Exception as exc:
                code=type(exc).__name__
                local_holds[code]=local_holds.get(code,0)+1
        return generation,len(rows),pairs,len(selected),rejected,local_holds
    async def subscribe_pair(self,pair):
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_044_ws_rotation_transport as v44
        token=str(pair.token);accounts=list(dict.fromkeys(str(a) for a in pair.watched_accounts()))
        if not accounts or not all(accounts):return False
        subscribed_before=set(self.transport.subscriptions)
        for address in accounts:
            if not await self.transport.subscribe(address):
                # Leave existing routes untouched; release only the unused new accounts.
                await self.transport.unsubscribe_unused(set(self.transport.subscriptions)-subscribed_before)
                return False
        if token in self.active:return False
        victim=None
        if len(self.active)>=CAP:
            victim=choose_victim(self.active,self.last_seen)
            if victim is None:return False
        # All ACKs have been delivered by the concurrent receiver.
        self.active[token]=pair;self.routes[token]=tuple(accounts)
        self.transport.routes[token]=tuple(accounts)
        self.transport.active[token]={'token':token,'pump_pool':str(pair.pump_pool),'meteora_pool':str(pair.meteora_pool)}
        self.last_seen[token]=time.monotonic()
        if victim:
            self.active.pop(victim,None);self.routes.pop(victim,None)
            self.transport.routes.pop(victim,None);self.transport.active.pop(victim,None)
            self.last_seen.pop(victim,None);self.rotations+=1
        try:await self.transport.unsubscribe_unused(set(self.transport.subscriptions))
        except Exception:self.hold('UNSUBSCRIBE_CLEANUP_PENDING')
        return True
    async def receiver(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt,oracle_024_fresh_candidate_revalidation as v24
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        while True:
            data=json.loads(await self.transport.ws.recv())
            response=await self.transport.accept(data)
            if not response:continue
            kind,address=response
            if kind=='ACK':self.acks+=1;continue
            if kind!='EVENT' or not address:continue
            ev=pd.parse_account_notification(data,self.transport.by_subscription)
            if not ev:continue
            self.events+=1
            for token,pair in list(self.active.items()):
                if address not in self.routes.get(token,()):continue
                if address==str(pair.pump_base_vault):name='PUMP_BASE'
                elif address==str(pair.pump_quote_vault):name='PUMP_QUOTE'
                elif address==str(pair.meteora_pool):name='DLMM_POOL'
                else:
                    name=next(('DLMM_ARRAY_'+str(i) for i,a in enumerate(pair.arrays) if str(a[1])==address),None)
                if name is None:continue
                try:
                    if not pd.apply_account_event(pair,name,address,ev['raw'],ev['slot'],ev['received_ns']):continue
                    self.last_seen[token]=time.monotonic()
                    snap=rt.immutable_snapshot(pair)
                    p2m=v24.quote_p2m(q18,snap)
                    m2p=v24.quote_m2p(q18,snap)
                    self.quotes+=1
                    # This is observation only. A positive quote is NOT executable profit.
                    if self.quotes%25==0:
                        print('[PRICING] count=%d active=%d p2m_net=%s m2p_net=%s'%(self.quotes,len(self.active),str(p2m.get('local_net')),str(m2p.get('local_net'))),flush=True)
                except Exception:self.hold('QUOTE_OR_EVENT_REJECTED')
    async def serve(self):
        import websockets
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_044_ws_rotation_transport as v44
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
        if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):raise RuntimeError('SECRET_ENVIRONMENT_REFUSED')
        original_rpc=core.rpc;original_keypair=core.keypair;original_signed=core.signed_tx;original_send=core.send
        self.guard=Budget(original_rpc);core.rpc=self.guard
        def deny(*a,**kw):raise RuntimeError('SIGNING_AND_SEND_DISABLED')
        core.keypair=core.signed_tx=core.send=deny
        self.worker=mry.ReplenishmentWorker(self.root,interval=REFRESH)
        started=time.monotonic();deadline=started+self.minutes*60 if self.minutes else float('inf')
        try:
            while time.monotonic()<deadline:
                try:
                    async with websockets.connect(pd.WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
                        self.transport=v44.Transport(ws,timeout=8)
                        receiver=asyncio.create_task(self.receiver())
                        try:
                            # Reestablish subscriptions after a reconnect.
                            for token,pair in list(self.active.items()):
                                for addr in self.routes[token]:
                                    if not await self.transport.subscribe(addr):raise RuntimeError('RECONNECT_ACK_FAILED')
                                self.transport.routes[token]=self.routes[token]
                                self.transport.active[token]={'token':token,'pump_pool':str(pair.pump_pool),'meteora_pool':str(pair.meteora_pool)}
                            next_refresh=0
                            while time.monotonic()<deadline:
                                if receiver.done():raise RuntimeError('WS_RECEIVER_TERMINATED')
                                now=time.monotonic()
                                if now>=next_refresh:
                                    self.status='REFRESHING'
                                    try:
                                        gen,count,pairs,matched,rejects,errors=await asyncio.to_thread(self.refresh_hydrate,not bool(self.active))
                                        self.generations+=1;self.discoveries+=count
                                        for k,v in errors.items():self.holds[k]=self.holds.get(k,0)+v
                                        for pair in pairs:
                                            if not await self.subscribe_pair(pair):self.hold('CANDIDATE_NOT_ADMITTED')
                                        self.status='LIVE_REPLENISHING'
                                        print('[GENERATION] n=%d discovered=%d matched=%d active=%d rotations=%d rpc=%d'%(self.generations,count,matched,len(self.active),self.rotations,self.guard.total),flush=True)
                                    except Exception as e:self.hold('REFRESH_'+type(e).__name__)
                                    persist(self.root,self.report())
                                    next_refresh=time.monotonic()+REFRESH
                                await asyncio.sleep(.25)
                        finally:
                            receiver.cancel();await asyncio.gather(receiver,return_exceptions=True)
                except Exception as exc:
                    self.hold('WS_'+type(exc).__name__)
                    self.status='RECONNECT_WAIT';persist(self.root,self.report())
                    await asyncio.sleep(5)
            self.status='SESSION_ENDED'
        finally:
            self.worker.close();core.rpc=original_rpc
            core.keypair=original_keypair;core.signed_tx=original_signed;core.send=original_send
            persist(self.root,self.report())

def child(root,minutes,rid):
    r=Runtime(root,minutes,rid)
    try:asyncio.run(r.serve());return 0
    except Exception as exc:
        r.hold('FATAL_'+type(exc).__name__);r.status='HOLD_FATAL';persist(root,r.report());return 2

def parent(root,minutes):
    rid=str(uuid.uuid4());cmd=[sys.executable,'-I',str(Path(__file__).resolve()),'--child','--minutes',str(minutes),'--run-id',rid]
    # Live child output can contain dependency warnings: avoid printing raw stderr/URLs.
    p=subprocess.Popen(cmd,cwd=root,env=scrub(os.environ),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for line in p.stdout:
        if line.startswith('[GENERATION]') or line.startswith('[PRICING]'):
            print(line.rstrip(),flush=True)
    p.wait()
    path=root/REPORT
    if path.exists():
        row=json.loads(path.read_text(encoding='utf-8'))
        if row.get('run_id')==rid:
            for key in ('status','generations','active_pairs','rotation_commits','ws_notifications','priced_events','holds','rpc_requests'):
                print('['+key.upper()+']',json.dumps(row.get(key)))
    return p.returncode

class Tests(unittest.TestCase):
    def test_budget(self):
        x=Budget(lambda m,p:True);x.used=RPC_CAP
        with self.assertRaises(RuntimeError):x('getSlot',[])
    def test_execution_denied(self):
        x=Budget(lambda m,p:True)
        with self.assertRaises(RuntimeError):x('sendTransaction',[])
        with self.assertRaises(RuntimeError):x('simulateTransaction',[])
    def test_scrub(self):
        self.assertEqual(scrub({'PATH':'ok','QSB_SOLANA_PRIVATE_KEY':'hidden'}),{'PATH':'ok'})
    def test_never_evict_recent(self):
        active={'A':1,'B':2};t=time.monotonic()
        self.assertIsNone(choose_victim(active,{'A':t,'B':t}))
    def test_evict_stale_only(self):
        t=time.monotonic();self.assertEqual(choose_victim({'A':1,'B':2},{'A':t-200,'B':t}),'A')
    def test_cap(self):self.assertEqual(CAP,8)
    def test_canary(self):self.assertEqual(CANARY,10_000_000)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--live',action='store_true');ap.add_argument('--child',action='store_true');ap.add_argument('--minutes',type=int,default=15);ap.add_argument('--run-id',default='');a=ap.parse_args();root=Path.cwd()
    if a.test:
        res=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));return 0 if res.wasSuccessful() else 1
    if a.child:
        sys.path.insert(0,str(root.resolve()));return child(root,a.minutes,a.run_id)
    if a.live:
        if a.minutes<0:print('[HOLD] INVALID_DURATION');return 2
        return parent(root,a.minutes)
    path=root/PKG/NAME
    if not path.parent.is_dir():print('[HOLD] EXECUTOR_PACKAGE_MISSING');return 2
    if path.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),path)
    print('[PASS]',VERSION);print('[MODE] PERSISTENT_MRIYA_REPLENISHMENT_AND_V24_QUOTE_OBSERVATION');print('[SCANNER] FROZEN [SIGNING] FALSE [BROADCAST] FALSE');return 0

if __name__=='__main__':raise SystemExit(main())
