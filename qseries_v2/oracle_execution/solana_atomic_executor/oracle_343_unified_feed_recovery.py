"""ORACLE-338..342 UNIFIED SHADOW ENGINE. One executable, five audited gates.
Consumes frozen ORACLE-322 events; unchanged ORACLE-333 WS full-account witness;
ORACLE-337 exact official SDK pricing and single-context bank confirmation;
ORACLE-331 strict native two-leg assembly. No private key, signing, broadcast or trades.
Gate outputs reflect physical evidence, not an assertion of production readiness.
"""
from __future__ import annotations
import argparse,base64,copy,hashlib,json,os,pathlib,sqlite3,subprocess,sys,time,unittest
from collections import Counter
from urllib.parse import urlsplit

ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
BUS=ROOT/'candidate_bus.sqlite3'
STATUS=ROOT/'oracle_343_shadow_status.json'
LEDGER=ROOT/'oracle_343_shadow_evidence.jsonl'
REPORT=ROOT/'oracle_343_shadow_report.json'
LOCK=ROOT/'oracle_343_shadow.lock'
CANARY=10_000_000
SIZES=tuple(range(CANARY,100_000_001,5_000_000))
DIRECTIONS=('PUMP_TO_METEORA','METEORA_TO_PUMP')
MAX_PACK=1232


def emit(name,obj):
    print('['+name+'] '+json.dumps(obj,sort_keys=True,default=str),flush=True)

def redacted(error):
    import re
    s=type(error).__name__+':'+str(error)
    s=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',s)
    s=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',s)
    return s[:220]

def invariant(cond,reason):
    if not cond:raise ValueError(reason)

def atomic_write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(value,sort_keys=True,indent=2,default=str),encoding='utf-8')
    os.replace(tmp,path)

def hold(stage,why,**extra):
    return dict(stage=stage,gate='HOLD_'+why,verified=False,**extra)

def quote_id(row):
    return (str(row['token']),str(row['pump_pool']),str(row['meteora_pool']),
            str(row['direction']),int(row['size_lamports']))

def parse_nomination(r):
    fields=('id','producer','token','pump_pool','meteora_pool','direction','size_lamports',
            'gross_lamports','slot','generation','created_ns','source')
    if not isinstance(r,dict):r=dict(zip(fields,r))
    out={k:r[k] for k in fields}
    for k in ('id','size_lamports','gross_lamports','slot','created_ns'):
        out[k]=int(out[k])
    invariant(out['size_lamports'] in SIZES,'NOM_SIZE_NOT_ALLOWED')
    invariant(out['direction'] in DIRECTIONS,'NOM_DIRECTION_BAD')
    invariant(out['gross_lamports']>0,'NOM_NOT_GROSS_POSITIVE')
    invariant(out['slot']>0 and out['id']>0,'NOM_UNBOUND_SLOT')
    invariant(all(out[k] for k in ('token','pump_pool','meteora_pool')),'NOM_ROUTE_INCOMPLETE')
    return out

def nomination_age(row,now_ns,ttl_ms=1100):
    age=(now_ns-int(row['created_ns']))/1e6
    return age if 0<=age<=ttl_ms else None

def scanner_health(db,now_ns):
    r=db.execute("SELECT unix_ns,admitted,emitted,producer,epoch FROM heartbeat WHERE name='scanner'").fetchone()
    if not r:return dict(ok=False,reason='NO_SCANNER_HEARTBEAT')
    age=(now_ns-int(r[0]))/1e9
    return dict(ok=(0<=age<=15),age_s=round(age,3),admitted=r[1],emitted=r[2],producer=r[3],epoch=r[4])

def next_nominations(db,cursor,limit=512):
    rows=db.execute('SELECT id,producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source FROM events WHERE id>? ORDER BY id ASC LIMIT ?',
                    (int(cursor),int(limit))).fetchall()
    return rows,(max([cursor]+[int(r[0]) for r in rows]))

def coalesce(rows):
    found={}
    for v in rows:
        try:r=parse_nomination(v)
        except (ValueError,KeyError,TypeError):continue
        key=quote_id(r);old=found.get(key)
        if old is None or (r['slot'],r['created_ns'],r['id'])>(old['slot'],old['created_ns'],old['id']):found[key]=r
    return sorted(found.values(),key=lambda r:(r['created_ns'],r['gross_lamports']),reverse=True)

def inventory_match(nom,catalog,all_pairs):
    identity=(nom['token'],nom['pump_pool'],nom['meteora_pool'])
    if identity not in {(p['token'],p['pump_pool'],p['meteora_pool']) for p in all_pairs}:
        return 'NOT_IN_FROZEN_INVENTORY'
    item=catalog.get(nom['token'])
    if not item:return 'NO_WITNESS_FOR_SCANNER_PAIR'
    if (item['token'],item['pump_pool'],item['meteora_pool'])!=identity:
        return 'WITNESS_POOL_IDENTITY_DIFFERENT'
    if not item['discovery_complete'] or item['bin_total']!=item['bin_selected']:
        return 'BIN_CATALOG_INCOMPLETE'
    return None

