
from __future__ import annotations
"""Final Boss V9: V8 verified prospect -> genuine scanner event -> native v0 -> signed SIM ONLY.

No discovery WebSocket, no scanner mutation, no write to canonical SQLite.
Simulation eligibility is intentionally NOT funded-execution eligibility.
Trusted references:
  https://solana.com/docs/rpc/http/simulatetransaction
  https://solana.com/docs/rpc/http/getfeeformessage
  https://solana.com/docs/tokens/extensions/metadata
  https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/reference.mdx
  https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_SWAP_README.md
"""
import argparse, collections, importlib, json, os, re, threading, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3] if len(Path(__file__).resolve().parents)>3 else Path.cwd()
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
V8=BASE/'mriya_crossvenue_prospects.json'
OUT=BASE/'final_boss_v9_simulation_gate.json'
PKG='qseries_v2.oracle_execution.solana_atomic_executor.'
GRID=tuple(range(10_000_000,100_000_001,5_000_000))
DIRS={'PUMP_TO_METEORA','METEORA_TO_PUMP'}
ADDR=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
WALLET_DEFAULT='7t4krNuD6e6srbZZh2pkMELy1mJSHFTM7HitbBm7vaBE'
SAFE=re.compile(r'^[A-Z][A-Z0-9_]{2,90}$')
TOKEN2022='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
SPL='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
REVIEW_EXT={'metadatapointer','tokenmetadata'}
V8_MAX_AGE=90
MAX_ATTEMPTS=3

class Hold(RuntimeError):pass

def mod(name):return importlib.import_module(PKG+name)

def hold_code(exc):
    if isinstance(exc,Hold) and SAFE.fullmatch(str(exc)):return str(exc)
    return type(exc).__name__.upper()

def load_v8(now=None,path=V8):
    now=time.time() if now is None else now
    if not path.is_file() or path.is_symlink() or path.stat().st_size>400_000:
        raise Hold('V8_VERIFIED_REPORT_MISSING_OR_LARGE')
    try:r=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,OSError,UnicodeError):raise Hold('V8_REPORT_UNREADABLE') from None
    if not isinstance(r,dict) or r.get('build')!='FINAL_BOSS_MRIYA_CROSSVENUE_V8' or r.get('source')!='FRESH_MRIYA_INDEXED_POOL_PROSPECTS_UNTRUSTED':
        raise Hold('V8_REPORT_SOURCE_INVALID')
    t=r.get('observed_unix')
    if type(t) not in (int,float) or not 0<=now-t<=V8_MAX_AGE:
        raise Hold('V8_REPORT_EXPIRED')
    if r.get('scanner_modified') is not False or r.get('read_only') is not True or r.get('execution_authority') is not False:
        raise Hold('V8_SOURCE_AUTHORITY_INVALID')
    if not isinstance(r.get('prospects'),list) or len(r['prospects'])>50:
        raise Hold('V8_PROSPECT_LIST_UNTRUSTED')
    return r

def _norm(name):return str(name).lower().replace('-','').replace('_','')

def review_mint(row):
    """Allows metadata-only Token2022 into *sim review*, never funded execution.

    A V8 JSON is an evidence hint, not an authoritative current on-chain mint.
    A fresh getAccountInfo review is repeated before native simulation.
    """
    if row.get('mint_check')=='PROVISIONAL_SPL_MINT_ONLY' and row.get('token2022_audit') is None:
        return 'SPL_PROVISIONAL_SIM_REVIEW'
    a=row.get('token2022_audit')
    if not isinstance(a,dict):raise Hold('TOKEN2022_EVIDENCE_MISSING')
    if a.get('status')!='HOLD_TOKEN2022_FULL_NATIVE_EXECUTION_SIM_REQUIRED':
        raise Hold('TOKEN2022_AUDIT_NOT_PROVISIONAL')
    if a.get('mint_authority_absent') is not True or a.get('freeze_authority_absent') is not True:
        raise Hold('MINT_OR_FREEZE_AUTHORITY_PRESENT')
    if a.get('hazardous_extensions')!=[] or a.get('unknown_extensions')!=[]:
        raise Hold('TOKEN2022_RESTRICTIVE_OR_UNKNOWN_EXTENSION')
    names=a.get('extensions')
    if not isinstance(names,list) or any(not isinstance(x,str) for x in names):
        raise Hold('TOKEN2022_EXTENSION_LIST_NOT_VERIFIED')
    if not set(map(_norm,names)).issubset(REVIEW_EXT):
        raise Hold('TOKEN2022_EXTENSION_NOT_WHITELISTED_FOR_SIM')
    return 'TOKEN2022_METADATA_ONLY_SIM_REVIEW'

