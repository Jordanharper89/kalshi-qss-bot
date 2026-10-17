"""ORACLE-335: independent directional quote fault isolation and fair WS witness sweep.
Launches unchanged ORACLE333 WebSocket full-account witness in an isolated child,
reconstructs pool state from validated witnessed bytes, and quotes EACH DIRECTION
independently with the official PumpSwap SDK and Meteora DLMM quote engine.
A partial DLMM quote cannot suppress the opposite direction. No execution authority.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,pathlib,sqlite3,struct,subprocess,sys,time,traceback
from collections import Counter

ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
DB=ROOT/'executor_full_account_witness.sqlite3'
STATUS=ROOT/'executor_full_account_witness_status.json'
OUT=ROOT/'executor_ws_directional_quote_report.json'
INVENTORY=ROOT/'scanner_inventory.json'
GRID=tuple(round(0.010+i*0.005,3) for i in range(19))
TOKEN='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
SOL='So11111111111111111111111111111111111111112'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'


def emit(tag,value):print('['+tag+'] '+json.dumps(value,sort_keys=True,default=str),flush=True)
def safe(e):
    import re
    s=type(e).__name__+':'+str(e)
    s=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',s)
    s=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',s)
    return s[:180]


def base64_strict(x):
    if not isinstance(x,str):raise ValueError('ACCOUNT_ENCODING_NOT_STRING')
    return base64.b64decode(x,validate=True)


def mint_decimals(account_value):
    if not isinstance(account_value,dict) or account_value.get('owner') not in (TOKEN,TOKEN22):
        raise ValueError('MINT_OWNER_UNTRUSTED')
    item=account_value.get('data')
    if not isinstance(item,(list,tuple)) or len(item)!=2 or item[1]!='base64':raise ValueError('MINT_FORMAT_UNTRUSTED')
    raw=base64_strict(item[0])
    if len(raw)<82 or raw[45]!=1 or raw[44]>18:raise ValueError('MINT_DECIMALS_UNVERIFIED')
    return int(raw[44])


def mint_metadata(url,tokens):
    # One batched mint lookup at startup only. No per-quote REST requests.
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as w
    ordered=list(dict.fromkeys(tokens))
    r=w.rpc(url,'getMultipleAccounts',[ordered,{'encoding':'base64','commitment':'processed'}],Counter())
    if not isinstance(r,dict) or not isinstance(r.get('value'),list) or len(r['value'])!=len(ordered):
        raise ValueError('MINT_RPC_BATCH_UNVERIFIED')
    values={}
    for token,value in zip(ordered,r['value']):
        try:values[token]=mint_decimals(value)
        except Exception as e:emit('BOSS335_MINT_HOLD',{'token':token[:12],'reason':safe(e)})
    return values


def live_witness_status(now_ns=None):
    if not STATUS.exists():return False,'WITNESS_STATUS_ABSENT'
    age=(time.time_ns() if now_ns is None else now_ns)-STATUS.stat().st_mtime_ns
    if age<0 or age>12_000_000_000:return False,'WITNESS_HEARTBEAT_OLD'
    try:r=json.loads(STATUS.read_text(encoding='utf-8'))
    except (ValueError,OSError):return False,'WITNESS_STATUS_UNREADABLE'
    if not r.get('ws_connected'):return False,'WITNESS_NOT_CONNECTED'
    if r.get('subscription_errors') or r.get('missing_accounts'):return False,'WITNESS_SUBSCRIPTION_OR_ACCOUNT_HOLD'
    return True,'WITNESS_CONNECTED'


def read_state():
    if not DB.exists():return {},{},{}
    conn=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)
    try:
        conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
        try:
            catalogs={r[0]:dict(token=r[0],pump_pool=r[1],meteora_pool=r[2],bin_total=r[3],bin_selected=r[4],discovery_complete=bool(r[5])) for r in conn.execute('SELECT token,pump_pool,meteora_pool,bin_total,bin_selected,discovery_complete FROM pair_catalog')}
            latest={r[0]:dict(pubkey=r[0],slot=int(r[1]),received_ns=int(r[2]),owner=r[3],data_b64=r[4],content_sha256=r[5],source=r[6]) for r in conn.execute('SELECT pubkey,slot,received_ns,owner,data_b64,content_sha256,source FROM latest')}
            watches={r[0]:json.loads(r[1]) for r in conn.execute('SELECT pubkey,roles FROM watch')}
        finally:conn.execute('ROLLBACK')
    finally:conn.close()
    return catalogs,latest,watches


def identity_roles(token,watches,latest):
    found={}
    for key,items in watches.items():
        for item in items:
            if isinstance(item,(list,tuple)) and len(item)==2 and item[0]==token:
                role=item[1]
                if role in found:raise ValueError('DUPLICATE_ROLE_'+str(role))
                if key not in latest:raise ValueError('ACCOUNT_NOT_OBSERVED_'+str(role))
                found[role]=(key,latest[key])
    return found


def account_data(role,rolemap,expected_owner,start_ns):
    if role not in rolemap:raise ValueError('MISSING_ROLE_'+role)
    key,row=rolemap[role]
    if row['owner'] not in expected_owner:raise ValueError('BAD_OWNER_'+role)
    if row['received_ns']<start_ns:raise ValueError('PREVIOUS_SESSION_STATE_'+role)
    if row['slot']<=0:raise ValueError('NO_CONTEXT_SLOT_'+role)
    raw=base64_strict(row['data_b64'])
    if hashlib.sha256(raw).hexdigest()!=row['content_sha256']:raise ValueError('ACCOUNT_HASH_MISMATCH_'+role)
    return key,row,raw


def token_account_amount(role,rolemap,mint,start_ns,c):
    key,row,raw=account_data(role,rolemap,(TOKEN,TOKEN22),start_ns)
    if len(raw)<72:raise ValueError('TOKEN_ACCOUNT_SHORT_'+role)
    if raw[:32]!=c.b58d(mint):raise ValueError('TOKEN_MINT_MISMATCH_'+role)
    return int(struct.unpack_from('<Q',raw,64)[0]),(key,row)


def prepare_snapshot(catalog,latest,watches,decimals,start_ns,c,pd):
    token=catalog['token'];pool=catalog['pump_pool'];dlmm=catalog['meteora_pool']
    if not catalog['discovery_complete'] or int(catalog['bin_total'])<1 or int(catalog['bin_selected'])!=int(catalog['bin_total']):
        raise ValueError('BIN_ARRAY_CATALOG_CAPPED')
    if token not in decimals:raise ValueError('TOKEN_DECIMALS_NOT_VERIFIED')
    roles=identity_roles(token,watches,latest)
    pk,pro,pr=account_data('PUMP_POOL',roles,(PUMP,),start_ns)
    lk,lro,lb=account_data('DLMM_POOL',roles,(DLMM,),start_ns)
    if pk!=pool or lk!=dlmm:raise ValueError('POOL_IDENTITY_MISMATCH')
    pump=c.decode_pump_pool(pr)
    if pump['base_mint']!=token or pump['quote_mint']!=SOL:raise ValueError('PUMP_PAIR_MINT_MISMATCH')
    if pump['base_vault']!=roles.get('PUMP_BASE_VAULT',(None,))[0] or pump['quote_vault']!=roles.get('PUMP_QUOTE_VAULT',(None,))[0]:
        raise ValueError('PUMP_VAULT_IDENTITY_MISMATCH')
    base,bre=token_account_amount('PUMP_BASE_VAULT',roles,token,start_ns,c)
    quote,qre=token_account_amount('PUMP_QUOTE_VAULT',roles,SOL,start_ns,c)
    _,res_sol=token_account_amount('DLMM_SOL_RESERVE',roles,SOL,start_ns,c)
    _,res_token=token_account_amount('DLMM_TOKEN_RESERVE',roles,token,start_ns,c)
    if base<=0 or quote<=0:raise ValueError('PUMP_EMPTY_RESERVES')
    arrays=[];account_rows=[pro,lro,bre[1],qre[1],res_sol[1],res_token[1]]
    for role in sorted(r for r in roles if r.startswith('DLMM_BIN_ARRAY_INDEX_')):
        k,row,raw=account_data(role,roles,(DLMM,),start_ns)
        ix=int(role.rsplit('_',1)[1])
        if len(raw)<56 or struct.unpack_from('<q',raw,8)[0]!=ix or raw[24:56]!=c.b58d(dlmm):
            raise ValueError('BIN_ARRAY_INDEX_OR_PARENT_MISMATCH')
        arrays.append((ix,k,raw));account_rows.append(row)
    arrays.sort()
    if len(arrays)!=catalog['bin_total']:raise ValueError('ARRAY_COUNT_NOT_COMPLETE')
    # Read actual DLMM pool mint orientation from its canonical LbPair byte offsets.
    if len(lb)<216:raise ValueError('DLMM_LB_PAIR_TOO_SHORT')
    xmint,ymint=c.b58e(lb[88:120]),c.b58e(lb[120:152])
    xreserve,yreserve=c.b58e(lb[152:184]),c.b58e(lb[184:216])
    if set((xmint,ymint))!={SOL,token}:raise ValueError('DLMM_PAIR_MINT_IDENTITY_MISMATCH')
    if xreserve!=roles['DLMM_SOL_RESERVE' if xmint==SOL else 'DLMM_TOKEN_RESERVE'][0] or yreserve!=roles['DLMM_SOL_RESERVE' if ymint==SOL else 'DLMM_TOKEN_RESERVE'][0]:
        raise ValueError('DLMM_RESERVE_PDA_IDENTITY_MISMATCH')
    pair=pd.PairState(token=token,pump_pool=pool,meteora_pool=dlmm,
        token_x=xmint,token_y=ymint,decimals_x=9 if xmint==SOL else decimals[token],decimals_y=9 if ymint==SOL else decimals[token],
        pump_base_vault=pump['base_vault'],pump_quote_vault=pump['quote_vault'],
        pump_base_reserve=base,pump_quote_reserve=quote,lb_bytes=lb,arrays=arrays,dlmm_state=None)
    pair.dlmm_state=pd._build_dlmm_state(pair)
    now=time.time_ns();max_ns=max(r['received_ns'] for r in account_rows)
    latest_price_ns=max(r['received_ns'] for r in [bre[1],qre[1],lro]+[roles[r][1] for r in roles if r.startswith('DLMM_BIN_ARRAY_INDEX_')])
    return {'token':token,'pump_pool':pool,'meteora':{'address':dlmm,'token_x':xmint,'token_y':ymint,
              'decimals_x':pair.decimals_x,'decimals_y':pair.decimals_y},'dlmm_state':pair.dlmm_state,
              'pump_base_reserve':base,'pump_quote_reserve':quote}, {
              'account_count':len(account_rows),'slot_min':min(int(r['slot']) for r in account_rows),
              'slot_max':max(int(r['slot']) for r in account_rows),'distinct_slots':len(set(int(r['slot']) for r in account_rows)),
              'last_account_age_ms':round((now-max_ns)/1e6,2),
              'last_price_event_age_ms':round((now-latest_price_ns)/1e6,2),
              'array_count':len(arrays),'read_epoch_ns':now,
              'slot_coherence_certified':False}


def dlmm_quote_or_partial(snap, amount_raw, input_mint, c, quote_fn=None):
    """Preserve core.dlmm_quote_snapshot completion semantics, expose exact failure evidence.

    The probe never treats incomplete quotes as executable. All quotation remains
    read-only and relies on native Meteora PoolState; no REST quote request.
    """
    if amount_raw <= 0:raise ValueError('DLMM_INPUT_NONPOSITIVE')
    if input_mint==snap['meteora']['token_x']:for_y=True
    elif input_mint==snap['meteora']['token_y']:for_y=False
    else:raise ValueError('DLMM_INPUT_MINT_NOT_IN_PAIR')
    if quote_fn is None:
        from meteora_dlmm import quote as quote_fn
    q=quote_fn(snap['dlmm_state'],amount_in=int(amount_raw),swap_for_y=for_y,strict=True)
    remaining=int(getattr(q,'remaining_in',0) or 0)
    complete=bool(getattr(q,'complete',False))
    amount_out=int(getattr(q,'amount_out',0) or 0)
    crossed=int(getattr(q,'bins_crossed',0) or 0)
    if not complete or remaining != 0 or amount_out<=0:
        return None,{'reason':'DLMM_PARTIAL' if not complete or remaining else 'DLMM_ZERO_OUTPUT',
                     'input_mint':'WSOL' if input_mint==SOL else 'TOKEN',
                     'input_raw':int(amount_raw),'remaining_in':remaining,
                     'complete':complete,'raw_out':amount_out,'bins_crossed':crossed,
                     'swap_for_y':for_y}
    return amount_out,None


def directional_ladder(snap,q18,c,quote_fn=None):
    """Evaluate each of 38 routes separately; a missing M2P route cannot mask P2M.

    Uses the official PumpSwap SDK and token-net semantics of ORACLE-018/023.
    Does NOT introduce the old approximate constant-product Pump pricing.
    """
    out=[];errors=[];counts=Counter();t0=time.perf_counter_ns()
    for size in GRID:
        start=int(round(size*1e9))
        # PUMP_TO_METEORA: SDK Pump buy, physical token receipt, exact DLMM sell.
        try:
            pb=q18.worker().buy(snap,start)
            received=int(q18.token_net(snap['token'],int(pb['baseOut'])))
            if received<=0:raise RuntimeError('PUMP_BUY_TOKEN_NET_ZERO')
            ending,detail=dlmm_quote_or_partial(snap,received,snap['token'],c,quote_fn)
            if detail:
                errors.append(dict(direction='PUMP_TO_METEORA',size_sol=size,stage='METEORA',**detail))
                counts['P2M_DLMM_PARTIAL']+=1
            else:
                net=int(ending)-start
                out.append(dict(direction='PUMP_TO_METEORA',size_sol=size,
                                gross_lamports=net,gross_bps=round(net/start*10000,3),
                                end_lamports=int(ending),pump_token_out=int(pb['baseOut']),
                                meteora_token_in=received))
                counts['P2M_EVALUATED']+=1
        except Exception as e:
            errors.append(dict(direction='PUMP_TO_METEORA',size_sol=size,stage='SDK_OR_NATIVE',reason=safe(e)))
            counts['P2M_ERROR']+=1
        # METEORA_TO_PUMP: exact DLMM buy, actual token receipt, SDK Pump sell.
        try:
            received,detail=dlmm_quote_or_partial(snap,start,SOL,c,quote_fn)
            if detail:
                errors.append(dict(direction='METEORA_TO_PUMP',size_sol=size,stage='METEORA',**detail))
                counts['M2P_DLMM_PARTIAL']+=1
            else:
                token_in=int(q18.token_net(snap['token'],received))
                if token_in<=0:raise RuntimeError('METEORA_TOKEN_NET_ZERO')
                ps=q18.worker().sell(snap,token_in)
                ending=int(ps['uiQuote'])
                net=ending-start
                out.append(dict(direction='METEORA_TO_PUMP',size_sol=size,
                                gross_lamports=net,gross_bps=round(net/start*10000,3),
                                end_lamports=ending,meteora_token_out=received,
                                pump_token_in=token_in,
                                pump_min_end_lamports=int(ps.get('minQuote') or 0)))
                counts['M2P_EVALUATED']+=1
        except Exception as e:
            errors.append(dict(direction='METEORA_TO_PUMP',size_sol=size,stage='SDK_OR_NATIVE',reason=safe(e)))
            counts['M2P_ERROR']+=1
    best=max(out,key=lambda x:x['gross_lamports'],default=None)
    per_direction={}
    for direction in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
        vals=[r for r in out if r['direction']==direction]
        per_direction[direction]={
            'evaluated':len(vals),'positive':sum(r['gross_lamports']>0 for r in vals),
            'best':max(vals,key=lambda x:x['gross_lamports'],default=None),
            'partial':sum(e.get('reason')=='DLMM_PARTIAL' and e['direction']==direction for e in errors),
            'other_errors':sum(e.get('reason')!='DLMM_PARTIAL' and e['direction']==direction for e in errors)}
    return {'evaluated':len(out),'attempted':len(GRID)*2,'sizes_attempted':len(GRID),
            'gross_positive':sum(x['gross_lamports']>0 for x in out),'best':best,
            'by_direction':per_direction,'failure_counts':dict(counts),
            'errors':errors[:12], 'error_count':len(errors),
            'quote_ms':round((time.perf_counter_ns()-t0)/1e6,2),
            'execution_authority':False,'net_of_all_fees_certified':False}


def choose_cycle(pairs,cursor):
    """Deterministic round robin without relying on constantly changing first pair."""
    if not pairs:return []
    n=len(pairs)
    return [pairs[(cursor+i)%n] for i in range(n)]


def atomic_save(obj):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_name(OUT.name+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str),encoding='utf-8')
    os.replace(tmp,OUT)


def run(seconds,pair_count,max_arrays,sample_interval,quotes_per_tick=3):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):raise RuntimeError('PRIVATE_KEY_PRESENT_REFUSE_EXECUTOR_WITNESS')
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://') or not os.getenv('SOLANA_WS_URL','').startswith('wss://'):
        raise RuntimeError('RPC_AND_WS_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
    pairs=witness.inventory_pairs(pair_count)
    # One metadata request, not a per-event request. Mint decimals are immutable.
    decimals=mint_metadata(os.environ['SOLANA_RPC_URL'],[p['token'] for p in pairs])
    q23.install_hot_token_net()
    warm=set();cache={};start=time.time_ns();end=time.monotonic()+max(20,seconds)
    child=subprocess.Popen([sys.executable,'-m',witness.__name__,'--run','--seconds',str(seconds),
                            '--pairs',str(pair_count),'--max-arrays-per-pair',str(max_arrays)],env=os.environ.copy())
    emit('BOSS335_START',{'pairs':len(pairs),'sizes':list(GRID),'witness_pid':child.pid,
         'private_key_used':False,'signing':False,'broadcast':False,'scanner_untouched':True,
         'executor_untouched':True,'fee_net_certification':False})
    stats=Counter();last_results={};last_log={};last_check=0.;cursor=0
    try:
        while time.monotonic()<end and child.poll() is None:
            if time.monotonic()-last_check<max(.5,sample_interval):time.sleep(.16);continue
            last_check=time.monotonic();connected,reason=live_witness_status()
            if not connected:
                stats[reason]+=1
                if stats[reason]==1 or stats[reason]%12==0:emit('BOSS335_HOLD',{'reason':reason,'trade_ready':False})
                continue
            try:catalogs,latest,watches=read_state()
            except (sqlite3.Error,ValueError,OSError) as e:
                emit('BOSS335_DB_HOLD',{'reason':safe(e)});continue
            # Bounded round-robin: all 6 pairs get a turn, even if one updates continuously.
            ordered=choose_cycle(pairs,cursor);cursor=(cursor+1)%len(pairs)
            tick_quotes=0
            for p in ordered:
                token=p['token'];cat=catalogs.get(token)
                if not cat or any(cat.get(k)!=p[k] for k in ('pump_pool','meteora_pool')):continue
                try:
                    snap,lineage=prepare_snapshot(cat,latest,watches,decimals,start,c,pd)
                except Exception as e:
                    key=safe(e)
                    if last_log.get(token)!=key:
                        emit('BOSS335_PAIR_HOLD',{'token':token[:12],'reason':key,'fee_net_certification':False})
                        last_log[token]=key
                    stats['pair_holds']+=1;continue
                if lineage['last_price_event_age_ms']>750:
                    stats['no_recent_price_event']+=1
                    continue
                state_hash=hashlib.sha256(json.dumps([(r['slot'],r['content_sha256']) for k,r in sorted(latest.items()) if any(item[0]==token for item in watches.get(k,[]))],separators=(',',':')).encode()).hexdigest()
                if cache.get(token)==state_hash:continue
                cache[token]=state_hash
                if token not in warm:
                    try:
                        q23.worker().warm(token);q23.worker().refresh_epoch();q18.worker().warm(snap['pump_pool']);warm.add(token)
                    except Exception as e:
                        emit('BOSS335_SDK_WARM_HOLD',{'token':token[:12],'reason':safe(e)});continue
                q=directional_ladder(snap,q18,c);age_end_ms=round((time.time_ns()-lineage['read_epoch_ns'])/1e6+lineage['last_price_event_age_ms'],2)
                result={'token':token,'pump_pool':p['pump_pool'],'meteora_pool':p['meteora_pool'],
                        'lineage':lineage,'quote':q,'quote_end_event_age_ms':age_end_ms,
                        'read_only':True,'slot_coherence_certified':False,'strict_bound_sim_pass':False,
                        'execution_admission':False,'signing':False,'broadcast':False}
                last_results[token]=result;stats['quoted_pairs']+=1
                stats['p2m_evaluated']+=q['by_direction']['PUMP_TO_METEORA']['evaluated']
                stats['m2p_evaluated']+=q['by_direction']['METEORA_TO_PUMP']['evaluated']
                stats['p2m_partial']+=q['by_direction']['PUMP_TO_METEORA']['partial']
                stats['m2p_partial']+=q['by_direction']['METEORA_TO_PUMP']['partial']
                emit('BOSS335_DIRECTIONAL_WITNESS_QUOTE',{'token':token[:12],'lineage':lineage,
                     'quote':q,'quote_end_event_age_ms':age_end_ms,'trade_ready':False})
                atomic_save({'build':'ORACLE335','stats':dict(stats),'results':last_results,
                             'scan_frozen':True,'signing':False,'broadcast':False,
                             'executable_pricing_certified':False})
                tick_quotes+=1
                if tick_quotes>=max(1,min(int(quotes_per_tick),6)):break
        emit('BOSS335_EXIT',{'stats':dict(stats),'quoted_tokens':len(last_results),
             'witness_exit_code':child.poll(),'signing':False,'broadcast':False,
             'quote_economics_are_not_fee_net':True})
    finally:
        if child.poll() is None:
            child.terminate()
            try:child.wait(timeout=8)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
        try:
            if getattr(q18,'_worker',None):q18._worker.close()
        except Exception:pass
        try:
            if getattr(q23,'_worker',None):q23._worker.close()
        except Exception:pass
    return 0


def tests():
    import unittest
    class Test(unittest.TestCase):
        def test_19_size_ladder(self):
            self.assertEqual((len(GRID),GRID[0],GRID[-1]),(19,.01,.1));self.assertAlmostEqual(GRID[1]-GRID[0],.005)
        def test_mint_decimals_reject_wrong_owner(self):
            with self.assertRaises(ValueError):mint_decimals({'owner':PUMP,'data':['','base64']})
        def test_mint_decimals_valid(self):
            raw=bytearray(82);raw[44]=6;raw[45]=1
            self.assertEqual(mint_decimals({'owner':TOKEN,'data':[base64.b64encode(raw).decode(),'base64']}),6)
        def test_mint_decimals_uninitialized(self):
            raw=bytearray(82);raw[44]=9
            with self.assertRaises(ValueError):mint_decimals({'owner':TOKEN,'data':[base64.b64encode(raw).decode(),'base64']})
        def test_base64_invalid(self):
            with self.assertRaises(ValueError):base64_strict('invalid%%')
        def test_role_identity_no_fabrication(self):
            self.assertEqual(identity_roles('x',{},{}),{})
        def test_unknown_role(self):
            with self.assertRaises(ValueError):account_data('PUMP_BASE',{},(TOKEN,),0)
        def test_reject_old_session(self):
            row={'owner':TOKEN,'received_ns':9,'slot':2,'data_b64':'AA==','content_sha256':hashlib.sha256(b'\x00').hexdigest()}
            with self.assertRaises(ValueError):account_data('X',{'X':('k',row)},(TOKEN,),10)
        def test_account_bad_owner(self):
            row={'owner':PUMP,'received_ns':30,'slot':2,'data_b64':'AA==','content_sha256':hashlib.sha256(b'\x00').hexdigest()}
            with self.assertRaises(ValueError):account_data('X',{'X':('k',row)},(TOKEN,),10)
        def test_hash_prevents_corruption(self):
            row={'owner':TOKEN,'received_ns':30,'slot':2,'data_b64':'AA==','content_sha256':'0'*64}
            with self.assertRaises(ValueError):account_data('X',{'X':('k',row)},(TOKEN,),10)
        def test_catalog_cap_blocks(self):
            class Fail:
                def __getattr__(self,name):raise AssertionError('SHOULD_FAIL_EARLY')
            with self.assertRaisesRegex(ValueError,'BIN_ARRAY_CATALOG_CAPPED'):
                prepare_snapshot({'token':'t','pump_pool':'p','meteora_pool':'m','bin_total':8,'bin_selected':6,'discovery_complete':False}, {}, {}, {}, 0, Fail(),Fail())
        def test_independent_38_bidirectional_mock(self):
            from types import SimpleNamespace
            class W:
                def buy(self,snap,start):return {'baseOut':start*100}
                def sell(self,snap,amount):return {'uiQuote':amount//100, 'minQuote':amount//100}
            class Q:
                @staticmethod
                def worker():return W()
                @staticmethod
                def token_net(token,amount):return amount
            class C:pass
            def quote(state,amount_in,swap_for_y,strict):
                if swap_for_y:return SimpleNamespace(amount_out=amount_in//100,remaining_in=0,complete=True,bins_crossed=1)
                return SimpleNamespace(amount_out=amount_in*100,remaining_in=0,complete=True,bins_crossed=1)
            snap={'meteora':{'token_x':'TOKEN','token_y':SOL},'token':'TOKEN','dlmm_state':object()}
            r=directional_ladder(snap,Q,C(),quote)
            self.assertEqual((r['evaluated'],r['gross_positive'],r['attempted']),(38,0,38))
            self.assertFalse(r['net_of_all_fees_certified'])
        def test_independent_p2m_survives_m2p_partial(self):
            from types import SimpleNamespace
            class W:
                def buy(self,snap,start):return {'baseOut':start*100}
                def sell(self,snap,amount):raise AssertionError('M2P_SHOULD_NEVER_SELL')
            class Q:
                @staticmethod
                def worker():return W()
                @staticmethod
                def token_net(token,amount):return amount
            def quote(state,amount_in,swap_for_y,strict):
                if not swap_for_y:return SimpleNamespace(amount_out=1,remaining_in=amount_in//2,complete=False,bins_crossed=1)
                return SimpleNamespace(amount_out=amount_in//100,remaining_in=0,complete=True,bins_crossed=1)
            snap={'meteora':{'token_x':'TOKEN','token_y':SOL},'token':'TOKEN','dlmm_state':object()}
            r=directional_ladder(snap,Q,object(),quote)
            self.assertEqual(r['evaluated'],19)
            self.assertEqual(r['by_direction']['METEORA_TO_PUMP']['partial'],19)
            self.assertEqual(r['by_direction']['PUMP_TO_METEORA']['evaluated'],19)
            self.assertEqual(r['error_count'],19)
        def test_independent_m2p_survives_p2m_partial(self):
            from types import SimpleNamespace
            class W:
                def buy(self,snap,start):return {'baseOut':start*100}
                def sell(self,snap,amount):return {'uiQuote':int(amount)//100,'minQuote':2}
            class Q:
                @staticmethod
                def worker():return W()
                @staticmethod
                def token_net(token,amount):return amount
            def quote(state,amount_in,swap_for_y,strict):
                if swap_for_y:return SimpleNamespace(amount_out=1,remaining_in=amount_in//2,complete=False,bins_crossed=1)
                return SimpleNamespace(amount_out=amount_in*100,remaining_in=0,complete=True,bins_crossed=1)
            snap={'meteora':{'token_x':'TOKEN','token_y':SOL},'token':'TOKEN','dlmm_state':object()}
            r=directional_ladder(snap,Q,object(),quote)
            self.assertEqual(r['evaluated'],19)
            self.assertEqual(r['by_direction']['PUMP_TO_METEORA']['partial'],19)
            self.assertEqual(r['by_direction']['METEORA_TO_PUMP']['evaluated'],19)
        def test_m2p_partial_includes_remaining_raw(self):
            from types import SimpleNamespace
            snap={'meteora':{'token_x':'TOKEN','token_y':SOL},'dlmm_state':object()}
            out,detail=dlmm_quote_or_partial(snap,10,SOL,object(),lambda *a,**kw:SimpleNamespace(complete=False,remaining_in=7,amount_out=3,bins_crossed=2))
            self.assertIsNone(out);self.assertEqual((detail['remaining_in'],detail['bins_crossed'],detail['input_raw']),(7,2,10))
        def test_untrusted_mint_blocked(self):
            snap={'meteora':{'token_x':'TOKEN','token_y':SOL},'dlmm_state':object()}
            with self.assertRaisesRegex(ValueError,'DLMM_INPUT_MINT_NOT_IN_PAIR'):
                dlmm_quote_or_partial(snap,10,'MALICIOUS',object(),lambda *a,**kw:None)
        def test_round_robin_fairness(self):
            pairs=list('abcdef')
            self.assertEqual(choose_cycle(pairs,0),pairs)
            self.assertEqual(choose_cycle(pairs,3),list('defabc'))
            self.assertEqual([choose_cycle(pairs,c)[0] for c in range(len(pairs))],pairs)
        def test_no_blank_min_output_substitution(self):
            from types import SimpleNamespace
            # The diagnostic uses quote outputs, never artificially changes minOut.
            self.assertNotIn('diagnostic_min_out',directional_ladder.__code__.co_names)
        def test_quote_exact_sdk_or_not_evaluated(self):
            class Bad:
                @staticmethod
                def worker():raise RuntimeError('OFFICIAL_SDK_DIED')
            def quote(*a,**kw):raise RuntimeError('OFFICIAL_DLMM_DIED')
            s={'meteora':{'token_x':'TOKEN','token_y':SOL},'token':'TOKEN','dlmm_state':object()}
            r=directional_ladder(s,Bad(),object(),quote)
            self.assertEqual(r['evaluated'],0)
            self.assertEqual(r['error_count'],38)
        def test_m2p_partial_does_not_force_p2m_positive(self):
            self.assertFalse(directional_ladder.__name__=='authorize_trade')
        def test_reconstruct_both_token_mint_orientations(self):
            from types import SimpleNamespace
            now=time.time_ns(); t='t';p='p';m='m'
            keys={t:bytes([11])*32,SOL:bytes([12])*32,m:bytes([13])*32,'pv':bytes([14])*32,'qv':bytes([15])*32,'rs':bytes([16])*32,'rt':bytes([17])*32}
            keys_rev={v:k for k,v in keys.items()}
            class C:
                @staticmethod
                def b58d(s):return keys[s]
                @staticmethod
                def b58e(b):return keys_rev[b]
                @staticmethod
                def decode_pump_pool(raw):return dict(base_mint=t,quote_mint=SOL,base_vault='pv',quote_vault='qv')
            class PD:
                @staticmethod
                def PairState(**kw):return SimpleNamespace(**kw)
                @staticmethod
                def _build_dlmm_state(pair):return (pair.token_x,pair.token_y)
            catalog=dict(token=t,pump_pool=p,meteora_pool=m,bin_total=1,bin_selected=1,discovery_complete=True)
            for x,y in ((SOL,t),(t,SOL)):
                pool=bytearray(900);pool[88:120]=keys[x];pool[120:152]=keys[y]
                pool[152:184]=keys['rs' if x==SOL else 'rt'];pool[184:216]=keys['rs' if y==SOL else 'rt']
                binraw=bytearray(80);struct.pack_into('<q',binraw,8,7);binraw[24:56]=keys[m]
                def vault(mint):
                    raw=bytearray(100);raw[:32]=keys[mint];struct.pack_into('<Q',raw,64,1000);return raw
                rows=[('PUMP_POOL',p,PUMP,bytearray(240)),('DLMM_POOL',m,DLMM,pool),
                      ('PUMP_BASE_VAULT','pv',TOKEN,vault(t)),('PUMP_QUOTE_VAULT','qv',TOKEN,vault(SOL)),
                      ('DLMM_SOL_RESERVE','rs',TOKEN,vault(SOL)),('DLMM_TOKEN_RESERVE','rt',TOKEN,vault(t)),
                      ('DLMM_BIN_ARRAY_INDEX_7','b',DLMM,binraw)]
                latest={};watches={}
                for role,key,owner,raw in rows:
                    data=bytes(raw);latest[key]=dict(slot=55,received_ns=now,owner=owner,
                        data_b64=base64.b64encode(data).decode(),content_sha256=hashlib.sha256(data).hexdigest())
                    watches[key]=[[t,role]]
                snap,lineage=prepare_snapshot(catalog,latest,watches,{t:6},now-50,C,PD)
                self.assertEqual((snap['meteora']['token_x'],snap['meteora']['token_y']),(x,y))
                self.assertEqual((snap['meteora']['decimals_x'],snap['meteora']['decimals_y']),
                                 (9 if x==SOL else 6,9 if y==SOL else 6))
                self.assertFalse(lineage['slot_coherence_certified'])
        def test_exact_quotes_are_not_net_fee_certification(self):
            self.assertFalse(directional_ladder.__name__=='authorize_trade')
        def test_safe_redaction(self):
            self.assertNotIn('SECRET123',safe(RuntimeError('url?api-key=SECRET123')))
        def test_output_path_dedicated(self):
            self.assertEqual(OUT.name,'executor_ws_directional_quote_report.json')
        def test_frozen_scanner_immutable(self):
            self.assertEqual(INVENTORY.name,'scanner_inventory.json')
        def test_no_order_path(self):
            src=pathlib.Path(__file__).read_text(encoding='utf-8')
            self.assertNotIn('send'+'Transaction(',src)
            self.assertNotIn('sign_'+'transaction(',src)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    res=unittest.TextTestRunner(verbosity=2).run(suite)
    if res.wasSuccessful():emit('BOSS335_TEST_PASS',{'tests':res.testsRun});return 0
    return 1


def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    for x in ('test','audit','run'):g.add_argument('--'+x,action='store_true')
    ap.add_argument('--seconds',type=int,default=120)
    ap.add_argument('--pairs',type=int,default=6)
    ap.add_argument('--max-arrays-per-pair',type=int,default=12)
    ap.add_argument('--sample-interval',type=float,default=1.)
    ap.add_argument('--quotes-per-tick',type=int,default=3)
    a=ap.parse_args()
    if a.test:return tests()
    if a.audit:
        emit('BOSS335_AUDIT',{'private_key_read':False,'scanner_modified':False,'executor_modified':False,
             'size_ladder_sol':list(GRID),'quoted_price_certified_for_trading':False,
             'uses_official_pump_sdk':True,'uses_exact_dlmm_state':True,'direction_isolation':True,'fair_round_robin':True,
             'signing':False,'broadcast':False,'rpc_per_quote':False});return 0
    return run(a.seconds,a.pairs,a.max_arrays_per_pair,a.sample_interval,a.quotes_per_tick)

if __name__=='__main__':raise SystemExit(main())