def compare_nomination(nom,local,now_ns):
    age=nomination_age(nom,now_ns)
    if age is None:return hold('338','NOMINATION_EXPIRED')
    exact=local.get('requested_exact')
    if not exact:return hold('338','DIRECTION_SIZE_UNPRICED',scanner_slot=nom['slot'])
    delta=int(exact['gross_lamports'])-nom['gross_lamports']
    return dict(stage='338',verified=True,scanner_slot=nom['slot'],
                scanner_gross=nom['gross_lamports'],executor_gross=int(exact['gross_lamports']),
                delta_lamports=delta,nomination_age_ms=round(age,3),
                direction=nom['direction'],size_lamports=nom['size_lamports'],
                same_pool_identity=True,same_bank_snapshot_proven=False,
                gate='REPRICED_POSITIVE' if exact['gross_lamports']>0 else 'REPRICED_NONPOSITIVE')

def quote_hot(nom,catalog,latest,watches,decimals,start_ns,bridge,core,decoder,q18):
    snap,lineage=bridge.prepare_snapshot(catalog,latest,watches,decimals,start_ns,core,decoder)
    age=lineage['last_price_event_age_ms']
    if age<0 or age>750:raise ValueError('HOT_ACCOUNT_EVENT_TOO_OLD')
    want=(nom['direction'],nom['size_lamports']/1e9)
    # EXACT SAME token, direction, original size. No linearized quote substitution.
    quoted=bridge.directional_ladder(snap,q18,core,requested=want)
    return snap,lineage,quoted

def bank_confirm(nom,cat,latest,watches,decimals,start_ns,bridge,core,decoder,q18,rpc_url,rpc_fn=None,clock=None):
    clock=clock or time.time_ns
    keys,min_slot=bridge.bank_account_keys(nom['token'],watches,latest)
    min_slot=max(int(min_slot),int(nom['slot']))
    if rpc_fn is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
        rpc_fn=witness.rpc
    start=clock()
    response=rpc_fn(rpc_url,'getMultipleAccounts',
      [keys,{'encoding':'base64','commitment':'processed','minContextSlot':min_slot}],Counter(),retries=1)
    rows,slot=bridge.bank_rows(response,keys,min_slot,start)
    received=clock()
    snap,lin=bridge.prepare_snapshot(cat,rows,watches,decimals,start_ns,core,decoder)
    invariant(lin['slot_min']==slot and lin['slot_max']==slot,'BANK_NOT_ONE_CONTEXT')
    quoted=bridge.directional_ladder(snap,q18,core,requested=(nom['direction'],nom['size_lamports']/1e9))
    exact=quoted.get('requested_exact')
    now=clock()
    # One response bank context, but changes may occur AFTER read; always revalidate later.
    outcome=dict(stage='340',bank_slot=slot,scanner_slot=nom['slot'],account_count=len(keys),
                 confirmation_ms=round((now-start)/1e6,2),rpc_ms=round((received-start)/1e6,2),
                 quote_ms=quoted['quote_ms'],bank_read_age_ms=round((now-received)/1e6,2),
                 direction=nom['direction'],size_lamports=nom['size_lamports'],
                 bank_gross=int(exact['gross_lamports']) if exact else None,
                 single_context_verified=True,fee_net_certified=False,
                 signing=False,broadcast=False)
    if not exact:return dict(outcome,gate='HOLD_BANK_DIRECTION_UNPRICED'),None,None
    if int(exact['gross_lamports'])<=0:return dict(outcome,gate='HOLD_BANK_GROSS_NONPOSITIVE'),None,None
    if (now-received)/1e6>750:return dict(outcome,gate='HOLD_BANK_REQUOTE_EXPIRED'),None,None
    outcome['gate']='BANK_GROSS_POSITIVE_PENDING_NATIVE_AND_FEES'
    return outcome,snap,exact

