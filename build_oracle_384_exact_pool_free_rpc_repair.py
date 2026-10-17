"""ORACLE-384: full executor-only exact-pool selection and guarded rotating native inventory.

Requires ORACLE-383 baseline. ORACLE-322 remains frozen; no signature, broadcast,
funded trade, secret reading or logging. Uses read-only validated scanner nominations
as *hints*, not as evidence of on-chain pool existence or profitable execution.
"""
from __future__ import annotations
import argparse
from collections import Counter, OrderedDict
import importlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.parse import quote
from unittest.mock import patch

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_384_exact_pool_free_rpc_repair.py')
REPORT = Path('runtime_state/oracle/final_boss_dual/oracle_384_exact_pool_free_rpc_report.json')
UPSTREAM = Path('runtime_state/oracle/final_boss_dual/oracle_383_sdk_rpc_native_report.json')
CAPACITY = Path('runtime_state/oracle/final_boss_dual/oracle_382_capacity_reconciliation.json')
MINT_SOL = 'So11111111111111111111111111111111111111112'
EXPECTED_CANARY = 10_000_000
MAX_HINTS = 8
MAX_SAMPLE = 2500
SCAN_REFRESH_S = 20
META_TTL_S = 55
EXECUTION_AUTHORITY = SIGNING = BROADCAST = False

class Hold(RuntimeError): pass

def modules():
    m383 = importlib.import_module(PKG+'.oracle_383_sdk_rpc_native_bridge')
    m382 = importlib.import_module(PKG+'.oracle_382_staged_native_capacity')
    m381 = importlib.import_module(PKG+'.oracle_381_canonical_replenishment_health')
    m380 = importlib.import_module(PKG+'.oracle_380_rpc_admission_diagnostics')
    pd,eng = m382.hot_modules()
    core = importlib.import_module('qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core')
    return m383,m382,m381,m380,pd,eng,core

def clean_json(path):
    try:
        data=json.loads(Path(path).read_text(encoding='utf8'))
        return data if isinstance(data,dict) else {}
    except (OSError,ValueError,TypeError):return {}

def save_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,delete=False) as f:
        json.dump(data,f,sort_keys=True,indent=2,default=str);tmp=f.name
    os.replace(tmp,path)

def is_pubkey(text,core):
    if not isinstance(text,str) or not 32<=len(text)<=44:return False
    try:return len(core.b58d(text))==32
    except (ValueError,TypeError,IndexError,OverflowError):return False

def parse_mint(v):
    if isinstance(v,str):return v
    if isinstance(v,dict):return v.get('address') or v.get('mint') or v.get('token_address')
    return None

def parse_exact_api_pool(rows,token,dlmm,core):
    """Match the *address* AND WSOL/token mints, never best-TVL substitution."""
    if not isinstance(rows,list):raise Hold('DLMM_METADATA_RESPONSE_INVALID')
    for v in rows:
        if not isinstance(v,dict):continue
        pool=v.get('address') or v.get('pool_address') or v.get('pubkey')
        x=v.get('token_x') or v.get('tokenX');y=v.get('token_y') or v.get('tokenY')
        mx,my=parse_mint(x),parse_mint(y)
        if pool!=dlmm or {mx,my}!={MINT_SOL,token}:continue
        def dec(t):
            if isinstance(t,dict) and str(t.get('decimals','')).isdigit():return int(t['decimals'])
            return None
        dx,dy=dec(x),dec(y)
        if dx is None or dy is None or not 0<=dx<=18 or not 0<=dy<=18:
            raise Hold('DLMM_META_DECIMALS_MISSING_FAIL_CLOSED')
        if not is_pubkey(pool,core):raise Hold('DLMM_META_POOL_ADDRESS_INVALID')
        return {'address':pool,'token_x':mx,'token_y':my,'decimals_x':dx,'decimals_y':dy}
    return None

def ranked_hints(rows,core,max_hints=MAX_HINTS):
    counts=Counter();last={};bad=0
    for row in rows:
        if len(row)!=6:bad+=1;continue
        eid,token,pump,dlmm,direction,size=row
        if type(eid) is not int or type(size) is not int or not 10_000_000<=size<=100_000_000 or direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
            bad+=1;continue
        if not all(is_pubkey(x,core) for x in (token,pump,dlmm)):
            bad+=1;continue
        triple=(token,pump,dlmm)
        counts[triple]+=1
        if token not in last or eid>last[token][0]:last[token]=(eid,triple)
    # Latest market identity per token, weighted by the latest valid triple's frequency.
    accepted=[(eid,t,cnt) for _,(eid,t) in last.items() if (cnt:=counts[t])>0]
    accepted.sort(key=lambda q:(-q[2],-q[0]))
    return OrderedDict((t[0],{'token':t[0],'pump_pool':t[1],'meteora_pool':t[2],
                       'event_id':eid,'nominations':n}) for eid,t,n in accepted[:max_hints]),bad