def exact_triple(row):
    t=tuple(row.get(k) for k in ('token','pump_pool','meteora_pool'))
    if not all(isinstance(k,str) and ADDR.fullmatch(k) for k in t) or len(set(t))!=3:
        raise Hold('V8_POOL_TRIPLE_INVALID')
    if row.get('onchain_pool_binding_verified') is not True or row.get('pool_program_owners_verified') is not True:
        raise Hold('V8_POOL_OWNER_OR_MINT_NOT_PROVEN')
    p=row.get('pump_witness');m=row.get('dlmm_witness')
    if not isinstance(p,dict) or not isinstance(m,dict):raise Hold('V8_ONCHAIN_POOL_WITNESS_MISSING')
    if p.get('reason')!='PUMP_POOL_HEADER_VERIFIED' or m.get('reason')!='DLMM_POOL_MINTS_VERIFIED':
        raise Hold('V8_ONCHAIN_POOL_BINDING_INCOMPLETE')
    if p.get('pair_mints_match') is not True or m.get('pair_mints_match') is not True:
        raise Hold('V8_MINT_BINDING_MISMATCH')
    if m.get('status')!=0 or type(m.get('bin_step')) is not int or m['bin_step']<=0:
        raise Hold('V8_DLMM_DISABLED_OR_INVALID')
    return t

def candidates(report):
    good={};holds=collections.Counter()
    for r in report['prospects']:
        try:
            triple=exact_triple(r)
            risk=review_mint(r)
            old=good.get(triple)
            if old is None or float(r.get('mriya_age_s',1e9))<old['mriya_age_s']:
                good[triple]={'risk':risk,'mriya_age_s':float(r.get('mriya_age_s',1e9))}
        except Exception as exc:holds[hold_code(exc)]+=1
    return good,dict(holds)

def recheck_mint(rpc,token,minslot,expected):
    """One bounded read via existing native RPC client; no new RPC session/socket.

    Parsed extensions must be visible; metadata-only is not execution authority.
    """
    if not callable(rpc):raise Hold('NATIVE_RPC_UNAVAILABLE_FOR_MINT_RECHECK')
    res=rpc('getMultipleAccounts',[[token],{'encoding':'jsonParsed','commitment':'confirmed','minContextSlot':minslot}])
    if not isinstance(res,dict) or not isinstance(res.get('context'),dict) or res['context'].get('slot',0)<minslot:
        raise Hold('TOKEN_MINT_RPC_CONTEXT_STALE')
    vals=res.get('value')
    if not isinstance(vals,list) or len(vals)!=1:raise Hold('TOKEN_MINT_BATCH_RESPONSE_INVALID')
    acc=vals[0]
    if not isinstance(acc,dict) or acc.get('owner') not in (SPL,TOKEN2022):
        raise Hold('TOKEN_MINT_RPC_OWNER_NOT_TRUSTED')
    d=acc.get('data') or {};p=d.get('parsed') if isinstance(d,dict) else None
    i=p.get('info') if isinstance(p,dict) else None
    if not isinstance(i,dict) or p.get('type')!='mint' or i.get('isInitialized') is not True:
        raise Hold('TOKEN_MINT_RPC_DECODE_INCOMPLETE')
    if 'mintAuthority' not in i or 'freezeAuthority' not in i or i['mintAuthority'] is not None or i['freezeAuthority'] is not None:
        raise Hold('TOKEN_MINT_RPC_AUTHORITY_UNSAFE')
    if expected=='SPL_PROVISIONAL_SIM_REVIEW':
        if acc['owner']!=SPL:raise Hold('TOKEN_MINT_PROGRAM_DRIFT')
    elif expected=='TOKEN2022_METADATA_ONLY_SIM_REVIEW':
        if acc['owner']!=TOKEN2022:raise Hold('TOKEN_MINT_PROGRAM_DRIFT')
        e=i.get('extensions')
        if not isinstance(e,list):raise Hold('TOKEN2022_FRESH_EXTENSIONS_MISSING')
        names=[_norm(x.get('extension')) for x in e if isinstance(x,dict)]
        if len(names)!=len(e) or not set(names).issubset(REVIEW_EXT):
            raise Hold('TOKEN2022_FRESH_RESTRICTIVE_EXTENSION')
    else:raise Hold('UNKNOWN_EXPECTED_MINT_REVIEW')
    return {'mint_program':'TOKEN2022' if acc['owner']==TOKEN2022 else 'SPL','rpc_slot':res['context']['slot'],'authority_absent':True}