def rpc_bank_without_ws(nom,catalog,watches,decimals,bridge,core,decoder,q18,rpc_url,rpc_fn=None,clock=None):
    """Non-trading shadow fallback. No witness state bytes enter this bank snapshot.
    Witness watch role identities must be discovered first; no fabricated addresses.
    """
    clock=clock or time.time_ns
    invariant(catalog['discovery_complete'] and catalog['bin_selected']==catalog['bin_total'],
              'RPC_CATALOG_INCOMPLETE')
    keys=sorted(k for k,labels in watches.items()
                if any(isinstance(v,(list,tuple)) and len(v)==2 and v[0]==nom['token'] for v in labels))
    invariant(6<=len(keys)<=100 and len(set(keys))==len(keys),'RPC_WATCH_ROLE_SET_INVALID')
    role_names=[v[1] for k in keys for v in watches[k] if v[0]==nom['token']]
    invariant(len(role_names)==len(set(role_names)),'RPC_WATCH_ROLE_DUPLICATE')
    required={'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT',
              'DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}
    invariant(required.issubset(role_names),'RPC_REQUIRED_ROLE_MISSING')
    if rpc_fn is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
        rpc_fn=witness.rpc
    begin=clock()
    response=rpc_fn(rpc_url,'getMultipleAccounts',
        [keys,{'encoding':'base64','commitment':'processed','minContextSlot':int(nom['slot'])}],
        Counter(),retries=1)
    # Exact ordered data and one bank context, never mixed with previous WebSocket rows.
    rows,slot=bridge.bank_rows(response,keys,int(nom['slot']),begin)
    after_rpc=clock()
    snap,lin=bridge.prepare_snapshot(catalog,rows,watches,decimals,begin-1,core,decoder)
    invariant(lin['slot_min']==slot and lin['slot_max']==slot,'RPC_SNAPSHOT_NOT_SINGLE_BANK')
    quote=bridge.directional_ladder(snap,q18,core,
                  requested=(nom['direction'],nom['size_lamports']/1e9))
    exact=quote.get('requested_exact')
    invariant(exact is not None,'RPC_DIRECTION_SIZE_UNPRICED')
    now=clock()
    elapsed_ms=(now-after_rpc)/1e6
    outcome=dict(stage='340',source='BOUNDED_RPC_ONE_BANK_WS_UNAVAILABLE',
                 gate=('BANK_GROSS_POSITIVE_PENDING_NATIVE_AND_FEES' if int(exact['gross_lamports'])>0
                       else 'HOLD_BANK_GROSS_NONPOSITIVE'),
                 bank_slot=slot,scanner_slot=int(nom['slot']),account_count=len(keys),
                 quote_ms=quote['quote_ms'],confirmation_ms=round((now-begin)/1e6,3),
                 bank_read_age_ms=round(elapsed_ms,3),
                 bank_gross=int(exact['gross_lamports']),
                 single_context_verified=True,fee_net_certified=False,signing=False,broadcast=False)
    if elapsed_ms>750:outcome['gate']='HOLD_RPC_SNAPSHOT_TOO_OLD'
    return outcome,snap,exact


def native_forward_quote(snap,size,core,q18):
    # Reconstruct the documented original q18 opportunity schema from bank bytes;
    # do NOT call the both-directions-together function that can mask a valid P2M.
    start=int(size);pb=q18.worker().buy(snap,start)
    gross=int(pb['baseOut']);received=int(q18.token_net(snap['token'],gross))
    invariant(gross>0 and received>0 and int(pb['maxQuote'])>0,'PUMP_SDK_INVALID_BOUNDS')
    mq=core.dlmm_quote_snapshot(snap,received,snap['token'])
    invariant(int(mq['raw_out'])>0,'METEORA_BANK_QUOTE_NOT_COMPLETE')
    net=int(mq['raw_out'])-start
    invariant(net>0,'NATIVE_ROUTE_LOST_POSITIVITY')
    return dict(token=snap['token'],pump_pool=snap['pump_pool'],meteora=snap['meteora'],
       start=start,size_sol=start/1e9,direction='PUMP_TO_METEORA',mq=mq,
       pump_base_out_gross=gross,pump_base_out_net=received,pump_max_quote=int(pb['maxQuote']),
       local_end=int(mq['raw_out']),local_net=net,local_bps=net/start*10000,pump_model='EXACT_PUMPSWAP_SDK')

def immutable_packet_gate(packet,limit=MAX_PACK):
    invariant(isinstance(packet,(bytes,bytearray)),'PACKET_NOT_BYTES')
    invariant(0<len(packet)<=limit,'ATOMIC_PACKET_OVERSIZE')
    return len(packet)

def strict_sim(native,bank_snap,nom,bank_exact,bank_slot,core,q18,max_arrays_variants=4):
    """Reuse original native builder, strictly preserving both economic bounds.
    Only PHYSICAL mainnet unsigned simulation. Never branch into relaxed-bound probes.
    Native warm is for templates, NOT the market snapshot or quote.
    """
    evidence=dict(stage='341',native_mode='EXACT_BANK_SNAPSHOT',bank_slot=int(bank_slot),
                  signing=False,broadcast=False,strict_bounds_preserved=True,
                  trade_ready=False,signed_simulation_certified=False)
    if nom['direction']=='METEORA_TO_PUMP':
        return dict(evidence,gate='HOLD_REVERSE_NATIVE_ASSEMBLER_NOT_CERTIFIED')
    if native is None:return dict(evidence,gate='HOLD_NATIVE_PREPARATION_UNAVAILABLE')
    try:
        from solders.transaction import VersionedTransaction
        from solders.message import to_bytes_versioned
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_executor_live as legacy
        if nom['token'] not in native.template_bank:
            # Single template hydration per token; never use hydrated prices for route.
            native.rehydrate(nom['token'],nom['pump_pool'],nom['meteora_pool'])
        native.activate_templates(nom['token'],nom['pump_pool'],nom['meteora_pool'])
        opportunity=native_forward_quote(bank_snap,nom['size_lamports'],core,q18)
        delta=abs(int(opportunity['local_net'])-int(bank_exact['gross_lamports']))
        invariant(delta<=2,'BANK_TO_NATIVE_QUOTE_MISMATCH')
        route=native.rt.same_snapshot_route(native.wallet,bank_snap,opportunity)
        variants=[x for x in native.q87.repaired_candidates(route) if x.get('name')=='FULL']
        invariant(variants,'NATIVE_FULL_ROUTE_MISSING')
        cand=variants[0]
        original=copy.deepcopy(cand['instructions'])
        idx=[i for i,x in enumerate(original) if x.get('programId')==native.q87.c.DLMM]
        invariant(len(idx)==1,'NATIVE_DLMM_INSTRUCTION_COUNT')
        choices=legacy.swap2_array_variants(original[idx[0]],native.rt.METEORA_TEMPLATES[nom['token']],
                                              native.q87.c.DLMM,limit=min(max_arrays_variants,4))
        invariant(bool(choices),'NATIVE_SWAP2_VARIANTS_MISSING')
        bh=native.q87.c.rpc('getLatestBlockhash',[{'commitment':'processed'}])['value']['blockhash']
        attempted=[]
        for patched,meta in choices:
            ix=copy.deepcopy(original);ix[idx[0]]=patched
            native_mutex=native.native_mutex
            with native_mutex:
                alt_fn=native.q87.c.alt_accounts
                try:
                    native.q87.c.alt_accounts=lambda keys:{k:native.cache[k] for k in keys}
                    comp=native.q87.compile_candidate(native.wallet,ix,[native.alts],bh)
                finally:native.q87.c.alt_accounts=alt_fn
            if not isinstance(comp,dict) or not comp.get('ok'):
                attempted.append({'arrays':meta['bin_arrays'],'hold':'ALT_COMPILE_REJECT'});continue
            raw=comp['unsigned'];nbytes=immutable_packet_gate(raw)
            tx=VersionedTransaction.from_bytes(raw)
            msg=base64.b64encode(to_bytes_versioned(tx.message)).decode()
            # Chain-estimated base+priority fee on the ACTUAL compiled message.
            fees=native.q87.c.rpc('getFeeForMessage',[msg,{'commitment':'processed','minContextSlot':bank_slot}])
            fee=fees.get('value') if isinstance(fees,dict) else None
            if not isinstance(fee,int) or fee<=0:
                return dict(evidence,gate='HOLD_ACTUAL_MESSAGE_FEE_UNAVAILABLE',packet_bytes=nbytes)
            if bank_exact['gross_lamports']<=fee:
                return dict(evidence,gate='HOLD_FEE_ESTIMATE_EXCEEDS_GROSS',fee_lamports=fee,
                           bank_gross=bank_exact['gross_lamports'],packet_bytes=nbytes)
            b64=base64.b64encode(raw).decode()
            rsp=native.q87.c.rpc('simulateTransaction',[b64,{'encoding':'base64','sigVerify':False,
                          'commitment':'processed','minContextSlot':bank_slot,'replaceRecentBlockhash':False}])
            val=rsp.get('value') if isinstance(rsp,dict) else None
            invariant(isinstance(val,dict),'SIM_RESPONSE_MISSING_VALUE')
            err=val.get('err');logs=val.get('logs') or []
            attempt={'arrays':meta['bin_arrays'],'packet_bytes':nbytes,'fee_lamports':fee,
                     'sim_error':err,'units':val.get('unitsConsumed'),'simulation_slot':(rsp.get('context') or {}).get('slot')}
            attempted.append(attempt)
            if err is None:
                # NOTE: The snapshot's local quote is NOT the post-simulation wallet delta;
                # do not certify profit or send even when sim succeeds.
                return dict(evidence,gate='UNSIGNED_STRICT_ATOMIC_SIM_PASS_PENDING_BALANCE_RECONCILIATION',
                            packet_bytes=nbytes,fee_lamports=fee,
                            bank_gross=bank_exact['gross_lamports'],
                            pre_residue_estimate=bank_exact['gross_lamports']-fee,
                            simulated_units=val.get('unitsConsumed'),
                            simulation_slot=attempt['simulation_slot'],
                            all_legs_strict_sim_pass=True,actual_wallet_delta_verified=False,
                            all_fees_and_residue_certified=False,attempts=attempted)
            # Only the exact 3005 missing keys may try a wider official pool bin set.
            if not legacy.is_bin_array_3005({'err':err,'logs':logs}):break
        return dict(evidence,gate='HOLD_STRICT_ATOMIC_SIMULATION',attempts=attempted,
                    error_logs_tail=[str(x)[:170] for x in (logs[-5:] if isinstance(logs,list) else [])])
    except Exception as e:
        return dict(evidence,gate='HOLD_NATIVE_'+redacted(e))

def evidence_summary(seq,nom,cmp,bank,native):
    return dict(build='ORACLE343_UNIFIED_RECOVERY',event_id=seq,token=nom['token'],
        direction=nom['direction'],size_lamports=nom['size_lamports'],
        scanner_gross=nom['gross_lamports'],scanner_slot=nom['slot'],
        stage_338=cmp,stage_339={'gate':'HOT_WITNESS_QUOTED' if cmp.get('verified') else 'HOT_HOLD',
                                'origin':'UNCHANGED_ORACLE333_WS'},
        stage_340=bank,stage_341=native,
        stage_342=dict(gate='SHADOW_CYCLE_RECORDED',
                      ready_for_funded_execution=False,
                      signer_not_tested=True,balance_reconciliation_not_tested=True,
                      strict_sim_pass=bool(native and native.get('all_legs_strict_sim_pass'))),
        execution_authority=False,signing=False,broadcast=False,money_moved=False)

def report_status(stats,sc,seen,token_status,last):
    return dict(build='ORACLE343_UNIFIED_RECOVERY',mode='CONTINUOUS_SHADOW',scanner=sc,
                stats=dict(stats),candidate_cursor=seen,monitored_tokens=token_status,
                recent_evidence=last[-6:],production_cutover=False,
                signing=False,broadcast=False,execution_authority=False)

def run(seconds=180,pair_count=6,max_arrays=12,max_bank=8,cooldown=3.,poll_ms=70,
        nomination_ttl_ms=1100,attempt_native=True):
    invariant(not os.getenv('QSB_SOLANA_PRIVATE_KEY'),'SHADOW_MUST_NOT_HAVE_PRIVATE_KEY')
    invariant(os.getenv('QSB_LIVE_ARM','NO')=='NO','SHADOW_MUST_BE_DISARMED')
    invariant(os.getenv('SOLANA_RPC_URL','').startswith('https://') and os.getenv('SOLANA_WS_URL','').startswith('wss://'),
              'HTTPS_AND_WSS_ENDPOINTS_REQUIRED')
    invariant(BUS.exists(),'FROZEN_SCANNER_BUS_NOT_FOUND')
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
    pairs=witness.inventory_pairs(pair_count)
    decimals=bridge.mint_metadata(os.environ['SOLANA_RPC_URL'],[p['token'] for p in pairs])
    q23.install_hot_token_net();native=None
    if attempt_native:
        try:
            from qseries_v2.oracle_execution.solana_atomic_executor import boss_executor_live as legacy
            wallet=os.getenv('QSB_SOLANA_WALLET','')
            alts=[x.strip() for x in os.getenv('QSB_SOLANA_ALT_ADDRESSES',legacy.DEFAULT_ALT).replace(';',',').split(',') if x.strip()]
            if wallet and alts:
                native=legacy.Native(wallet,alts);native.init()
            else:emit('ORACLE343_NATIVE_HOLD',{'reason':'PUBLIC_WALLET_OR_ALT_MISSING'})
        except Exception as e:emit('ORACLE343_NATIVE_HOLD',{'reason':redacted(e)})
    ROOT.mkdir(parents=True,exist_ok=True)
    try:lock_fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise RuntimeError('UNIFIED_SHADOW_ALREADY_RUNNING')
    os.close(lock_fd)
    db=None;child=None;stats=Counter();recent=[];cursor=0;last_bank=0.;latest_seen={}
    start_ns=time.time_ns();end=time.monotonic()+max(30,int(seconds));last_status=0.;last_witness_read=0.;
    catalogs={};latest={};watches={}
    try:
        db=sqlite3.connect(BUS.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)
        db.execute('PRAGMA query_only=ON')
        cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
        child=subprocess.Popen([sys.executable,'-m',witness.__name__,'--run','--seconds',str(max(30,seconds)),
                '--pairs',str(pair_count),'--max-arrays-per-pair',str(max_arrays)],env=os.environ.copy())
        # Warm the same SDK/token-fee workers already used in ORACLE-336.
        # One bounded warm per selected pair; no quote-time REST hydration.
        warmed=set()
        for pair in pairs:
            try:
                q23.worker().warm(pair['token'])
                q18.worker().warm(pair['pump_pool'])
                warmed.add(pair['token'])
            except Exception as e:
                emit('ORACLE343_SDK_WARM_HOLD',{'token':pair['token'][:12],'reason':redacted(e)})
        try:q23.worker().refresh_epoch()
        except Exception as e:emit('ORACLE343_TOKEN_EPOCH_HOLD',{'reason':redacted(e)})
        emit('ORACLE343_START',dict(scanner='ORACLE322_FROZEN',seen_after_event_id=cursor,
             pairs=len(pairs),witness_pid=child.pid,sizes=19,directions=2,
             native_available=bool(native),signing=False,broadcast=False))
        with LEDGER.open('a',encoding='utf-8') as file:
            while time.monotonic()<end and child.poll() is None:
                now=time.monotonic();wall=time.time_ns()
                sc=scanner_health(db,wall)
                if now-last_witness_read>.18:
                    last_witness_read=now
                    # Catalog and account identity may be available even while the WS
                    # handshake is rate-limited. Never treat its stale bytes as fresh.
                    try:catalogs,latest,watches=bridge.read_state()
                    except (OSError,ValueError,sqlite3.Error):stats['witness_db_holds']+=1
                if not sc['ok']:
                    stats['scanner_heartbeat_holds']+=1
                    time.sleep(poll_ms/1000);continue
                rows,cursor=next_nominations(db,cursor)
                if rows:stats['scanner_nominations_seen']+=len(rows)
                for nom in coalesce(rows):
                    stats['coalesced_candidates']+=1
                    if nomination_age(nom,wall,nomination_ttl_ms) is None:
                        stats['expired_nominations']+=1;continue
                    issue=inventory_match(nom,catalogs,pairs)
                    if issue is None and nom['token'] not in warmed:issue='SDK_POOL_NOT_WARMED'
                    if issue:
                        stats['hold_'+issue]+=1;continue
                    # WS outage fallback: eligible live scanner nominations receive a
                    # rate-limited ONE-bank-context HTTP reprice, not reused stale bytes.
                    if not bridge.live_witness_status()[0]:
                        stats['ws_unavailable_candidates']+=1
                        if now-last_bank<float(cooldown) or stats['bank_requotes']>=int(max_bank):
                            stats['rpc_fallback_rate_or_budget_hold']+=1
                            continue
                        last_bank=now;stats['bank_requotes']+=1
                        stats['rpc_fallback_probes']+=1
                        try:
                            bank,bank_snap,exact=rpc_bank_without_ws(nom,catalogs[nom['token']],
                                watches,decimals,bridge,core,decoder,q18,os.environ['SOLANA_RPC_URL'])
                            cmp=dict(stage='338',verified=True,gate='RPC_BANK_REPRICED',
                                scanner_slot=nom['slot'],bank_slot=bank['bank_slot'],
                                scanner_gross=nom['gross_lamports'],
                                executor_gross=bank['bank_gross'],
                                delta_lamports=bank['bank_gross']-nom['gross_lamports'],
                                origin='BANK_FALLBACK_NOT_WS_HOT')
                        except Exception as e:
                            bank=hold('340','BANK_FALLBACK_'+redacted(e));bank_snap=None;exact=None
                            cmp=hold('338','WS_DISABLED_BANK_FAILED')
                            stats['rpc_fallback_holds']+=1
                        physical=hold('341','BANK_NOT_ADMITTED')
                        if exact and bank['gate']=='BANK_GROSS_POSITIVE_PENDING_NATIVE_AND_FEES':
                            stats['bank_positives']+=1
                            physical=strict_sim(native,bank_snap,nom,exact,bank['bank_slot'],core,q18)
                            stats['native_attempts']+=1
                            if physical.get('all_legs_strict_sim_pass'):
                                stats['strict_unsigned_sim_passes']+=1
                        ev=evidence_summary(nom['id'],nom,cmp,bank,physical)
                        ev['stage_339']={'gate':'WS_UNAVAILABLE_RPC_FALLBACK',
                                         'hot_websocket_certified':False,
                                         'source':'SINGLE_BANK_RPC_SHADOW_ONLY'}
                        file.write(json.dumps(ev,sort_keys=True,default=str)+'\n');file.flush()
                        recent.append(dict(id=nom['id'],token=nom['token'][:12],
                          gate=physical['gate'] if exact else bank['gate']))
                        emit('ORACLE343_BANK_FALLBACK_RESULT',ev)
                        if len(recent)>60:recent=recent[-30:]
                        continue
                    try:
                        snap,lin,local=quote_hot(nom,catalogs[nom['token']],latest,watches,
                                          decimals,start_ns,bridge,core,decoder,q18)
                        cmp=compare_nomination(nom,local,time.time_ns())
                        cmp['hot_lineage']=lin
                    except Exception as e:
                        stats['hot_quote_holds']+=1
                        cmp=hold('338','HOT_'+redacted(e));continue
                    if cmp['gate']!='REPRICED_POSITIVE':
                        stats['scanner_positive_executor_nonpositive']+=1
                        # A negative comparison is still valuable measured evidence.
                        ev=evidence_summary(nom['id'],nom,cmp,hold('340','NOT_POSITIVE'),hold('341','NOT_ADMITTED'))
                        file.write(json.dumps(ev,sort_keys=True,default=str)+'\n');file.flush()
                        recent.append(dict(id=nom['id'],token=nom['token'][:12],gate=cmp['gate']))
                        continue
                    stats['hot_positive']+=1
                    if now-last_bank<float(cooldown) or stats['bank_requotes']>=int(max_bank):
                        stats['bank_rate_holds']+=1;continue
                    last_bank=now;stats['bank_requotes']+=1
                    try:
                        bank,bank_snap,exact=bank_confirm(nom,catalogs[nom['token']],latest,watches,
                            decimals,start_ns,bridge,core,decoder,q18,os.environ['SOLANA_RPC_URL'])
                    except Exception as e:
                        bank=hold('340','RPC_'+redacted(e));bank_snap=None;exact=None
                    physical=hold('341','BANK_NOT_ADMITTED')
                    if exact and bank['gate']=='BANK_GROSS_POSITIVE_PENDING_NATIVE_AND_FEES':
                        stats['bank_positives']+=1
                        physical=strict_sim(native,bank_snap,nom,exact,bank['bank_slot'],core,q18)
                        stats['native_attempts']+=1
                        if physical.get('all_legs_strict_sim_pass'):stats['strict_unsigned_sim_passes']+=1
                    ev=evidence_summary(nom['id'],nom,cmp,bank,physical)
                    file.write(json.dumps(ev,sort_keys=True,default=str)+'\n');file.flush()
                    recent.append(dict(id=nom['id'],token=nom['token'][:12],
                         scanner_gross=nom['gross_lamports'],bank_gross=bank.get('bank_gross'),
                         gate=physical['gate'] if exact else bank['gate']))
                    emit('ORACLE343_SHADOW_RESULT',ev)
                    if len(recent)>60:recent=recent[-30:]
                if now-last_status>=5:
                    last_status=now
                    rpt=report_status(stats,sc,cursor,len(catalogs),recent)
                    atomic_write(STATUS,rpt);atomic_write(REPORT,rpt)
                    emit('ORACLE343_HEARTBEAT',dict(stats=dict(stats),scanner=sc,
                        bank_requotes=stats['bank_requotes'],strict_unsigned_sim_passes=stats['strict_unsigned_sim_passes'],
                        witness_tokens=len(catalogs),signing=False,broadcast=False))
                time.sleep(max(.02,poll_ms/1000))
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=7)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
        if db:db.close()
        for module in [locals().get('q18'),locals().get('q23')]:
            if module:
                try:
                    if getattr(module,'_worker',None):module._worker.close()
                except Exception:pass
        try:LOCK.unlink()
        except OSError:pass
    emit('ORACLE343_EXIT',dict(stats=dict(stats),mode='SHADOW_ONLY',funded_execution=False))
    return 0