class ScannerExactPoolRouter:
    def __init__(self,core,scanner_factory,clock=None):
        self.core=core;self.scanner_factory=scanner_factory;self.clock=clock or time.monotonic
        self.lock=threading.RLock();self.hints=OrderedDict();self.refresh_at=-1e12
        self.epoch=None;self.producer=None;self.high_id=0;self.invalid=0
        self.metacache={};self.negative_until={};self.counts=Counter();self.verdicts=OrderedDict()
        self.original_raw=None;self.original_discover=None
    def read_hints(self,force=False):
        with self.lock:
            if not force and self.clock()-self.refresh_at<SCAN_REFRESH_S:return self.hints
            conn=None
            try:
                scanner=self.scanner_factory()
                conn=scanner.bus()
                conn.execute('PRAGMA query_only=ON')
                conn.execute('PRAGMA busy_timeout=500')
                validated=scanner.validate_scanner(conn)  # frozen original validator
                if not isinstance(validated,dict) or type(validated.get('epoch')) is not int:
                    raise Hold('SCANNER_HEALTH_UNVERIFIED')
                rows=conn.execute('SELECT id,token,pump_pool,meteora_pool,direction,size_lamports '
                    'FROM events ORDER BY id DESC LIMIT ?', (MAX_SAMPLE,)).fetchall()
                hints,bad=ranked_hints(rows,self.core)
                high=max((int(x[0]) for x in rows),default=0)
                if self.epoch is not None and validated['epoch']!=self.epoch:
                    self.metacache.clear();self.negative_until.clear();self.counts['epoch_rebinds']+=1
                self.epoch=validated['epoch'];self.producer=str(validated.get('producer_id') or '')[:12]
                self.hints=hints;self.invalid=bad;self.high_id=high
                self.refresh_at=self.clock();self.counts['scanner_reads']+=1
                return hints
            except Exception:
                self.counts['scanner_health_or_read_failure']+=1
                # Do not admit new hints from a failed validator.
                self.hints=OrderedDict();self.refresh_at=-1e12
                raise Hold('SCANNER_VALIDATED_BUS_READ_FAILED') from None
            finally:
                if conn is not None:
                    try:conn.close()
                    except Exception:pass
    def raw_universe(self,root):
        hints=list(self.read_hints().values())
        legacy=list(self.original_raw(root))
        selected=[{'token':r['token'],'pump_pool':r['pump_pool'],
                   'source':'VALIDATED_SCANNER_HINT_NOT_EXECUTION_PROOF','age':None} for r in hints]
        seen={r['token'] for r in selected}
        selected.extend(r for r in legacy if r.get('token') not in seen)
        self.counts['scanner_hint_universe_merges']+=1
        return selected[:48]
    def discover(self,token):
        hint=self.read_hints().get(token)
        if not hint:return self.original_discover(token)
        pool=hint['meteora_pool'];key=(token,pool)
        with self.lock:
            if self.clock()<self.negative_until.get(key,0):
                self.counts['unverified_pool_cached_hold']+=1
                raise Hold('SCANNER_POOL_UNVERIFIED_COOLDOWN')
            previous=self.metacache.get(key)
            if previous and self.clock()-previous[0]<META_TTL_S:
                self.counts['api_meta_cache_hits']+=1
                return dict(previous[1])
        # Official Meteora /pools/{address} first; fallback to bounded indexed query.
        # No new WS or HTTP-per-quote, and no highest-TVL pool substitution.
        url='https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query='+quote(token,safe='')
        try:
            try:
                direct=self.core.http('https://dlmm.datapi.meteora.ag/pools/'+quote(pool,safe=''))
            except Exception as direct_exc:
                if getattr(direct_exc,'code',None)==404:direct={}
                else:raise
            obj=direct.get('data',direct) if isinstance(direct,dict) else direct
            meta=parse_exact_api_pool(obj if isinstance(obj,list) else [obj],token,pool,self.core)
            if not meta:
                self.counts['direct_pool_metadata_unmatched']+=1
                for page in (1,2,3):
                    page_url=url.replace('page=1&','page='+str(page)+'&',1)
                    payload=self.core.http(page_url)
                    rows=payload.get('data') if isinstance(payload,dict) else payload
                    meta=parse_exact_api_pool(rows,token,pool,self.core)
                    if meta or not isinstance(rows,list) or len(rows)<100:break
            if not meta:
                self.counts['scanner_pool_missing_meteora_api']+=1
                with self.lock:self.negative_until[key]=self.clock()+45
                self.verdicts[token]='SCANNER_POOL_MISSING_API_NO_UNSAFE_POOL_SUBSTITUTION'
                raise Hold('SCANNER_POOL_NOT_VERIFIED_BY_METEORA_API')
            # Required additional on-chain verification: owner must be the Meteora DLMM program.
            data,owner=self.core.account(pool)
            if owner!=self.core.DLMM or not isinstance(data,bytes) or len(data)<80:
                self.counts['dlmm_onchain_owner_rejected']+=1
                raise Hold('DLMM_POOL_ONCHAIN_OWNER_OR_DATA_INVALID')
            with self.lock:
                self.metacache[key]=(self.clock(),meta)
                self.counts['exact_scanner_pools_verified']+=1
                self.verdicts[token]='METEORA_API_AND_PROGRAM_OWNER_VERIFIED_NOT_PROFIT'
            return dict(meta)
        except Hold:raise
        except Exception as exc:
            self.counts['exact_pool_meta_or_rpc_failed']+=1
            # Preserve provider cooldown handling; never swallow 429.
            if getattr(exc,'code',None)==429 or '429' in str(exc):raise
            raise Hold('EXACT_POOL_METADATA_OR_OWNER_READ_FAILED') from None
    def snapshot(self):
        with self.lock:
            return {'mode':'READ_ONLY_SCANNER_ROUTED_EXACT_POOL','sampled_event_max_id':self.high_id,
                    'scanner_epoch':self.epoch,'hint_count':len(self.hints),
                    'invalid_scanner_rows':self.invalid,
                    'hints':[{'token_prefix':t[:12],'pump_pool_prefix':v['pump_pool'][:12],
                       'meteora_pool_prefix':v['meteora_pool'][:12],'nominations':v.get('nominations',0)}
                       for t,v in list(self.hints.items())[:MAX_HINTS]],
                    'verdicts':{k[:12]:v for k,v in self.verdicts.items()},
                    'counts':dict(self.counts),'scanner_mutated':False}

