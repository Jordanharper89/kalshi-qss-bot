"""ORACLE-317 COMPLETE REPLACEMENT installer and launcher.
Replaces only canonical Final Boss, preserving frozen ORACLE018/020/025.
No trading, signing, or broadcast.
"""
import argparse,hashlib,os,pathlib,py_compile,subprocess,sys
from urllib.parse import quote
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.final_boss'
TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/final_boss.py')
SOURCE=r'''
"""ORACLE-317 FINAL BOSS: canonical single-writer read-only market and native preflight supervisor.
No signing, broadcasts, or portfolio mutation. Runs the original ORACLE025/020/018 scanner.
Epoch-boundary inventory replenishment until hot WS subscription cutover is certified.
"""
from __future__ import annotations
import argparse
import builtins
import contextlib
import hashlib
import json
import os
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time
import traceback
import unittest
from collections import Counter
from unittest.mock import patch

ROOT=pathlib.Path('runtime_state/oracle/final_boss')
LEDGER=ROOT/'native_preflight.jsonl'
STATUS=ROOT/'status.json'
INVENTORY=ROOT/'inventory.json'
LOCK=ROOT/'boss.lock'
CANARY=10_000_000
PACKET_LIMIT=1232
DEFAULT_ALT='HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'
KEY_RE=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SOURCE_FILES={'SQ':ROOT/'sq_candidates.json','UNIVERSAL':ROOT/'universal_candidates.json'}
CORE_FILES={
 'q18':'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py',
 'q20':'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py',
 'q25':'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py',
 'engine':'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py',
 'atomic':'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py',
 'compiler':'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering/qarb_087_two_second_compaction_liquidity_repair.py'
}

def emit(tag,data):
    builtins.print('['+tag+'] '+json.dumps(data,sort_keys=True,default=str),flush=True)

def atomic_json(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(data,sort_keys=True,indent=2,default=str),encoding='utf-8')
    os.replace(tmp,path)

def safe_error(e):
    s=type(e).__name__+':'+str(e)
    s=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',s)
    s=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',s)
    return s[:180]

def validate_public(s):
    if not KEY_RE.fullmatch(str(s or '')):return False
    # Regex validates format only; solders checks exact 32-byte base58 keys when available.
    try:
        from solders.pubkey import Pubkey
        return len(bytes(Pubkey.from_string(str(s))))==32
    except ImportError:return True
    except (ValueError,RuntimeError):return False

def source_candidates(source):
    p=SOURCE_FILES[source]
    if not p.is_file():return []
    try:
        data=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('schema')!='oracle-final-boss-candidates-v1':return []
        if str(data.get('source','')).upper()!=source:return []
        if time.time()-float(data.get('generated_at',0))>120:return []
        rows=data.get('candidates') or []
        if not isinstance(rows,list):return []
        result=[]
        for a in rows[:128]:
            if not isinstance(a,dict):continue
            token=a.get('token');pool=a.get('pump_pool')
            if validate_public(token) and validate_public(pool):
                result.append({'token':token,'pump_pool':pool,'source':source,'age':a.get('age'),
                               'source_weight':a.get('rank_score',0)})
        return result
    except (OSError,ValueError,TypeError):return []

def _number(value,default=0.,minval=0.,maxval=100.):
    try:return max(minval,min(maxval,float(value)))
    except (ValueError,TypeError,OverflowError):return default

def rank_inventory(original,extras,prior=()):
    """Combine multiple discovery feeds without double-counting token/pool identities."""
    groups={};retained=set(prior)
    for item in list(original)+list(extras):
        if not isinstance(item,dict):continue
        token,pool=item.get('token'),item.get('pump_pool')
        if not (isinstance(token,str) and isinstance(pool,str) and validate_public(token) and validate_public(pool)):
            continue
        key=(token,pool)
        rec=groups.setdefault(key,{'token':token,'pump_pool':pool,'sources':set(),'age':None,'weight':0.})
        raw_src=str(item.get('source') or 'LIVE_TAPE').upper()
        src='MRIYA' if raw_src.startswith('MRIYA') else raw_src
        rec['sources'].add(src)
        try:
            a=float(item.get('age'))
            if a>=0:rec['age']=a if rec['age'] is None else min(a,rec['age'])
        except (ValueError,TypeError,OverflowError):pass
        rec['weight']=max(rec['weight'],_number(item.get('source_weight'),0,0,25))
    rows=[]
    base={'MRIYA':65,'SQ':55,'UNIVERSAL':55,'LIVE_TAPE':40}
    for rec in groups.values():
        sources=sorted(rec.pop('sources'))
        a=rec['age']
        age_bonus=max(0,20-min(a,240)/12) if a is not None else 0
        score=max((base.get(s,20) for s in sources),default=0)+min(15,(len(sources)-1)*7.5)+age_bonus+rec['weight']
        if rec['token'] in retained:score+=12  # hysteresis; avoid gratuitous rotation
        rec.update(source='MULTI_SOURCE' if len(sources)>1 else sources[0],sources=sources,
                   score=round(score,4))
        rows.append(rec)
    return sorted(rows,key=lambda x:(-x['score'],x['token'],x['pump_pool']))

def sha_audit():
    import ast
    required={'q18':{'exact_snapshot_opportunities'},'q20':{'LatestStateLane','run'},
              'q25':{'run','prepare_once','install_hot_math_and_prewarm'},
              'engine':{'raw_candidate_universe','candidate_universe'},
              'atomic':{'same_snapshot_route','prebuild_templates','prebuild_meteora_templates'},
              'compiler':{'compile_candidate','repaired_candidates'}}
    audit={}
    for name,filename in CORE_FILES.items():
        p=pathlib.Path(filename)
        if not p.is_file():raise RuntimeError('MISSING_FROZEN_SOURCE:'+filename)
        raw=p.read_bytes();tree=ast.parse(raw.decode('utf-8-sig'),filename)
        defs={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
        if not required[name].issubset(defs):raise RuntimeError('FROZEN_SOURCE_INTERFACE_CHANGED:'+name)
        audit[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    return audit

@contextlib.contextmanager
def singleton():
    ROOT.mkdir(parents=True,exist_ok=True)
    fd=None
    try:
        fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(json.dumps({'pid':os.getpid(),'time':time.time()}))
        fd=None
    except FileExistsError:
        # Never blindly delete an existing lock; this prevents competing subscription writers.
        raise RuntimeError('BOSS_ALREADY_RUNNING_LOCK:'+str(LOCK))
    finally:
        if fd is not None:os.close(fd)
    try:yield
    finally:
        try:
            if json.loads(LOCK.read_text(encoding='utf-8'))['pid']==os.getpid():LOCK.unlink()
        except (OSError,ValueError,KeyError):pass

class NativePreflight:
    def __init__(self,wallet,alts,simulate_unsigned=False,age_limit=.5):
        self.wallet=wallet;self.alts=list(alts);self.loaded={};self.blockhash=None
        self.rt=None;self.q87=None;self.native_ready=set();self.age_limit=age_limit
        self.simulate_unsigned=simulate_unsigned;self.diagnostic_sim_negative=True;self.q=queue.Queue(maxsize=64)
        self.stop=threading.Event();self.thread=None;self.seen={};self.observations={}
        self.counts=Counter();self.outcomes=[];self.guard=threading.Lock();self.last_probe={}
        self.cache_status='HOLD_NOT_PRELOADED';self.boot=time.monotonic()

    def prepare(self,rt,q87):
        self.rt=rt;self.q87=q87
        if not validate_public(self.wallet):
            self.cache_status='HOLD_PUBLIC_WALLET_MISSING';return
        if not self.alts:
            self.cache_status='HOLD_ALT_NOT_CONFIGURED';return
        try:
            data=q87.c.alt_accounts(self.alts)
            if set(data)!=set(self.alts) or any(not x or len(x)>256 or any(len(y)!=32 for y in x) for x in data.values()):
                self.cache_status='HOLD_ALT_MISSING_OR_EMPTY';return
            self.loaded=data
            self.cache_status='ALT_READY'
            rt.BLOCKHASH.start()
            self.blockhash=rt.BLOCKHASH
        except Exception as e:
            self.cache_status='HOLD_ALT_PRELOAD_'+safe_error(e)
        emit('BOSS_ALT',{'status':self.cache_status,'tables':len(self.loaded),'addresses':sum(map(len,self.loaded.values()))})

    def templates(self,state,warmed,max_native=8):
        if self.cache_status!='ALT_READY':return
        try:
            # Prebuild priority tier first; do not block WS startup on all 28 routes.
            subset=dict(state,pairs=list(state.get('pairs') or [])[:max_native])
            self.rt.USER=self.wallet
            self.rt.prebuild_templates(subset,self.wallet)
            self.rt.prebuild_meteora_templates(subset,self.wallet,warmed)
            self.native_ready=set(self.rt.READY_TOKENS)
            emit('BOSS_NATIVE_READY',{'pairs':len(self.native_ready),'prebuilt_pump':len(self.rt.TEMPLATES),
                                      'prebuilt_meteora':len(self.rt.METEORA_TEMPLATES)})
        except Exception as e:
            emit('BOSS_NATIVE_HOLD',{'error':safe_error(e)})

    def mark_current(self,token,slot):
        with self.guard:self.seen[token]=int(slot)

    def submit(self,snap,op,slot):
        if int(op.get('start') or 0)!=CANARY:return
        token=str(snap.get('token',''))
        if token not in self.native_ready or op.get('direction')!='PUMP_TO_METEORA':return
        now=time.monotonic();positive=int(op.get('local_net') or 0)>0
        last=self.last_probe.get(token,0)
        if not positive and token in self.observations:return
        if positive and now-last<.25:return
        self.last_probe[token]=now
        # Keep the exact snapshot containing Meteora metadata + hydrated DLMM state.
        # The former two-field stub caused HOLD_NATIVE_KeyError:'meteora'.
        if not isinstance(snap.get('meteora'),dict) or snap.get('dlmm_state') is None:
            self.counts['HOLD_SNAPSHOT_MISSING_DLMM']+=1;return
        item=(now,int(slot),dict(snap),dict(op),positive)
        try:self.q.put_nowait(item)
        except queue.Full:self.counts['HOLD_NATIVE_QUEUE_FULL']+=1

    def compile_one(self,item):
        t,slot,snap,op,positive=item
        token=snap['token'];row={'token':token,'slot':slot,'direction':'PUMP_TO_METEORA',
            'size_lamports':CANARY,'gross_lamports':int(op.get('local_net') or 0),
            'broadcast':False,'signing':False,'execution_admission':False,
            'sim_signed':False,'timestamp':time.time()}
        def gate(label,**kw):row.update(gate=label,**kw);return row
        if token not in self.native_ready:return gate('HOLD_NATIVE_NOT_PREBUILT')
        if not isinstance(snap.get('meteora'),dict) or snap.get('dlmm_state') is None:
            return gate('HOLD_SNAPSHOT_MISSING_DLMM')
        if int(op.get('start') or 0)!=CANARY:return gate('HOLD_NOT_EXACT_CANARY')
        if op.get('direction')!='PUMP_TO_METEORA':return gate('HOLD_REVERSE_NOT_NATIVE_CERTIFIED')
        if time.monotonic()-t>self.age_limit:return gate('HOLD_EXPIRED_BEFORE_ROUTE')
        with self.guard:
            if self.seen.get(token,slot)>slot:return gate('HOLD_SUPERSEDED_SLOT')
        try:
            route=self.rt.same_snapshot_route(self.wallet,snap,op)
            if time.monotonic()-t>self.age_limit:return gate('HOLD_STALE_AFTER_NATIVE_BUILD')
            candidates=[x for x in self.q87.repaired_candidates(route)
                        if 'PUMP_METEORA_ONLY' not in str(x.get('name',''))]
            if not candidates:return gate('HOLD_NO_HELPER_COMPLETE_ATOMIC_CANDIDATE')
            # Already cached blockhash + ALT: no address lookup RPC on the hot compile path.
            bh=self.blockhash.get()
            best=None;fail=[]
            for c in candidates:
                result=self.q87.compile_candidate(self.wallet,c['instructions'],[self.alts],bh)
                if not result.get('ok'):
                    fail.append(str(result.get('error') or 'FAIL')[:85]);continue
                n=len(result['unsigned'])
                if n>PACKET_LIMIT:fail.append('OVERSIZE:'+str(n));continue
                if best is None or n<best[0]:best=(n,c,result)
            if best is None:return gate('HOLD_NO_LEGAL_V0_ALT_PACKET',errors=fail[:6])
            n,c,compiled=best
            row.update(bytes=n,candidate=str(c['name']),alt_count=len(self.alts),
                       legal_v0=True,latency_ms=round((time.monotonic()-t)*1000,2))
            with self.guard:
                if self.seen.get(token,slot)>slot:return gate('HOLD_SUPERSEDED_BEFORE_SIM')
            if time.monotonic()-t>self.age_limit:return gate('HOLD_STALE_PACKET')
            # Diagnostic simulation uses ORIGINAL exact swap bounds even for negative economics.
            # Never promote its result to a trading decision; the packet is never sent.
            if not self.simulate_unsigned:return gate('PACKET_BUILT_NEGATIVE_REAL_SNAPSHOT_NO_TRADE' if not positive else 'HOLD_UNSIGNED_SIM_DISABLED')
            if not positive and not self.diagnostic_sim_negative:return gate('PACKET_BUILT_NEGATIVE_REAL_SNAPSHOT_NO_TRADE')
            row['diagnostic_negative_quote']=not positive
            row['economic_admission']=False
            row['diagnostic_rpc_simulation']=True
            import base64
            result=self.q87.c.rpc('simulateTransaction',[base64.b64encode(compiled['unsigned']).decode(),
                {'encoding':'base64','sigVerify':False,'commitment':'processed','replaceRecentBlockhash':False}])
            value=result.get('value') if isinstance(result,dict) else None
            if not isinstance(value,dict):return gate('HOLD_RPC_SIM_VALUE_UNAVAILABLE')
            # Keep the precise Solana instruction/custom error and bounded program-log tail.
            # This diagnostic is read-only; public on-chain program logs may be printed,
            # but redact anything resembling secrets or RPC query credentials.
            err=value.get('err')
            logs=value.get('logs') or []
            if not isinstance(logs,list):logs=[]
            row.update(sim_units=value.get('unitsConsumed'),sim_fee_lamports=value.get('fee'),
                       sim_error_type=type(err).__name__ if err is not None else None,
                       sim_error=safe_error(json.dumps(err,default=str))[:350] if err is not None else None,
                       sim_log_tail=[safe_error(str(x))[:350] for x in logs[-12:]],
                       simulation_signed=False)
            if err is not None:return gate('HOLD_DIAGNOSTIC_SIM_FAILED' if not positive else 'HOLD_UNSIGNED_SIM_FAILED')
            return gate('DIAGNOSTIC_NEGATIVE_SIM_PASS_NO_TRADE' if not positive else 'UNSIGNED_SIM_PASS_SIGNED_NET_UNCERTIFIED')
        except Exception as e:return gate('HOLD_NATIVE_'+safe_error(e))

    def start(self):
        self.stop.clear()
        def loop():
            ROOT.mkdir(parents=True,exist_ok=True)
            with LEDGER.open('a',encoding='utf-8') as logfile:
                while not self.stop.is_set() or not self.q.empty():
                    try:item=self.q.get(timeout=.1)
                    except queue.Empty:continue
                    row=self.compile_one(item)
                    self.counts[row['gate']]+=1
                    self.observations[row['token']]=row
                    logfile.write(json.dumps(row,sort_keys=True,default=str)+'\n');logfile.flush()
                    emit('BOSS_NATIVE_PACKET',row)
                    self.q.task_done()
        self.thread=threading.Thread(target=loop,daemon=True,name='boss-native-preflight');self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=20)
            if self.thread.is_alive():self.counts['HOLD_NATIVE_DRAIN_TIMEOUT']+=1
        if self.blockhash:self.blockhash.close()

    def report(self):return {'alt_status':self.cache_status,'native_template_pairs':len(self.native_ready),
            'native_packet_counts':dict(self.counts),'positive_observations':sum(1 for x in self.observations.values() if x['gross_lamports']>0),
            'signing':False,'broadcast':False,'execution_admission':False,'signed_sim_certified':False,'m2p_certified':False}


def select_ranked(existing,prior=()):
    ext=[];feed_counts={}
    for src in ('SQ','UNIVERSAL'):
        x=source_candidates(src);feed_counts[src]=len(x);ext.extend(x)
    ranking=rank_inventory(existing,ext,prior)
    feed_counts['MRIYA']=sum('MRIYA' in r['sources'] for r in ranking)
    feed_counts['LIVE_TAPE']=sum('LIVE_TAPE' in r['sources'] for r in ranking)
    return ranking,feed_counts


def epoch(seconds,config,number):
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine,live_account_stream as pd
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as merged

    native=NativePreflight(config.wallet,config.alts,config.simulate_unsigned)
    native.prepare(rt,q87)
    org_raw=engine.raw_candidate_universe
    org_prep=q25.prepare_once;org_warm=q25.install_hot_math_and_prewarm
    org_price=q18.exact_snapshot_opportunities;org_scan=q20.LatestStateLane._price
    original_pair_cap=pd.MAX_PAIRS;original_token_cap=engine.MAX_TOKENS
    original_budget=engine.DISCOVERY_BUDGET;original_account_cap=merged.MAX_ACCOUNTS
    original_hot=(q20.FAST_SIZES,q20.EXPAND_SIZES)
    old_print=getattr(q20,'print',None);had_print='print' in q20.__dict__
    old_alt=q87.c.alt_accounts;old_send=q87.c.send;old_keypair=q87.c.keypair;old_sign=q87.c.signed_tx
    old_rpc=q87.c.rpc
    tls=threading.local();state_box={};ranked_box={};stats=Counter();last_report={}
    prior=[]
    if INVENTORY.is_file():
        try:prior=[x['token'] for x in json.loads(INVENTORY.read_text(encoding='utf-8')).get('pairs',[])]
        except (ValueError,OSError,KeyError):pass

    def new_raw(root):
        base=org_raw(root);ranked,counts=select_ranked(base,prior)
        ranked_box.update(ranking=ranked,feeds=counts)
        return ranked[:engine.DISCOVERY_BUDGET]

    def prepare(root):
        state,cap=org_prep(root)
        state_box['state']=state
        # Verify that every watched Pump and DLMM account is actually subscribed.
        active=set(state.get('addresses') or [])
        missing=set(state.get('preg') or {})-active
        if missing:raise RuntimeError('BOSS_WATCH_ACCOUNT_CAP_EXCLUDES_REQUIRED:'+str(len(missing)))
        source_by_token={r['token']:r for r in ranked_box.get('ranking',[])}
        entries=[]
        for p in state.get('pairs') or []:
            rec=source_by_token.get(str(p.token),{})
            entries.append({'token':str(p.token),'pump_pool':str(p.pump_pool),'meteora_pool':str(p.meteora_pool),
                            'sources':rec.get('sources',['UNATTRIBUTED']),'tier':('ULTRA_HOT' if len(entries)<8 else
                            'HOT' if len(entries)<20 else 'ACTIVE'),
                            'watched_accounts':len(p.watched_accounts())})
        report={'build':'ORACLE317','epoch':number,'capacity':config.pairs,'admitted':len(entries),
                'missing_required_ws_accounts':0,'ws_account_count':len(active),'pairs':entries,
                'discovery_source_counts':ranked_box.get('feeds',{}),'ranking_count':len(ranked_box.get('ranking',[])),
                'rotation_semantics':'EPOCH_BOUNDARY_NOT_SEAMLESS'}
        atomic_json(INVENTORY,report);emit('BOSS_INVENTORY',{
            k:v for k,v in report.items() if k!='pairs'})
        return state,cap

    def warm(state):
        x=org_warm(state)
        native.templates(state,x,config.native_prebuild)
        return x

    def scan(self,token,row):
        tls.slot=int(row[1]);native.mark_current(token,int(row[1]))
        try:return org_scan(self,token,row)
        finally:tls.slot=None

    def quote(snap,size):
        rows=org_price(snap,size)
        if abs(float(size)-.010)>1e-8:return rows
        stats['canary_quoted']+=len(rows)
        slot=getattr(tls,'slot',0) or 0
        for op in rows:
            if int(op.get('local_net') or 0)>0:
                stats['gross_positive']+=1
                emit('BOSS_POSITIVE_QUOTE',{'token':str(snap.get('token')),'slot':slot,'direction':op.get('direction'),
                                            'size':.010,'gross_lamports':int(op.get('local_net') or 0),
                                            'net_certified':False})
            native.submit(snap,op,slot)
        return rows

    def print_filtered(*args,**kwargs):
        s=' '.join(map(str,args))
        if not config.verbose and s.startswith('[ORACLE020_EXACT_LATEST]') and 'net=-' in s:
            stats['suppressed_negative_prints']+=1;return
        return builtins.print(*args,**kwargs)

    def blocked(*args,**kwargs):raise RuntimeError('ORACLE314_EXECUTION_AUTHORITY_FALSE')
    def safe_rpc(method,*args,**kwargs):
        if method in ('sendTransaction','sendRawTransaction','requestAirdrop'):
            raise RuntimeError('ORACLE314_BROADCAST_RPC_BLOCKED')
        return old_rpc(method,*args,**kwargs)
    started=time.monotonic();status='COMPLETED';err=None
    try:
        engine.raw_candidate_universe=new_raw
        engine.MAX_TOKENS=max(config.pairs*2,56)
        engine.DISCOVERY_BUDGET=max(96,config.pairs*3)
        engine._cross_cache['at']=0.;engine._cross_cache['rows']=[]
        pd.MAX_PAIRS=config.pairs
        merged.MAX_ACCOUNTS=config.accounts
        q25.prepare_once=prepare;q25.install_hot_math_and_prewarm=warm
        q18.exact_snapshot_opportunities=quote
        q20.LatestStateLane._price=scan
        q20.FAST_SIZES=tuple(round(.010+.005*i,3) for i in range(19));q20.EXPAND_SIZES=()
        q20.print=print_filtered
        # The private key is absent; additionally seal all known transaction-authority functions.
        q87.c.send=blocked;q87.c.signed_tx=blocked;q87.c.keypair=blocked;q87.c.rpc=safe_rpc
        def cached_alt(keys):
            if any(k not in native.loaded for k in keys):raise RuntimeError('ALT_UNPRELOADED')
            return {k:native.loaded[k] for k in keys}
        # Install cache only after venue-native templates finish hydrating.
        old_warm=q25.install_hot_math_and_prewarm
        def warm_cache(state):
            warmed=old_warm(state)
            if native.cache_status=='ALT_READY':q87.c.alt_accounts=cached_alt
            return warmed
        q25.install_hot_math_and_prewarm=warm_cache
        native.start()
        emit('BOSS_EPOCH_START',{'epoch':number,'seconds':seconds,'pair_target':config.pairs,
                                 'max_accounts':config.accounts,'canary_sol':.010,'mode':'SCAN_AND_NATIVE_PREFLIGHT_NO_SEND'})
        q25.run(float(seconds))
    except KeyboardInterrupt:
        status='USER_STOP'
    except Exception as e:
        status='FAILED';err=safe_error(e);emit('BOSS_EPOCH_ERROR',{'epoch':number,'error':err})
    finally:
        # Drain the real native compile worker while the pinned ALT cache is still active.
        native.close()
        # Restore every wrapped seam, even following exceptions.
        engine.raw_candidate_universe=org_raw;engine.MAX_TOKENS=original_token_cap
        engine.DISCOVERY_BUDGET=original_budget;pd.MAX_PAIRS=original_pair_cap
        merged.MAX_ACCOUNTS=original_account_cap
        q25.prepare_once=org_prep;q25.install_hot_math_and_prewarm=org_warm
        q18.exact_snapshot_opportunities=org_price;q20.LatestStateLane._price=org_scan
        q20.FAST_SIZES,q20.EXPAND_SIZES=original_hot
        if had_print:q20.print=old_print
        else:del q20.print
        q87.c.alt_accounts=old_alt;q87.c.send=old_send;q87.c.signed_tx=old_sign;q87.c.keypair=old_keypair;q87.c.rpc=old_rpc
        report={'build':'ORACLE317','epoch':number,'status':status,'error':err,'elapsed_seconds':round(time.monotonic()-started,2),
                'scanner':'ORACLE025->ORACLE020->ORACLE018','canary_sol':.010,
                'gross_positive_010':stats['gross_positive'],'canary_quote_events':stats['canary_quoted'],
                'suppressed_negative_prints':stats['suppressed_negative_prints'],
                'native':native.report(),'signing':False,'broadcast':False,'execution_admission':False,
                'source_inventory':str(INVENTORY),'packet_ledger':str(LEDGER)}
        atomic_json(STATUS,report);emit('BOSS_EPOCH_RESULT',report)
    return report

def scrubbed_child(args):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        env=os.environ.copy();env.pop('QSB_SOLANA_PRIVATE_KEY',None);env['QSB_LIVE_ARM']='NO'
        result=subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.final_boss',*args],env=env)
        return result
    return None

def stage_discovery():
    # Runs outside the hot pricing process. Only stages nominations; never mutates
    # subscribed pools or replaces a quote under an in-flight transaction.
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
    upstream=engine.raw_candidate_universe(pathlib.Path.cwd())
    ranking,feeds=select_ranked(upstream)
    payload={'generated_at':time.time(),'count':len(ranking),'feeds':feeds,
             'top':[dict(x) for x in ranking[:56]],'live_subscription_cutover':False}
    atomic_json(ROOT/'staged_discovery.json',payload)
    return payload

def run(args):
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://'):raise RuntimeError('BOSS_SECURE_RPC_REQUIRED')
    if not os.getenv('SOLANA_WS_URL','').startswith('wss://'):raise RuntimeError('BOSS_SECURE_WS_REQUIRED')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('BOSS_DISARMED_CHILD_REQUIRED')
    if not 1<=args.pairs<=28 or args.accounts<128 or not 1<=args.native_prebuild<=28:
        raise ValueError('BOSS_INVENTORY_CAP_INVALID')
    sha=sha_audit();atomic_json(ROOT/'frozen_hashes.json',sha)
    if args.worker_epoch:
        report=epoch(args.seconds,args,args.epoch_number)
        return 0 if report['status']=='COMPLETED' else 1
    with singleton():
        number=0
        while True:
            number+=1
            # An epoch runs in a fresh process; native scanner monkeypatches cannot survive
            # into subsequent epochs, and only one WebSocket scanner is active at a time.
            command=[sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.final_boss',
                     '--run','--worker-epoch','--epoch-number',str(number),
                     '--seconds',str(args.seconds),'--pairs',str(args.pairs),
                     '--accounts',str(args.accounts),'--native-prebuild',str(args.native_prebuild),'--wallet',args.wallet,
                     '--alts',','.join(args.alts)]
            if args.simulate_unsigned:command.append('--simulate-unsigned')
            if args.verbose:command.append('--verbose')
            worker=subprocess.Popen(command,env=os.environ.copy())
            next_refresh=time.monotonic()+min(45.,max(15.,args.seconds/2.))
            last_staged=None
            try:
                while worker.poll() is None:
                    time.sleep(.25)
                    if time.monotonic()<next_refresh:continue
                    next_refresh=time.monotonic()+max(30.,float(args.stage_interval))
                    try:
                        staged=stage_discovery()
                        fingerprint=tuple((x['token'],x['pump_pool']) for x in staged['top'][:28])
                        if fingerprint!=last_staged:
                            emit('BOSS_REPLENISH_STAGED',{'candidate_count':staged['count'],'sources':staged['feeds'],
                                                         'live_subscriptions_changed':False})
                            last_staged=fingerprint
                    except Exception as e:emit('BOSS_REPLENISH_HOLD',{'error':safe_error(e)})
                code=worker.wait()
            except KeyboardInterrupt:
                worker.terminate()
                try:worker.wait(timeout=10)
                except subprocess.TimeoutExpired:worker.kill();worker.wait()
                raise
            if code:
                emit('BOSS_SUPERVISOR_HOLD',{'epoch':number,'exit_code':code,'signing':False,'broadcast':False})
                return code
            if args.epochs and number>=args.epochs:return 0
            emit('BOSS_ROTATE',{'next_epoch':number+1,'mode':'ORDERLY_WS_EPOCH_CUTOVER',
                                 'note':'No seamless in-place subscription cutover certified'})
    return 0

def tests():
    class T(unittest.TestCase):
        def test_rank_merge(self):
            k='11111111111111111111111111111111';a='So11111111111111111111111111111111111111112'
            rows=rank_inventory([{'token':a,'pump_pool':k,'source':'MRIYA_HOT','age':7}],
                                [{'token':a,'pump_pool':k,'source':'SQ'}])
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['source'],'MULTI_SOURCE')
        def test_hysteresis(self):
            k='11111111111111111111111111111111';a='So11111111111111111111111111111111111111112'
            r=rank_inventory([{'token':a,'pump_pool':k,'source':'LIVE_TAPE'}],[],[a]);self.assertGreater(r[0]['score'],40)
        def test_public_invalid(self):self.assertFalse(validate_public('bad_key'))
        def test_source_schema_reject(self):
            with contextlib.ExitStack() as stk:
                temp=stk.enter_context(__import__('tempfile').TemporaryDirectory())
                with patch.dict(SOURCE_FILES,{'SQ':pathlib.Path(temp)/'sq.json'}):
                    p=SOURCE_FILES['SQ'];p.write_text('{}');self.assertEqual(source_candidates('SQ'),[])
        def test_canary_preflight_negative(self):
            class RT:
                READY_TOKENS={'T'};TEMPLATES={'T':1};METEORA_TEMPLATES={'T':1}
                def same_snapshot_route(self,*a):return {}
            class Q:
                def repaired_candidates(self,*a):return [{'name':'FULL','instructions':[]}]
                def compile_candidate(self,*a):return {'ok':True,'unsigned':b'x'*1000}
            n=NativePreflight('wallet',['alt']);n.rt=RT();n.q87=Q();n.native_ready={'T'}
            n.blockhash=type('BH',(),{'get':lambda self:'block'})()
            r=n.compile_one((time.monotonic(),40,{'token':'T','pump_pool':'p','meteora':{'address':'x'},'dlmm_state':object()},
                             {'direction':'PUMP_TO_METEORA','local_net':-100,'start':CANARY},False))
            self.assertEqual(r['gate'],'PACKET_BUILT_NEGATIVE_REAL_SNAPSHOT_NO_TRADE')
        def test_negative_real_shape_attempts_rpc_sim_and_keeps_hold(self):
            class C:
                def rpc(self,method,params):
                    self.method=method
                    return {'value':{'err':{'InstructionError':[5,{'Custom':6017}]},'logs':['Program log: swap rejected'], 'unitsConsumed':89999,'fee':5000}}
            class Q:
                c=C()
                def repaired_candidates(self,*a):return [{'name':'FULL','instructions':[{'program_id':'p'}]}]
                def compile_candidate(self,*a):return {'ok':True,'unsigned':b'X'*1100}
            class R:
                def same_snapshot_route(self,*a):return {'complete':True}
            n=NativePreflight('w',['a'],True);n.rt=R();n.q87=Q();n.native_ready={'T'}
            n.blockhash=type('BH',(),{'get':lambda self:'block'})()
            x=n.compile_one((time.monotonic(),40,{'token':'T','meteora':{'address':'m'},'dlmm_state':object()},
                             {'direction':'PUMP_TO_METEORA','local_net':-99,'start':CANARY},False))
            self.assertEqual(x['gate'],'HOLD_DIAGNOSTIC_SIM_FAILED')
            self.assertEqual(x['sim_error']['InstructionError'][0],5) if isinstance(x['sim_error'],dict) else self.assertIn('6017',x['sim_error'])
            self.assertTrue(x['diagnostic_negative_quote'])
            self.assertFalse(x['execution_admission']);self.assertFalse(x['broadcast'])
            self.assertEqual(n.q87.c.method,'simulateTransaction')
        def test_diagnostic_sim_success_never_admits_negative(self):
            class C:
                def rpc(self,*a):return {'value':{'err':None,'logs':[],'unitsConsumed':50500,'fee':5000}}
            class Q:
                c=C()
                def repaired_candidates(self,*a):return [{'name':'FULL','instructions':[]}]
                def compile_candidate(self,*a):return {'ok':True,'unsigned':b'X'*1100}
            class R:
                def same_snapshot_route(self,*a):return {}
            n=NativePreflight('w',['a'],True);n.rt=R();n.q87=Q();n.native_ready={'T'}
            n.blockhash=type('BH',(),{'get':lambda self:'block'})()
            x=n.compile_one((time.monotonic(),40,{'token':'T','meteora':{'address':'m'},'dlmm_state':object()},
                             {'direction':'PUMP_TO_METEORA','local_net':-99,'start':CANARY},False))
            self.assertEqual(x['gate'],'DIAGNOSTIC_NEGATIVE_SIM_PASS_NO_TRADE')
            self.assertFalse(x['execution_admission']);self.assertFalse(x['signing'])
        def test_preserves_live_snapshot(self):
            n=NativePreflight('wallet',[]);n.native_ready={'T'}
            state=object();snap={'token':'T','pump_pool':'p','meteora':{'address':'m'},'dlmm_state':state}
            n.submit(snap,{'direction':'PUMP_TO_METEORA','local_net':-1,'start':CANARY},7)
            row=n.q.get_nowait();self.assertIs(row[2]['dlmm_state'],state)
            self.assertEqual(row[2]['meteora']['address'],'m')
        def test_missing_dlmm_rejected(self):
            n=NativePreflight('wallet',[]);n.native_ready={'T'}
            n.submit({'token':'T','pump_pool':'p'}, {'direction':'PUMP_TO_METEORA','local_net':5,'start':CANARY},7)
            self.assertTrue(n.q.empty())
            self.assertEqual(n.counts['HOLD_SNAPSHOT_MISSING_DLMM'],1)
        def test_safe_simulation_error_carries_instruction_code(self):
            err={'InstructionError':[6,{'Custom':6001}]}
            encoded=safe_error(json.dumps(err))
            self.assertIn('InstructionError',encoded)
            self.assertIn('6001',encoded)
        def test_simulation_log_redaction(self):
            row=safe_error('authorization=not_a_key')
            self.assertNotIn('not_a_key',row)
        def test_expired_snapshot(self):
            n=NativePreflight('wallet',[]);n.native_ready={'T'}
            r=n.compile_one((time.monotonic()-1,40,{'token':'T','meteora':{'address':'m'},'dlmm_state':object()},{'direction':'PUMP_TO_METEORA','start':CANARY,'local_net':100},True))
            self.assertEqual(r['gate'],'HOLD_EXPIRED_BEFORE_ROUTE')
        def test_reverse_held(self):
            n=NativePreflight('wallet',[]);n.native_ready={'T'}
            n.submit({'token':'T'},{'direction':'METEORA_TO_PUMP','start':CANARY},10)
            self.assertTrue(n.q.empty())
        def test_signed_never_admitted(self):
            n=NativePreflight('wallet',[]);self.assertFalse(n.report()['broadcast'])
            self.assertFalse(n.report()['signed_sim_certified'])
        def test_packet_limit(self):self.assertEqual(PACKET_LIMIT,1232)
        def test_tier_capacity(self):self.assertEqual(8+12+8,28)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    emit('BOSS317_TEST_PASS',{'tests':result.testsRun,'real_venue_data':False,'broadcast':False})

def main(argv=None):
    p=argparse.ArgumentParser(description='ORACLE-317 FINAL BOSS, read-only canonical supervisor')
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test',action='store_true');mode.add_argument('--audit',action='store_true')
    mode.add_argument('--run',action='store_true');mode.add_argument('--status',action='store_true')
    mode.add_argument('--inventory',action='store_true')
    p.add_argument('--seconds',type=int,default=120,help='Seconds per epoch')
    p.add_argument('--epochs',type=int,default=1,help='0 repeats; each epoch reconnects WS')
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--accounts',type=int,default=1280)
    p.add_argument('--native-prebuild',type=int,default=8)
    p.add_argument('--stage-interval',type=int,default=45)
    p.add_argument('--wallet',default=os.getenv('QSB_SOLANA_WALLET',''))
    p.add_argument('--alts',default=os.getenv('QSB_SOLANA_ALT_ADDRESSES',DEFAULT_ALT))
    p.add_argument('--simulate-unsigned',action='store_true')
    p.add_argument('--verbose',action='store_true')
    p.add_argument('--worker-epoch',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--epoch-number',type=int,default=1,help=argparse.SUPPRESS)
    a=p.parse_args(argv)
    if a.test:tests();return 0
    if a.audit:
        emit('BOSS_AUDIT',{'originals':sha_audit(),'enabled_source_files':{
            k:str(v) for k,v in SOURCE_FILES.items() if v.is_file()},'target_pairs':a.pairs,
            'critical_constraints':{'no_sign':True,'no_send':True,'read_only':True,'m2p_uncertified':True}});return 0
    if a.status:
        emit('BOSS_STATUS',json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.is_file() else {'status':'NOT_RUN'});return 0
    if a.inventory:
        emit('BOSS_INVENTORY',json.loads(INVENTORY.read_text(encoding='utf-8')) if INVENTORY.is_file() else {'status':'NOT_RUN'});return 0
    if a.epochs<0 or a.seconds<10:raise ValueError('INVALID_EPOCH_WINDOW')
    child=scrubbed_child(sys.argv[1:])
    if child is not None:return child
    alts=[x.strip() for x in a.alts.replace(';',',').split(',') if x.strip()]
    if len(set(alts))!=len(alts) or len(alts)>8 or any(not validate_public(x) for x in alts):
        raise ValueError('BOSS_ALT_ADDRESSES_INVALID')
    a.alts=alts
    return run(a)

if __name__=='__main__':raise SystemExit(main())


'''
EXPECTED_SHA256='a5cc5179a5731169f5f38c360e657a3e7c9cf6a1620d7246649382bdcef42d66'
ALLOWED_PREVIOUS={'286a9272a3ad6a0448b06f438a03e2ef2b05a7b48f8e258332cbc21f125402cf','b57e2f2bf04186cb3378fa0ac04b15da30ee4510d3a26e19abbf0cfb727c1661','95527db78ac7c482c2c03eb441fd969f0b058336826902b397094d25595e43ef',EXPECTED_SHA256}
def install():
    if hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()!=EXPECTED_SHA256:raise RuntimeError('SOURCE_HASH_MISMATCH')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.exists():
        old=hashlib.sha256(TARGET.read_bytes()).hexdigest()
        if old not in ALLOWED_PREVIOUS:raise RuntimeError('UNEXPECTED_CANONICAL_RUNTIME_HASH_REFUSE_OVERWRITE:'+old)
    tmp=TARGET.with_name(TARGET.name+'.317.installing')
    tmp.write_bytes(SOURCE.encode('utf-8'))
    py_compile.compile(str(tmp),cfile=str(TARGET.parent/'boss317check.pyc'),doraise=True)
    os.replace(tmp,TARGET)
    try:(TARGET.parent/'boss317check.pyc').unlink()
    except OSError:pass
    if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED_SHA256:raise RuntimeError('INSTALLED_BYTES_BAD')
    print('[ORACLE317_INSTALLED] '+str(TARGET))
    print('[ORACLE317_SHA256_PASS] '+EXPECTED_SHA256)
