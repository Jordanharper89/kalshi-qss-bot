"""ORACLE-331 complete replacement installer: isolated executor runtime.
Windows CMD: python {Path(__file__).name} --install
Original Q25/Q20/Q18 modules are never rewritten.
"""
from __future__ import annotations
import argparse,hashlib,os,pathlib,py_compile,subprocess,sys
from urllib.parse import quote
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.boss_executor_live'
TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_executor_live.py')
SOURCE=r'''"""ORACLE-331 independent dual-direction evidence-driven native executor.
Consumes exact scanner nominations with 19-size independent structural preflight.
NO PRIVATE KEY, NO SIGNATURE, NO BROADCAST. Do not use for money movement yet.
"""
from __future__ import annotations
import argparse,base64,contextlib,copy,hashlib,json,os,pathlib,sqlite3,struct,sys,time,traceback,threading,queue,random
from collections import Counter
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
BUS=ROOT/'candidate_bus.sqlite3';LEDGER=ROOT/'execution_diagnostics.jsonl'
STATUS=ROOT/'executor_status.json';LOCK=ROOT/'executor.lock'
CANARY=10_000_000;PACKET_LIMIT=1232
SIZE_LADDER=tuple(range(10_000_000,100_000_001,5_000_000))
SIZE_SET=frozenset(SIZE_LADDER)
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
    if int(r['size_lamports']) not in SIZE_SET:return 'HOLD_SIZE_POLICY'
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

def inspect_dlmm_instruction(ix,dlmm):
    """Deterministically decode the *actual* DLMM instruction shape; no network calls."""
    if not isinstance(ix,dict):
        raise RuntimeError('DLMM_INSTRUCTION_NOT_OBJECT')
    if ix.get('programId')!=dlmm:
        raise RuntimeError('DLMM_PROGRAM_IDENTITY_MISMATCH')
    data=ix.get('data')
    if not isinstance(data,str):
        raise RuntimeError('DLMM_DATA_NOT_BASE64_STRING')
    try:
        raw=base64.b64decode(data,validate=True)
    except Exception as exc:
        raise RuntimeError('DLMM_DATA_INVALID_BASE64') from exc
    disc=raw[:8]
    shape={
        'data_len':len(raw),'discriminator_hex':disc.hex(),
        'expected_legacy_hex':OLD_DISC.hex(),
        'expected_swap2_hex':SWAP2_DISC.hex(),
        'account_count':len(ix.get('accounts') or []),
        'program_identity_ok':True,
        'encoding':'base64',
        'known_form':'UNKNOWN',
    }
    if len(raw)==24 and disc==OLD_DISC:
        shape['known_form']='LEGACY_SWAP_EXACT_IN'
    elif len(raw)==28 and disc==SWAP2_DISC:
        shape['known_form']='SWAP2_EMPTY_REMAINING_ARRAY_CANDIDATE' if raw[24:]==b'\x00'*4 else 'SWAP2_NONEMPTY_OR_UNKNOWN_REMAINING'
    elif disc==OLD_DISC:
        shape['known_form']='LEGACY_SWAP_INVALID_LENGTH'
    elif disc==SWAP2_DISC:
        shape['known_form']='SWAP2_INVALID_LENGTH'
    return raw,shape

def rebuild_swap2(ix,template,dlmm):
    """Normalize supported exact-in DLMM instructions to IDL-compatible Swap2.

    Preserve validated exact input/minOut. Reject unsupported hook accounts,
    unknown discriminators, missing quoted arrays, or template account drift.
    Only intended for UNSIGNED diagnostics until live source/slot validation.
    """
    raw,shape=inspect_dlmm_instruction(ix,dlmm)
    form=shape['known_form']
    if form not in ('LEGACY_SWAP_EXACT_IN','SWAP2_EMPTY_REMAINING_ARRAY_CANDIDATE'):
        raise RuntimeError('DLMM_INSTRUCTION_UNSUPPORTED:'+str(form)+':len='+str(shape['data_len'])+':disc='+shape['discriminator_hex']+':accounts='+str(shape['account_count']))
    amount,minimum=struct.unpack_from('<QQ',raw,8)
    if not amount or not minimum:raise RuntimeError('DLMM_NONPOSITIVE_EXACT_SWAP_BOUNDS')
    fixed=template.get('fixed_accounts')
    arrays=template.get('arrays')
    if not isinstance(fixed,list) or len(fixed)!=15 or not isinstance(arrays,list) or not arrays:
        raise RuntimeError('CANONICAL_DLMM_TEMPLATE_INCOMPLETE')
    prefix=[{'pubkey':str(pk),'isSigner':bool(s),'isWritable':bool(w)} for pk,s,w in fixed]
    if prefix[9]['pubkey']!=dlmm or prefix[14]['pubkey']!=dlmm:
        raise RuntimeError('CANONICAL_PROGRAM_PLACEHOLDER_DRIFT')
    prefix.insert(13,dict(pubkey=MEMO,isSigner=False,isWritable=False))
    if len(prefix)!=16 or prefix[13]['pubkey']!=MEMO or prefix[15]['pubkey']!=dlmm:
        raise RuntimeError('SWAP2_CANONICAL_ACCOUNT_ORDER_INVALID')
    known={str(p[1]) for p in arrays}
    original=list(ix.get('accounts') or [])
    offset=15 if form=='LEGACY_SWAP_EXACT_IN' else 16
    if len(original)<=offset:raise RuntimeError('NO_SOURCE_BIN_ARRAYS')
    selected=[];seen=set()
    for a in original[offset:]:
        pk=a.get('pubkey') if isinstance(a,dict) else None
        if pk not in known:raise RuntimeError('BIN_ARRAY_NOT_IN_LIVE_POOL_TEMPLATE')
        if pk in seen:raise RuntimeError('DUPLICATE_BIN_ARRAY')
        seen.add(pk);selected.append({'pubkey':pk,'isSigner':False,'isWritable':True})
    if not selected:raise RuntimeError('NO_QUOTED_BIN_ARRAYS')
    # Borsh vec length for RemainingAccountsInfo{slices: []} is four zero bytes.
    # Nonempty transfer-hook slices cannot be inferred from cached pool arrays.
    data=SWAP2_DISC+struct.pack('<QQI',amount,minimum,0)
    out=dict(ix,accounts=prefix+selected,data=base64.b64encode(data).decode())
    return out,dict(fixed_accounts=16,bin_arrays=len(selected),amount_in=amount,
                    min_out=minimum,source_form=form,source_data_len=len(raw),
                    source_discriminator_hex=shape['discriminator_hex'])


def swap2_array_variants(ix,template,dlmm,limit=4):
    """Diagnose on-chain AccountNotEnoughKeys with validated *consecutive*
    bin arrays. No RPC/price inference, no trading authorization.

    Direction comes from the official prewarmed pool descriptor; the legacy
    builder chose a prefix in this orientation. Adding from its trailing edge
    ensures that existing exact size/min_out and all fixed accounts are intact.
    """
    legal,meta=rebuild_swap2(ix,template,dlmm)
    source=legal['accounts'][16:]
    chosen=[a['pubkey'] for a in source]
    all_arrays=template.get('arrays') or []
    forward=[str(row[1]) for row in all_arrays]
    if not bool(template.get('swap_for_y')):forward.reverse()
    if len(set(forward))!=len(forward) or not forward:
        raise RuntimeError('DLMM_BIN_ARRAY_CATALOG_DUPLICATE_OR_EMPTY')
    # The first selected array must be at the start of the quote direction's
    # range. We do not manufacture arbitrary accounts or reverse the price path.
    if chosen!=forward[:len(chosen)]:
        raise RuntimeError('DLMM_SOURCE_BIN_ARRAY_ORDER_DRIFT:source='+str(len(chosen)))
    if len(chosen)>limit:limit=len(chosen)
    variants=[]
    for count in range(len(chosen),min(len(forward),int(limit))+1):
        add=forward[len(chosen):count]
        accounts=copy.deepcopy(legal['accounts'])
        accounts.extend(dict(pubkey=key,isSigner=False,isWritable=True) for key in add)
        variants.append((dict(legal,accounts=accounts),dict(meta,bin_arrays=count,
            bin_array_pubkeys=forward[:count],additional_arrays=len(add))))
    return variants

def is_bin_array_3005(sim):
    """Only retry the exact Anchor 3005 bin_array missing-key failure."""
    if not isinstance(sim,dict):return False
    e=sim.get('err')
    if not isinstance(e,dict):return False
    v=e.get('InstructionError')
    if not isinstance(v,list) or len(v)!=2 or not isinstance(v[1],dict):return False
    if v[1].get('Custom')!=3005:return False
    return any('account: bin_array' in str(x) for x in (sim.get('logs') or []))



def is_dlmm_slippage_6003(sim):
    """Positive confirmation of Meteora Swap2 6003, NOT any generic 6003."""
    if not isinstance(sim,dict):return False
    e=sim.get('err')
    if not isinstance(e,dict):return False
    ix=e.get('InstructionError')
    if not isinstance(ix,list) or len(ix)!=2 or not isinstance(ix[1],dict):return False
    if ix[1].get('Custom')!=6003:return False
    logs=[str(x) for x in (sim.get('logs') or [])]
    return any('Instruction: Swap2' in z for z in logs) and any(
        'ExceededAmountSlippageTolerance' in z for z in logs)

def isolate_meteora_min_out_only(ixs,dlmm_program,expected_index):
    """Modify ONLY Meteora minOut (to one) in a deep-copied UNSIGNED diagnostic.

    Retain Pump bounds, Meteora exact input, account order, and all other native
    instructions. Never return an executable, profitable or trade-authorized route.
    """
    if not isinstance(ixs,list):raise RuntimeError('6003_PROBE_EXPECTED_INSTRUCTION_LIST')
    out=copy.deepcopy(ixs)
    indexes=[i for i,x in enumerate(out) if x.get('programId')==dlmm_program]
    if indexes!=[expected_index]:raise RuntimeError('6003_PROBE_DLMM_LEG_IDENTITY_MISMATCH')
    raw,shape=inspect_dlmm_instruction(out[expected_index],dlmm_program)
    if shape.get('known_form')!='SWAP2_EMPTY_REMAINING_ARRAY_CANDIDATE':
        raise RuntimeError('6003_PROBE_UNSUPPORTED_SWAP2_SHAPE:'+str(shape.get('known_form')))
    if len(raw)!=28 or raw[24:]!=b'\x00'*4:
        raise RuntimeError('6003_PROBE_UNSUPPORTED_REMAINING_SLICES')
    amount,minimum=struct.unpack_from('<QQ',raw,8)
    if amount<=0 or minimum<=1:raise RuntimeError('6003_PROBE_MIN_OUT_NOT_RELAXABLE')
    edited=bytearray(raw);edited[16:24]=struct.pack('<Q',1)
    out[expected_index]['data']=base64.b64encode(edited).decode()
    if len(out)!=len(ixs):raise RuntimeError('6003_PROBE_LENGTH_DRIFT')
    return out,dict(phase='NON_ECONOMIC_METEORA_MIN_OUT_ISOLATION',
        original_min_out=minimum,diagnostic_min_out=1,original_amount_in=amount,
        meteora_input_unchanged=True,pump_instruction_unchanged=True,
        same_account_layout=True,no_execution_admission=True,
        signing=False,broadcast=False,net_profit_unmeasurable=True,
        strict_packet_untouched=True)

def pump_slippage_6040(sim):
    """Identify exact Pump AMM 6040 and read simulated Left/Right; reject unrelated errors."""
    if not isinstance(sim,dict):return None
    e=sim.get('err')
    if not isinstance(e,dict):return None
    ix=e.get('InstructionError')
    if not isinstance(ix,list) or len(ix)!=2 or not isinstance(ix[1],dict) or ix[1].get('Custom')!=6040:return None
    logs=[str(x) for x in (sim.get('logs') or [])]
    if not any('BuySlippageBelowMinBaseAmountOut' in z for z in logs):return None
    import re
    left=right=None
    for line in logs:
        m=re.search(r'\bLeft:\s*(\d+)\b',line)
        if m:left=int(m.group(1))
        m=re.search(r'\bRight:\s*(\d+)\b',line)
        if m:right=int(m.group(1))
    if left is None or right is None or not (0<left<right):return None
    return dict(error_code=6040,observed_base_out=left,required_min_base_out=right,
                deficit_base_units=right-left,deficit_bps=round((right-left)*10000/right,3),
                cause='PUMP_MIN_BASE_OUT_EXCEEDS_SIMULATED_OUTPUT',
                original_economic_route_rejected=True)

def make_probe_only_packet(ixs,pump_program,dlmm_program,buy_quote_disc,observed_base_out,discount_bps=200):
    """Create ONLY an unsigned NON-ECONOMIC structure probe, never an admissible route.

    Original strict instructions are deep-copied and never modified. A simulated
    output from Pump 6040 is not a fresh quote or a tradeable slippage bound.
    DLMM minOut=1 is for isolating account/program errors, NOT financial execution.
    """
    if not (1<=discount_bps<=500):raise RuntimeError('STRUCTURAL_PROBE_DISCOUNT_OUT_OF_RANGE')
    if not (0<int(observed_base_out)<=2**64-1):raise RuntimeError('STRUCTURAL_PROBE_INVALID_OBSERVED_BASE')
    out=copy.deepcopy(ixs)
    ps=[i for i,v in enumerate(out) if v.get('programId')==pump_program]
    ds=[i for i,v in enumerate(out) if v.get('programId')==dlmm_program]
    if len(ps)!=1 or len(ds)!=1 or ps[0]>=ds[0]:raise RuntimeError('STRUCTURAL_PROBE_REQUIRES_ORDERED_TWO_LEGS')
    pi=out[ps[0]];di=out[ds[0]]
    try:praw=bytearray(base64.b64decode(pi['data'],validate=True))
    except Exception as e:raise RuntimeError('STRUCTURAL_PROBE_INVALID_PUMP_DATA') from e
    if len(praw)<24 or bytes(praw[:8])!=buy_quote_disc:raise RuntimeError('STRUCTURAL_PROBE_UNEXPECTED_PUMP_FORMAT')
    spendable,old_min=struct.unpack_from('<QQ',praw,8)
    if spendable<=0 or old_min<=int(observed_base_out):
        raise RuntimeError('STRUCTURAL_PROBE_PUMP_BOUND_NOT_IN_EXPECTED_FAILED_STATE')
    observed=int(observed_base_out)
    probe_token=max(1,observed*(10000-discount_bps)//10000)
    if not (0<probe_token<old_min):raise RuntimeError('STRUCTURAL_PROBE_NOT_STRICTLY_LOWER')
    draw,dshape=inspect_dlmm_instruction(di,dlmm_program)
    if dshape['known_form']!='SWAP2_EMPTY_REMAINING_ARRAY_CANDIDATE':
        raise RuntimeError('STRUCTURAL_PROBE_SWAP2_REQUIRED:'+dshape['known_form'])
    dr=bytearray(draw)
    old_dlmm_in,old_dlmm_min=struct.unpack_from('<QQ',dr,8)
    if old_dlmm_in<=0 or old_dlmm_min<=0:raise RuntimeError('STRUCTURAL_PROBE_INVALID_DLMM_BOUNDS')
    praw[16:24]=struct.pack('<Q',probe_token)
    dr[8:24]=struct.pack('<QQ',probe_token,1)
    pi['data']=base64.b64encode(praw).decode()
    di['data']=base64.b64encode(dr).decode()
    return out,dict(probe_only=True,non_economic=True,execution_admission=False,
        source='PUMP_6040_SIMULATED_LEFT_NOT_QUOTE',discount_bps=int(discount_bps),
        pump_spend_lamports_unchanged=spendable,
        original_pump_min_base_out=old_min,probe_pump_min_base_out=probe_token,
        original_dlmm_input=old_dlmm_in,probe_dlmm_input=probe_token,
        original_dlmm_min_out=old_dlmm_min,probe_dlmm_min_out=1,
        strict_original_packet_preserved=True,
        net_profit_unmeasurable=True,not_for_signing_or_broadcast=True)

# All new warm state is diagnostic/preflight only. A cached quote is never an execution authorization.
WARM_TTL_NS=750_000_000
DIAGNOSTIC_STRUCTURE_TTL_NS=120_000_000_000
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
    def peek_diagnostic(self,token,pump,meteora,now_ns=None):
        """Diagnostic ONLY: stale market state is permitted to expose instruction errors.
        NEVER use this result to certify profitability, quote freshness or broadcast.
        """
        k=self.identity(token,pump,meteora)
        with self.mu:
            row=self.snapshots.get(k)
            if row is None:return None,'DIAGNOSTIC_STRUCTURE_NOT_HYDRATED'
            age=(time.monotonic_ns() if now_ns is None else now_ns)-row['completed_ns']
            if age<0 or age>DIAGNOSTIC_STRUCTURE_TTL_NS:return None,'DIAGNOSTIC_STRUCTURE_TOO_OLD'
            return row,'DIAGNOSTIC_STALE_STRUCTURE_ONLY'
    def start(self):
        if self.thread:return
        self.thread=threading.Thread(target=self.loop,daemon=True,name='boss330-warm-hydration')
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
        self.native_mutex=threading.RLock();self.warm=None;self.template_bank={}
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
        # The repository prebuild functions RESET global dictionaries on each warm.
        # Persist token-keyed native structure and restore it under native_mutex
        # before constructing a route; never mistake a warm quote for fresh state.
        self.template_bank[token]=dict(
            pump_pool=pump_pool,meteora_pool=meteora_pool,
            pump=copy.deepcopy(self.rt.TEMPLATES[token]),
            meteora=copy.deepcopy(self.rt.METEORA_TEMPLATES[token]))
        self.last_complete_pair=dict(token=token,pump_pool=pump_pool,meteora_pool=meteora_pool,observed_ns=time.time_ns())
        return snap
    def activate_templates(self,token,pump_pool,meteora_pool):
        """Restore one immutable native template pair under native_mutex.

        The original prebuild functions reset module-wide template registries.
        A warm snapshot therefore needs its own matching pool templates.
        """
        b=self.template_bank.get(token)
        if b is None:raise RuntimeError('NATIVE_TEMPLATE_BANK_MISS')
        if b['pump_pool']!=pump_pool or b['meteora_pool']!=meteora_pool:
            raise RuntimeError('NATIVE_TEMPLATE_BANK_POOL_DRIFT')
        if b['pump'].get('pump_pool')!=pump_pool or b['meteora'].get('pool')!=meteora_pool:
            raise RuntimeError('NATIVE_TEMPLATE_BANK_INTERNAL_IDENTITY_DRIFT')
        self.rt.TEMPLATES[token]=copy.deepcopy(b['pump'])
        self.rt.METEORA_TEMPLATES[token]=copy.deepcopy(b['meteora'])
        self.rt.READY_TOKENS.add(token)
        return True
    def simulate(self,token,pump_pool,meteora_pool,diagnostic=False,direction="PUMP_TO_METEORA",size_lamports=CANARY):
        out=dict(build='ORACLE331',token=token,direction=direction,size_lamports=int(size_lamports),
                 diagnostic=bool(diagnostic),signing=False,broadcast=False,execution_admission=False,
                 strict_market_slot_certified=False)
        elapsed={};started=metric()
        try:
            if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):raise RuntimeError('DIRECTION_UNSUPPORTED')
            if int(size_lamports) not in SIZE_SET:raise RuntimeError('SIZE_NOT_ON_SCANNER_LADDER')
            row,cache_gate=self.warm.peek(token,pump_pool,meteora_pool) if self.warm else (None,'WARM_WORKER_NOT_STARTED')
            if row is None and diagnostic and self.warm:
                row,cache_gate=self.warm.peek_diagnostic(token,pump_pool,meteora_pool)
                if row is not None:
                    out['diagnostic_stale_market_state']=True
                    out['economic_certification']=False
                    out['market_freshness_certified']=False
            if row is None:
                if self.warm:self.warm.request(token,pump_pool,meteora_pool)
                out.update(gate='HOLD_'+cache_gate,warm_ready=False)
                return out
            snap=copy.deepcopy(row['snapshot'])
            out['warm_ready']=cache_gate=='WARM_CACHE_FRESH_BY_AGE_ONLY'
            out['warm_snapshot_age_ms']=round((time.monotonic_ns()-row['completed_ns'])/1e6,2)
            out['warm_snapshot_slot_certified']=False
            out['execution_admission']=False
            elapsed['warm_read_ms']=took(started);out['pool_identity_validated']=True
            started=metric()
            with self.native_mutex:
                ops=self.q18.exact_snapshot_opportunities(snap,size_lamports/1_000_000_000)
            forward=next((x for x in ops if x.get('direction')==direction and int(x.get('start') or 0)==size_lamports),None)
            if forward is None:raise RuntimeError('NO_EXACT_DIRECTION_REQUOTE')
            elapsed['quote_ms']=took(started);started=metric()
            gross=int(forward['local_net']);out['fresh_gross_lamports']=gross
            if gross<=0 and not diagnostic:
                out['gate']='HOLD_FRESH_REQUOTE_NONPOSITIVE';return out
            if direction=='METEORA_TO_PUMP':
                assembler=getattr(self.rt,'same_snapshot_reverse_route',None)
                if not callable(assembler):
                    out['gate']='HOLD_REVERSE_NATIVE_ASSEMBLER_UNAVAILABLE'
                    out['reverse_builder']='NOT_CERTIFIED'
                    return out
                with self.native_mutex:
                    self.activate_templates(token,pump_pool,meteora_pool)
                    route=assembler(self.wallet,snap,forward)
            else:
                with self.native_mutex:
                    self.activate_templates(token,pump_pool,meteora_pool)
                    route=self.rt.same_snapshot_route(self.wallet,snap,forward)
            elapsed['native_build_ms']=took(started)
            candidates=[x for x in self.q87.repaired_candidates(route) if x.get('name')=='FULL']
            if not candidates:raise RuntimeError('NO_NATIVE_HELPER_COMPLETE_CANDIDATES')
            bs=metric()
            bh=self.q87.c.rpc('getLatestBlockhash',[{'commitment':'processed'}])['value']['blockhash']
            elapsed['blockhash_ms']=took(bs)
            errors=[]
            for candidate_row in candidates:
                try:
                    strict_ixs=copy.deepcopy(candidate_row['instructions'])
                    ids=[k for k,x in enumerate(strict_ixs) if x.get('programId')==self.q87.c.DLMM]
                    if len(ids)!=1:raise RuntimeError('NEED_EXACTLY_ONE_DLMM_LEG')
                    i=ids[0]
                    _,shape=inspect_dlmm_instruction(strict_ixs[i],self.q87.c.DLMM)
                    out['dlmm_instruction_probe']=shape
                    emit('BOSS331_DLMM_INSTRUCTION_PROBE',dict(token=token[:12],direction=direction,
                        size_lamports=int(size_lamports),diagnostic=diagnostic,shape=shape))
                    phase_ixs=strict_ixs
                    phase='STRICT_EXACT_BOUNDS'
                    # Never enter probe branch outside read-only diagnostics.
                    for stage in range(2 if diagnostic and direction=='PUMP_TO_METEORA' else 1):
                        if stage==1 and phase!='NON_ECONOMIC_STRUCTURAL_PROBE':break
                        variants=swap2_array_variants(phase_ixs[i],self.rt.METEORA_TEMPLATES[token],
                                                      self.q87.c.DLMM,limit=4 if diagnostic else 1)
                        if not variants:raise RuntimeError('DLMM_NO_LEGAL_BIN_ARRAY_VARIANTS')
                        out['array_coverage']=dict(source_arrays=variants[0][1]['bin_arrays'],
                            catalog_arrays=len(self.rt.METEORA_TEMPLATES[token].get('arrays') or []),
                            attempted=0,available_variants=len(variants),direction_for_y=bool(
                                self.rt.METEORA_TEMPLATES[token].get('swap_for_y')))
                        should_probe=False
                        for vi,(legal,meta) in enumerate(variants):
                            ix_copy=copy.deepcopy(phase_ixs)
                            ix_copy[i]=legal
                            entry=dict(phase=phase,array_count=meta['bin_arrays'],extra=meta['additional_arrays'],
                                arrays=meta['bin_array_pubkeys'],unsigned_only=True,
                                executable_certification=False)
                            try:
                                cstart=metric()
                                original_alt=self.q87.c.alt_accounts
                                try:
                                    self.q87.c.alt_accounts=lambda keys:{k:self.cache[k] for k in keys}
                                    compiled=self.q87.compile_candidate(self.wallet,ix_copy,[self.alts],bh)
                                finally:self.q87.c.alt_accounts=original_alt
                                if not compiled.get('ok'):
                                    raise RuntimeError('ALT_COMPILE:'+str(compiled.get('error'))[:140])
                                if len(compiled['unsigned'])>PACKET_LIMIT:raise RuntimeError('PACKET_EXCEEDS_1232')
                                entry.update(packet_bytes=len(compiled['unsigned']),compile_ms=took(cstart))
                            except Exception as exc:
                                entry.update(gate='HOLD_ATOMIC_PACKET_COMPILE',error=safe(exc))
                                out.setdefault('array_attempts',[]).append(entry)
                                out['gate']='HOLD_ATOMIC_PACKET_COMPILE'
                                return out
                            payload=base64.b64encode(compiled['unsigned']).decode()
                            try:
                                if stage>0 or vi>0:time.sleep(.65)
                                sim_start=metric()
                                rsp=self.q87.c.rpc('simulateTransaction',[payload,{'encoding':'base64',
                                    'sigVerify':False,'commitment':'processed',
                                    'replaceRecentBlockhash':False}])
                                entry['simulate_ms']=took(sim_start)
                                sim=rsp.get('value') if isinstance(rsp,dict) else None
                                if not isinstance(sim,dict):raise RuntimeError('RPC_SIMULATION_RESPONSE_MALFORMED')
                            except Exception as exc:
                                entry.update(gate='HOLD_RPC_SIMULATION',error=safe(exc))
                                out.setdefault('array_attempts',[]).append(entry)
                                out['gate']='HOLD_RPC_SIMULATION'
                                return out
                            logs=sim.get('logs') or []
                            pump_failure=pump_slippage_6040(sim) if phase=='STRICT_EXACT_BOUNDS' else None
                            entry.update(gate='UNSIGNED_SIM_PASS' if sim.get('err') is None else 'HOLD_MAINNET_SIM_FAILED',
                                sim_err=sim.get('err'),sim_units=sim.get('unitsConsumed'),
                                missing_bin_array=is_bin_array_3005(sim),
                                pump_6040=pump_failure)
                            out.setdefault('array_attempts',[]).append(entry)
                            out.update(packet_bytes=entry['packet_bytes'],candidate=candidate_row.get('name'),
                                swap2_fixed_accounts=meta['fixed_accounts'],swap2_bin_arrays=meta['bin_arrays'],
                                swap2_source_form=meta['source_form'],exact_bounds_preserved=(stage==0),
                                sim_err=sim.get('err'),sim_units=sim.get('unitsConsumed'),
                                sim_log_tail=[str(z)[:300] for z in logs[-12:]] if isinstance(logs,list) else [])
                            out['array_coverage']['attempted']+=1
                            if sim.get('err') is None:
                                out['gate']=('UNSIGNED_STRUCTURAL_PROBE_PASS_NON_ECONOMIC' if stage==1 else
                                    'UNSIGNED_DIAGNOSTIC_PASS_NO_TRADE' if diagnostic or gross<=0 else
                                    'UNSIGNED_SIM_PASS_SIGNED_NET_UNCERTIFIED')
                                out['economic_certification']=False
                                out['market_freshness_certified']=False
                                out['trade_ready']=False
                                elapsed['simulation_ms']=entry['simulate_ms']
                                elapsed['alt_compile_ms']=entry['compile_ms']
                                return out
                            if pump_failure is not None and diagnostic and stage==0:
                                out['strict_original_failure']=pump_failure
                                emit('BOSS331_STRICT_PUMP_SLIPPAGE',dict(token=token[:12],
                                    strict_failure=pump_failure,signing=False,broadcast=False))
                                try:
                                    phase_ixs,probe=make_probe_only_packet(strict_ixs,self.q87.c.PUMP,
                                        self.q87.c.DLMM,self.rt.BUY_EXACT_QUOTE_IN_DISC,
                                        pump_failure['observed_base_out'])
                                except Exception as exc:
                                    out.update(gate='HOLD_STRUCTURAL_PROBE_UNAVAILABLE',probe_error=safe(exc))
                                    return out
                                out['structural_probe']=probe
                                phase='NON_ECONOMIC_STRUCTURAL_PROBE'
                                should_probe=True
                                break
                            if (diagnostic and stage==0 and direction=='PUMP_TO_METEORA'
                                and is_dlmm_slippage_6003(sim)):
                                # A specific Swap2 6003 means bin account coverage is present.
                                # ONLY an isolated unsigned diagnostic may lower Meteora minOut.
                                # Never change the strict packet, Pump bounds, Meteora input,
                                # fixed accounts, number of arrays, or any market-state gates.
                                original_data,_orig_shape=inspect_dlmm_instruction(ix_copy[i],self.q87.c.DLMM)
                                _input, _min_out=struct.unpack_from('<QQ',original_data,8)
                                out['strict_meteora_swap2_bounds']=dict(amount_in=_input,min_out=_min_out)
                                out['strict_sim_err']=copy.deepcopy(sim.get('err'))
                                try:
                                    p_ixs,p_meta=isolate_meteora_min_out_only(ix_copy,self.q87.c.DLMM,i)
                                    out['meteora_6003_isolation']=p_meta
                                    raw_strict=copy.deepcopy(ix_copy)
                                    if raw_strict!=ix_copy:raise RuntimeError('6003_PROBE_STRICT_PACKET_MUTATED')
                                    cstart=metric()
                                    original_alt=self.q87.c.alt_accounts
                                    try:
                                        self.q87.c.alt_accounts=lambda keys:{k:self.cache[k] for k in keys}
                                        p_compiled=self.q87.compile_candidate(self.wallet,p_ixs,[self.alts],bh)
                                    finally:self.q87.c.alt_accounts=original_alt
                                    if not p_compiled.get('ok'):
                                        raise RuntimeError('6003_PROBE_ALT_COMPILE:'+str(p_compiled.get('error'))[:130])
                                    p_length=len(p_compiled['unsigned'])
                                    if p_length>PACKET_LIMIT:raise RuntimeError('6003_PROBE_PACKET_EXCEEDS_1232')
                                    isolation=dict(phase='NON_ECONOMIC_METEORA_MIN_OUT_ISOLATION',
                                        unsigned_only=True,signing=False,broadcast=False,
                                        execution_admission=False,economic_certification=False,
                                        market_freshness_certified=False,packet_bytes=p_length,
                                        array_count=meta['bin_arrays'],arrays=meta['bin_array_pubkeys'],
                                        compile_ms=took(cstart),bound_isolation=p_meta)
                                    time.sleep(.65)
                                    pstart=metric()
                                    sim_rsp=self.q87.c.rpc('simulateTransaction',[
                                        base64.b64encode(p_compiled['unsigned']).decode(),
                                        {'encoding':'base64','sigVerify':False,'commitment':'processed',
                                         'replaceRecentBlockhash':False}])
                                    isolation['simulate_ms']=took(pstart)
                                    s2=sim_rsp.get('value') if isinstance(sim_rsp,dict) else None
                                    if not isinstance(s2,dict):raise RuntimeError('6003_PROBE_RPC_RESPONSE_INVALID')
                                    isolation['sim_err']=s2.get('err')
                                    isolation['sim_units']=s2.get('unitsConsumed')
                                    isolation['sim_log_tail']=[str(z)[:250] for z in (s2.get('logs') or [])[-10:]]
                                    isolation['gate']=('STRUCTURAL_ONLY_P2M_SWAP2_COMPLETED_NOT_PROFITABLE'
                                        if s2.get('err') is None else 'HOLD_6003_ISOLATION_NEXT_FAILURE')
                                    out['meteora_isolation_attempt']=isolation
                                    out['gate']=isolation['gate']
                                    out['economic_certification']=False
                                    out['market_freshness_certified']=False
                                    out['trade_ready']=False
                                    out['execution_admission']=False
                                    out['signing']=False
                                    out['broadcast']=False
                                    emit('BOSS331_METEORA_6003_ISOLATION',dict(token=token[:12],
                                        strict_err=sim.get('err'),isolation_gate=isolation['gate'],
                                        probe_err=s2.get('err'),array_count=meta['bin_arrays'],
                                        packet_bytes=p_length,trade_ready=False,signing=False,broadcast=False))
                                except Exception as exc:
                                    out['gate']='HOLD_6003_ISOLATION_UNAVAILABLE'
                                    out['meteora_isolation_failure']=safe(exc)
                                return out
                            if diagnostic and entry['missing_bin_array']:
                                if vi+1<len(variants):continue
                                out['gate']='HOLD_DLMM_BIN_ARRAY_COVERAGE_EXHAUSTED'
                                return out
                            out['gate']=('HOLD_NON_ECONOMIC_STRUCTURAL_PROBE_FAILED' if stage==1 else
                                'HOLD_PUMP_6040_FRESH_STATE_REQUIRED' if pump_failure is not None else
                                'HOLD_MAINNET_SIM_FAILED')
                            return out
                        if should_probe:continue
                        # All variants require an explicit result; never fall through into success.
                        out['gate']='HOLD_BIN_ARRAY_VARIANTS_EXHAUSTED';return out
                except Exception as exc:errors.append(safe(exc))
            out.update(gate='HOLD_ATOMIC_PACKET_COMPILE',errors=errors[:6]);return out
        except Exception as e:
            out.update(gate='HOLD_NATIVE_'+safe(e));return out
        finally:out['latency_ms']=elapsed

def diagnostic_size_sweep(native, token, pump_pool, meteora_pool):
    """Quote entire frozen Q20 19-size ladder on structural cache; never authorize a trade."""
    result={'sizes_sol':[round(v/1e9,3) for v in SIZE_LADDER], 'evaluated':0,
            'positive':0, 'best':None, 'read_only':True, 'slot_certified':False}
    if not native.warm:return dict(result,gate='NO_WARM_WORKER')
    row,reason=native.warm.peek_diagnostic(token,pump_pool,meteora_pool)
    if row is None:return dict(result,gate=reason)
    snap=copy.deepcopy(row['snapshot'])
    result['snapshot_age_ms']=round((time.monotonic_ns()-row['completed_ns'])/1e6,2)
    # Quote with native pricing; do not extrapolate a 0.010 quote linearly.
    candidates=[]
    with native.native_mutex:
        for amt in SIZE_LADDER:
            try:
                ops=native.q18.exact_snapshot_opportunities(snap,amt/1e9)
                for op in ops:
                    if int(op.get('start') or 0)!=amt:continue
                    direction=op.get('direction')
                    if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):continue
                    gross=int(op.get('local_net') or 0)
                    result['evaluated']+=1
                    if gross>0:
                        result['positive']+=1
                        candidates.append(dict(size_lamports=amt,size_sol=round(amt/1e9,3),
                            direction=direction,gross_lamports=gross))
            except Exception as exc:
                result.setdefault('size_errors',[]).append(dict(size_lamports=amt,error=safe(exc)))
    result['best']=max(candidates,key=lambda x:x['gross_lamports']) if candidates else None
    result['gate']='STRUCTURAL_LADDER_ONLY_NOT_FRESH_NOT_EXECUTABLE'
    return result

def tests():
    import unittest,tempfile
    class T(unittest.TestCase):
        def test_6040_extracts_exact_observed_bound(self):
            sim={'err':{'InstructionError':[4,{'Custom':6040}]},'logs':[
                'Program log: Error Code: BuySlippageBelowMinBaseAmountOut.',
                'Program log: Left: 4506634195','Program log: Right: 4507629940']}
            x=pump_slippage_6040(sim)
            self.assertEqual(x['deficit_base_units'],995745)
            self.assertEqual(x['error_code'],6040)
            self.assertTrue(x['original_economic_route_rejected'])
        def test_6040_does_not_misclassify_other_errors(self):
            self.assertIsNone(pump_slippage_6040({'err':{'InstructionError':[4,{'Custom':3005}]},'logs':['BuySlippageBelowMinBaseAmountOut']}))
            self.assertIsNone(pump_slippage_6040({'err':{'InstructionError':[4,{'Custom':6040}]},'logs':['another program failed']}))
            self.assertIsNone(pump_slippage_6040({'err':{'InstructionError':[4,{'Custom':6040}]},'logs':['BuySlippageBelowMinBaseAmountOut']}))
        def test_probe_changes_only_two_swap_bounds_and_is_non_economic(self):
            buy=b'12345678';d='DLMM';p='PUMP'
            initial=[{'programId':'SYSTEM','data':'AA=='},
                dict(programId=p,data=base64.b64encode(buy+struct.pack('<QQ',10_000_000,5000)+b'\x01').decode()),
                dict(programId=d,data=base64.b64encode(SWAP2_DISC+struct.pack('<QQI',4990,15,0)).decode())]
            before=copy.deepcopy(initial)
            out,meta=make_probe_only_packet(initial,p,d,buy,observed_base_out=4900)
            self.assertEqual(initial,before)
            self.assertEqual(out[0],initial[0])
            self.assertEqual(out[1]['programId'],p)
            bb=base64.b64decode(out[1]['data']);db=base64.b64decode(out[2]['data'])
            self.assertEqual(struct.unpack_from('<Q',bb,8)[0],10_000_000)
            self.assertEqual(struct.unpack_from('<Q',bb,16)[0],4802)
            self.assertEqual(struct.unpack_from('<QQ',db,8),(4802,1))
            self.assertEqual(bb[24:],b'\x01')
            self.assertTrue(meta['non_economic'])
            self.assertTrue(meta['not_for_signing_or_broadcast'])
            self.assertFalse(meta['execution_admission'])
        def test_probe_fails_closed_for_unknown_pump_discriminator(self):
            x=[dict(programId='PUMP',data=base64.b64encode(b'12345678'+struct.pack('<QQ',10000,100)).decode()),
               dict(programId='DLMM',data=base64.b64encode(SWAP2_DISC+struct.pack('<QQI',90,1,0)).decode())]
            with self.assertRaisesRegex(RuntimeError,'UNEXPECTED_PUMP_FORMAT'):
                make_probe_only_packet(x,'PUMP','DLMM',b'BAD_DISC',90)
        def test_probe_requires_lossy_6040_not_profits(self):
            buy=b'12345678';x=[dict(programId='PUMP',data=base64.b64encode(buy+struct.pack('<QQ',10000,50)).decode()),
               dict(programId='DLMM',data=base64.b64encode(SWAP2_DISC+struct.pack('<QQI',40,1,0)).decode())]
            with self.assertRaisesRegex(RuntimeError,'NOT_IN_EXPECTED_FAILED_STATE'):
                make_probe_only_packet(x,'PUMP','DLMM',buy,90)
        def test_probe_never_activates_for_nondiagnostic(self):
            import inspect
            source=inspect.getsource(Native.simulate)
            self.assertIn("if pump_failure is not None and diagnostic and stage==0:",source)
            self.assertIn('out[\'execution_admission\']=False',source)
            self.assertIn('UNSIGNED_STRUCTURAL_PROBE_PASS_NON_ECONOMIC',source)
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
        def test_already_swap2_idempotent_conversion(self):
            d='dlmm';k=[f'K{i}' for i in range(15)];k[9]=d;k[14]=d
            canonical=dict(fixed_accounts=[(x,False,False) for x in k],arrays=[(0,'BIN1')])
            initial=dict(programId=d,accounts=[{'pubkey':x} for x in k[:13]]+
                         [{'pubkey':MEMO}]+[{'pubkey':x} for x in k[13:]]+
                         [{'pubkey':'BIN1','isWritable':True}],
                         data=base64.b64encode(SWAP2_DISC+struct.pack('<QQI',200,190,0)).decode())
            out,meta=rebuild_swap2(initial,canonical,d)
            self.assertEqual(meta['source_form'],'SWAP2_EMPTY_REMAINING_ARRAY_CANDIDATE')
            self.assertEqual(base64.b64decode(out['data']),SWAP2_DISC+struct.pack('<QQI',200,190,0))
            self.assertEqual(len(out['accounts']),17)
            second,_=rebuild_swap2(out,canonical,d)
            self.assertEqual(second,out)
        def test_unsupported_swap2_remaining_slices_diagnostic(self):
            d='dlmm';a=dict(programId=d,accounts=[{}]*17,
              data=base64.b64encode(SWAP2_DISC+struct.pack('<QQI',3,2,1)).decode())
            _,s=inspect_dlmm_instruction(a,d)
            self.assertEqual(s['known_form'],'SWAP2_NONEMPTY_OR_UNKNOWN_REMAINING')
            with self.assertRaisesRegex(RuntimeError,'SWAP2_NONEMPTY_OR_UNKNOWN_REMAINING'):
                rebuild_swap2(a,dict(fixed_accounts=[],arrays=[]),d)
        def test_wrong_discriminator_actionable_signature(self):
            d='dlmm';a=dict(programId=d,accounts=[{}]*16,
              data=base64.b64encode(b'12345678'+struct.pack('<QQ',3,2)).decode())
            _,shape=inspect_dlmm_instruction(a,d)
            self.assertEqual(shape['data_len'],24)
            self.assertEqual(shape['discriminator_hex'],'3132333435363738')
            with self.assertRaisesRegex(RuntimeError,'DLMM_INSTRUCTION_UNSUPPORTED:UNKNOWN:len=24:disc=3132333435363738'):
                rebuild_swap2(a,{},d)
        def test_truncated_swap2_actionable_length(self):
            d='dlmm';a=dict(programId=d,accounts=[{}]*16,
              data=base64.b64encode(SWAP2_DISC+struct.pack('<QQ',3,2)).decode())
            _,shape=inspect_dlmm_instruction(a,d)
            self.assertEqual(shape['known_form'],'SWAP2_INVALID_LENGTH')
            with self.assertRaisesRegex(RuntimeError,'SWAP2_INVALID_LENGTH:len=24'):
                rebuild_swap2(a,{},d)
        def test_per_token_templates_survive_global_reset(self):
            from types import SimpleNamespace
            n=Native('PUBLIC_WALLET',[])
            n.rt=SimpleNamespace(TEMPLATES={},METEORA_TEMPLATES={},READY_TOKENS=set())
            n.template_bank={
                'A':dict(pump_pool='PA',meteora_pool='MA',pump={'pump_pool':'PA','instructions':[1]},meteora={'pool':'MA','arrays':[(0,'X')]}),
                'B':dict(pump_pool='PB',meteora_pool='MB',pump={'pump_pool':'PB'},meteora={'pool':'MB'})}
            self.assertTrue(n.activate_templates('A','PA','MA'))
            n.rt.TEMPLATES={};n.rt.METEORA_TEMPLATES={};n.rt.READY_TOKENS=set()
            self.assertTrue(n.activate_templates('B','PB','MB'))
            self.assertTrue(n.activate_templates('A','PA','MA'))
            self.assertEqual(n.rt.METEORA_TEMPLATES['A']['pool'],'MA')
            n.rt.TEMPLATES['A']['instructions'].append(2)
            self.assertEqual(n.template_bank['A']['pump']['instructions'],[1])
        def test_template_bank_rejects_wrong_pool(self):
            n=Native('PUBLIC_WALLET',[])
            n.template_bank={'A':dict(pump_pool='PA',meteora_pool='MA',pump={'pump_pool':'PA'},meteora={'pool':'MA'})}
            with self.assertRaisesRegex(RuntimeError,'NATIVE_TEMPLATE_BANK_POOL_DRIFT'):
                n.activate_templates('A','WRONG','MA')
        def test_invalid_base64_is_closed_not_guessed(self):
            with self.assertRaisesRegex(RuntimeError,'DLMM_DATA_INVALID_BASE64'):
                inspect_dlmm_instruction(dict(programId='dlmm',data='???'), 'dlmm')
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
        def test_diagnostic_structural_cache_never_qualifies_trading(self):
            w=WarmState(None,ttl_ns=100)
            k=('T','P','M');w.snapshots[k]={'snapshot':{'token':'T'},'completed_ns':1000}
            self.assertEqual(w.peek(*k,now_ns=1150)[1],'WARM_CACHE_EXPIRED')
            row,flag=w.peek_diagnostic(*k,now_ns=1150)
            self.assertEqual(flag,'DIAGNOSTIC_STALE_STRUCTURE_ONLY')
            self.assertEqual(row['snapshot']['token'],'T')
        def test_structural_diagnostic_age_and_identity(self):
            w=WarmState(None)
            k=('T','P','M');w.snapshots[k]={'snapshot':{},'completed_ns':1000}
            self.assertIsNone(w.peek_diagnostic('X','P','M',now_ns=1100)[0])
            self.assertIsNone(w.peek_diagnostic(*k,now_ns=1000+DIAGNOSTIC_STRUCTURE_TTL_NS+1)[0])
        def test_structural_cache_is_diagnostic_only(self):
            import inspect
            ss=inspect.getsource(Native.simulate)
            self.assertIn('if row is None and diagnostic',ss)
            self.assertIn('diagnostic_stale_market_state',ss)
            self.assertIn('execution_admission',ss)
        def test_warm_does_not_claim_slot_or_execution(self):
            import inspect
            ss=inspect.getsource(Native.simulate)
            self.assertIn('warm_snapshot_slot_certified',ss)
            self.assertIn("out['execution_admission']=False",ss)
        def test_size_ladder_19_points(self):
            self.assertEqual(len(SIZE_LADDER),19)
            self.assertEqual(SIZE_LADDER[0],10_000_000)
            self.assertEqual(SIZE_LADDER[-1],100_000_000)
            self.assertTrue(all(b-a==5_000_000 for a,b in zip(SIZE_LADDER,SIZE_LADDER[1:])))
        def test_size_policy_accepts_all_scanner_sizes(self):
            r=dict(size_lamports=CANARY,direction='PUMP_TO_METEORA',slot=1,gross_lamports=1,
                   created_ns=time.time_ns(),token='t',pump_pool='p',meteora_pool='m')
            for v in SIZE_LADDER:self.assertEqual(verify_event(dict(r,size_lamports=v),dict(status='FRESH')),'ACCEPT_NOMINATION_NOT_EXECUTION')
            self.assertEqual(verify_event(dict(r,size_lamports=101_000_000),dict(status='FRESH')),'HOLD_SIZE_POLICY')
        def test_dlmm_variant_prefix_and_order(self):
            d='DLM';names=['A','B','C','D','E']
            fixed=[(str(i),False,False) for i in range(15)]
            fixed[9]=(d,False,True);fixed[14]=(d,False,False)
            template=dict(fixed_accounts=fixed,arrays=[(i,name) for i,name in enumerate(names)],swap_for_y=True)
            ix=dict(programId=d,data=base64.b64encode(OLD_DISC+struct.pack('<QQ',30,20)).decode(),
                    accounts=[dict(pubkey=str(x[0])) for x in fixed]+[dict(pubkey='A')])
            variants=swap2_array_variants(ix,template,d,limit=4)
            self.assertEqual([m['bin_arrays'] for _,m in variants],[1,2,3,4])
            for instr,meta in variants:
                self.assertEqual([x['pubkey'] for x in instr['accounts'][16:]],names[:meta['bin_arrays']])
                self.assertEqual(instr['accounts'][13]['pubkey'],MEMO)
                self.assertEqual(struct.unpack_from('<QQ',base64.b64decode(instr['data']),8),(30,20))
        def test_dlmm_variants_reverse_orientation(self):
            d='DLM';fixed=[(str(i),False,False) for i in range(15)]
            fixed[9]=(d,False,True);fixed[14]=(d,False,False)
            template=dict(fixed_accounts=fixed,arrays=[(i,str(i)) for i in range(5)],swap_for_y=False)
            ix=dict(programId=d,data=base64.b64encode(OLD_DISC+struct.pack('<QQ',30,20)).decode(),
                    accounts=[dict(pubkey=str(x[0])) for x in fixed]+[dict(pubkey='4')])
            variants=swap2_array_variants(ix,template,d,limit=3)
            self.assertEqual([x['pubkey'] for x in variants[-1][0]['accounts'][16:]],['4','3','2'])
        def test_dlmm_variants_cannot_invent_bin_keys(self):
            d='DLM';fixed=[(str(i),False,False) for i in range(15)]
            fixed[9]=(d,False,True);fixed[14]=(d,False,False)
            template=dict(fixed_accounts=fixed,arrays=[(0,'A'),(1,'B')],swap_for_y=True)
            ix=dict(programId=d,data=base64.b64encode(OLD_DISC+struct.pack('<QQ',30,20)).decode(),
                    accounts=[dict(pubkey=str(x[0])) for x in fixed]+[dict(pubkey='B')])
            with self.assertRaisesRegex(RuntimeError,'ORDER_DRIFT'):swap2_array_variants(ix,template,d)
        def test_only_exact_bin_array_3005_retries(self):
            self.assertTrue(is_bin_array_3005(dict(err={'InstructionError':[5,{'Custom':3005}]},
                logs=['AnchorError caused by account: bin_array. Error Code: AccountNotEnoughKeys'])))
            self.assertFalse(is_bin_array_3005(dict(err={'InstructionError':[5,{'Custom':3005}]},
                logs=['AnchorError caused by account: user_token_in. Error Code: AccountNotEnoughKeys'])))
            self.assertFalse(is_bin_array_3005(dict(err={'InstructionError':[5,{'Custom':6000}]},
                logs=['AnchorError caused by account: bin_array'])))
        def test_specific_meteora_6003_with_logs(self):
            good={'err':{'InstructionError':[5,{'Custom':6003}]},'logs':[
                'Program log: Instruction: Swap2',
                'Error Code: ExceededAmountSlippageTolerance']}
            self.assertTrue(is_dlmm_slippage_6003(good))
            self.assertFalse(is_dlmm_slippage_6003(dict(good,logs=['Other instruction error'])))
            self.assertFalse(is_dlmm_slippage_6003(dict(good,err={'InstructionError':[5,{'Custom':3005}]})))
        def test_meteora_only_minimum_isolation(self):
            d='DLMM';p='PUMP';pump=dict(programId=p,data='abc',accounts=[dict(pubkey='P')])
            ix=dict(programId=d,data=base64.b64encode(SWAP2_DISC+struct.pack('<QQ',123456,30000)+b'\x00'*4).decode(),
                accounts=[dict(pubkey=str(i)) for i in range(17)])
            orig=[copy.deepcopy(pump),copy.deepcopy(ix),dict(programId='EXTRA',data='q',accounts=[])]
            old=copy.deepcopy(orig)
            changed,meta=isolate_meteora_min_out_only(orig,d,1)
            self.assertEqual(orig,old)
            self.assertEqual(changed[0],pump)
            self.assertEqual(changed[2],orig[2])
            self.assertEqual(changed[1]['accounts'],ix['accounts'])
            raw=base64.b64decode(changed[1]['data'])
            self.assertEqual(struct.unpack_from('<QQ',raw,8),(123456,1))
            self.assertEqual(raw[:8],SWAP2_DISC)
            self.assertEqual(raw[24:],b'\x00'*4)
            self.assertTrue(meta['no_execution_admission'])
            self.assertTrue(meta['pump_instruction_unchanged'])
            self.assertTrue(meta['same_account_layout'])
            self.assertTrue(meta['net_profit_unmeasurable'])
        def test_6003_probe_invalid_minimum_and_multiple_programs(self):
            d='DLMM';ix=dict(programId=d,
                data=base64.b64encode(SWAP2_DISC+struct.pack('<QQ',12,1)+b'\x00'*4).decode(),
                accounts=[])
            with self.assertRaisesRegex(RuntimeError,'NOT_RELAXABLE'):
                isolate_meteora_min_out_only([ix],d,0)
            with self.assertRaisesRegex(RuntimeError,'IDENTITY_MISMATCH'):
                isolate_meteora_min_out_only([ix,ix],d,0)
        def test_6003_probe_remains_only_diagnostic(self):
            import inspect
            s=inspect.getsource(Native.simulate)
            self.assertIn("diagnostic and stage==0 and direction=='PUMP_TO_METEORA'",s)
            self.assertIn('is_dlmm_slippage_6003(sim)',s)
            self.assertIn('NON_ECONOMIC_METEORA_MIN_OUT_ISOLATION',s)
            self.assertIn("time.sleep(.65)",s)
            self.assertNotIn('sendTransaction',s)
            self.assertNotIn('sign_transaction',s)
        def test_probe_output_never_claims_profit(self):
            import inspect
            s=inspect.getsource(isolate_meteora_min_out_only)
            self.assertIn('net_profit_unmeasurable=True',s)
            self.assertIn('strict_packet_untouched=True',s)
            s=inspect.getsource(Native.simulate)
            self.assertIn("out['trade_ready']=False",s)
            self.assertIn("out['execution_admission']=False",s)
        def test_simulation_never_signs_or_broadcasts(self):
            import inspect
            s=inspect.getsource(Native.simulate)
            self.assertIn('sigVerify\':False',s)
            self.assertNotIn('sendTransaction',s)
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
        emit('BOSS331_EXECUTOR_START',dict(restore_cursor=cursor,scan='ORACLE322_FROZEN',directions='BIDIRECTIONAL_PREFLIGHT',signing=False,broadcast=False))
        with LEDGER.open('a',encoding='utf-8') as ledger:
            while True:
                h=heartbeat(c);now=time.monotonic()
                if now-last_status>10:
                    emit('BOSS331_HEARTBEAT',dict(scanner=h,seen=stats['events'],sim_pass=stats['sim_pass'],diagnostic=stats['diagnostics'],coalesced=stats['coalesced'],warm=dict(n.warm.stats),warm_queue=n.warm.work.qsize(),reverse_holds=stats['HOLD_REVERSE_NATIVE_ASSEMBLER_UNAVAILABLE'],broadcast=False))
                    save(STATUS,dict(build='ORACLE331',scanner=h,counters=dict(stats),broadcast=False,signing=False,mode='MAINNET_UNSIGNED_PREFLIGHT'))
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
                            row=n.simulate(r['token'],r['pump_pool'],r['meteora_pool'],diagnostic=False,direction=r['direction'],size_lamports=int(r['size_lamports']))
                            row['latency_ms']['end_to_end_ms']=took(started)
                            row['latency_ms']['queue_age_at_start_ms']=round((start_ns-int(r['created_ns']))/1e6,3)
                            row['nomination']=dict(slot=r['slot'],gross=r['gross_lamports'],source=r['source'],age_ms=round((time.time_ns()-int(r['created_ns']))/1e6,2))
                            row['lineage']=quote_lineage(r,row)
                            ledger.write(json.dumps(row,sort_keys=True,default=str)+'\n');ledger.flush()
                            emit('BOSS331_NATIVE_RESULT',row);stats[row['gate']]+=1
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
                            sweep=diagnostic_size_sweep(n,p['token'],p['pump_pool'],p['meteora_pool'])
                            best=sweep.get('best')
                            audit_size=int(best['size_lamports']) if best else CANARY
                            rr=n.simulate(p['token'],p['pump_pool'],p['meteora_pool'],diagnostic=True,direction=(best['direction'] if best else 'PUMP_TO_METEORA'),size_lamports=audit_size)
                            rr['size_sweep']=sweep
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
                    emit('BOSS331_DIAGNOSTIC',row);stats[row['gate']]+=1
                time.sleep(poll)

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    for x in ('test','audit','status','run'):m.add_argument('--'+x,action='store_true')
    p.add_argument('--diagnostic-interval',type=int,default=60)
    a=p.parse_args()
    if a.test:return tests()
    if a.audit:
        emit('BOSS331_AUDIT',dict(candidate_bus=str(BUS),
             canonical_scanner='ORACLE025->ORACLE020->ORACLE018',
             native='qseries_v2.oracle_execution.solana_atomic_executor.runtime',
             signing=False,broadcast=False,m2p_certified=False));return 0
    if a.status:
        emit('BOSS331_STATUS',json.loads(STATUS.read_text()) if STATUS.is_file() else {'status':'NOT_STARTED'});return 0
    if a.diagnostic_interval<20:raise RuntimeError('DIAGNOSTIC_INTERVAL_TOO_LOW')
    return run(a.diagnostic_interval)
if __name__=='__main__':raise SystemExit(main())



'''
EXPECTED='3781f0983e7b5e724cf97f594204a3e0cb34ded9491f791ded3293c2d8fdedae'
def install():
    raw=SOURCE.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise RuntimeError('SOURCE_HASH_MISMATCH')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    # This build owns only its distinct runtime module; frozen source is untouched.
    temp=TARGET.with_name(TARGET.name+'.331.installing')
    temp.write_bytes(raw)
    check=TARGET.with_name('boss331check.pyc')
    try:py_compile.compile(str(temp),cfile=str(check),doraise=True)
    finally:
        if check.exists():check.unlink()
    os.replace(temp,TARGET)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:raise RuntimeError('BYTE_HASH_MISMATCH')
    print('[ORACLE331_INSTALLED]',TARGET)
    print('[ORACLE331_SHA256_PASS]',EXPECTED)

def call(opts,env=None):
    if not TARGET.is_file() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError('INSTALL_ORACLE331_FIRST')
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
    p=argparse.ArgumentParser(description='ORACLE-331 executor full replacement installer/launcher')
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