def rotating_replenishment_factory(legacy_factory,router):
    def create(m380):
        Original=legacy_factory(m380)
        class Rotating(Original):
            def close(self):
                # ORACLE-380 used a 0.3s join: the background hydration could
                # outlive the scoped RPC/SDK hooks at the end of a live session.
                # Drain before hooks are restored, without accepting new work.
                with self.cv:
                    self.dead=True;self.cv.notify_all()
                if self.worker:
                    self.worker.join(timeout=45.)
                    if self.worker.is_alive():
                        self.provider.refresh_fatal=True
                        self.last_status='HOLD_BACKGROUND_SHUTDOWN_INCOMPLETE'
                        self.counts['background_shutdown_incomplete']+=1
            def attempt_once(self):
                p=self.provider;self.phase='SCANNER_EXACT_DISCOVERY';self.last_error=None
                self.attempt_started=self.clock()
                try:
                    router.read_hints(force=True)
                    state,_=p.old.q25.q60b2.prepare_once(Path.cwd())
                    pairs=list(state.get('pairs') or [])
                    if not pairs:raise Hold('ROTATION_NO_VALIDATED_CANONICAL_PAIRS')
                    fresh={str(x.token):x for x in pairs}
                    if len(fresh)!=len(pairs):raise Hold('ROTATION_DUPLICATE_TOKEN')
                    # Every hydrated pair was validated by Q25; scanner hints alone never enter here.
                    for pair in pairs:
                        if not all(is_pubkey(getattr(pair,k,None),router.core)
                                   for k in ('token','pump_pool','meteora_pool')):
                            raise Hold('ROTATION_BAD_EXACT_PAIR_IDENTITY')
                    oldpairs=dict(p.forward.pairs)
                    removed=set(oldpairs)-set(fresh)
                    changed={t for t in set(oldpairs)&set(fresh)
                             if (oldpairs[t].pump_pool,oldpairs[t].meteora_pool)!=(fresh[t].pump_pool,fresh[t].meteora_pool)}
                    added=set(fresh)-set(oldpairs)
                    self.latest_canonical_size=len(fresh)
                    self.latest_canonical_prefixes=[x[:12] for x in sorted(fresh)[:24]]
                    self.latest_validated=True
                    self.nonmonotonic_missing=len(removed)
                    self.counts['canonical_rotation_seen']+=bool(removed or changed)
                    with self.cv:
                        for token in list(self.pending):
                            if token not in fresh:
                                self.pending.pop(token,None)
                                self.excluded[token]=self.clock()+90.
                                self.counts['confirmed_not_in_canonical_discovery']+=1
                    pending_cold=any(t in fresh and t not in p.old.READY_TOKENS for t in list(self.pending))
                    if not (added or removed or changed or pending_cold):
                        self.last_status='IDENTICAL_EXACT_PAIR_UNIVERSE_NO_REBUILD'
                        self.failures=0
                        with self.cv:
                            for token in list(self.pending):
                                if token in p.old.READY_TOKENS and token in p.forward.pairs:
                                    self.pending.pop(token,None)
                                    self.counts['already_ready_resolved']+=1
                        return
                    if self.dead:return
                    self.phase='STAGED_ROTATION_NATIVE_PREWARM'
                    with p.forward.lock:
                        if self.dead or getattr(p,'refresh_fatal',False):return
                        try:
                            p.old.q25.bind_cached_state(state)
                            warmed=p.old.install_proven_hot_math(state)
                            p.old.prebuild_templates(state,p.forward.wallet)
                            p.old.prebuild_meteora_templates(state,p.forward.wallet,warmed)
                            programs={str(x['token']):str(x['program']) for x in warmed
                                if isinstance(x,dict) and x.get('token') and x.get('program')}
                            ready=set(str(x) for x in p.old.READY_TOKENS)
                            if not set(fresh).issubset(ready) or not set(fresh).issubset(programs):
                                raise Hold('ROTATION_INCOMPLETE_NATIVE_TEMPLATES')
                            # Fresh-event cursor is captured *after* the complete rebuild.
                            router.read_hints(force=True)
                            cursor=router.high_id
                            p.forward.state=state;p.forward.pairs=fresh
                            p.forward.indexes={str(x.token):i for i,x in enumerate(pairs)}
                            p.forward.programs=programs
                            # Cutover requires an event after full publish; no stale queue admission.
                            if not hasattr(p,'_oracle384_original_prepare'):
                                p._oracle384_original_prepare=p.prepare_unsigned
                                def guarded(row):
                                    if type(row.get('event_id')) is not int or row['event_id']<=p._oracle384_cutover_id:
                                        raise Hold('ROTATION_REQUIRES_POST_CUTOVER_FRESH_EVENT')
                                    return p._oracle384_original_prepare(row)
                                p.prepare_unsigned=guarded
                            p._oracle384_cutover_id=cursor
                        except Exception:
                            p.refresh_fatal=True
                            raise Hold('ROTATION_PARTIAL_TEMPLATE_CHANGE_FAIL_CLOSED') from None
                    self.counts['rotations_committed']+=1
                    self.counts['pairs_retired_on_rotation']+=len(removed)
                    self.counts['pair_identity_changes']+=len(changed)
                    self.counts['new_pairs_warmed']+=len(added)
                    self.last_success=self.clock();self.failures=0
                    self.last_status='EXACT_POOL_ROTATION_PUBLISHED_REQUIRE_NEW_EVENT'
                    with self.cv:
                        for token in list(self.pending):
                            if token in fresh:self.pending.pop(token,None)
                except Exception as exc:
                    self.failures+=1
                    self.last_error=m380.error_identity(exc,'EXACT_POOL_ROTATION')
                    if getattr(p,'refresh_fatal',False):
                        self.last_status='HOLD_ROTATION_PARTIAL_MUTATION_FATAL'
                        with self.cv:self.next_allowed=float('inf')
                    elif m380.is_429(exc):
                        self.counts['http_429']+=1
                        self.last_status='HOLD_ROTATION_HTTP_429_BACKOFF'
                        with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+m380.rate_delay(exc,self.failures))
                    else:
                        self.counts['rotation_held']+=1
                        self.last_status=self.last_error['reason']
                        with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+m380.rate_delay(exc,self.failures))
                finally:
                    self.last_elapsed_ms=round((self.clock()-self.attempt_started)*1000,2)
                    self.phase='IDLE'
        return Rotating
    return create

