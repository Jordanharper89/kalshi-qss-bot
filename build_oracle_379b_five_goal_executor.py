"""ORACLE-379 complete executor capacity installer (NO trade authority).

Focus: executor-only 28x2 lane correctness, fair bounded scheduling, inventory
visibility, persistent unsigned SDK interface, measured latency and backpressure.
Reuses ORACLE-378 protected native bank/simulation gates; ORACLE-322 untouched.

This is a capacity and instrumentation release, NOT certified profit or proof
all 28 scanner pairs have legitimate same-token DLMM counterparts.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import importlib
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT/'oracle_379_five_goal_executor.py'
NODE_DIR = ROOT/'oracle_376_native_sdk'
NODE_HELPER = NODE_DIR/'oracle_379_persistent_unsigned.mjs'
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_379_capacity_report.json')
SOURCE_REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_379_native_session_report.json')
MAX_LANES = 512
MAX_AGE_MS = 1500
FIRST_CANARY = 10_000_000
AUTHORITY = False
SIGNING = False
BROADCAST = False
DIRECTIONS = ('PUMP_TO_METEORA','METEORA_TO_PUMP')
CODE = re.compile(r'^[A-Z][A-Z0-9_]{2,90}$')
KEY_DENY = re.compile(r'(PRIVATE.?KEY|SECRET|MNEMONIC|SEED|RECOVERY.?PHRASE|KEYPAIR)',re.I)

class Hold(RuntimeError): pass

def clean_env(env=None):
    return {k:v for k,v in (os.environ if env is None else env).items() if not KEY_DENY.search(k)}

def safe_exc(exc):
    s=str(exc)
    return s if type(exc).__name__ in ('Hold','StopRun') and CODE.fullmatch(s) else 'HOLD_'+type(exc).__name__.upper()

def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
        json.dump(obj,f,indent=2,sort_keys=True,default=str); tmp=f.name
    os.replace(tmp,path)

def modules():
    m363=importlib.import_module(PKG+'.oracle_363_verified_scanner_bus_binding')
    m368=importlib.import_module(PKG+'.oracle_368_source_boundary_repair')
    m374=importlib.import_module(PKG+'.oracle_374_persistent_dual_native_handoff')
    m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
    return m363,m368,m374,m378

def key_of(row):
    """No cross-direction or cross-size supersession."""
    try:
        key=(row['token'],row['pump_pool'],row['meteora_pool'],row['direction'],row['size_lamports'])
    except (KeyError,TypeError): raise Hold('INVALID_LANE_IDENTITY') from None
    if (not all(isinstance(x,str) and x for x in key[:4]) or
            key[3] not in DIRECTIONS or type(key[4]) is not int or key[4]<=0):
        raise Hold('INVALID_LANE_IDENTITY')
    return key

def quantiles(samples):
    if not samples:return {'samples':0,'p50_ms':None,'p95_ms':None,'p99_ms':None,'max_ms':None}
    s=sorted(samples)
    def q(p):return round(s[min(len(s)-1,max(0,int((len(s)-1)*p+0.999999)))],4)
    return {'samples':len(s),'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99),'max_ms':round(s[-1],4)}

class Metrics:
    def __init__(self):
        self.lock=threading.Lock();self.counts=collections.Counter()
        self.times=collections.defaultdict(lambda:collections.deque(maxlen=25000))
        self.max_pending=0
    def count(self,name,n=1):
        with self.lock:self.counts[name]+=n
    def timing(self,stage,ms):
        with self.lock:self.times[stage].append(float(ms))
    def depth(self,n):
        with self.lock:self.max_pending=max(self.max_pending,n)
    def report(self):
        with self.lock:
            return {'counts':dict(self.counts),'max_pending_lanes':self.max_pending,
                    'latency':{k:quantiles(list(v)) for k,v in self.times.items()}}

METRICS=Metrics()

def make_ingress(base, metrics):
    """Complete validated accept for the canonical ORACLE-363 local event contract."""
    class DirectionIngress(base.LocalIngress):
        def accept(self,raw):
            if self.failed or self.epoch is None:return None
            n=self._decode(raw)
            if not n:
                self.counts['invalid_schema']+=1;metrics.count('ingress_invalid_schema');return None
            try:
                eid=base.exact_int(n['id'],positive=True)
                created=base.exact_int(n['created_ns'],positive=True)
                slot=base.exact_int(n['slot'],positive=True)
                size=base.exact_int(n['size_lamports'],positive=True)
                token=n['token'];pump=n['pump_pool'];meteora=n['meteora_pool'];direction=n['direction']
            except (KeyError,TypeError,ValueError):
                self.counts['invalid_schema']+=1;metrics.count('ingress_invalid_schema');return None
            if (not all(base.valid_pubkey(v) for v in (token,pump,meteora)) or
                    direction not in base.DIRECTIONS or not base.MIN_SIZE<=size<=base.MAX_SIZE):
                self.counts['invalid_identity_or_size']+=1;metrics.count('ingress_invalid_identity');return None
            now=self.clock_ns();age_ns=now-created
            if not 0<=age_ns<=self.max_age_ns:
                self.counts['stale_or_future']+=1;metrics.count('ingress_stale');return None
            if eid in self.recent_ids:
                self.counts['duplicate']+=1;metrics.count('ingress_duplicate');return None
            key=(token,pump,meteora,direction,size);old=self.latest.get(key)
            if old is not None and eid<=old['event_id']:
                self.counts['superseded']+=1;metrics.count('ingress_older_same_lane');return None
            hint=base.gross_hint(n)
            self.recent_ids[eid]=None
            if len(self.recent_ids)>4096:self.recent_ids.popitem(last=False)
            if hint=='INVALID' or isinstance(hint,int) and hint<=0:
                self.counts['nonpositive_or_invalid_gross']+=1;metrics.count('ingress_negative')
                if old is not None:
                    self.latest.pop(key,None);self.deadlines.pop(key,None);self.changed=True
                    metrics.count('same_lane_invalidations')
                return None
            expires_ns=min(self.ttl_ns,self.max_age_ns)-age_ns
            if expires_ns<=0:
                self.counts['stale_or_future']+=1;metrics.count('ingress_stale');return None
            if old is None and len(self.latest)>=MAX_LANES:
                self.counts['capacity_rejected']+=1;metrics.count('ingress_capacity_rejected');return None
            row={
                'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1','event_id':eid,
                'scanner_epoch':self.epoch,'scanner_producer':self.producer,'scanner_slot':slot,
                'token':token,'pump_pool':pump,'meteora_pool':meteora,'direction':direction,
                'size_lamports':size,'scanner_gross_lamports_hint':hint,
                'scanner_gross_proven':False,'identity_vetted_by_352':False,
                'fresh_bank_pricing_certified':False,'fee_adjusted_profit_certified':False,
                'native_atomic_simulation_certified':False,'stage':'REPRICE_AND_VET_REQUIRED',
                'not_trade_ready':True,'first_funded_canary_lamports':FIRST_CANARY,
                'execution_authority':False,'signing':False,'broadcast':False,
                'source_age_at_ingress_ms':round(age_ns/1e6,3),
                'expires_at_unix_ms':int((now+expires_ns)//1_000_000)}
            self.latest[key]=row;self.deadlines[key]=self.mono_ns()+expires_ns
            self.changed=True;self.ever_staged+=1;self.counts['ingressed']+=1
            if old is not None:self.counts['replaced']+=1;metrics.count('ingress_same_lane_replaced')
            self.published_ages_ms.append(round(age_ns/1e6,3));self.published_ages_ms=self.published_ages_ms[-256:]
            self.last_signal_slot=slot;metrics.count('ingress_accepted')
            metrics.depth(len(self.latest))
            if self.callback:
                try:self.callback(dict(row))
                except Exception:
                    self.fail('ATOMIC_REPRICE_CALLBACK_FAILED');metrics.count('ingress_callback_failed');return None
            return row
        def report(self):
            r=super().report()
            r['latest_token_prefixes']=[str(k[0])[:12] for k in self.latest]
            r['latest_direction_lanes']=dict(collections.Counter(k[3] for k in self.latest))
            r['candidate_key_scope']='TOKEN_PUMP_DLMM_DIRECTION_SIZE'
            return r
    return DirectionIngress

def make_scheduling_worker(legacy_factory,base_core,native,provider,rpc,accum,metrics):
    """FIFO at the lane level, replace only within identical key, serial wallet exposure."""
    legacy=legacy_factory(base_core,native,provider,rpc,accum)
    class DirectionWorker(legacy):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.enqueued_at={}
        def submit(self,row):
            key=key_of(row); now=time.perf_counter_ns()
            with self.cv:
                if self.stop or self.invalidated:
                    metrics.count('worker_closed_rejected');return
                if key not in self.latest and len(self.latest)>=MAX_LANES:
                    metrics.count('worker_capacity_rejected');return
                if key in self.latest:
                    metrics.count('worker_same_lane_replaced');self.counts['replaced']+=1
                self.generations[key]=self.generations.get(key,0)+1
                self.latest[key]=(dict(row),self.generations[key])
                self.enqueued_at[key]=now
                self.counts['submitted']+=1;metrics.count('worker_submitted')
                metrics.depth(len(self.latest));self.cv.notify()
        def reconcile(self,active_candidates):
            with self.cv:
                active=set(active_candidates)
                for key in list(self.generations):
                    if key not in active:
                        self.generations[key]+=1;self.latest.pop(key,None)
                        self.enqueued_at.pop(key,None)
                        self.counts['source_invalidations']+=1
                        metrics.count('source_invalidations')
                        del self.generations[key]
                self.cv.notify_all()
        def loop(self):
            while True:
                with self.cv:
                    while not self.latest and not self.stop:self.cv.wait(.2)
                    if self.stop:return
                    key=next(iter(self.latest))
                    row,generation=self.latest.pop(key)
                    enqueue=self.enqueued_at.pop(key,time.perf_counter_ns())
                start=time.perf_counter_ns();metrics.timing('queue_ms',(start-enqueue)/1e6)
                result={'stage':'HOLD','reason':'NOT_CERTIFIED'}
                try:
                    if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_BEFORE_NATIVE')
                    issue=base_core.stage1_nomination(row)
                    if issue:raise native.Hold(issue)
                    a=time.perf_counter_ns()
                    proof=provider.prepare_unsigned(row)
                    b=time.perf_counter_ns();metrics.timing('native_ms',(b-a)/1e6)
                    if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_BEFORE_SIM')
                    a=time.perf_counter_ns()
                    result=base_core.simulation_gate(row,proof,rpc)
                    metrics.timing('simulation_and_fee_ms',(time.perf_counter_ns()-a)/1e6)
                    if not isinstance(result,dict) or result.get('stage') not in ('HOLD','UNSIGNED_SIM_NET_ESTIMATE_PASS'):
                        raise native.Hold('SIM_GATE_RESULT_INVALID')
                    if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_AFTER_SIM')
                except Exception as exc:
                    result={'stage':'HOLD','reason':safe_exc(exc)}
                metrics.timing('queue_to_decision_ms',(time.perf_counter_ns()-enqueue)/1e6)
                reason=str(result.get('reason') or result.get('stage') or 'UNKNOWN')[:95]
                metrics.count('decision_'+re.sub('[^A-Za-z0-9_]','_',reason))
                if result.get('stage')=='UNSIGNED_SIM_NET_ESTIMATE_PASS':
                    metrics.count('unsigned_sim_net_estimate_pass_not_realized_profit')
                with self.cv:
                    self.results.append(result);self.results=self.results[-80:]
                    self.counts[reason]+=1
                accum[reason]+=1
                print('[ORACLE379_GATE]',json.dumps({'stage':result.get('stage'),
                    'reason':reason,'direction':row.get('direction'),'size_lamports':row.get('size_lamports'),
                    'event_id':row.get('event_id')},sort_keys=True),flush=True)
    return DirectionWorker

# SDK helper is the official ORACLE-378 implementation converted to a persistent
# JSON-lines process. It imports SDKs only once. The RPC/native calls inside
# construct() STILL occur per nominated candidate; they are not certified fast.
NODE_TAIL_MARK='// One-shot structured stdin: payload contains public keys, public amounts only.'
def persistent_node_source(m378):
    source=m378.NODE_SOURCE
    if source.count(NODE_TAIL_MARK)!=1:raise Hold('ORACLE378_SDK_SOURCE_SHAPE_CHANGED')
    header=source.split(NODE_TAIL_MARK)[0]
    header=header.replace("import {readFileSync} from 'node:fs';", "import {createInterface} from 'node:readline';")
    return header+'''// Persistent unsigned JSON-lines worker; no wallet key material.
process.stdout.write(JSON.stringify({worker_ready:true})+'\\n');
const rl=createInterface({input:process.stdin,crlfDelay:Infinity,terminal:false});
for await(const line of rl){
 try{
   const req=JSON.parse(line);
   const r=await construct(req);
   process.stdout.write(JSON.stringify(r)+'\\n');
 }catch(e){
   const reason=String(e?.message||'').match(/^[A-Z][A-Z0-9_]{3,80}$/)?.[0]||'SDK_NATIVE_BUILDER_ERROR';
   process.stdout.write(JSON.stringify({ok:false,reason})+'\\n');
 }
}
'''

class PersistentUnsignedSdk:
    def __init__(self,node=NODE_HELPER,timeout_s=15):
        self.node=node;self.timeout_s=timeout_s
        self.lock=threading.Lock();self.proc=None;self.lines=queue.Queue();self.reader=None
        self.startups=0;self.calls=0
    def start(self):
        if self.proc and self.proc.poll() is None:return
        if not self.node.is_file():raise Hold('ORACLE379_NODE_INSTALL_FIRST')
        self.proc=subprocess.Popen(['node',str(self.node.resolve())],cwd=self.node.parent,
             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
             env=clean_env(),text=True,bufsize=1)
        self.lines=queue.Queue(maxsize=4)
        proc=self.proc;target_queue=self.lines
        def reader():
            for line in proc.stdout:
                try:target_queue.put(line,timeout=.1)
                except queue.Full:pass
        self.reader=threading.Thread(target=reader,daemon=True,name='oracle379-unsigned-node-reader')
        self.reader.start();self.startups+=1
        try:
            ready=json.loads(self.lines.get(timeout=20))
            if ready!={'worker_ready':True}:raise Hold('PERSISTENT_NODE_NOT_READY')
        except (queue.Empty,ValueError):
            self.close();raise Hold('PERSISTENT_NODE_STARTUP_TIMEOUT') from None
    def request(self,payload):
        if not isinstance(payload,dict):raise Hold('INVALID_UNSIGNED_PAYLOAD')
        if any(KEY_DENY.search(str(k)) for k in payload):raise Hold('SECRET_FIELD_BLOCKED')
        if not os.environ.get('SOLANA_RPC_URL','').startswith('https://'):
            raise Hold('HTTPS_RPC_REQUIRED')
        with self.lock:
            self.start();self.calls+=1
            try:
                self.proc.stdin.write(json.dumps(payload,separators=(',',':'))+'\n')
                self.proc.stdin.flush()
                out=self.lines.get(timeout=self.timeout_s)
                obj=json.loads(out)
                if not isinstance(obj,dict):raise Hold('NODE_BAD_RESPONSE')
                if not obj.get('ok'):raise Hold(str(obj.get('reason','SDK_NATIVE_HOLD')) if CODE.fullmatch(str(obj.get('reason',''))) else 'SDK_NATIVE_HOLD')
                return obj
            except (BrokenPipeError,queue.Empty,ValueError,OSError) as exc:
                self.close();raise Hold('PERSISTENT_NODE_'+type(exc).__name__.upper()) from None
    def close(self):
        p=self.proc;self.proc=None
        if p is not None:
            try:
                if p.stdin:p.stdin.close()
                p.terminate();p.wait(timeout=2)
            except (OSError,subprocess.TimeoutExpired):
                try:p.kill()
                except OSError:pass

class InventoryProviderFactory:
    """Native prep only at startup; do not pretend Q25 produced 28 exact pairs."""
    def __init__(self,m378,metrics):self.m378=m378;self.metrics=metrics;self.inventory=None
    def provider_class(self):
        factory=self
        class InventoryProvider(factory.m378.CompatibleNativeProvider):
            def prewarm(self):
                started=time.perf_counter_ns()
                super().prewarm()
                # Eager Q25 discovery/replenishment happens once at process STARTUP,
                # never in a fresh-candidate callback. This uses the canonical
                # same-token pair objects and existing official template builders.
                initial=set(str(k) for k in getattr(self.old,'READY_TOKENS',[]))
                initial_pairs=len(self.forward.pairs)
                discovery_status='UNATTEMPTED'
                discovered_count=initial_pairs
                try:
                    if not callable(getattr(self.old.q25.q60b2,'prepare_once',None)):
                        raise Hold('CANONICAL_Q25_DISCOVERY_UNAVAILABLE')
                    fresh,_=self.old.q25.q60b2.prepare_once(Path.cwd())
                    if not isinstance(fresh,dict) or not isinstance(fresh.get('pairs'),(list,tuple)):
                        raise Hold('CANONICAL_DISCOVERY_RESULT_INVALID')
                    allpairs=list(fresh['pairs'])
                    discovered_count=len(allpairs)
                    if len(allpairs)>initial_pairs:
                        identities=[str(pair.token) for pair in allpairs]
                        if len(set(identities))!=len(identities):
                            raise Hold('DUPLICATE_CANONICAL_PAIR_TOKEN')
                        self.old.q25.bind_cached_state(fresh)
                        warmed=self.old.install_proven_hot_math(fresh)
                        self.old.prebuild_templates(fresh,self.forward.wallet)
                        self.old.prebuild_meteora_templates(fresh,self.forward.wallet,warmed)
                        self.forward.state=fresh
                        self.forward.pairs={str(pair.token):pair for pair in allpairs}
                        self.forward.indexes={str(pair.token):i for i,pair in enumerate(allpairs)}
                        self.forward.programs={str(x['token']):str(x['program']) for x in warmed
                          if isinstance(x,dict) and x.get('token') and x.get('program')}
                        discovery_status='EAGER_CANONICAL_REPLENISH_APPLIED'
                    else:
                        discovery_status='CANONICAL_DISCOVERY_DID_NOT_EXPAND'
                except Hold:
                    raise
                except Exception:
                    # Any attempted partial canonical rebind must stop the run.
                    raise Hold('EAGER_CANONICAL_PREWARM_FAILED') from None
                factory.metrics.timing('initial_native_warm_ms',(time.perf_counter_ns()-started)/1e6)
                ready=set(str(k) for k in getattr(self.old,'READY_TOKENS',[]))
                pairs=self.forward.pairs
                excluded=[]
                for mint,pair in pairs.items():
                    missing=[]
                    if mint not in ready:missing.append('CANONICAL_TEMPLATE_NOT_READY')
                    if mint not in self.forward.programs:missing.append('TOKEN_PROGRAM_NOT_PREWARMED')
                    excluded.append({'token_prefix':mint[:12], 'reason':missing or ['NATIVE_TEMPLATE_READY'],
                                     'eligible':not missing})
                factory.inventory={'initial_native_pairs':initial_pairs,
                    'initial_native_ready':len(initial),
                    'eager_discovery_pairs':discovered_count,
                    'eager_discovery_status':discovery_status,
                    'discovered_in_native_state':len(pairs),
                    'native_ready_reported':len(ready),
                    'native_ready_with_token_program':sum(x['eligible'] for x in excluded),
                    'direction_template_proof':'NOT_CERTIFIED_FOR_ALL_PAIRS',
                    'scanner_target_pairs':28,'canonical_exclusions':excluded,
                    'native_capacity_limit_4_removed_in_379_scheduler':True,
                    'scope':'EAGER_PREWARM_BUT_NOT_28_PAIR_CERTIFICATION'}
                print('[ORACLE379_NATIVE_INVENTORY]',json.dumps({
                    'initial_pairs':initial_pairs,'discovery_pairs':discovered_count,
                    'eligible':factory.inventory['native_ready_with_token_program'],
                    'scanner_target':28,'fully_prewarmed_28_certified':False,
                    'discovery_status':discovery_status},sort_keys=True),flush=True)
        return InventoryProvider

def install():
    data=Path(__file__).resolve().read_bytes()
    compile(data.decode('utf-8'),str(TARGET),'exec')
    try:
        m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
        source=persistent_node_source(m378)
    except (ImportError,AttributeError) as exc:
        raise Hold('ORACLE378_INSTALLATION_REQUIRED') from None
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile(mode='wb',dir=TARGET.parent,delete=False) as f:f.write(data);tmp=f.name
        os.replace(tmp,TARGET)
    NODE_DIR.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=NODE_DIR,delete=False) as f:f.write(source);tmp=f.name
    os.replace(tmp,NODE_HELPER)
    print('[ORACLE379_INSTALL_PASS]',TARGET,'node='+str(NODE_HELPER),
          'sha256='+hashlib.sha256(data).hexdigest(),flush=True)

def audit():
    if not TARGET.exists() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE379_INSTALLED_SOURCE_MISMATCH')
    m363,m368,m374,m378=modules()
    m378.audit()
    if not NODE_HELPER.exists() or NODE_HELPER.read_text(encoding='utf-8')!=persistent_node_source(m378):
        raise Hold('ORACLE379_NODE_SOURCE_MISMATCH')
    p=subprocess.run(['node','--check',str(NODE_HELPER)],capture_output=True,timeout=12,env=clean_env())
    if p.returncode:raise Hold('ORACLE379_NODE_SYNTAX_FAILED')
    if any((AUTHORITY,SIGNING,BROADCAST,m378.EXECUTION_AUTHORITY,m378.SIGNING,m378.BROADCAST)):
        raise Hold('EXECUTION_AUTHORITY_VIOLATION')
    print('[ORACLE379_AUDIT_PASS] 322_FROZEN 378_NATIVE_GATE_PRESERVED '
          'DIRECTION_LANES BOUNDED_FIFO PERSISTENT_UNSIGNED_NODE NO_SIGN_NO_BROADCAST',flush=True)

def burst(n=28):
    """Deterministic 28 tokens x 2 routes + same-key replacement at two boundaries."""
    from collections import OrderedDict
    base=type('Mock363',(),{})
    base.DIRECTIONS=DIRECTIONS;base.MIN_SIZE=FIRST_CANARY;base.MAX_SIZE=100_000_000
    base.valid_pubkey=lambda s:isinstance(s,str) and s.startswith('k')
    base.exact_int=lambda x,positive=False:int(x) if type(x) is int and (not positive or x>0) else (_ for _ in ()).throw(ValueError())
    base.gross_hint=lambda r:r['gross']
    class BaseIngress:
        def __init__(self,callback=None):
            self.failed=False;self.epoch=1;self.producer='synthetic-test';self.cursor=0
            self.latest={};self.deadlines={};self.counts=collections.Counter()
            self.ttl_ns=2_500_000_000;self.max_age_ns=1_500_000_000
            self.clock_ns=lambda:10_000_000_000;self.mono_ns=lambda:10_000_000_000
            self.callback=callback;self.recent_ids=OrderedDict();self.changed=False
            self.ever_staged=0;self.published_ages_ms=[];self.last_signal_slot=None
        def _decode(self,x):return x
        def fail(self,why):self.failed=True
        def report(self):return {'latest_token_prefixes':[]}
    base.LocalIngress=BaseIngress
    metr=Metrics();ing=make_ingress(base,metr)()
    eid=0
    def send(tok,di,gross=100,sz=FIRST_CANARY):
        nonlocal eid
        eid+=1
        return ing.accept({'id':eid,'created_ns':9_999_900_000,'slot':11,'size_lamports':sz,
                   'token':'k'+str(tok),'pump_pool':'k-pump'+str(tok),'meteora_pool':'k-dlmm'+str(tok),
                   'direction':di,'gross':gross})
    for t in range(n):
        for d in DIRECTIONS:assert send(t,d) is not None
    assert len(ing.latest)==2*n
    assert send(0,DIRECTIONS[1],-4) is None
    assert len(ing.latest)==2*n-1 and key_of(next(iter(ing.latest.values())))[3]==DIRECTIONS[0]
    assert send(0,DIRECTIONS[1]) is not None
    assert len(ing.latest)==2*n
    assert send(0,DIRECTIONS[0]) is not None and len(ing.latest)==2*n
    assert send(0,DIRECTIONS[0],sz=15_000_000) is not None and len(ing.latest)==2*n+1
    # Driver uses the same key-of logic at the worker boundary; no token-only keys.
    keys={key_of(r) for r in ing.latest.values()}
    assert len(keys)==2*n+1
    return {'tokens':n,'independent_direction_lanes':2*n,'size_variant_lanes':1,
            'total_final':len(keys),'cross_direction_loss':0,
            'metrics':metr.report()}

def tests():
    class Tests(unittest.TestCase):
        def test_28x2(self):self.assertEqual(burst()['total_final'],57)
        def test_lanes(self):
            a={'token':'X','pump_pool':'P','meteora_pool':'D','direction':DIRECTIONS[0],'size_lamports':10}
            b=dict(a,direction=DIRECTIONS[1]);self.assertNotEqual(key_of(a),key_of(b))
        def test_size_lane(self):
            a={'token':'X','pump_pool':'P','meteora_pool':'D','direction':DIRECTIONS[0],'size_lamports':10}
            self.assertNotEqual(key_of(a),key_of(dict(a,size_lamports=11)))
        def test_pool_identity(self):
            a={'token':'X','pump_pool':'P','meteora_pool':'D','direction':DIRECTIONS[0],'size_lamports':10}
            self.assertNotEqual(key_of(a),key_of(dict(a,meteora_pool='OTHER')))
        def test_invalid_direction(self):
            with self.assertRaises(Hold):key_of({'token':'X','pump_pool':'P','meteora_pool':'D','direction':'OTHER','size_lamports':10})
        def test_percentiles(self):self.assertEqual(quantiles([1,2,3,4,5])['p95_ms'],5)
        def test_empty_percentiles(self):self.assertEqual(quantiles([])['samples'],0)
        def test_bounded_input(self):self.assertEqual(MAX_LANES,512)
        def test_secrets_scrubbed(self):
            x=clean_env({'A':'1','QSB_SOLANA_PRIVATE_KEY':'do_not_log','SEED_PHRASE':'bad'})
            self.assertEqual(x,{'A':'1'})
        def test_key_not_broadcast(self):self.assertEqual((AUTHORITY,SIGNING,BROADCAST),(False,False,False))
        def test_fixed_canary(self):self.assertEqual(FIRST_CANARY,10_000_000)
        def test_native_worker_no_send(self):
            import inspect
            src=inspect.getsource(make_scheduling_worker)
            self.assertNotIn('sendTransaction',src)
            self.assertIn('simulation_gate',src)
        def test_negative_doesnt_nuke_opposite(self):self.assertEqual(burst(1)['total_final'],3)
        def test_node_protocol_source(self):
            class Fake:
                NODE_SOURCE="import {readFileSync} from 'node:fs';\n"+NODE_TAIL_MARK+"\ntry{}catch(e){}"
            src=persistent_node_source(Fake)
            self.assertIn('for await(const line of rl)',src)
            self.assertIn('worker_ready:true',src)
            self.assertNotIn('readFileSync(0',src)
        def test_node_secret_payload(self):
            with patch.object(PersistentUnsignedSdk,'start',return_value=None):
                client=PersistentUnsignedSdk()
                with self.assertRaises(Hold):client.request({'SEED':'no'})
        def test_worker_direction_and_size_capacity(self):
            # Exercise the actual new worker submit/reconcile methods, not just key_of.
            class Base:
                def __init__(self,*args,**kwargs):
                    self.cv=threading.Condition();self.stop=False;self.invalidated=False
                    self.latest={};self.generations={};self.results=[];self.counts=collections.Counter()
                    self.thread=None
                def newer_or_invalid(self,key,generation):
                    with self.cv:return self.invalidated or self.generations.get(key)!=generation
            class Core:
                @staticmethod
                def stage1_nomination(row):return None
                @staticmethod
                def simulation_gate(row,proof,rpc):return {'stage':'HOLD','reason':'FIXTURE_NO_PROFIT'}
            class Native:
                class Hold(RuntimeError):pass
            class Provider:
                def prepare_unsigned(self,row):return {'fixture':True}
            m=Metrics()
            worker_cls=make_scheduling_worker(lambda *args:Base,Core,Native,Provider(),object(),collections.Counter(),m)
            worker=worker_cls()
            for t in range(28):
                for direction in DIRECTIONS:
                    row={'token':str(t),'pump_pool':'p'+str(t),'meteora_pool':'m'+str(t),
                         'direction':direction,'size_lamports':FIRST_CANARY,'event_id':t+1}
                    worker.submit(row)
            self.assertEqual(len(worker.latest),56)
            self.assertEqual(worker.counts['submitted'],56)
            first=dict(worker.latest[next(iter(worker.latest))][0])
            worker.submit(first)
            self.assertEqual(len(worker.latest),56)
            self.assertEqual(worker.counts['replaced'],1)
            alternate=dict(first,direction=DIRECTIONS[1]);key=key_of(alternate)
            self.assertIn(key,worker.latest)
            worker.reconcile({key})
            self.assertEqual(len(worker.latest),1)
            self.assertEqual(worker.counts['source_invalidations'],55)
        def test_worker_queue_bound_explicit(self):
            class Base:
                def __init__(self,*args,**kwargs):
                    self.cv=threading.Condition();self.stop=False;self.invalidated=False
                    self.latest={};self.generations={};self.counts=collections.Counter()
            met=Metrics();worker=make_scheduling_worker(lambda *args:Base,object(),object(),None,None,collections.Counter(),met)()
            for i in range(MAX_LANES+1):
                worker.submit({'token':str(i),'pump_pool':'p','meteora_pool':'m',
                    'direction':DIRECTIONS[0],'size_lamports':FIRST_CANARY})
            self.assertEqual(len(worker.latest),MAX_LANES)
            self.assertEqual(met.report()['counts']['worker_capacity_rejected'],1)
        def test_v2_probe_is_api_only(self):
            import inspect
            src=inspect.getsource(v2_probe)
            self.assertIn('v2_native_route_enabled',src)
            self.assertNotIn('sendTransaction',src)
        def test_no_rpc_per_quote_claim(self):
            import inspect
            self.assertIn('sdk_rpcs_inside_construct_are_still_cold',inspect.getsource(run))
        def test_report_only_aggregate(self):
            m=Metrics();m.count('accepted');m.timing('stage',3.25)
            self.assertEqual(m.report()['counts']['accepted'],1)
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not r.wasSuccessful():return 1
    print('[ORACLE379_BURST_PASS]',json.dumps({k:v for k,v in burst().items() if k!='metrics'},sort_keys=True),flush=True)
    print('[ORACLE379_TEST_PASS]',r.testsRun,flush=True)
    return 0

def v2_probe():
    """API capability only: v2 parity/cashback economics are NOT certified."""
    m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
    m378.sdk_check()
    js=("import {PUMP_AMM_SDK} from '@pump-fun/pump-swap-sdk'; "
        "const x={sellV2:typeof PUMP_AMM_SDK?.sellV2Instructions==='function',"
        "buyV2:typeof PUMP_AMM_SDK?.buyV2Instructions==='function'};"
        "console.log(JSON.stringify(x));")
    try:
        p=subprocess.run(['node','--input-type=module','-e',js],cwd=NODE_DIR,
            capture_output=True,text=True,env=clean_env(),timeout=20)
        if p.returncode:raise Hold('PUMP_V2_PROBE_UNAVAILABLE')
        caps=json.loads(p.stdout.strip())
        if not isinstance(caps,dict):raise Hold('PUMP_V2_PROBE_INVALID')
    except (OSError,subprocess.TimeoutExpired,ValueError):
        raise Hold('PUMP_V2_PROBE_UNAVAILABLE') from None
    print('[ORACLE379_PUMP_V2_API_ONLY]',json.dumps({
        'sdk_exports':caps,'cashback_eligibility_tested':False,
        'v2_quote_parity_tested':False,'v2_native_route_enabled':False},sort_keys=True),flush=True)

def run(minutes,poll_ms,wallet):
    """Actual ORACLE-374 native pipeline, isolated runtime-bound executor replacements."""
    m363,m368,m374,m378=modules()
    audit()
    if not m374.PUBKEY.fullmatch(wallet):raise Hold('PUBLIC_WALLET_REQUIRED')
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUN_BOUNDS_INVALID')
    sdk=PersistentUnsignedSdk()
    metrics=Metrics();factory=InventoryProviderFactory(m378,metrics)
    original=(m363.LocalIngress,m374.make_worker,m374.RecoveringNativeProvider,
              m374.REPORT,m378._sdk_reverse)
    ingress=make_ingress(m363,metrics)
    build_worker=m374.make_worker
    def wrapped_worker(core,native,provider,rpc,accum):
        return make_scheduling_worker(build_worker,core,native,provider,rpc,accum,metrics)
    m363.LocalIngress=ingress
    m374.make_worker=wrapped_worker
    m374.RecoveringNativeProvider=factory.provider_class()
    m374.REPORT=SOURCE_REPORT
    m378._sdk_reverse=sdk.request
    started=time.perf_counter_ns()
    status='HOLD_UNKNOWN';code=2
    try:
        # The SDK worker starts before scanner candidate intake, never on signal.
        sdk.start()
        code=m374.launch(minutes=minutes,poll_ms=poll_ms,wallet_pubkey=wallet)
        status='NATIVE_SESSION_COMPLETED' if code==0 else 'NATIVE_SESSION_HOLD'
    except Exception as exc:
        status=safe_exc(exc)
        print('[ORACLE379_RUNTIME_HOLD]',status,flush=True)
    finally:
        (m363.LocalIngress,m374.make_worker,m374.RecoveringNativeProvider,
          m374.REPORT,m378._sdk_reverse)=original
        sdk.close()
        report={'build':'ORACLE379','status':status,'pipeline_return_code':code,
                'runtime_seconds':round((time.perf_counter_ns()-started)/1e9,3),
                'scanner_322_modified':False,'execution_authority':False,
                'signing':False,'broadcast':False,'realized_profit_certified':False,
                'native_atomic_profit_certified':False,'inventory':factory.inventory,
                'sdk_node_process_startups':sdk.startups,'sdk_calls':sdk.calls,
                'sdk_rpcs_inside_construct_are_still_cold':True,
                'candidate_pipeline':metrics.report()}
        write_json(REPORT,report)
        print('[ORACLE379_CAPACITY_REPORT]',REPORT,flush=True)
        print('[ORACLE379_STATUS]',status,flush=True)
    return code if status=='NATIVE_SESSION_COMPLETED' else 2

def main():
    p=argparse.ArgumentParser()
    for flag in ('install','test','audit','sdk-check','burst','run','observe','v2-probe'):p.add_argument('--'+flag,action='store_true')
    p.add_argument('--minutes',type=int,default=5)
    p.add_argument('--poll-ms',type=int,default=5)
    p.add_argument('--seconds',type=int,default=30)
    p.add_argument('--wallet-pubkey',default=os.getenv('QSB_SOLANA_WALLET',''))
    a=p.parse_args()
    if not any((a.install,a.test,a.audit,a.sdk_check,a.burst,a.run,a.observe,a.v2_probe)):p.error('SPECIFY_ACTION')
    if a.install:install()
    if a.test:
        rc=tests()
        if rc:return rc
    if a.audit:audit()
    if a.sdk_check:
        m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
        m378.sdk_check()
        print('[ORACLE379_SDK_CHECK_PASS] inherited_official_378_sdk',flush=True)
    if a.v2_probe:v2_probe()
    if a.burst:print('[ORACLE379_CAPACITY_FIXTURE]',json.dumps(burst(),sort_keys=True),flush=True)
    if a.observe:
        m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
        return m378.observe(a.seconds)
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Hold as e:print('[ORACLE379_HOLD]',safe_exc(e),flush=True);raise SystemExit(2)
