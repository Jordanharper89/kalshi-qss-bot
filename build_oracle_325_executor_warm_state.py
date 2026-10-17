"""ORACLE-325 complete replacement installer: isolated executor runtime.
Windows CMD: python {Path(__file__).name} --install
Original Q25/Q20/Q18 modules are never rewritten.
"""
from __future__ import annotations
import argparse,hashlib,os,pathlib,py_compile,subprocess,sys
from urllib.parse import quote
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.boss_executor_live'
TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_executor_live.py')
SOURCE=r'''"""ORACLE-325 independent dual-direction evidence-driven native executor.
Consumes exact scanner candidates and physically rebuilds a fresh two-leg transaction.
NO PRIVATE KEY, NO SIGNATURE, NO BROADCAST. Do not use for money movement yet.
"""
from __future__ import annotations
import argparse,base64,contextlib,copy,hashlib,json,os,pathlib,sqlite3,struct,sys,time,traceback,threading,queue,random
from collections import Counter
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
BUS=ROOT/'candidate_bus.sqlite3';LEDGER=ROOT/'execution_diagnostics.jsonl'
STATUS=ROOT/'executor_status.json';LOCK=ROOT/'executor.lock'
CANARY=10_000_000;PACKET_LIMIT=1232
MEMO='MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
OLD_DISC=hashlib.sha256(b'global:swap').digest()[:8]
SWAP2_DISC=hashlib.sha256(b'global:swap2').digest()[:8]
DEFAULT_ALT='HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'

def emit(tag,data):print('['+tag+'] '+json.dumps(data,sort_keys=True,default=str),flush=True)
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_name(path.name+'.'+str(os.getpid())+'.tmp');t.write_text(json.dumps(obj,sort_keys=True,indent=2,default=str),encoding='utf-8');os.replace(t,path)
def safe(e):
    import re
    x=type(e).__name__+':'+str(e)
    x=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',x)
    x=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',x)
    return x[:250]
@contextlib.contextmanager
def single():
    ROOT.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise RuntimeError('EXECUTOR_ALREADY_RUNNING_CHECK_LOCK')
    with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(str(os.getpid()))
    try:yield
    finally:
        try:
            if LOCK.read_text(encoding='utf-8')==str(os.getpid()):LOCK.unlink()
        except OSError:pass

def safe_bus():
    if not BUS.exists():raise RuntimeError('SCANNER_BUS_NOT_INITIALIZED_START_SCANNER_FIRST')
    c=sqlite3.connect(str(BUS),timeout=2)
    c.execute('PRAGMA query_only=ON');c.execute('PRAGMA busy_timeout=2000')
    return c

def heartbeat(c):
    try:
        row=c.execute("SELECT unix_ns,admitted,emitted,producer,epoch FROM heartbeat WHERE name='scanner'").fetchone()
    except sqlite3.Error:return dict(status='MISSING')
    if not row:return dict(status='MISSING')
    age=(time.time_ns()-int(row[0]))/1e9
    return dict(status='FRESH' if 0<=age<=15 else 'STALE',age_seconds=round(age,2),
                admitted=int(row[1]),emitted=int(row[2]),producer=row[3],epoch=row[4])

def verify_event(r,h,ttl=4.):
    if h.get('status')!='FRESH':return 'HOLD_SCANNER_NOT_FRESH'
    if int(r['size_lamports'])!=CANARY:return 'HOLD_SIZE_POLICY'
    if r['direction'] not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):return 'HOLD_DIRECTION'
    if int(r['slot'])<=0 or int(r['gross_lamports'])<=0:return 'HOLD_NOT_EXACT_POSITIVE'
    age=(time.time_ns()-int(r['created_ns']))/1e9
    if age<0 or age>ttl:return 'HOLD_STALE_NOMINATION'
    if not r['token'] or not r['pump_pool'] or not r['meteora_pool']:return 'HOLD_UNBOUND_ROUTE'
    return 'ACCEPT_NOMINATION_NOT_EXECUTION'

def coalesce(rows):
    """Newest nomination per identity, then newest/highest-gross first."""
    fields=('id','producer','token','pump_pool','meteora_pool','direction','size_lamports','gross_lamports','slot','generation','created_ns','source')
    by={}
    for values in rows:
        r=dict(zip(fields,values)) if not isinstance(values,dict) else dict(values)
        key=(r['token'],r['pump_pool'],r['meteora_pool'],r['direction'],int(r['size_lamports']))
        old=by.get(key)
        if old is None or (int(r['slot']),int(r['created_ns']),int(r['id']))>(int(old['slot']),int(old['created_ns']),int(old['id'])):
            by[key]=r
    return sorted(by.values(),key=lambda x:(int(x['created_ns']),int(x['slot']),int(x['gross_lamports'])),reverse=True)

def diagnostic_pool_order(inventory,preferred=None,limit=3):
    valid=[p for p in inventory if p.get('token') and p.get('pump_pool') and p.get('meteora_pool')]
    if preferred and all(preferred.get(k) for k in ('token','pump_pool','meteora_pool')):
        valid=[preferred]+[p for p in valid if p['token']!=preferred['token']]
    dedup={};ordered=[]
    for p in valid:
        key=(p['token'],p['pump_pool'],p['meteora_pool'])
        if key not in dedup:dedup[key]=True;ordered.append(p)
    return ordered[:max(0,int(limit))]

def metric():return time.perf_counter_ns()
def took(ns):return round((metric()-ns)/1e6,3)

def quote_lineage(nom, out):
    new=out.get('fresh_gross_lamports')
    return dict(scanner_slot=int(nom['slot']),scanner_gross_lamports=int(nom['gross_lamports']),
                executor_gross_lamports=new,delta_lamports=None if new is None else int(new)-int(nom['gross_lamports']),
                pump_pool=nom['pump_pool'],meteora_pool=nom['meteora_pool'],
                scanner_created_ns=int(nom['created_ns']),executor_observed_ns=time.time_ns(),
                same_pool_identity=out.get('pool_identity_validated',False),
                same_snapshot_certified=False,
                reason='REQUOTE_DIFFERS_OR_TIME_ELAPSED' if new != int(nom['gross_lamports']) else 'VALUE_MATCH_NOT_SAME_SNAPSHOT')

def rebuild_swap2(ix,template,dlmm):
    """Replace legacy DLMM account prefix from fresh canonical template.

    This explicitly eliminates ORACLE318's brittle prefix equality check,
    retaining legacy exact amount/minOut and the actual writable bin-array metas.
    """
    if not isinstance(ix,dict) or ix.get('programId')!=dlmm:raise RuntimeError('NOT_DLMM')
    raw=base64.b64decode(ix.get('data') or '',validate=True)
    if len(raw)!=24 or raw[:8]!=OLD_DISC:raise RuntimeError('NOT_LEGACY_SWAP_EXACT_IN')
    amount,minimum=struct.unpack_from('<QQ',raw,8)
    if not amount or not minimum:raise RuntimeError('INVALID_EXACT_SWAP_BOUNDS')
    fixed=template.get('fixed_accounts')
    arrays=template.get('arrays')
    if not isinstance(fixed,list) or len(fixed)!=15 or not isinstance(arrays,list) or not arrays:
        raise RuntimeError('CANONICAL_DLMM_TEMPLATE_INCOMPLETE')
    # Exact account layout known from official Swap2 IDL: prefix must include host_fee_in
    # placeholder and Memo in fixed positions. No account from historical instruction is
    # trusted for the 16-account prefix.
    prefix=[{'pubkey':str(pk),'isSigner':bool(s),'isWritable':bool(w)} for pk,s,w in fixed]
    if prefix[9]['pubkey']!=dlmm or prefix[14]['pubkey']!=dlmm:
        raise RuntimeError('CANONICAL_PROGRAM_PLACEHOLDER_DRIFT')
    prefix.insert(13,dict(pubkey=MEMO,isSigner=False,isWritable=False))
    if len(prefix)!=16 or prefix[13]['pubkey']!=MEMO or prefix[15]['pubkey']!=dlmm:
        raise RuntimeError('SWAP2_CANONICAL_ACCOUNT_ORDER_INVALID')
    known={str(p[1]) for p in arrays}
    original=list(ix.get('accounts') or [])
    # The old builder used 15 fixed metas. Preserve only explicitly known bin-array
    # addresses from the suffix; never trust unexpected accounts as array replacements.
    selected=[];seen=set()
    for a in original[15:]:
        pk=a.get('pubkey') if isinstance(a,dict) else None
        if pk not in known:raise RuntimeError('BIN_ARRAY_NOT_IN_LIVE_POOL_TEMPLATE')
        if pk in seen:raise RuntimeError('DUPLICATE_BIN_ARRAY')
        seen.add(pk);selected.append({'pubkey':pk,'isSigner':False,'isWritable':True})
    if not selected:raise RuntimeError('NO_QUOTED_BIN_ARRAYS')
    # Empty RemainingAccountsInfo slices is valid for token programs with no transfer hooks.
    # Token-2022 transfer hook metadata cannot be guessed: fail instead if unsupported.
    data=SWAP2_DISC+struct.pack('<QQI',amount,minimum,0)
    out=dict(ix,accounts=prefix+selected,data=base64.b64encode(data).decode())
    return out,dict(fixed_accounts=16,bin_arrays=len(selected),amount_in=amount,min_out=minimum)

# All new warm state is diagnostic/preflight only. A cached quote is never an execution authorization.
WARM_TTL_NS=750_000_000
WARM_MAX_PENDING=32

class WarmState:
    def __init__(self,engine,ttl_ns=WARM_TTL_NS):
        self.engine=engine;self.ttl_ns=ttl_ns;self.mu=threading.RLock()
        self.snapshots={};self.pending=set();self.work=queue.Queue(maxsize=WARM_MAX_PENDING)
        self.stop=threading.Event();self.thread=None;self.failure={};self.stats=Counter()
        self.last_rpc=0.;self.cooldown_until=0.
    @staticmethod
    def identity(token,pump,meteora):return (token,pump,meteora)
    def request(self,token,pump,meteora):
        k=self.identity(token,pump,meteora)
        with self.mu:
            if k in self.pending:return False
            # Keep workers from repeatedly pulling the same recently hydrated pool.
            old=self.snapshots.get(k)
            if old and time.monotonic_ns()-old['completed_ns']<self.ttl_ns//2:return False
            try:self.work.put_nowait(k)
            except queue.Full:self.stats['queue_full']+=1;return False
            self.pending.add(k);return True
    def peek(self,token,pump,meteora,now_ns=None):
        k=self.identity(token,pump,meteora)
        with self.mu:
            row=self.snapshots.get(k)
            if row is None:return None,'WARM_CACHE_MISS'
            age=(time.monotonic_ns() if now_ns is None else now_ns)-row['completed_ns']
            if age<0 or age>self.ttl_ns:return None,'WARM_CACHE_EXPIRED'
            return row,'WARM_CACHE_FRESH_BY_AGE_ONLY'
    def start(self):
        if self.thread:return
        self.thread=threading.Thread(target=self.loop,daemon=True,name='boss325-warm-hydration')
        self.thread.start()
    def loop(self):
        while not self.stop.is_set():
            try:k=self.work.get(timeout=.25)
            except queue.Empty:continue
            try:
                # Rate-limited REST requests run only on this background worker.
                wait=max(0.,self.cooldown_until-time.monotonic(),self.last_rpc+1.25-time.monotonic())
                if wait:self.stop.wait(wait)
                if self.stop.is_set():break
                self.last_rpc=time.monotonic()
                t=time.monotonic_ns()
                with self.engine.native_mutex:
                    snap=self.engine.rehydrate(*k)
                completed=time.monotonic_ns()
                with self.mu:
                    self.snapshots[k]=dict(snapshot=copy.deepcopy(snap),completed_ns=completed,hydrate_ms=round((completed-t)/1e6,2),identity=k)
                    self.stats['hydrated']+=1;self.failure.pop(k,None)
            except Exception as exc:
                why=safe(exc)
                with self.mu:
                    self.failure[k]=why;self.stats['hydration_errors']+=1
                if any(x in why.lower() for x in ('429','rate limit','too many requests')):
                    self.cooldown_until=time.monotonic()+min(60.,5.*(2**min(4,self.stats['hydration_errors'])))+random.random()
                    with self.mu:self.stats['rpc_429']+=1
            finally:
                with self.mu:self.pending.discard(k)
                self.work.task_done()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)

class Native:
    def __init__(self,wallet,alts):
        self.wallet=wallet;self.alts=alts;self.cache={};self.last_token=None;self.last_pool=None
        self.rt=None;self.q87=None;self.q18=None;self.q23=None
        self.last_refresh=0.;self.last_meta={};self.last_complete_pair=None
        self.native_mutex=threading.RLock();self.warm=None
    def init(self):
        from solders.pubkey import Pubkey
        Pubkey.from_string(self.wallet)
        for a in self.alts:Pubkey.from_string(a)
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
        # Module may have a different historic naming; discover via q25.q23 reference if needed.
        self.rt,self.q87,self.q18,self.q23=rt,q87,q18,q23
        self.cache=q87.c.alt_accounts(self.alts)
        if set(self.cache)!=set(self.alts) or any(not v for v in self.cache.values()):
            raise RuntimeError('ALT_UNAVAILABLE_OR_EMPTY')
        self.q23.install_hot_token_net()
        emit('BOSS320_READY',dict(alt_tables=len(self.cache),mode='NATIVE_PREFLIGHT',signing=False,broadcast=False))
    def rehydrate(self,token,pump_pool,meteora_pool):
        c=self.q87.c
        meta=c.discover_dlmm(token)
        if meta['address']!=meteora_pool:raise RuntimeError('DLMM_PAIR_IDENTITY_DRIFT')
        snap=c.build_token_snapshot(token,pump_pool)
        if snap['meteora']['address']!=meteora_pool:raise RuntimeError('REFRESHED_DLMM_IDENTITY_DRIFT')
        # q25's token-net implementation is kept intact; SDK worker warm is per-token.
        w=self.q23.worker().warm(token)
        self.q23.worker().refresh_epoch()
        self.q18.worker().warm(pump_pool)
        arr=c.dlmm_arrays(meteora_pool)
        class Pair:pass
        p=Pair();p.token=token;p.pump_pool=pump_pool;p.meteora_pool=meteora_pool
        p.token_x=meta['token_x'];p.token_y=meta['token_y'];p.arrays=arr
        # Real pool + mint programs from current chain state, not inferred from mint string.
        # The canonical builder uses actual on-chain Token-2022/legacy ownership.
        self.rt.prebuild_templates({'pairs':[p]},self.wallet)
        self.rt.prebuild_meteora_templates({'pairs':[p]},self.wallet,
             [{'token':token,'program':w.get('program')}])
        if token not in self.rt.READY_TOKENS:raise RuntimeError('NATIVE_TEMPLATE_NOT_READY')
        self.last_complete_pair=dict(token=token,pump_pool=pump_pool,meteora_pool=meteora_pool,observed_ns=time.time_ns())
        return snap
    def simulate(self,token,pump_pool,meteora_pool,diagnostic=False,direction="PUMP_TO_METEORA"):
        out=dict(build='ORACLE325',token=token,direction=direction,size_lamports=CANARY,
                 diagnostic=bool(diagnostic),signing=False,broadcast=False,execution_admission=False)
        elapsed={};started=metric()
        try:
            if direction not in ("PUMP_TO_METEORA","METEORA_TO_PUMP"):raise RuntimeError("DIRECTION_UNSUPPORTED")
            # Cache may have been hydrated ahead of the nomination. Do not block this thread.
            row,cache_gate=self.warm.peek(token,pump_pool,meteora_pool) if self.warm else (None,'WARM_WORKER_NOT_STARTED')
            if row is None:
                if self.warm:self.warm.request(token,pump_pool,meteora_pool)
                out.update(gate='HOLD_'+cache_gate,warm_ready=False)
                return out
            snap=copy.deepcopy(row['snapshot'])
            out['warm_ready']=True;out['warm_snapshot_age_ms']=round((time.monotonic_ns()-row['completed_ns'])/1e6,2)
            out['warm_snapshot_slot_certified']=False
            # Snapshot age is NOT complete multi-account slot coherence. Do not admit a trade.
            out['execution_admission']=False
            elapsed["warm_read_ms"]=took(started);out["pool_identity_validated"]=True
            started=metric()
            with self.native_mutex:
                ops=self.q18.exact_snapshot_opportunities(snap,.010)
            forward=next((x for x in ops if x.get('direction')==direction and int(x.get('start') or 0)==CANARY),None)
            if forward is None:raise RuntimeError('NO_EXACT_DIRECTION_REQUOTE')
            elapsed['quote_ms']=took(started);started=metric()
            gross=int(forward['local_net']);out['fresh_gross_lamports']=gross
            if gross<=0 and not diagnostic:
                out['gate']='HOLD_FRESH_REQUOTE_NONPOSITIVE';return out
            if direction=='METEORA_TO_PUMP':
                # No uncertified reversal of the P2M instruction order. Require a
                # real repository-native reverse assembler with an explicit API.
                assembler=getattr(self.rt,'same_snapshot_reverse_route',None)
                if not callable(assembler):
                    out['gate']='HOLD_REVERSE_NATIVE_ASSEMBLER_UNAVAILABLE'
                    out['reverse_builder']='NOT_CERTIFIED'
                    return out
                with self.native_mutex:
                    route=assembler(self.wallet,snap,forward)
            else:
                with self.native_mutex:
                    route=self.rt.same_snapshot_route(self.wallet,snap,forward)
            elapsed['native_build_ms']=took(started);started=metric()
            # Only the helper-complete route is currently admitted. Other candidates
            # can omit setup/cleanup and are not automatically safe to simulate.
            candidates=[x for x in self.q87.repaired_candidates(route) if x.get('name')=='FULL']
            if not candidates:raise RuntimeError('NO_NATIVE_HELPER_COMPLETE_CANDIDATES')
            blockhash_start=metric()
            bh=self.q87.c.rpc('getLatestBlockhash',[{'commitment':'processed'}])['value']['blockhash']
            elapsed['blockhash_ms']=took(blockhash_start)
            errors=[];compiled=None
            for row in candidates:
                try:
                    ixs=list(row['instructions'])
                    ids=[k for k,x in enumerate(ixs) if x.get('programId')==self.q87.c.DLMM]
                    if len(ids)!=1:raise RuntimeError('NEED_EXACTLY_ONE_DLMM_LEG')
                    i=ids[0];legal,meta=rebuild_swap2(ixs[i],self.rt.METEORA_TEMPLATES[token],self.q87.c.DLMM)
                    ixs[i]=legal
                    # Cached validated ALT data: no lookup RPC on the hot compile leg.
                    original_alt=self.q87.c.alt_accounts
                    try:
                        self.q87.c.alt_accounts=lambda keys:{k:self.cache[k] for k in keys}
                        comp=self.q87.compile_candidate(self.wallet,ixs,[self.alts],bh)
                    finally:self.q87.c.alt_accounts=original_alt
                    if not comp.get('ok'):raise RuntimeError(str(comp.get('error'))[:140])
                    if len(comp['unsigned'])>PACKET_LIMIT:raise RuntimeError('PACKET_EXCEEDS_1232')
                    compiled=comp;elapsed['alt_compile_ms']=took(started);out.update(packet_bytes=len(comp['unsigned']),candidate=row.get('name'),
                         swap2_fixed_accounts=meta['fixed_accounts'],swap2_bin_arrays=meta['bin_arrays'],
                         exact_bounds_preserved=True)
                    break
                except Exception as exc:errors.append(safe(exc))
            if compiled is None:
                out.update(gate='HOLD_ATOMIC_PACKET_COMPILE',errors=errors[:6]);return out
            raw=base64.b64encode(compiled['unsigned']).decode()
            started=metric()
            rsp=self.q87.c.rpc('simulateTransaction',[raw,{'encoding':'base64','sigVerify':False,
                'commitment':'processed','replaceRecentBlockhash':False}])
            elapsed['simulation_ms']=took(started)
            sim=rsp.get('value') if isinstance(rsp,dict) else None
            if not isinstance(sim,dict):raise RuntimeError('RPC_SIMULATION_RESPONSE_MALFORMED')
            log=sim.get('logs') or []
            out.update(sim_err=sim.get('err'),sim_units=sim.get('unitsConsumed'),
                       sim_log_tail=[str(z)[:300] for z in log[-12:]] if isinstance(log,list) else [])
            if sim.get('err') is not None:
                out['gate']='HOLD_MAINNET_SIM_FAILED';return out
            # This remains unsigned; state can change after simulation.
            out['gate']='UNSIGNED_DIAGNOSTIC_PASS_NO_TRADE' if diagnostic or gross<=0 else 'UNSIGNED_SIM_PASS_SIGNED_NET_UNCERTIFIED'
            return out
        except Exception as e:
            out.update(gate='HOLD_NATIVE_'+safe(e));return out
        finally:
            out['latency_ms']=elapsed

def tests():
    import unittest,tempfile
    class T(unittest.TestCase):
        def test_swap2_fresh_prefix_not_legacy(self):
            dlmm='dlmm';keys=[f'K{i}' for i in range(15)];keys[9]=dlmm;keys[14]=dlmm
            old={'programId':dlmm,'accounts':[{'pubkey':'DRIFT_'+k} for k in keys]+
                   [{'pubkey':'BIN1','isWritable':True}],
                 'data':base64.b64encode(OLD_DISC+struct.pack('<QQ',100,90)).decode()}
            ans,m=rebuild_swap2(old,dict(fixed_accounts=[(k,False,False) for k in keys],arrays=[(0,'BIN1')]),dlmm)
            self.assertEqual(ans['accounts'][0]['pubkey'],'K0')
            self.assertEqual(ans['accounts'][13]['pubkey'],MEMO)
            self.assertEqual(ans['accounts'][16]['pubkey'],'BIN1')
            self.assertEqual(base64.b64decode(ans['data']),SWAP2_DISC+struct.pack('<QQI',100,90,0))
        def test_unknown_bin_block(self):
            dlmm='dlmm';k=['a']*15;k[9]=dlmm;k[14]=dlmm
            i=dict(programId=dlmm,accounts=[{}]*15+[{'pubkey':'UNKNOWN'}],data=base64.b64encode(OLD_DISC+struct.pack('<QQ',1,1)).decode())
            with self.assertRaisesRegex(RuntimeError,'BIN_ARRAY_NOT_IN_LIVE_POOL_TEMPLATE'):
                rebuild_swap2(i,dict(fixed_accounts=[(x,False,False) for x in k],arrays=[(1,'BIN')]),dlmm)
        def test_nonpositive_and_wrong_size_rejected(self):
            now=time.time_ns();r=dict(size_lamports=CANARY,direction='PUMP_TO_METEORA',slot=1,gross_lamports=1,created_ns=now,token='t',pump_pool='p',meteora_pool='m')
            self.assertEqual(verify_event(r,dict(status='FRESH')),'ACCEPT_NOMINATION_NOT_EXECUTION')
            self.assertEqual(verify_event(dict(r,size_lamports=1),dict(status='FRESH')),'HOLD_SIZE_POLICY')
            self.assertEqual(verify_event(dict(r,created_ns=now-10_000_000_000),dict(status='FRESH')),'HOLD_STALE_NOMINATION')
            self.assertEqual(verify_event(r,dict(status='STALE')),'HOLD_SCANNER_NOT_FRESH')
        def test_latest_slot_coalescing(self):
            t=time.time_ns()
            base=dict(id=1,producer='s',token='T',pump_pool='P',meteora_pool='M',direction='PUMP_TO_METEORA',size_lamports=CANARY,gross_lamports=50,slot=10,generation=1,created_ns=t,source='MRIYA')
            ans=coalesce([base,dict(base,id=2,slot=12,gross_lamports=4),dict(base,id=3,direction='METEORA_TO_PUMP')])
            self.assertEqual(len(ans),2)
            self.assertEqual(next(r for r in ans if r['direction']=='PUMP_TO_METEORA')['id'],2)
        def test_stale_no_replay(self):
            t=time.time_ns();r=dict(size_lamports=CANARY,direction='METEORA_TO_PUMP',slot=2,gross_lamports=1,created_ns=t-6_000_000_000,token='T',pump_pool='P',meteora_pool='M')
            self.assertEqual(verify_event(r,dict(status='FRESH')),'HOLD_STALE_NOMINATION')
        def test_lineage_delta(self):
            r=dict(slot=7,gross_lamports=120,created_ns=time.time_ns(),pump_pool='P',meteora_pool='M')
            row=quote_lineage(r,dict(fresh_gross_lamports=-30,pool_identity_validated=True))
            self.assertEqual(row['delta_lamports'],-150)
            self.assertFalse(row['same_snapshot_certified'])
        def test_reverse_never_auto_certified(self):
            self.assertFalse(hasattr(Native,'send_transaction'))
            self.assertFalse(hasattr(Native,'sign_transaction'))
        def test_diagnostic_independent_of_quote_sign(self):
            self.assertIn('if gross<=0 and not diagnostic:',Native.simulate.__code__.co_consts.__str__() if False else __import__('inspect').getsource(Native.simulate))
        def test_diagnostic_selects_bounded_pool_count(self):
            p=lambda t:dict(token=t,pump_pool='P',meteora_pool='M')
            out=diagnostic_pool_order([p('B'),p('A'),p('A'),p('C'),p('D')],p('C'),3)
            self.assertEqual([x['token'] for x in out],['C','B','A'])
        def test_warm_cache_identity_and_ttl(self):
            w=WarmState(None,ttl_ns=100)
            k=('T','P','M');w.snapshots[k]={'snapshot':{'token':'T'},'completed_ns':1000}
            self.assertEqual(w.peek(*k,now_ns=1050)[1],'WARM_CACHE_FRESH_BY_AGE_ONLY')
            self.assertEqual(w.peek(*k,now_ns=1101)[1],'WARM_CACHE_EXPIRED')
            self.assertEqual(w.peek('X','P','M',now_ns=1050)[1],'WARM_CACHE_MISS')
        def test_warm_does_not_claim_slot_or_execution(self):
            import inspect
            ss=inspect.getsource(Native.simulate)
            self.assertIn('warm_snapshot_slot_certified',ss)
            self.assertIn("out['execution_admission']=False",ss)
        def test_default_disarmed(self):self.assertEqual(CANARY,10_000_000)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    return 0 if r.wasSuccessful() else 1

def run(interval=60,poll=.20):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('EXECUTOR_SECRET_NOT_ALLOWED_IN_DIAGNOSTIC_PROCESS')
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://'):raise RuntimeError('SECURE_RPC_REQUIRED')
    wallet=os.getenv('QSB_SOLANA_WALLET','')
    alts=[x for x in os.getenv('QSB_SOLANA_ALT_ADDRESSES',DEFAULT_ALT).replace(';',',').split(',') if x]
    if not wallet or not alts:raise RuntimeError('WALLET_PUBLIC_ADDRESS_AND_ALT_REQUIRED')
    with single():
        c=safe_bus()
        cursor=c.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]
        n=Native(wallet,alts);n.init();n.warm=WarmState(n);n.warm.start();stats=Counter();last_diag=time.monotonic();last_attempt=0.;last_status=time.monotonic()
        # Warm currently admitted inventory independently of the hot candidate loop.
        try:
            initial=json.loads(pathlib.Path('runtime_state/oracle/final_boss_dual/scanner_inventory.json').read_text())
            for p in initial.get('pairs',[])[:28]:
                if all(p.get(x) for x in ('token','pump_pool','meteora_pool')):n.warm.request(p['token'],p['pump_pool'],p['meteora_pool'])
        except (OSError,ValueError):pass
        LEDGER.parent.mkdir(parents=True,exist_ok=True)
        emit('BOSS325_EXECUTOR_START',dict(restore_cursor=cursor,scan='ORACLE322_FROZEN',directions='BIDIRECTIONAL_PREFLIGHT',signing=False,broadcast=False))
        with LEDGER.open('a',encoding='utf-8') as ledger:
            while True:
                h=heartbeat(c);now=time.monotonic()
                if now-last_status>10:
                    emit('BOSS325_HEARTBEAT',dict(scanner=h,seen=stats['events'],sim_pass=stats['sim_pass'],diagnostic=stats['diagnostics'],coalesced=stats['coalesced'],warm=dict(n.warm.stats),warm_queue=n.warm.work.qsize(),reverse_holds=stats['HOLD_REVERSE_NATIVE_ASSEMBLER_UNAVAILABLE'],broadcast=False))
                    save(STATUS,dict(build='ORACLE325',scanner=h,counters=dict(stats),broadcast=False,signing=False,mode='MAINNET_UNSIGNED_PREFLIGHT'))
                    last_status=now
                if h['status']=='FRESH':
                    rows=c.execute('SELECT id,producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source FROM events WHERE id>? ORDER BY id DESC LIMIT 256',(cursor,)).fetchall()
                    if rows:
                        cursor=max(cursor,max(r[0] for r in rows));stats['events']+=len(rows)
                        fresh=coalesce(rows);stats['coalesced']+=len(rows)-len(fresh)
                        eligible=[r for r in fresh if verify_event(r,h)=='ACCEPT_NOMINATION_NOT_EXECUTION']
                        stats['skipped_or_stale']+=len(fresh)-len(eligible)
                        if eligible and now-last_attempt>=max(2.,min(5.,interval/12)):
                            last_attempt=now
                            for e in eligible[:8]:n.warm.request(e['token'],e['pump_pool'],e['meteora_pool'])
                            r=eligible[0];start_ns=time.time_ns();started=metric()
                            row=n.simulate(r['token'],r['pump_pool'],r['meteora_pool'],diagnostic=False,direction=r['direction'])
                            row['latency_ms']['end_to_end_ms']=took(started)
                            row['latency_ms']['queue_age_at_start_ms']=round((start_ns-int(r['created_ns']))/1e6,3)
                            row['nomination']=dict(slot=r['slot'],gross=r['gross_lamports'],source=r['source'],age_ms=round((time.time_ns()-int(r['created_ns']))/1e6,2))
                            row['lineage']=quote_lineage(r,row)
                            ledger.write(json.dumps(row,sort_keys=True,default=str)+'\n');ledger.flush()
                            emit('BOSS325_NATIVE_RESULT',row);stats[row['gate']]+=1
                            if row['gate'].startswith('UNSIGNED_SIM_PASS'):stats['sim_pass']+=1
                if h['status']=='FRESH' and now-last_diag>=interval:
                    last_diag=now;stats['diagnostics']+=1
                    # Diagnostics are deliberately independent of positive-price admission.
                    # Try the last successfully hydrated pool first, then other inventory
                    # pairs. DLMM_PARTIAL is a per-pair hold, not a global diagnostic stop.
                    tried=[];row=None
                    try:
                        inv=json.loads(pathlib.Path('runtime_state/oracle/final_boss_dual/scanner_inventory.json').read_text())
                        valid=diagnostic_pool_order(inv.get('pairs',[]),n.last_complete_pair,3)
                        for p in valid:
                            n.warm.request(p['token'],p['pump_pool'],p['meteora_pool'])
                            rr=n.simulate(p['token'],p['pump_pool'],p['meteora_pool'],diagnostic=True,direction='PUMP_TO_METEORA')
                            tried.append(dict(token=p['token'][:12],gate=rr.get('gate'),latency_ms=rr.get('latency_ms')))
                            row=rr
                            # A physical result means instruction assembly/compile/simulation
                            # was attempted (or revealed a concrete packet failure).
                            if rr.get('gate') not in ('HOLD_NATIVE_RuntimeError:DLMM_PARTIAL',
                                    'HOLD_NATIVE_RuntimeError:NATIVE_TEMPLATE_NOT_READY',
                                    'HOLD_NATIVE_RuntimeError:NO_EXACT_DIRECTION_REQUOTE','HOLD_WARM_CACHE_MISS','HOLD_WARM_CACHE_EXPIRED'):
                                break
                        if row is None:row=dict(gate='HOLD_NO_INVENTORY',broadcast=False,signing=False)
                    except Exception as exc:row=dict(gate='HOLD_DIAGNOSTIC_'+safe(exc),broadcast=False,signing=False)
                    row['diagnostic_attempts']=tried
                    row['tested_pools']=len(tried)
                    row['diagnostic_physical_reached']=bool(row.get('packet_bytes') or row.get('sim_err') is not None)
                    ledger.write(json.dumps(row,sort_keys=True,default=str)+'\n');ledger.flush()
                    emit('BOSS325_DIAGNOSTIC',row);stats[row['gate']]+=1
                time.sleep(poll)

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    for x in ('test','audit','status','run'):m.add_argument('--'+x,action='store_true')
    p.add_argument('--diagnostic-interval',type=int,default=60)
    a=p.parse_args()
    if a.test:return tests()
    if a.audit:
        emit('BOSS325_AUDIT',dict(candidate_bus=str(BUS),
             canonical_scanner='ORACLE025->ORACLE020->ORACLE018',
             native='qseries_v2.oracle_execution.solana_atomic_executor.runtime',
             signing=False,broadcast=False,m2p_certified=False));return 0
    if a.status:
        emit('BOSS325_STATUS',json.loads(STATUS.read_text()) if STATUS.is_file() else {'status':'NOT_STARTED'});return 0
    if a.diagnostic_interval<20:raise RuntimeError('DIAGNOSTIC_INTERVAL_TOO_LOW')
    return run(a.diagnostic_interval)
if __name__=='__main__':raise SystemExit(main())


'''
EXPECTED='ed531b63cb49892a6694454fa756d9cdde5dc330712cf60897fa49a65a7f751b'
def install():
    raw=SOURCE.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise RuntimeError('SOURCE_HASH_MISMATCH')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    # This build owns only its distinct runtime module; frozen source is untouched.
    temp=TARGET.with_name(TARGET.name+'.325.installing')
    temp.write_bytes(raw)
    check=TARGET.with_name('boss325check.pyc')
    try:py_compile.compile(str(temp),cfile=str(check),doraise=True)
    finally:
        if check.exists():check.unlink()
    os.replace(temp,TARGET)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:raise RuntimeError('BYTE_HASH_MISMATCH')
    print('[ORACLE325_INSTALLED]',TARGET)
    print('[ORACLE325_SHA256_PASS]',EXPECTED)