def certify_sdk_post_template(runtime,q18,bridge,state):
    """Critical ORACLE-383 sequencing repair: NEW native templates must warm SDK too.

    Only called from canonical startup or rate-paced background replenishment, never
    from a candidate callback. Without this, native_ready=6 can mean SDK_ready=4.
    """
    traffic=bridge.traffic
    count=0
    for pair in state.get('pairs') or []:
        token=str(pair.token);pool=str(pair.pump_pool)
        if token not in runtime.READY_TOKENS:continue
        if pool in traffic.sdk_warm_pool:continue
        name=threading.current_thread().name
        if name not in ('MainThread','oracle380-rpc-budget-replenisher'):
            raise Hold('SDK_POST_TEMPLATE_WARM_NOT_ON_BACKGROUND_THREAD')
        traffic.acquire(3.,warm=True)
        t0=time.perf_counter()
        try:
            q18.worker().warm(pool)  # ORACLE-383 isolated wallet SDK worker
            if pool not in traffic.sdk_warm_pool:
                raise Hold('SDK_POST_TEMPLATE_READY_ACK_MISSING')
        except Exception:
            runtime.READY_TOKENS.discard(token)
            traffic.observe('sdk_post_template_warm_hold')
            raise Hold('SDK_POST_TEMPLATE_WARM_FAILED_FAIL_CLOSED') from None
        finally:
            with traffic.lock:
                traffic.sdk_times_ms.append((time.perf_counter()-t0)*1000)
                traffic.sdk_times_ms=traffic.sdk_times_ms[-100:]
        count+=1
        traffic.observe('sdk_post_template_warmed')
        print('[ORACLE384_SDK_POST_TEMPLATE_READY]',json.dumps({
            'token_prefix':token[:12],'pool_prefix':pool[:12]},sort_keys=True),flush=True)
    return count