def same_event(row,origin,grid=GRID):
    if row.get('schema')!='ORACLE363_ATOMIC_REPRICE_REQUEST_V1':raise Hold('CANONICAL_SCHEMA_UNEXPECTED')
    if row.get('direction') not in DIRS:raise Hold('DIRECTION_INVALID')
    size=row.get('size_lamports')
    if type(size) is not int or size not in grid:raise Hold('SIZE_NOT_ON_19_POINT_CURVE')
    if origin!=(row.get('token'),row.get('pump_pool'),row.get('meteora_pool')):
        raise Hold('CANONICAL_SOURCE_POOL_DIFFERENT_FROM_V8')
    if type(row.get('scanner_gross_lamports_hint')) is not int or row['scanner_gross_lamports_hint']<=0:
        raise Hold('NOT_POSITIVE_SCANNER_NOMINATION')
    return size

def conservation(proof,sim):
    """Deduct ALL native declared conservative costs; no fabricated profit."""
    if not isinstance(sim,dict) or type(sim.get('fee_adjusted_conservative_sim_net_lamports')) is not int:
        raise Hold('SIM_FEE_ADJUSTED_RESULT_MISSING')
    if sim.get('token_residue_raw')!=0:raise Hold('SIM_TOKEN_RESIDUE_NOT_ZERO')
    if not isinstance(proof,dict) or any(type(proof.get(k)) is not int or proof[k]<0 for k in
        ('transfer_fee_lamports','rent_cost_lamports','tip_lamports','residue_lamports','adverse_buffer_lamports')):
        raise Hold('NATIVE_ADVERSE_COST_BOUNDS_MISSING')
    net=sim['fee_adjusted_conservative_sim_net_lamports']-sum(proof[k] for k in
       ('transfer_fee_lamports','rent_cost_lamports','tip_lamports','residue_lamports','adverse_buffer_lamports'))
    if net<=0:raise Hold('CONSERVATIVE_SIGNED_SIM_NET_NONPOSITIVE')
    return net

def save(obj):
    BASE.mkdir(parents=True,exist_ok=True)
    # No raw tx bytes, private keys, or RPC URLs are included in obj.
    tmp=OUT.with_name(OUT.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding='utf-8')
    os.replace(tmp,OUT)

