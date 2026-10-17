"""ORACLE-382: complete installer, staged executor-only canonical hot inventory.

ORACLE-322 is frozen. The old QARB live_account_stream defaults to only four
prepared pairs, regardless of scanner coverage. This installer DOES NOT change
that source file or scanner. It temporarily increases that executor module's
MAX_PAIRS in bounded background replenishment stages. All canonical, native,
profit and source-health gates remain in charge. No keys, signing, broadcasting.
"""
from __future__ import annotations
import argparse
from collections import Counter, OrderedDict
import importlib
import inspect
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_382_staged_native_capacity.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_382_capacity_reconciliation.json')
BASE_REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_381_replenishment_health.json')
INSPECT_REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_382_scanner_inventory_inspect.json')
HOT_MODULE='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.live_account_stream'
ENGINE_MODULE='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.engine'
MAX_PAIRS=28
STAGE_STEP=2
CAP_LOCK=threading.RLock()
EXECUTION_AUTHORITY=SIGNING=BROADCAST=False
FIRST_FUNDED_CANARY=10_000_000

class Hold(RuntimeError):pass

def dep():
    return importlib.import_module(PKG+'.oracle_381_canonical_replenishment_health')

def hot_modules():
    return importlib.import_module(HOT_MODULE),importlib.import_module(ENGINE_MODULE)

def safe_read(path):
    try:
        v=json.loads(Path(path).read_text(encoding='utf8'))
        return v if isinstance(v,dict) else {}
    except (OSError,ValueError,TypeError):return {}

def atomic_json(path,record):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,delete=False) as f:
        json.dump(record,f,sort_keys=True,indent=2,default=str);tmp=f.name
    os.replace(tmp,path)

def target_stage(existing, current_cap=4, max_pairs=MAX_PAIRS,step=STAGE_STEP):
    """Never go backwards or exceed 28; one incremental group at a time."""
    if not (1<=max_pairs<=28 and 1<=step<=4):raise Hold('PAIR_STAGE_CONFIG_INVALID')
    if type(existing) is not int or existing<0:raise Hold('NATIVE_PAIR_COUNT_INVALID')
    if type(current_cap) is not int or current_cap<1:raise Hold('HOT_CAP_INVALID')
    return min(max_pairs,max(4,existing)+step)

def pair_identity(x):
    """Public canonical triple; strictly type/shape-checked, never wallet keys."""
    if isinstance(x,dict):
        triple=tuple(x.get(k) for k in ('token','pump_pool','meteora_pool'))
    else:
        triple=tuple(getattr(x,k,None) for k in ('token','pump_pool','meteora_pool'))
    if any(not isinstance(v,str) or not 20<=len(v)<=60 for v in triple):
        return None
    return triple

def reconcile_identity(triple,known,ready=()):
    """A scanner nomination is NOT proof an executable crosslisted pair exists."""
    if not triple:return 'BAD_NOMINATION_IDENTITY'
    token,pump,dlmm=triple
    matches=[c for c in known if c[0]==token]
    if not matches:return 'TOKEN_ABSENT_EXACT_CROSSLIST'
    if (token,pump,dlmm) not in matches:return 'TOKEN_PRESENT_BUT_POOL_IDENTITY_DIFFERENT'
    if token not in ready:return 'EXACT_POOLS_MATCH_NOT_NATIVE_READY'
    return 'EXACT_POOLS_MATCH_NATIVE_READY_NOT_PROFIT_CERTIFIED'