def sdk_post_template_bridge_factory(Base):
    class BridgeWithPostTemplateWarm(Base):
        def __enter__(self):
            obj=super().__enter__()
            runtime,q18,c=modules()[0].modules()
            self._oracle384_original_prebuild=runtime.prebuild_templates
            def installed_prebuild(state,wallet):
                result=self._oracle384_original_prebuild(state,wallet)
                certify_sdk_post_template(runtime,q18,self,state)
                return result
            runtime.prebuild_templates=installed_prebuild
            return obj
        def __exit__(self,*args):
            if hasattr(self,'_oracle384_original_prebuild'):
                runtime=modules()[0].modules()[0]
                runtime.prebuild_templates=self._oracle384_original_prebuild
            return super().__exit__(*args)
    return BridgeWithPostTemplateWarm

class Session:
    def __init__(self):self.originals=None;self.router=None
    def __enter__(self):
        m383,m382,m381,m380,pd,eng,core=modules()
        if (EXECUTION_AUTHORITY,SIGNING,BROADCAST)!=(False,False,False):raise Hold('AUTHORITY_REPAIR_CONTRACT')
        # Source module version checks: fail closed if an upstream contract changed.
        if not callable(getattr(m381,'replenishment_class',None)) or not callable(getattr(eng,'raw_candidate_universe',None)):
            raise Hold('REPLACEMENT_SEAMS_CHANGED_REAUDIT_REQUIRED')
        original=(eng.raw_candidate_universe,core.discover_dlmm,m381.replenishment_class,m383.Bridge)
        def scanner_factory():
            m379,_=m381.imports().import_deps()
            return m379.modules()[0].resolve_scanner_bus()
        router=ScannerExactPoolRouter(core,scanner_factory)
        router.original_raw=original[0];router.original_discover=original[1]
        router.read_hints(force=True)
        eng.raw_candidate_universe=router.raw_universe
        core.discover_dlmm=router.discover
        m381.replenishment_class=rotating_replenishment_factory(original[2],router)
        m383.Bridge=sdk_post_template_bridge_factory(original[3])
        self.originals=(eng,core,m381,m383,*original)
        self.router=router
        return self
    def __exit__(self,*a):
        if self.originals:
            eng,core,m381,m383,raw,discover,original,bridge=self.originals
            eng.raw_candidate_universe=raw;core.discover_dlmm=discover
            m381.replenishment_class=original;m383.Bridge=bridge
            self.originals=None
        return False

def install():
    if not (TARGET.parent/'oracle_383_sdk_rpc_native_bridge.py').is_file():
        raise Hold('ORACLE383_CANONICAL_BASE_REQUIRED')
    source=Path(__file__).resolve().read_bytes()
    compile(source.decode('utf8'),str(TARGET),'exec')
    if TARGET.resolve()!=Path(__file__).resolve():
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:
            f.write(source);tmp=f.name
        os.replace(tmp,TARGET)
    print('[ORACLE384_INSTALL_PASS]',TARGET,flush=True)

def audit():
    if not TARGET.is_file() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE384_COMPLETE_INSTALL_MISMATCH')
    m383,m382,m381,m380,pd,eng,core=modules()
    m383.audit()
    assert EXPECTED_CANARY==10_000_000 and not any((EXECUTION_AUTHORITY,SIGNING,BROADCAST))
    if not callable(getattr(core,'account',None)) or not hasattr(core,'DLMM'):
        raise Hold('METEORA_ONCHAIN_OWNER_VALIDATOR_MISSING')
    print('[ORACLE384_AUDIT_PASS] SCANNER322_FROZEN EXACT_API_PLUS_ONCHAIN_POOL_VERIFICATION '
          'ROTATING_NATIVE_CAPACITY FAIL_CLOSED_FRESH_EVENT NO_SIGN_NO_BROADCAST',flush=True)