def audit():
    result={'build':'FINAL_BOSS_V9','mode':'AUDIT','status':'HOLD','broadcast':False,
        'scanner_modified':False,'additional_websockets':0,'signing':False,
        'production_execution_certified':False,'protected_min_out_certified':False,
        'grid_min_sol':0.010,'grid_max_sol':0.100,'grid_sizes':len(GRID)}
    try:
        report=load_v8();routes,holds=candidates(report)
        result.update(v8_pool_routes=len(report['prospects']),sim_review_routes=len(routes),
                      risk_holds=holds,sim_review_t22=sum(z['risk'].startswith('TOKEN2022') for z in routes.values()))
        owner=mod('oracle_399_final_boss_execution_owner')
        result['frozen_sources_verified']=len(owner.source_hashes())
        scan=mod('oracle_344_scanner_align')
        c=scan.bus()
        try:
            c.execute('PRAGMA query_only=ON')
            h=scan.validate_scanner(c)
        finally:c.close()
        if not isinstance(h,dict) or h.get('ok') is not True:raise Hold('SCANNER_CANONICAL_HEALTH_FAILED')
        result.update(scanner_health=True,scanner_epoch=h.get('epoch'),producer_prefix=str(h.get('producer',''))[:12])
        result['status']='READY_FOR_CANONICAL_EVENT_IF_MATCHED' if routes else 'HOLD_NO_V8_SIM_REVIEW_ROUTES'
    except Exception as exc:result['status']='HOLD_'+hold_code(exc)
    save(result);print('[FINAL_BOSS_V9_AUDIT]',json.dumps(result,sort_keys=True),flush=True)
    print('[REPORT]',OUT.relative_to(ROOT),flush=True)
    return 0 if result['status']=='READY_FOR_CANONICAL_EVENT_IF_MATCHED' else 2