def tests():
    class T(unittest.TestCase):
        def setUp(self):
            self.r=dict(id=12,producer='ORACLE322',token='T',pump_pool='P',meteora_pool='M',
                        direction='PUMP_TO_METEORA',size_lamports=CANARY,gross_lamports=100000,
                        slot=200,generation=1,created_ns=1000000000,source='SCANNER')
        def test_rpc_fallback_role_validation(self):
            class B:pass
            with self.assertRaisesRegex(ValueError,'RPC_CATALOG_INCOMPLETE'):
                rpc_bank_without_ws(self.r,dict(discovery_complete=False,bin_selected=1,bin_total=2),
                    {},{},B,None,None,None,'https://x')
        def test_rpc_fallback_no_fabricated_keys(self):
            class B:pass
            with self.assertRaisesRegex(ValueError,'RPC_WATCH_ROLE_SET_INVALID'):
                rpc_bank_without_ws(self.r,dict(discovery_complete=True,bin_selected=2,bin_total=2),
                    {},{},B,None,None,None,'https://x')
        def test_rpc_fallback_exact_one_context_negative(self):
            roles=['PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT',
                'DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE','DLMM_BIN_ARRAY_INDEX_0']
            watches={str(i):[['T',name]] for i,name in enumerate(roles)}
            class B:
                bank_rows=staticmethod(lambda resp,keys,slot,begin:({k:{'slot':250} for k in keys},250))
                prepare_snapshot=staticmethod(lambda *args:({'token':'T'},dict(slot_min=250,slot_max=250)))
                directional_ladder=staticmethod(lambda *args,**kwargs:dict(requested_exact={'gross_lamports':-10},quote_ms=1.))
            times=iter([100000,100010,100100])
            result,_,_=rpc_bank_without_ws(self.r,dict(discovery_complete=True,bin_selected=1,bin_total=1),
                watches,{},B,None,None,None,'https://x',lambda *x,**kw:{},lambda:next(times))
            self.assertEqual(result['gate'],'HOLD_BANK_GROSS_NONPOSITIVE')
            self.assertEqual(result['bank_slot'],250)
        def test_rpc_fallback_min_slot_is_scanner_slot(self):
            roles=['PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT',
                'DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE','DLMM_BIN_ARRAY_INDEX_0']
            watches={str(i):[['T',name]] for i,name in enumerate(roles)}
            class B:
                bank_rows=staticmethod(lambda resp,keys,slot,begin:({k:{'slot':250} for k in keys},250))
                prepare_snapshot=staticmethod(lambda *args:({'token':'T'},dict(slot_min=250,slot_max=250)))
                directional_ladder=staticmethod(lambda *args,**kwargs:dict(requested_exact={'gross_lamports':10},quote_ms=1.))
            def rpc(url,method,params,*args,**kwargs):
                self.assertEqual(params[1]['minContextSlot'],200)
                self.assertEqual(len(params[0]),7)
                return {}
            times=iter([100000,100010,100100])
            result,_,_=rpc_bank_without_ws(self.r,dict(discovery_complete=True,bin_selected=1,bin_total=1),
                watches,{},B,None,None,None,'https://x',rpc,lambda:next(times))
            self.assertEqual(result['gate'],'BANK_GROSS_POSITIVE_PENDING_NATIVE_AND_FEES')
        def test_grid(self):self.assertEqual((len(SIZES),SIZES[0],SIZES[-1]),(19,10000000,100000000))
        def test_directions(self):self.assertEqual(len(DIRECTIONS),2)
        def test_parse(self):self.assertEqual(quote_id(parse_nomination(self.r)),('T','P','M','PUMP_TO_METEORA',CANARY))
        def test_zero_gross(self):
            r=dict(self.r,gross_lamports=0)
            with self.assertRaises(ValueError):parse_nomination(r)
        def test_wrong_direction(self):
            r=dict(self.r,direction='OTHER')
            with self.assertRaises(ValueError):parse_nomination(r)
        def test_wrong_size(self):
            r=dict(self.r,size_lamports=11_000_000)
            with self.assertRaises(ValueError):parse_nomination(r)
        def test_expired(self):self.assertIsNone(nomination_age(self.r,2500000000))
        def test_fresh(self):self.assertEqual(nomination_age(self.r,1100000000),100.)
        def test_future(self):self.assertIsNone(nomination_age(self.r,999999999))
        def test_coalesce(self):
            older=dict(self.r,id=10,slot=199)
            self.assertEqual(coalesce([older,self.r])[0]['id'],12)
        def test_inventory_good(self):
            p=dict(token='T',pump_pool='P',meteora_pool='M')
            cat=dict(p,bin_total=2,bin_selected=2,discovery_complete=True)
            self.assertIsNone(inventory_match(self.r,{'T':cat},[p]))
        def test_inventory_drift(self):
            p=dict(token='T',pump_pool='P',meteora_pool='M')
            c=dict(p,meteora_pool='WRONG',bin_total=2,bin_selected=2,discovery_complete=True)
            self.assertEqual(inventory_match(self.r,{'T':c},[p]),'WITNESS_POOL_IDENTITY_DIFFERENT')
        def test_inventory_missing(self):
            p=dict(token='T',pump_pool='P',meteora_pool='M')
            self.assertEqual(inventory_match(self.r,{},[p]),'NO_WITNESS_FOR_SCANNER_PAIR')
        def test_catalog_capped(self):
            p=dict(token='T',pump_pool='P',meteora_pool='M')
            c=dict(p,bin_total=3,bin_selected=2,discovery_complete=False)
            self.assertEqual(inventory_match(self.r,{'T':c},[p]),'BIN_CATALOG_INCOMPLETE')
        def test_compare_positive(self):
            v=compare_nomination(self.r,dict(requested_exact=dict(gross_lamports=100001)),1100000000)
            self.assertEqual((v['gate'],v['delta_lamports']),('REPRICED_POSITIVE',1))
        def test_compare_negative(self):
            v=compare_nomination(self.r,dict(requested_exact=dict(gross_lamports=-1)),1100000000)
            self.assertEqual(v['gate'],'REPRICED_NONPOSITIVE')
        def test_compare_missing(self):
            self.assertEqual(compare_nomination(self.r,dict(requested_exact=None),1100000000)['gate'],'HOLD_DIRECTION_SIZE_UNPRICED')
        def test_packet_limit(self):self.assertEqual(immutable_packet_gate(b'x'*1232),1232)
        def test_packet_oversize(self):
            with self.assertRaises(ValueError):immutable_packet_gate(b'x'*1233)
        def test_packet_zero(self):
            with self.assertRaises(ValueError):immutable_packet_gate(b'')
        def test_native_reverse_hold(self):
            r=dict(self.r,direction='METEORA_TO_PUMP')
            self.assertEqual(strict_sim(None,{},r,{},250,None,None)['gate'],'HOLD_REVERSE_NATIVE_ASSEMBLER_NOT_CERTIFIED')
        def test_native_absent_hold(self):
            self.assertEqual(strict_sim(None,{},self.r,{},250,None,None)['gate'],'HOLD_NATIVE_PREPARATION_UNAVAILABLE')
        def test_bank_context_happy(self):
            import types
            base=self.r
            class Bridge:
                @staticmethod
                def bank_account_keys(t,w,l):return ['a'],120
                @staticmethod
                def bank_rows(rep,keys,slot,start):return ({'a':{'slot':250}},250)
                @staticmethod
                def prepare_snapshot(*a):return ({'token':'T'},dict(slot_min=250,slot_max=250))
                @staticmethod
                def directional_ladder(*a,**kw):return dict(quote_ms=2.,requested_exact={'gross_lamports':10000})
            def rpc(url,method,params,stats,retries=1):
                self.assertEqual(params[1]['minContextSlot'],200)
                return {'context':{'slot':250},'value':[{}]}
            times=iter([1000000000,1000000001,1000001000])
            result,snap,exact=bank_confirm(base,{}, {},{}, {},0,Bridge,None,None,None,'https://example',rpc,lambda:next(times))
            self.assertTrue(result['single_context_verified']);self.assertIsNotNone(snap)
        def test_bank_negative_hold(self):
            class Bridge:
                bank_account_keys=lambda *x:(['a'],120)
                bank_rows=lambda *x:({'a':{}},250)
                prepare_snapshot=lambda *x:({},dict(slot_min=250,slot_max=250))
                directional_ladder=lambda *x,**kw:dict(quote_ms=1.,requested_exact={'gross_lamports':-5})
            result,_,_=bank_confirm(self.r,{}, {},{}, {},0,Bridge,None,None,None,'https://x',lambda *x,**kw:{},lambda:100)
            self.assertEqual(result['gate'],'HOLD_BANK_GROSS_NONPOSITIVE')
        def test_evidence_not_certified(self):
            r=evidence_summary(1,self.r,{'verified':True}, {},{'all_legs_strict_sim_pass':True})
            self.assertFalse(r['stage_342']['ready_for_funded_execution']);self.assertFalse(r['signing'])
        def test_status_not_cutover(self):self.assertFalse(report_status(Counter(),{},1,0,[])['production_cutover'])
        def test_secret_redaction(self):
            self.assertNotIn('SECRET123',redacted(ValueError('https://x/?api-key=SECRET123')))
        def test_source_has_no_send(self):
            import inspect
            s=inspect.getsource(strict_sim)+inspect.getsource(run)
            self.assertNotIn('sendTransaction',s)
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',inspect.getsource(strict_sim))
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    emit('ORACLE343_TEST_PASS' if result.wasSuccessful() else 'ORACLE343_TEST_FAIL',{'tests':result.testsRun})
    return 0 if result.wasSuccessful() else 1