def tests():
    from types import SimpleNamespace as NS
    # Valid public keys from repository fixtures / standard Solana programs.
    t='Ce2gx9KGXJ6C9Mp5b5x1sn9Mg87JwEbrQby4Zqo3pump'
    p='5wNu5QhdpRGrL37ffcd6TMMqZugQgxwafgz477rShtHy'
    d='BkocTzcvrhjwQk9BNHvEF4qrMxNPHPjWgcq4pRxjAu2'  # fixture opaque, use decoder stub
    c=NS(DLMM='DLMM_PROGRAM',b58d=lambda s:b'X'*32 if len(s)>=32 else (_ for _ in ()).throw(ValueError()),
         account=lambda a:(b'Z'*100,'DLMM_PROGRAM'),http=lambda u:{'data':[]})
    class T(unittest.TestCase):
        def setUp(self):self.row={'token':t,'pump_pool':p,'meteora_pool':d}
        def test_canary(self):self.assertEqual(EXPECTED_CANARY,10_000_000)
        def test_no_execution_auth(self):self.assertFalse(any((EXECUTION_AUTHORITY,SIGNING,BROADCAST)))
        def test_pubkey(self):self.assertTrue(is_pubkey(t,c))
        def test_pubkey_bad(self):self.assertFalse(is_pubkey('invalid',c))
        def test_mint_dict(self):self.assertEqual(parse_mint({'address':t}),t)
        def test_mint_string(self):self.assertEqual(parse_mint(MINT_SOL),MINT_SOL)
        def test_mint_none(self):self.assertIsNone(parse_mint(22))
        def meta(self):return [{'address':d,'token_x':{'address':MINT_SOL,'decimals':9},
                                   'token_y':{'address':t,'decimals':6},'tvl':1}]
        def test_exact_select(self):self.assertEqual(parse_exact_api_pool(self.meta(),t,d,c)['address'],d)
        def test_no_tvl_substitution(self):self.assertIsNone(parse_exact_api_pool(self.meta(),t,p,c))
        def test_wrong_token_rejected(self):self.assertIsNone(parse_exact_api_pool(self.meta(),p,d,c))
        def test_missing_decimals_hold(self):
            rows=self.meta();del rows[0]['token_x']['decimals']
            with self.assertRaises(Hold):parse_exact_api_pool(rows,t,d,c)
        def test_bad_api_shape(self):
            with self.assertRaises(Hold):parse_exact_api_pool({},t,d,c)
        def test_rank_single(self):
            rows=[(3,t,p,d,'PUMP_TO_METEORA',EXPECTED_CANARY)]
            k,b=ranked_hints(rows,c);self.assertIn(t,k);self.assertEqual(b,0)
        def test_rank_wrong_size(self):
            k,b=ranked_hints([(3,t,p,d,'PUMP_TO_METEORA',1)],c)
            self.assertFalse(k);self.assertEqual(b,1)
        def test_rank_latest_identity(self):
            rows=[(1,t,p,d,'PUMP_TO_METEORA',EXPECTED_CANARY),
                  (2,t,p,t,'METEORA_TO_PUMP',EXPECTED_CANARY)]
            k,_=ranked_hints(rows,c);self.assertEqual(k[t]['meteora_pool'],t)
        def test_rank_direction_filter(self):
            k,b=ranked_hints([(1,t,p,d,'DUMMY',EXPECTED_CANARY)],c);self.assertEqual(b,1)
        def test_readonly_sqlite_hint_and_health(self):
            import sqlite3
            db=sqlite3.connect(':memory:')
            db.execute('CREATE TABLE events (id INTEGER, token TEXT, pump_pool TEXT, '
                       'meteora_pool TEXT, direction TEXT, size_lamports INTEGER)')
            db.execute('INSERT INTO events VALUES (7,?,?,?,?,?)',
                       (t,p,d,'PUMP_TO_METEORA',EXPECTED_CANARY))
            db.commit()
            scanner=NS(bus=lambda:db,validate_scanner=lambda conn:{'epoch':3})
            router=ScannerExactPoolRouter(c,lambda:scanner)
            got=router.read_hints(force=True)
            self.assertEqual(got[t]['meteora_pool'],d)
            self.assertEqual(router.high_id,7)
            self.assertEqual(router.epoch,3)
            self.assertFalse(router.snapshot()['scanner_mutated'])
        def test_scanner_validator_fail_closed(self):
            import sqlite3
            db=sqlite3.connect(':memory:')
            scanner=NS(bus=lambda:db,validate_scanner=lambda conn:(_ for _ in ()).throw(RuntimeError()))
            router=ScannerExactPoolRouter(c,lambda:scanner)
            with self.assertRaises(Hold):router.read_hints(force=True)
            self.assertEqual(len(router.hints),0)
        def test_router_uses_exact_api(self):
            r=ScannerExactPoolRouter(c,lambda:None)
            r.hints=OrderedDict([(t,self.row)]);r.refresh_at=r.clock()
            c.http=lambda u:{'data':self.meta()}
            r.original_discover=lambda token:{'address':p}
            self.assertEqual(r.discover(t)['address'],d)
            self.assertEqual(r.snapshot()['counts']['exact_scanner_pools_verified'],1)
        def test_router_owner_fail_closed(self):
            other=NS(**vars(c));other.http=lambda u:{'data':self.meta()}
            other.account=lambda pool:(b'Z'*100,'WRONG_OWNER')
            r=ScannerExactPoolRouter(other,lambda:None);r.hints=OrderedDict([(t,self.row)]);r.refresh_at=r.clock()
            with self.assertRaises(Hold):r.discover(t)
        def test_router_fallback_for_non_scanner(self):
            r=ScannerExactPoolRouter(c,lambda:None);r.refresh_at=r.clock()
            r.original_discover=lambda token:{'address':'LEGACY'}
            self.assertEqual(r.discover(t)['address'],'LEGACY')
        def test_router_prefers_scanner_raw(self):
            r=ScannerExactPoolRouter(c,lambda:None);r.refresh_at=r.clock()
            r.hints=OrderedDict([(t,self.row)]);r.original_raw=lambda _: [{'token':t,'pump_pool':'LEGACY'}]
            self.assertEqual(r.raw_universe(None)[0]['pump_pool'],p)
        def test_router_does_not_expose_api_key(self):
            r=ScannerExactPoolRouter(c,lambda:None)
            self.assertNotIn('api-key',json.dumps(r.snapshot()))
        def test_router_no_scanner_write(self):
            import inspect
            s=inspect.getsource(ScannerExactPoolRouter.read_hints)
            self.assertIn('query_only=ON',s);self.assertNotIn('INSERT INTO',s)
        def test_rotation_protected(self):
            import inspect
            s=inspect.getsource(rotating_replenishment_factory)
            self.assertIn('p.refresh_fatal=True',s)
            self.assertIn('ROTATION_REQUIRES_POST_CUTOVER_FRESH_EVENT',s)
        def test_rotation_no_automatic_trades(self):
            import inspect
            s=inspect.getsource(rotating_replenishment_factory)
            self.assertNotIn('sendTransaction',s)
        def test_install_not_modify_scanner(self):
            import inspect
            s=inspect.getsource(install)
            self.assertNotIn('322_scanner_isolated_discovery.py',s)
        def stage_fixture(self,fail=False):
            from types import SimpleNamespace as N
            import threading
            from collections import Counter
            old_token=p
            old_pair=N(token=old_token,pump_pool=p,meteora_pool=d)
            new_pair=N(token=t,pump_pool=p,meteora_pool=d)
            state={'pairs':[new_pair]}
            old=N(READY_TOKENS={old_token},
                prebuild_templates=lambda state,wallet: None,
                prebuild_meteora_templates=lambda state,wallet,warmed: None)
            old.q25=N(bind_cached_state=lambda state:None,
                       q60b2=N(prepare_once=lambda root:(state,{})))
            old.install_proven_hot_math=lambda st:[{'token':t,'program':'TOKEN_PROGRAM'}]
            def templates(st,wallet):
                if fail:raise RuntimeError('fixture failure')
                old.READY_TOKENS={t}
            old.prebuild_templates=templates
            forward=N(pairs={old_token:old_pair},lock=threading.Lock(),wallet='WALLET',
                      state={'pairs':[old_pair]},indexes={old_token:0},programs={old_token:'OLD'})
            provider=N(forward=forward,old=old,refresh_fatal=False,
                       prepare_unsigned=lambda row:{'accepted':row['event_id']})
            class Base:
                def __init__(self):
                    self.provider=provider;self.phase='WAITING';self.last_error=None
                    self.clock=lambda:100.;self.cv=threading.Condition()
                    self.pending={};self.excluded={};self.dead=False
                    self.failures=0;self.counts=Counter();self.next_allowed=0
                    self.last_status='WAITING';self.last_success=0
            router=N(core=c,high_id=12,read_hints=lambda force=True: {})
            m380=N(error_identity=lambda exc,stage:{'reason':stage+'_HOLD'},
                   is_429=lambda exc:False,rate_delay=lambda exc,fail:1.)
            factory=rotating_replenishment_factory(lambda ignored:Base,router)
            obj=factory(m380)()
            return obj,provider,old_token,new_pair
        def test_native_rotation_retires_old_and_requires_new_event(self):
            obj,provider,old_token,new_pair=self.stage_fixture()
            obj.attempt_once()
            self.assertFalse(provider.refresh_fatal)
            self.assertNotIn(old_token,provider.forward.pairs)
            self.assertIn(new_pair.token,provider.forward.pairs)
            self.assertEqual(obj.counts['rotations_committed'],1)
            with self.assertRaises(Hold):provider.prepare_unsigned({'event_id':12})
            self.assertEqual(provider.prepare_unsigned({'event_id':13})['accepted'],13)
        def test_partial_rotation_fails_closed(self):
            obj,provider,old_token,new_pair=self.stage_fixture(fail=True)
            obj.attempt_once()
            self.assertTrue(provider.refresh_fatal)
            self.assertIn(old_token,provider.forward.pairs)
            self.assertNotIn(new_pair.token,provider.forward.pairs)
            self.assertEqual(obj.last_status,'HOLD_ROTATION_PARTIAL_MUTATION_FATAL')
        def test_post_template_sdk_pool_ready(self):
            ready=set()
            class FakeWorker:
                def warm(self,pool):ready.add(pool)
            class Traffic:
                def __init__(self):
                    self.sdk_warm_pool=ready;self.lock=threading.RLock()
                    self.sdk_times_ms=[];self.events=Counter()
                def acquire(self,units,warm=False):
                    if units!=3 or not warm:raise AssertionError('not a paced warm')
                def observe(self,label):self.events[label]+=1
            runtime=NS(READY_TOKENS={t});sdk=NS(worker=lambda:FakeWorker())
            bridge=NS(traffic=Traffic());pair=NS(token=t,pump_pool=p)
            self.assertEqual(certify_sdk_post_template(runtime,sdk,bridge,{'pairs':[pair]}),1)
            self.assertIn(p,ready)
            self.assertEqual(certify_sdk_post_template(runtime,sdk,bridge,{'pairs':[pair]}),0)
        def test_post_template_sdk_failure_removes_native_ready(self):
            class DeadWorker:
                def warm(self,pool):raise RuntimeError('worker unavailable')
            class Traffic:
                sdk_warm_pool=set();lock=threading.RLock();sdk_times_ms=[]
                def acquire(self,*a,**kw):return None
                def observe(self,*a):return None
            runtime=NS(READY_TOKENS={t});sdk=NS(worker=lambda:DeadWorker())
            with self.assertRaises(Hold):certify_sdk_post_template(runtime,sdk,NS(traffic=Traffic()),
                  {'pairs':[NS(token=t,pump_pool=p)]})
            self.assertNotIn(t,runtime.READY_TOKENS)
        def test_rejected_old_pool(self):self.assertIsNone(parse_exact_api_pool([],t,d,c))
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE384_TEST_PASS]' if r.wasSuccessful() else '[ORACLE384_TEST_FAIL]',r.testsRun,flush=True)
    return 0 if r.wasSuccessful() else 1