def observe(seconds,wallet,signed_sim=False):
    if not 1<=seconds<=900:raise Hold('SECONDS_OUT_OF_RANGE')
    if not isinstance(wallet,str) or not ADDR.fullmatch(wallet):raise Hold('PUBLIC_WALLET_INVALID')
    outcome={'build':'FINAL_BOSS_V9','mode':'SIGNED_SIM_ONLY' if signed_sim else 'UNSIGNED_OBSERVATION',
       'status':'HOLD','scanner_modified':False,'additional_websockets':0,'broadcast':False,
       'signing':False,'signed_simulation_requested':bool(signed_sim),
       'production_execution_certified':False,'protected_min_out_certified':False,
       'allowed_size_grid_lamports':list(GRID), 'real_events':0,'matching_events':0,
       'native_unsigned':0,'signed_simulations':0,'best_size_lamports':None,
       'best_conservative_sim_net_lamports':None,'candidate_holds':{},'sizes_actually_simulated':[],'eligible_to_broadcast':False}
    db=None;stop=threading.Event();guard=threading.Lock();queue=collections.deque(maxlen=20)
    worker=None;counts=collections.Counter();selected=set();attempted=set();source={}
    try:
        report=load_v8();routes,risk_holds=candidates(report)
        outcome.update(verified_v8_prospects=len(report['prospects']),sim_review_routes=len(routes),risk_holds=risk_holds)
        if not routes:raise Hold('NO_V8_SAFETY_REVIEW_ROUTES')
        owner=mod('oracle_399_final_boss_execution_owner')
        if len(owner.source_hashes())!=4:raise Hold('SOURCE_FREEZE_NOT_VERIFIED')
        scan=mod('oracle_344_scanner_align');persistent=mod('oracle_374_persistent_dual_native_handoff')
        first=persistent.read_heartbeat(scan)
        native=mod('oracle_370_native_atomic_executor');rev=mod('oracle_378_native_reverse_atomic')
        exec402=mod('oracle_402_source_first_handoff')
        with exec402.native_capacity_scope():
            provider=rev.CompatibleNativeProvider(native,wallet)
            provider.prewarm()
        inventory=exec402.native_inventory(provider)
        available={t for t in routes if t in set(inventory['triples'].values()) and t[0] in inventory['ready']}
        outcome.update(native_ready_tokens=len(inventory['ready']),v8_native_ready_overlap=len(available))
        if not available:
            raise Hold('NO_V8_ROUTE_IN_CURRENT_NATIVE_SCANNER_INVENTORY')
        core=mod('oracle_368_source_boundary_repair')
        bridge=mod('oracle_401_canonical_signed_preflight') if signed_sim else None
        # Never load the signer before a real fresh verified route reaches simulation.
        m363=mod('oracle_363_verified_scanner_bus_binding')
        m365=mod('oracle_365_sqlite_columnar_event_handoff')
        m379=mod('oracle_379_five_goal_executor')
        m359=mod('oracle_359_lock_safe_handoff')
        metrics=m379.Metrics();Gate=m379.make_ingress(m363,metrics)
        ingress=Gate(ttl_ms=2500,max_age_ms=1500)
        source.update(producer=first['producer'],epoch=first['epoch'])
        def receive(row):
            with guard:
                outcome['real_events']+=1
                try:
                    triple=(row.get('token'),row.get('pump_pool'),row.get('meteora_pool'))
                    if triple not in available:return
                    same_event(row,triple)
                    issue=exec402.precheck(row,source['producer'],source['epoch'])
                    if issue:raise Hold('CANONICAL_EVENT_AGE_OR_PRODUCER_INVALID')
                    nonce=(row.get('scanner_producer'),row.get('scanner_epoch'),row.get('event_id'))
                    if nonce in attempted:return
                    attempted.add(nonce)
                    outcome['matching_events']+=1
                    selected.add(row['size_lamports'])
                    if len(queue)>=20:counts['QUEUE_COALESCED']+=1
                    queue.append(dict(row))
                except Exception as exc:counts[hold_code(exc)]+=1
        ingress.callback=receive
        def prepare_loop():
            while not stop.is_set():
                with guard:
                    row=queue.popleft() if queue else None
                    if row and outcome.get('attempts',0)>=MAX_ATTEMPTS:row=None
                    if row:outcome['attempts']=outcome.get('attempts',0)+1
                if row is None:
                    stop.wait(.015);continue
                try:
                    token=row['token'];triple=(token,row['pump_pool'],row['meteora_pool'])
                    if exec402.precheck(row,source['producer'],source['epoch']):raise Hold('EVENT_EXPIRED_DURING_NATIVE_PREPARE')
                    proof=provider.prepare_unsigned(row)
                    exec402.proof_contract(row,proof,core.bank_native_gate)
                    with guard:outcome['native_unsigned']+=1
                    if not signed_sim:continue
                    if row['direction']=='METEORA_TO_PUMP' and bridge.checks()['reverse_validator_program_id_drift']:
                        raise Hold('REVERSE_PROGRAM_ID_DRIFT')
                    # Explicit independent mint re-read at the bank slot: no stale V8 risk authority.
                    fresh=recheck_mint(native._rpc,token,proof['bank_slot'],routes[triple]['risk'])
                    if exec402.precheck(row,source['producer'],source['epoch']):raise Hold('EVENT_EXPIRED_BEFORE_SIGNED_SIM')
                    sim_key=bridge.signer(wallet)
                    sim=bridge.signed_preflight(row,proof,wallet,sim_key,native._rpc)
                    net=conservation(proof,sim)
                    with guard:
                        outcome['signed_simulations']+=1
                        outcome['sizes_actually_simulated'].append(row['size_lamports'])
                        if outcome['best_conservative_sim_net_lamports'] is None or net>outcome['best_conservative_sim_net_lamports']:
                            outcome['best_conservative_sim_net_lamports']=net
                            outcome['best_size_lamports']=row['size_lamports']
                            outcome['best_direction']=row['direction']
                        outcome['last_mint_program']=fresh['mint_program']
                        outcome['status']='SIM_OBSERVED_MINOUT_CERTIFICATION_PENDING'
                except Exception as exc:
                    with guard:counts[hold_code(exc)]+=1
        # Never consume more than MAX_ATTEMPTS signed simulations per run.
        worker=threading.Thread(target=prepare_loop,daemon=True,name='v9_native_sim_only')
        worker.start()
        with m359.ExclusiveLock():
            db=scan.bus();db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA busy_timeout=500')
            hb=scan.validate_scanner(db)
            if hb.get('ok') is not True or hb.get('producer')!=first['producer']:
                raise Hold('SCANNER_CHANGED_BEFORE_ATTACH')
            source.update(producer=hb['producer'],epoch=hb['epoch'])
            cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            ingress.attach(hb,cursor)
            outcome['canonical_source_attached']=True
            deadline=time.monotonic()+seconds;next_health=0
            gate_counts=collections.Counter();inbox=BASE/'v9_transient_ingress.json'
            try:
                while time.monotonic()<deadline and outcome['signed_simulations']==0:
                    now=time.monotonic()
                    if now>=next_health:
                        recent=scan.validate_scanner(db)
                        if recent.get('ok') is not True:raise Hold('CANONICAL_HEALTH_FAILED_DURING_OBSERVE')
                        if recent.get('producer')!=hb['producer'] or recent.get('epoch')!=hb['epoch']:
                            raise Hold('SCANNER_PRODUCER_OR_EPOCH_CHANGED')
                        ingress.health(recent)
                        if ingress.failed:raise Hold('INGRESS_HEALTH_FAILED')
                        next_health=now+.25
                    m365.consume(scan,db,ingress,gate_counts,inbox)
                    if ingress.failed:raise Hold('CANONICAL_INGRESS_FAILED')
                    time.sleep(.005)
            finally:
                try:inbox.unlink(missing_ok=True)
                except OSError:pass
            with guard:outcome['source_holds']=dict(gate_counts)
        with guard:
            if outcome['signed_simulations']:
                outcome['status']='SIM_OBSERVED_MINOUT_CERTIFICATION_PENDING'
            elif outcome['native_unsigned']:
                outcome['status']='NATIVE_UNSIGNED_PREPARED_NO_SIGNED_SIM' if not signed_sim else 'HOLD_NO_SUCCESSFUL_SIGNED_SIM'
            elif outcome['matching_events']:
                outcome['status']='HOLD_NATIVE_PREPARATION_NOT_COMPLETED'
            else:outcome['status']='HOLD_NO_NEW_FRESH_V8_MATCHING_SCANNER_EVENT'
    except Exception as exc:
        outcome['status']='HOLD_'+hold_code(exc)
    finally:
        stop.set()
        if worker is not None:worker.join(timeout=2)
        if db is not None:
            try:db.close()
            except Exception:pass
        outcome['candidate_holds']=dict(counts)
        outcome['observed_nominated_sizes']=sorted(selected)
        outcome['simulation_transaction_signed']=bool(outcome['signed_simulations'])
        outcome['execution_signing_authorized']=False
        outcome['protected_min_out_certified']=False
        outcome['production_execution_certified']=False
        outcome['eligible_to_broadcast']=False
        save(outcome)
        print('[FINAL_BOSS_V9_SIMULATION]',json.dumps(outcome,sort_keys=True),flush=True)
        print('[REPORT]',OUT.relative_to(ROOT),flush=True)
    return 0 if outcome['status'] in ('SIM_OBSERVED_MINOUT_CERTIFICATION_PENDING','NATIVE_UNSIGNED_PREPARED_NO_SIGNED_SIM') else 2