def call(cmd,env=None):
    if not TARGET.exists() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED_SHA256:raise RuntimeError('INSTALL_317_FIRST')
    return subprocess.call([sys.executable,'-m',MODULE,*cmd],env=env)
def main():
    p=argparse.ArgumentParser(description='ORACLE317 full Final Boss replacement installer')
    m=p.add_mutually_exclusive_group(required=True)
    for mode in ('install','test','audit','launch','status','inventory'):m.add_argument('--'+mode,action='store_true')
    p.add_argument('--seconds',type=int,default=120);p.add_argument('--epochs',type=int,default=1)
    p.add_argument('--pairs',type=int,default=28);p.add_argument('--accounts',type=int,default=1280)
    p.add_argument('--native-prebuild',type=int,default=8);p.add_argument('--simulate-unsigned',action='store_true')
    a=p.parse_args()
    if a.install:install();return 0
    if a.test:return call(['--test'])
    if a.audit:return call(['--audit'])
    if a.status:return call(['--status'])
    if a.inventory:return call(['--inventory'])
    if a.launch:
        if not os.getenv('QSB_SOLANA_WALLET'):raise RuntimeError('PUBLIC_WALLET_REQUIRED')
        from build_oracle_182_secure_windows_credentials import load,api,HELIUS
        k=load(api(),HELIUS)
        if not k:raise RuntimeError('HELIUS_CREDENTIAL_MISSING')
        e=os.environ.copy();e.pop('QSB_SOLANA_PRIVATE_KEY',None);e['QSB_LIVE_ARM']='NO'
        e['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+quote(k,safe='')
        e['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+quote(k,safe='')
        del k
        cmd=['--run','--seconds',str(a.seconds),'--epochs',str(a.epochs),'--pairs',str(a.pairs),
             '--accounts',str(a.accounts),'--native-prebuild',str(a.native_prebuild)]
        if a.simulate_unsigned:cmd.append('--simulate-unsigned')
        return call(cmd,e)
    return 1
if __name__=='__main__':raise SystemExit(main())