def inspect():
    r=clean_json(REPORT);prior=clean_json(UPSTREAM);cap=clean_json(CAPACITY)
    print('[ORACLE384_INSPECT]',json.dumps({'status':r.get('status'),
        'native_pairs_last':r.get('native_pairs_final'),'sdk_ready_last':prior.get('guard_metrics',{}).get('sdk_ready_pool_count'),
        'pool_routing':r.get('pool_routing',{}).get('counts',{}),
        'latest_replenishment_status':(cap.get('replenishment') or [{}])[-1].get('status')},sort_keys=True),flush=True)

def run(minutes,poll_ms,wallet):
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUNTIME_BOUNDS_INVALID')
    audit();m383,m382,m381,m380,pd,eng,core=modules()
    h=m381.scanner_bus_probe()
    if h.get('validator')!='PASS':raise Hold('SCANNER_ORIGINAL_HEALTH_HOLD')
    session=Session();started=time.monotonic();code=2;status='READ_ONLY_HOLD'
    try:
        with session:
            code=m383.run(minutes,poll_ms,wallet)
        status='READ_ONLY_SESSION_DONE' if code==0 else 'READ_ONLY_HOLD'
    finally:
        cap=clean_json(CAPACITY);repl=(cap.get('replenishment') or [{}])[-1]
        router=session.router.snapshot() if session.router else {}
        prior=clean_json(UPSTREAM)
        obj={'build':'ORACLE384','status':status,'duration_s':round(time.monotonic()-started,2),
             'pool_routing':router,'native_pairs_final':repl.get('native_pairs_current'),
             'native_stage':repl.get('cap_attempts',[]),
             'sdk_ready_pools':prior.get('guard_metrics',{}).get('sdk_ready_pool_count'),
             'sdk_warm_failures':prior.get('guard_metrics',{}).get('sdk_warm_failed_by_pool_prefix'),
             'free_rpc_python_counts':prior.get('guard_metrics',{}).get('counts'),
             'original_scanner_health_gate':'PASS','scanner_mutated':False,
             'execution_authority':False,'private_key_used':False,'signing':False,'broadcast':False,
             'funded_canary_lamports':EXPECTED_CANARY,'realized_profit_certified':False,
             'warning':'Scanner hints and Meteora API validation do not replace native same-bank/simulation/profit gates'}
        save_json(REPORT,obj)
        print('[ORACLE384_POOL_ROUTING]',json.dumps(router,sort_keys=True),flush=True)
        print('[ORACLE384_RUNTIME_REPORT]',REPORT,flush=True)
        print('[ORACLE384_STATUS]',status,flush=True)
    return code