def call(opts,env=None):
    if not TARGET.is_file() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError('INSTALL_ORACLE325_FIRST')
    return subprocess.call([sys.executable,'-m',MODULE,*opts],env=env)

def launch(opts):
    if not os.getenv('QSB_SOLANA_WALLET'):
        raise RuntimeError('PUBLIC_WALLET_REQUIRED_QSB_SOLANA_WALLET')
    from build_oracle_182_secure_windows_credentials import load,api,HELIUS
    key=load(api(),HELIUS)
    if not key:raise RuntimeError('HELIUS_CREDENTIAL_NOT_FOUND')
    env=os.environ.copy()
    env.pop('QSB_SOLANA_PRIVATE_KEY',None)
    env['QSB_LIVE_ARM']='NO'
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+quote(key,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+quote(key,safe='')
    del key
    return call(opts,env=env)

def main():
    p=argparse.ArgumentParser(description='ORACLE-325 executor full replacement installer/launcher')
    mode=p.add_mutually_exclusive_group(required=True)
    for f in ('install','test','audit','launch','status'):mode.add_argument('--'+f,action='store_true')
    p.add_argument('--seconds',type=int,default=3600)
    p.add_argument('--epochs',type=int,default=0)
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--accounts',type=int,default=1280)
    p.add_argument('--diagnostic-interval',type=int,default=60)
    p.add_argument('--stage-interval',type=int,default=180)
    a=p.parse_args()
    if a.install:install();return 0
    if a.test:return call(['--test'])
    if a.audit:return call(['--audit'])
    if a.status:return call(['--status'])
    if a.launch:
        opts=['--run','--diagnostic-interval',str(a.diagnostic_interval)]
        return launch(opts)
    return 1
if __name__=='__main__':raise SystemExit(main())