def audit():
    emit('ORACLE343_AUDIT',dict(stages=['338_lineage','339_hot_ws','340_single_bank','341_native_unsigned','342_shadow_evidence'],
      unchanged_components=['ORACLE322_SCANNER','ORACLE331_NATIVE_EXECUTOR','ORACLE333_WS_WITNESS','ORACLE337_BANK_QUOTE'],
      actual_message_fee_rpc=True,strict_bounds_only=True,signed_simulation=False,
      reconciliation_certified=False,price_certification_claim=False,execution_authority=False,
      signing=False,broadcast=False,funded_cycle=False))
    return 0

def main():
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True)
    for name in ('run','test','audit'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--pairs',type=int,default=6)
    p.add_argument('--max-arrays-per-pair',type=int,default=12)
    p.add_argument('--max-bank-probes',type=int,default=8)
    p.add_argument('--bank-cooldown-seconds',type=float,default=3.)
    p.add_argument('--poll-ms',type=int,default=70)
    p.add_argument('--nomination-ttl-ms',type=int,default=1100)
    p.add_argument('--no-native',action='store_true')
    a=p.parse_args()
    if a.test:return tests()
    if a.audit:return audit()
    return run(a.seconds,a.pairs,a.max_arrays_per_pair,a.max_bank_probes,a.bank_cooldown_seconds,
               a.poll_ms,a.nomination_ttl_ms,not a.no_native)

if __name__=='__main__':raise SystemExit(main())