def tests():
    import tempfile
    from unittest.mock import patch
    token='a'*40;pump='b'*40;dlmm='c'*40
    row={'token':token,'pump_pool':pump,'meteora_pool':dlmm,
       'onchain_pool_binding_verified':True,'pool_program_owners_verified':True,
       'pump_witness':{'reason':'PUMP_POOL_HEADER_VERIFIED','pair_mints_match':True},
       'dlmm_witness':{'reason':'DLMM_POOL_MINTS_VERIFIED','pair_mints_match':True,'status':0,'bin_step':20},
       'mint_check':'HOLD_TOKEN2022_FULL_NATIVE_EXECUTION_SIM_REQUIRED',
       'token2022_audit':{'status':'HOLD_TOKEN2022_FULL_NATIVE_EXECUTION_SIM_REQUIRED',
          'mint_authority_absent':True,'freeze_authority_absent':True,
          'hazardous_extensions':[],'unknown_extensions':[],
          'extensions':['metadataPointer','tokenMetadata']}}
    assert exact_triple(row)==(token,pump,dlmm)
    assert review_mint(row)=='TOKEN2022_METADATA_ONLY_SIM_REVIEW'
    x=dict(row,token2022_audit=dict(row['token2022_audit'],extensions=['transferHook']))
    try:review_mint(x)
    except Hold:pass
    else:raise AssertionError('unsafe extension accepted')
    x=dict(row,dlmm_witness=dict(row['dlmm_witness'],status=1))
    try:exact_triple(x)
    except Hold:pass
    else:raise AssertionError('disabled pool accepted')
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'report.json';r={'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V8','source':'FRESH_MRIYA_INDEXED_POOL_PROSPECTS_UNTRUSTED',
           'observed_unix':1000.,'scanner_modified':False,'read_only':True,'execution_authority':False,'prospects':[row]}
        path.write_text(json.dumps(r));doc=load_v8(1040.,path)
        cand,holds=candidates(doc);assert len(cand)==1 and not holds
        try:load_v8(1200.,path)
        except Hold:pass
        else:raise AssertionError('stale V8 accepted')
    class MockRpc:
        def __call__(self,method,args):
            assert method=='getMultipleAccounts'
            return {'context':{'slot':900},'value':[{'owner':TOKEN2022,'data':{'parsed':{'type':'mint','info':{
              'isInitialized':True,'mintAuthority':None,'freezeAuthority':None,
              'extensions':[{'extension':'metadataPointer'},{'extension':'tokenMetadata'}]}}}}]}
    assert recheck_mint(MockRpc(),token,899,'TOKEN2022_METADATA_ONLY_SIM_REVIEW')['authority_absent']
    try:recheck_mint(MockRpc(),token,1000,'TOKEN2022_METADATA_ONLY_SIM_REVIEW')
    except Hold:pass
    else:raise AssertionError('stale mint slot accepted')
    ev={'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1','direction':'PUMP_TO_METEORA',
       'size_lamports':55_000_000,'scanner_gross_lamports_hint':2000,'token':token,'pump_pool':pump,'meteora_pool':dlmm}
    assert same_event(ev,(token,pump,dlmm))==55_000_000
    assert len(GRID)==19 and GRID[0]==10_000_000 and GRID[-1]==100_000_000
    assert conservation({'transfer_fee_lamports':0,'rent_cost_lamports':10,
      'tip_lamports':5,'residue_lamports':0,'adverse_buffer_lamports':50},
      {'fee_adjusted_conservative_sim_net_lamports':100,'token_residue_raw':0})==35
    try:conservation({'transfer_fee_lamports':0,'rent_cost_lamports':10,
      'tip_lamports':5,'residue_lamports':0,'adverse_buffer_lamports':100},
      {'fee_adjusted_conservative_sim_net_lamports':100,'token_residue_raw':0})
    except Hold:pass
    else:raise AssertionError('nonpositive sim accepted')
    assert hold_code(RuntimeError('https://rpc/api-key=SECRET'))=='RUNTIMEERROR'
    print('[PASS] FINAL_BOSS_V9 V8 binding, T22 metadata-only review, 19 sizes, live source-only, mint RPC recheck, fee/residue fails closed')
    print('[SCOPE] Deterministic fixtures only; no scanner mutation, no broadcast; live signed simulation unclaimed')

def main():
    ap=argparse.ArgumentParser()
    act=ap.add_mutually_exclusive_group(required=True)
    act.add_argument('--test',action='store_true')
    act.add_argument('--audit',action='store_true')
    act.add_argument('--observe',action='store_true')
    ap.add_argument('--seconds',type=int,default=90)
    ap.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',WALLET_DEFAULT))
    ap.add_argument('--signed-sim',action='store_true',help='Explicit opt-in: signs transaction in memory, calls only simulateTransaction')
    a=ap.parse_args()
    if a.test:tests();return 0
    if a.audit:return audit()
    return observe(a.seconds,a.wallet,a.signed_sim)
if __name__=='__main__':raise SystemExit(main())