def bounded_bus_sample(m381,limit=1200,conn=None,validator=None,canonical=None,ready=()):
    """One read-only SQLite connection; no RPC or WS and no scanner mutation."""
    if not 1<=limit<=2000:raise Hold('BUS_SAMPLE_BOUNDS_INVALID')
    own=False;health=None
    try:
        if conn is None:
            m379,_=m381.imports().import_deps()
            scanner=m379.modules()[0].resolve_scanner_bus()
            conn=scanner.bus();own=True;validator=scanner.validate_scanner
        conn.execute('PRAGMA query_only=ON')
        conn.execute('PRAGMA busy_timeout=500')
        if validator:
            health=validator(conn)
            if not isinstance(health,dict) or type(health.get('epoch')) is not int:
                raise Hold('SCANNER_HEALTH_CONTRACT_INVALID')
        cols=[x[1] for x in conn.execute('PRAGMA table_info(events)')]
        mandatory=('id','token','pump_pool','meteora_pool','direction','size_lamports')
        if any(k not in cols for k in mandatory):raise Hold('SCANNER_EVENTS_SCHEMA_UNVERIFIED')
        last=int(conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
        # Bounded query: only latest event IDs; a committed cursor cannot be falsified.
        lo=max(0,last-limit)
        cur=conn.execute('SELECT id,token,pump_pool,meteora_pool,direction,size_lamports '
                         'FROM events WHERE id>? ORDER BY id DESC LIMIT ?', (lo,limit))
        observed=[];directions=Counter();size_counts=Counter();tokens=Counter()
        latest={};bad=0
        for eid,token,pump,dlmm,direction,size in cur:
            triple=pair_identity({'token':token,'pump_pool':pump,'meteora_pool':dlmm})
            if triple is None or direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP') or type(size) is not int:
                bad+=1;continue
            if triple not in latest:latest[triple]=(eid,direction,size)
            directions[direction]+=1;size_counts[size]+=1;tokens[token]+=1
        for triple,(eid,direction,size) in sorted(latest.items(),key=lambda x:x[1][0],reverse=True)[:20]:
            observed.append({'token_prefix':triple[0][:12],'pump_pool_prefix':triple[1][:12],
                   'meteora_pool_prefix':triple[2][:12],'event_id':eid,'direction':direction,
                   'size_lamports':size,
                   'canonical_verdict':reconcile_identity(triple,canonical,ready) if canonical is not None
                       else 'CANONICAL_SNAPSHOT_UNAVAILABLE'})
        return {'mode':'READ_ONLY_SCANNER_SQLITE','scanner_health':'PASS' if health else 'NOT_CERTIFIED',
                'epoch':health.get('epoch') if health else None,'latest_event_id':last,
                'sampled_events':sum(directions.values()),'invalid_rows':bad,
                'unique_tokens':len(tokens),'unique_pool_triples':len(latest),
                'direction_counts':dict(directions),'size_lamports_counts':{str(k):v for k,v in size_counts.items()},
                'hot_tokens':[{'token_prefix':t[:12],'nominations':count} for t,count in tokens.most_common(8)],
                'recent_pool_triples':observed,'scoped_read_only':True}
    finally:
        if own and conn is not None:
            try:conn.close()
            except Exception:pass

def staged_class(m381,m380,pd,engine):
    Base=m381.replenishment_class(m380)
    class StagedNativeInventory(Base):
        def __init__(self,provider,**kw):
            super().__init__(provider,**kw)
            self.cap_attempts=[]
            self.nominated=OrderedDict()
            self.exact_triples=[]
            self.discovery_cache_timestamp=None
            self.discovery_cache_unix_s=None
            self.cap_phase='WAITING'
        def request(self,token):
            if isinstance(token,str) and 20<=len(token)<=60:
                if token not in self.nominated and len(self.nominated)>=128:
                    self.nominated.popitem(last=False)
                self.nominated[token]=self.clock()
            return super().request(token)
        def attempt_once(self):
            with CAP_LOCK:
                base_cap=getattr(pd,'MAX_PAIRS',None)
                base_tokens=getattr(engine,'MAX_TOKENS',None)
                if type(base_cap) is not int or type(base_tokens) is not int:
                    raise Hold('CANONICAL_HOT_CAP_CONTRACT_MISSING')
                before=len(self.provider.forward.pairs)
                cap=target_stage(before,base_cap)
                started=self.clock();self.cap_phase='BACKGROUND_DISCOVERY'
                try:
                    # Scoped to this executor process and one background call.
                    pd.MAX_PAIRS=cap
                    engine.MAX_TOKENS=max(base_tokens,MAX_PAIRS)
                    super().attempt_once()  # original Q25 / canonical / native fail-closed gates
                finally:
                    pd.MAX_PAIRS=base_cap
                    engine.MAX_TOKENS=base_tokens
                    self.cap_phase='IDLE'
                    after=len(self.provider.forward.pairs)
                    cache=getattr(engine,'_cross_cache',{})
                    age=(time.time()-cache.get('at',0)) if isinstance(cache,dict) else float('inf')
                    if isinstance(cache,dict) and 0<=age<=120 and isinstance(cache.get('rows'),list):
                        self.exact_triples=[t for x in cache['rows'] if (t:=pair_identity(x))]
                        self.discovery_cache_timestamp=round(age,3)
                        self.discovery_cache_unix_s=float(cache.get('at',0))
                    self.cap_attempts.append({'requested_cap':cap,'native_before':before,
                       'native_after':after,'duration_ms':round((self.clock()-started)*1000,2),
                       'status':str(self.last_status)[:85],
                       'underfilled_cap':len(self.exact_triples)>=cap and after<cap,
                       'potential_hydration_limit_not_429_proof':len(self.exact_triples)>=cap and after<cap})
                    self.cap_attempts=self.cap_attempts[-15:]
        def snapshot(self):
            s=super().snapshot()
            ready=set(str(k) for k in getattr(self.provider.old,'READY_TOKENS',()))
            exact=list(self.exact_triples)
            statuses=[]
            for token in list(self.nominated)[-20:]:
                count=sum(p[0]==token for p in exact)
                status=('NOT_IN_LAST_CACHED_EXACT_CROSSLIST' if not count else
                    'IN_EXACT_CROSSLIST_NATIVE_READY' if token in ready and token in self.provider.forward.pairs
                    else 'IN_EXACT_CROSSLIST_NOT_NATIVE_READY')
                statuses.append({'token_prefix':token[:12], 'status':status})
            s.update({'four_pair_default_source':'qarb_clean_bot/live_account_stream.py',
                'four_pair_default_removed_in_background':True,'scanner_target_pairs':28,
                'target_hot_cap':MAX_PAIRS,'step_pairs':STAGE_STEP,
                'cap_attempts':list(self.cap_attempts), 'cap_phase':self.cap_phase,
                'last_cached_crosslist_age_s_at_attempt':self.discovery_cache_timestamp,
                'exact_crosslisted_token_count':len(set(t[0] for t in exact)),
                'cached_crosslist_unix_s':self.discovery_cache_unix_s,
                'exact_pool_triples':[{'token':x[0],'pump_pool':x[1],'meteora_pool':x[2]}
                    for x in exact[:28]],
                'native_ready_tokens_public':sorted(t for t in ready if t in self.provider.forward.pairs),
                'exact_pool_identities':[{'token_prefix':x[0][:12],
                    'pump_pool_prefix':x[1][:12],'meteora_pool_prefix':x[2][:12]} for x in exact[:28]],
                'nominated_token_verdicts':statuses,
                'native_ready_current':len(ready), 'native_pairs_current':len(self.provider.forward.pairs),
                'diagnostic_limit':'NO_EXECUTION_OR_PROFIT_CERTIFICATION'})
            return s
    return StagedNativeInventory

def install():
    if not (ROOT/'oracle_381_canonical_replenishment_health.py').is_file():
        raise Hold('ORACLE381_FULL_BASELINE_REQUIRED')
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf8'),str(TARGET),'exec')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:
            f.write(src);tmp=f.name
        os.replace(tmp,TARGET)
    print('[ORACLE382_INSTALL_PASS]',TARGET,flush=True)

def audit():
    if not TARGET.is_file() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE382_FULL_INSTALL_INTEGRITY_FAILED')
    m381=dep();m381.audit()
    pd,engine=hot_modules()
    source=inspect.getsource(pd.prepare_pairs)
    if not ('MAX_PAIRS' in source and 'len(out)' in source):
        raise Hold('CANONICAL_FOUR_PAIR_LIMIT_CHANGED_REAUDIT_REQUIRED')
    if any((EXECUTION_AUTHORITY,SIGNING,BROADCAST)) or FIRST_FUNDED_CANARY!=10_000_000:
        raise Hold('EXECUTION_AUTHORITY_INVARIANT_FAILURE')
    print('[ORACLE382_AUDIT_PASS] FOUR_PAIR_SOURCE_VERIFIED STAGED_EXECUTOR_ONLY_CAP '
        'Q25_CANONICAL_NATIVE_GATES_PRESERVED ORIGINAL_SCANNER_HEALTH_NO_BYPASS '
        'NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)

def tests():
    import sqlite3
    from types import SimpleNamespace as O
    class FakeBase:
        def __init__(self,p,**kw):
            self.provider=p;self.clock=kw.get('clock',lambda:12.)
            self.last_status='NOT_RUN';self.accepted=[]
        def request(self,token):self.accepted.append(token);return 'QUEUED'
        def attempt_once(self):
            self.provider.seen_caps.append((pd.MAX_PAIRS,engine.MAX_TOKENS))
            if self.provider.raise_now:raise ValueError('synthetic failure')
            if self.provider.advance:self.provider.forward.pairs['B'*43]=object()
            self.last_status='COMPLETE'
        def snapshot(self):return {'status':self.last_status}
    pd=O(MAX_PAIRS=4);engine=O(MAX_TOKENS=12,_cross_cache={'at':0.,'rows':[]})
    m381=O(replenishment_class=lambda x:FakeBase)
    Class=staged_class(m381,O(),pd,engine)
    def fake():
        p=O(forward=O(pairs={t*43:object() for t in ('A','C','D','E')}),
            old=O(READY_TOKENS={t*43 for t in ('A','C','D','E')}),
            seen_caps=[],advance=True,raise_now=False)
        return Class(p,clock=lambda:100.)
    class T(unittest.TestCase):
        def test_cap_progress(self):self.assertEqual(target_stage(4),6)
        def test_cap_max(self):self.assertEqual(target_stage(28),28)
        def test_cap_not_overridden_by_large_env(self):self.assertEqual(target_stage(4,28),6)
        def test_cap_invalid(self):
            with self.assertRaises(Hold):target_stage(-1)
        def test_cap_spaced(self):self.assertEqual(target_stage(11),13)
        def test_scoped_restoration(self):
            w=fake();w.attempt_once();self.assertEqual(w.provider.seen_caps,[(6,28)])
            self.assertEqual((pd.MAX_PAIRS,engine.MAX_TOKENS),(4,12))
        def test_failed_restoration(self):
            w=fake();w.provider.raise_now=True
            with self.assertRaises(ValueError):w.attempt_once()
            self.assertEqual((pd.MAX_PAIRS,engine.MAX_TOKENS),(4,12))
        def test_proven_native_growth(self):
            w=fake();w.attempt_once();self.assertEqual(w.snapshot()['native_pairs_current'],5)
        def test_token_record(self):
            w=fake();self.assertEqual(w.request('B'*43),'QUEUED')
            self.assertEqual(len(w.snapshot()['nominated_token_verdicts']),1)
        def test_no_unauthorized_promotion(self):
            w=fake();w.attempt_once();s=w.snapshot()
            self.assertEqual(s['diagnostic_limit'],'NO_EXECUTION_OR_PROFIT_CERTIFICATION')
        def test_exact_identity(self):
            s='A'*43;self.assertEqual(pair_identity(O(token=s,pump_pool=s,meteora_pool=s)),(s,s,s))
        def test_bad_identity(self):self.assertIsNone(pair_identity({'token':'bad'}))
        def test_missing_pair(self):
            s='A'*43;self.assertEqual(reconcile_identity((s,s,s),[]),'TOKEN_ABSENT_EXACT_CROSSLIST')
        def test_pool_mismatch(self):
            a='A'*43;b='B'*43
            self.assertEqual(reconcile_identity((a,a,b),[(a,b,b)]),'TOKEN_PRESENT_BUT_POOL_IDENTITY_DIFFERENT')
        def test_ready_not_profit(self):
            s='A'*43
            self.assertEqual(reconcile_identity((s,s,s),[(s,s,s)],{s}),
                       'EXACT_POOLS_MATCH_NATIVE_READY_NOT_PROFIT_CERTIFIED')
        def test_not_ready(self):
            s='A'*43
            self.assertEqual(reconcile_identity((s,s,s),[(s,s,s)]),'EXACT_POOLS_MATCH_NOT_NATIVE_READY')
        def test_bus_read_only_health(self):
            c=sqlite3.connect(':memory:')
            c.execute('CREATE TABLE events (id INTEGER PRIMARY KEY,token TEXT,pump_pool TEXT,meteora_pool TEXT,direction TEXT,size_lamports INTEGER)')
            s='A'*43;c.execute('INSERT INTO events VALUES(1,?,?,?,?,?)',(s,s,s,'PUMP_TO_METEORA',10000000))
            report=bounded_bus_sample(None,conn=c,validator=lambda con:{'epoch':1})
            self.assertEqual(report['sampled_events'],1)
            self.assertEqual(report['unique_pool_triples'],1)
            self.assertEqual(c.execute('PRAGMA query_only').fetchone()[0],1)
        def test_bus_health_fail(self):
            c=sqlite3.connect(':memory:')
            with self.assertRaises(Hold):bounded_bus_sample(None,conn=c,validator=lambda con:None)
        def test_bus_schema_fail(self):
            c=sqlite3.connect(':memory:');c.execute('CREATE TABLE events (id INTEGER)')
            with self.assertRaises(Hold):bounded_bus_sample(None,conn=c)
        def test_bus_bound(self):
            with self.assertRaises(Hold):bounded_bus_sample(None,limit=50000,conn=O())
        def test_fresh_canonical_join(self):
            s='A'*43
            obj={'replenishment':[{'cached_crosslist_unix_s':100.,
                'exact_pool_triples':[{'token':s,'pump_pool':s,'meteora_pool':s}],
                'native_ready_tokens_public':[s]}]}
            c,r,status=get_current_canonical(obj,now=120.)
            self.assertEqual(reconcile_identity((s,s,s),c,r),
                'EXACT_POOLS_MATCH_NATIVE_READY_NOT_PROFIT_CERTIFIED')
        def test_stale_canonical_not_trusted(self):
            c,r,status=get_current_canonical({'replenishment':[{'cached_crosslist_unix_s':100.,
                'exact_pool_triples':[]}]},now=999.)
            self.assertIsNone(c)
        def test_immutable_canary(self):self.assertEqual(FIRST_FUNDED_CANARY,10000000)
        def test_no_authority(self):self.assertEqual((EXECUTION_AUTHORITY,SIGNING,BROADCAST),(False,False,False))
        def test_source_scanner_untouched(self):
            s=inspect.getsource(staged_class)
            self.assertNotIn('scanner_status.json',s)
            self.assertIn('super().attempt_once()',s)
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE382_TEST_PASS]' if r.wasSuccessful() else '[ORACLE382_TEST_FAIL]',r.testsRun,flush=True)
    return 0 if r.wasSuccessful() else 1

def get_current_canonical(report,now=None):
    """Only join matching pool IDs when a recent completed native snapshot exists."""
    now=now or time.time()
    reps=report.get('replenishment') or []
    if not isinstance(reps,list) or not reps:return None,(), 'NO_NATIVE_SNAPSHOT'
    v=reps[-1]
    if not isinstance(v,dict):return None,(), 'INVALID_NATIVE_SNAPSHOT'
    at=v.get('cached_crosslist_unix_s')
    if not isinstance(at,(int,float)) or not 0<=now-at<=600:
        return None,(), 'STALE_OR_MISSING_CANONICAL_SNAPSHOT'
    triples=[t for x in v.get('exact_pool_triples',[]) if (t:=pair_identity(x))]
    if not triples:return None,(), 'EMPTY_CANONICAL_SNAPSHOT'
    ready=set(str(t) for t in v.get('native_ready_tokens_public',[]) if isinstance(t,str))
    return triples,ready,'RECENT_CACHED_CANONICAL_SNAPSHOT'

def inspect_read_only():
    m381=dep()
    prior=safe_read(BASE_REPORT)
    base=safe_read(Path('runtime_state/oracle/final_boss_dual/oracle_380_capacity_and_rpc.json'))
    result={'build':'ORACLE382','mode':'NO_RPC_READ_ONLY_INSPECTION',
        'original_scanner_validator':m381.scanner_bus_probe(),
        'prior_status':prior.get('session_status'),
        'prior_native_ready':((base.get('replenishment') or [{}])[-1].get('native_ready_final')
             if base.get('replenishment') else None),
        'previous_replenishment':base.get('replenishment',[]),
        'execution_authority':False,'signing':False,'broadcast':False}
    if result['original_scanner_validator']['validator']!='PASS':
        raise Hold('ORIGINAL_SCANNER_HEALTH_HOLD')
    latest=safe_read(REPORT)
    canon,ready,proof=get_current_canonical(latest)
    result['canonical_snapshot_quality']=proof
    result['scanner_events']=bounded_bus_sample(m381,canonical=canon,ready=ready)
    print('[ORACLE382_READ_ONLY_INSPECT]',json.dumps({'prior_status':result['prior_status'],
        'prior_native_ready':result['prior_native_ready'],
        'scanner_events':result['scanner_events']},sort_keys=True),flush=True)
    atomic_json(INSPECT_REPORT,result)
    print('[ORACLE382_INSPECT_REPORT]',INSPECT_REPORT,flush=True)
    return result

def run(minutes,poll_ms,wallet):
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUN_BOUNDS_INVALID')
    audit();m381=dep();pd,engine=hot_modules()
    health=m381.scanner_bus_probe()
    if health.get('validator')!='PASS':raise Hold('ORIGINAL_SCANNER_HEALTH_HOLD')
    original=m381.replenishment_class
    m381.replenishment_class=lambda m380:staged_class(OProxy(original),m380,pd,engine)
    # OProxy wraps the old *factory* while preserving its implementation.
    rc=2
    try:
        rc=m381.run(minutes,poll_ms,wallet)
    finally:
        m381.replenishment_class=original
        base=safe_read(BASE_REPORT)
        canon,ready,proof=get_current_canonical(base)
        base['canonical_snapshot_quality']=proof
        try:base['postrun_scanner_pool_match']=bounded_bus_sample(m381,canonical=canon,ready=ready)
        except Exception as exc:
            base['postrun_scanner_pool_match']={'hold':type(exc).__name__[:50],
                'note':'NO_HEALTH_BYPASS_NO_CANONICAL_CERTIFICATION'}
        base.update({'build':'ORACLE382','status':'READ_ONLY_EXECUTOR_COMPLETE' if rc==0 else 'READ_ONLY_EXECUTOR_HOLD',
              'four_pair_default_removed_in_background':True,'hot_pairs_max_target':MAX_PAIRS,
              'hot_pairs_per_successful_stage':STAGE_STEP,'scoped_executor_only':True,
              'execution_authority':False,'signing':False,'broadcast':False,
              'realized_profit_certified':False,'funded_canary_lamports':FIRST_FUNDED_CANARY})
        atomic_json(REPORT,base)
        fills=base.get('replenishment') or []
        state=fills[-1] if fills and isinstance(fills[-1],dict) else {}
        print('[ORACLE382_NATIVE_STAGE]',json.dumps({
            'native_pairs_current':state.get('native_pairs_current'),
            'native_ready_current':state.get('native_ready_current'),
            'stages':state.get('cap_attempts',[]),
            'nominated_token_verdicts':state.get('nominated_token_verdicts',[]),
            'exact_crosslisted_token_count':state.get('exact_crosslisted_token_count'),
            'replenishment_status':state.get('status'),
            'cap_expansion_certified':type(state.get('native_pairs_current')) is int and state['native_pairs_current']>4},sort_keys=True),flush=True)
        pool=base.get('postrun_scanner_pool_match',{})
        print('[ORACLE382_POOL_MATCH]',json.dumps({
            'canonical_snapshot_quality':proof,
            'scanner_health':pool.get('scanner_health'),
            'hot_tokens':pool.get('hot_tokens'),
            'recent_pool_triples':(pool.get('recent_pool_triples') or [])[:4]},sort_keys=True),flush=True)
        print('[ORACLE382_CAPACITY_REPORT]',REPORT,flush=True)
        print('[ORACLE382_STATUS]',base['status'],flush=True)
    return rc

class OProxy:
    def __init__(self,old_factory):self.factory=old_factory
    def replenishment_class(self,m380):return self.factory(m380)

def main():
    ap=argparse.ArgumentParser()
    for mode in ('install','test','audit','sdk-check','burst','inspect','health-gate','run'):
        ap.add_argument('--'+mode,action='store_true')
    ap.add_argument('--minutes',type=int,default=5)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=ap.parse_args()
    if not any([a.install,a.test,a.audit,a.sdk_check,a.burst,a.inspect,a.health_gate,a.run]):
        ap.error('ACTION_REQUIRED')
    if a.install:install()
    if a.test and tests():return 1
    if a.audit:audit()
    if a.sdk_check:dep().imports().import_deps()[0].sdk_check_visible()
    if a.burst:print('[ORACLE382_BURST_PASS]',json.dumps(dep().imports().import_deps()[0].burst(),sort_keys=True),flush=True)
    if a.inspect:inspect_read_only()
    if a.health_gate:
        probe=dep().scanner_bus_probe()
        if probe.get('validator')!='PASS':
            print('[ORACLE382_SCANNER_HEALTH_HOLD]',json.dumps(probe,sort_keys=True),flush=True)
            return 2
        print('[ORACLE382_SCANNER_HEALTH_PASS]',json.dumps(probe,sort_keys=True),flush=True)
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        # Fail closed; never echo raw exception text containing RPC URL/API tokens.
        print('[ORACLE382_HOLD]',type(exc).__name__,flush=True)
        raise SystemExit(2)