def main():
    p=argparse.ArgumentParser()
    for a in ('install','test','audit','node-check','sdk-check','burst','health-gate','inspect','run'):
        p.add_argument('--'+a,action='store_true')
    p.add_argument('--minutes',type=int,default=5);p.add_argument('--poll-ms',type=int,default=5)
    p.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    x=p.parse_args()
    if not any(getattr(x,a.replace('-','_')) for a in ('install','test','audit','node-check','sdk-check','burst','health-gate','inspect','run')):
        p.error('ACTION_REQUIRED')
    if x.install:install()
    if x.test and tests():return 1
    if x.audit:audit()
    if x.node_check:modules()[0].node_check()
    if x.sdk_check:modules()[0].deps().dep().imports().import_deps()[0].sdk_check_visible()
    if x.burst:print('[ORACLE384_BURST_PASS]',json.dumps(modules()[0].deps().dep().imports().import_deps()[0].burst(),sort_keys=True),flush=True)
    if x.health_gate:
        h=modules()[2].scanner_bus_probe()
        if h.get('validator')!='PASS':
            print('[ORACLE384_SCANNER_HEALTH_HOLD]',json.dumps(h,sort_keys=True),flush=True);return 2
        print('[ORACLE384_SCANNER_HEALTH_PASS]',json.dumps(h,sort_keys=True),flush=True)
    if x.inspect:inspect()
    if x.run:return run(x.minutes,x.poll_ms,x.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print('[ORACLE384_HOLD]',type(e).__name__,flush=True)
        raise SystemExit(2)
