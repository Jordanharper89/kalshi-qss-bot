"""ORACLE-305: two-budgeted-batch pair-complete native P2M/M2P evidence, never orders."""
import argparse,base64,hashlib,json,os,sqlite3,struct,time
from collections import Counter
from pathlib import Path

ROOT=Path('runtime_state/oracle/oracle_live_execution')
REPORT=ROOT/'ORACLE305_PAIR_COMPLETE_NATIVE.json'
LEDGER=ROOT/'ORACLE305_NATIVE_QUOTES.sqlite3'
CACHE=ROOT/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json'
GRID=tuple(round(.010+.005*i,3) for i in range(19))
WSOL='So11111111111111111111111111111111111111112'
TOKEN_PROGRAMS={'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def disarm():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('CHILD_MUST_BE_DISARMED')

def pairs_from_inventory(inventory,cache,max_pairs=2):
    pools={}
    for addr,refs in inventory.items():
        for token,venue in refs:
            if venue=='PUMPSWAP_WS':pools.setdefault(token,{})['pump']=addr
            if venue=='METEORA_WS':pools.setdefault(token,{})['meteora']=addr
    out=[]
    for pool,info in sorted(cache.get('pools',{}).items()):
        token=info.get('token'); links=pools.get(token,{})
        arrays=info.get('addresses',[])
        if info.get('historical_only') is not True or links.get('meteora')!=pool or not links.get('pump') or not arrays:continue
        out.append({'token':token,'pump':links['pump'],'meteora':pool,'arrays':arrays})
    return out[:max_pairs]

def unpack_rpc(reply,addresses):
    if not isinstance(reply,dict) or 'error' in reply:raise RuntimeError('RPC_RESPONSE_ERROR')
    result=reply.get('result') or {};slot=(result.get('context') or {}).get('slot');vals=result.get('value')
    if type(slot)!=int or slot<=0 or not isinstance(vals,list) or len(vals)!=len(addresses):raise RuntimeError('RPC_CARDINALITY')
    seen={};holds=Counter()
    for addr,v in zip(addresses,vals):
        if not isinstance(v,dict):holds['ACCOUNT_MISSING']+=1;continue
        d=v.get('data')
        if not isinstance(d,list) or len(d)!=2 or d[1]!='base64':holds['ENCODING_INVALID']+=1;continue
        try:raw=base64.b64decode(d[0],validate=True)
        except (TypeError,ValueError):holds['BASE64_INVALID']+=1;continue
        if not raw or len(raw)>240000:holds['SIZE_INVALID']+=1;continue
        seen[addr]={'slot':slot,'raw':raw,'owner':v.get('owner'),'sha':hashlib.sha256(raw).hexdigest()}
    return slot,seen,holds

def selection(stage):
    addresses=[]
    for row in stage:
        addresses.extend((row['pump'],row['meteora']))
        addresses.extend(a['address'] for a in row['arrays'])
    return list(dict.fromkeys(addresses))

def dependency_addresses(stage,first,decode):
    need=[];holds=Counter();info={}
    for row in stage:
        p=first.get(row['pump'])
        if not p or p['owner']!=PUMP:
            holds['PUMP_POOL_MISSING_OR_OWNER']+=1;continue
        try:
            decoded=decode(p['raw'])
            if decoded['base_mint']!=row['token'] or decoded['quote_mint']!=WSOL:raise ValueError('PUMP_MINT_MISMATCH')
            for key in ('base_vault','quote_vault'):
                if not decoded.get(key):raise ValueError('VAULT_ADDRESS_MISSING')
            info[row['token']]=decoded
            need.extend((decoded['base_vault'],decoded['quote_vault'],row['token']))
        except (ValueError,KeyError) as e:holds[str(e)[:70]]+=1
    need.append(WSOL)
    return list(dict.fromkeys(need)),info,holds

def mint_decimals(row,mint):
    if not row or row['owner'] not in TOKEN_PROGRAMS or len(row['raw'])<45:raise ValueError('MINT_ACCOUNT_NOT_VERIFIED')
    if len(row['raw'])<82:raise ValueError('MINT_LAYOUT_SHORT')
    value=int(row['raw'][44]);
    if value>18:raise ValueError('MINT_DECIMALS_OUT_OF_RANGE')
    return value

def hydrate(stage,records,decoded,core,decimals):
    from meteora_dlmm import PoolState
    from oracle_300_canonical_mint_quote import lb_pair_mints
    good=[];holds=Counter()
    for row in stage:
        token=row['token'];p=records.get(row['pump']);m=records.get(row['meteora']);info=decoded.get(token)
        if not all((p,m,info)):
            holds['PAIR_POOL_OR_DEPENDENCY_MISSING']+=1;continue
        try:
            if p['owner']!=PUMP or m['owner']!=DLMM:raise ValueError('POOL_OWNER_MISMATCH')
            xm,ym=lb_pair_mints(m['raw'])
            if {xm,ym}!={token,WSOL}:raise ValueError('METEORA_MINT_MISMATCH')
            base=records.get(info['base_vault']);quote=records.get(info['quote_vault'])
            if not base or not quote:raise ValueError('PUMP_VAULT_BYTES_MISSING')
            for v,expect in ((base,token),(quote,WSOL)):
                if v['owner'] not in TOKEN_PROGRAMS or len(v['raw'])<72 or core.b58e(v['raw'][:32])!=expect:raise ValueError('VAULT_MINT_OR_OWNER_MISMATCH')
            br=struct.unpack_from('<Q',base['raw'],64)[0];qr=struct.unpack_from('<Q',quote['raw'],64)[0]
            if not br or not qr:raise ValueError('PUMP_RESERVES_EMPTY')
            arrays=[]
            for arr in row['arrays']:
                a=records.get(arr['address']);index=arr['array_index']
                if not a or a['owner']!=DLMM or len(a['raw'])<56:raise ValueError('BIN_BYTES_MISSING')
                if a['raw'][24:56]!=core.b58d(row['meteora']) or struct.unpack_from('<q',a['raw'],8)[0]!=index:raise ValueError('BIN_IDENTITY_MISMATCH')
                arrays.append((index,a['raw']))
            if not arrays:raise ValueError('BIN_EMPTY')
            arrays.sort(key=lambda x:x[0])
            state=PoolState.from_accounts(m['raw'],[a for _,a in arrays],
                decimals_x=decimals[xm],decimals_y=decimals[ym],lb_pair_key=core.b58d(row['meteora']),exhaustive=True)
            snap={'token':token,'pump_pool':row['pump'],'meteora':{'address':row['meteora'],
                'token_x':xm,'token_y':ym,'decimals_x':decimals[xm],'decimals_y':decimals[ym]},
                'dlmm_state':state,'pump_base_reserve':br,'pump_quote_reserve':qr}
            good.append((row,snap))
        except Exception as e:
            name=str(e)[:100] if isinstance(e,ValueError) else 'HYDRATION_'+type(e).__name__
            holds[name]+=1
    return good,holds

def ledger():
    ROOT.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(LEDGER,timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('''CREATE TABLE IF NOT EXISTS quotes(epoch REAL,slot1 INTEGER,slot2 INTEGER,
       token TEXT,pump TEXT,meteora TEXT,direction TEXT,size_sol REAL,status TEXT,
       end_lamports INTEGER,gross_bps REAL,reason TEXT)''')
    return con

def evaluate(good,q18,slots):
    results=[];stats=Counter()
    for info,snap in good:
        for size in GRID:
            try:
                outcomes=q18.exact_snapshot_opportunities(snap,size)
                if not isinstance(outcomes,list) or len(outcomes)!=2:raise ValueError('NATIVE_RETURN_INVALID')
                if {r['direction'] for r in outcomes}!={'PUMP_TO_METEORA','METEORA_TO_PUMP'}:raise ValueError('NATIVE_DIRECTIONS_INVALID')
                for r in outcomes:
                    end=int(r['local_end']);start=round(size*1e9)
                    if end<=0:raise ValueError('NONPOSITIVE_END')
                    bps=(end-start)*10000/start
                    status='GROSS_POSITIVE_CANDIDATE' if end>start else 'GROSS_NONPOSITIVE'
                    stats[status]+=1
                    results.append((time.time(),*slots,info['token'],info['pump'],info['meteora'],r['direction'],size,status,end,bps,''))
            except Exception as e:
                detail=str(e).upper();reason='DLMM_PARTIAL' if 'DLMM_PARTIAL' in detail else 'PUMP_WORKER' if 'PUMP_SDK_WORKER' in detail else 'NETWORK_FORBIDDEN' if 'NETWORK' in detail else type(e).__name__
                stats['HOLD_'+reason]+=1
                for direction in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
                    results.append((time.time(),*slots,info['token'],info['pump'],info['meteora'],direction,size,'HOLD_'+reason,0,None,reason))
    return results,stats

def run():
    disarm()
    import build_oracle_269_persistent_token_lifecycle as life
    import build_oracle_270_verified_pool_ws_lifecycle as bridge
    import build_oracle_299_fresh_quote_activation as batch
    import build_oracle_304_canonical_reconnect as old
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    inv=bridge.inventory(bridge.INPUTS,set(life.load(life.DB)['tokens']))
    cache=json.loads(CACHE.read_text(encoding='utf-8'))
    if cache.get('build')!='ORACLE279' or not isinstance(cache.get('pools'),dict):raise RuntimeError('CACHE_UNTRUSTED')
    stage=pairs_from_inventory(inv,cache,2)
    if not stage:raise RuntimeError('NO_CACHED_PAIRED_BIN_INVENTORY')
    first_addresses=selection(stage)
    if not 1<=len(first_addresses)<=100:raise RuntimeError('FIRST_BATCH_TOO_LARGE')
    url=os.getenv('SOLANA_RPC_URL','')
    first_slot,first,first_holds=unpack_rpc(batch.perform_rpc(url,first_addresses),first_addresses)
    second_addresses,decoded,discovery_holds=dependency_addresses(stage,first,core.decode_pump_pool)
    if not 1<=len(second_addresses)<=100:raise RuntimeError('SECOND_BATCH_TOO_LARGE')
    second_slot,second,second_holds=unpack_rpc(batch.perform_rpc(url,second_addresses),second_addresses)
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    old.freeze_network()
    q18,core=old.native_contract()
    records={**first,**second};decimals={}
    for mint in {x['token'] for x in stage}|{WSOL}:
        try:decimals[mint]=mint_decimals(records.get(mint),mint)
        except ValueError:pass
    ready=[];hydration_holds=Counter()
    for item in stage:
        if item['token'] not in decimals or WSOL not in decimals:hydration_holds['TOKEN_MINT_DECIMALS_MISSING']+=1;continue
        pairs,holds=hydrate([item],records,decoded,core,decimals)
        ready.extend(pairs);hydration_holds.update(holds)
    quotes,stats=evaluate(ready,q18,(first_slot,second_slot))
    con=ledger()
    try:
        con.executemany('INSERT INTO quotes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',quotes);con.commit()
    finally:con.close()
    report={'build':'ORACLE305','status':'NATIVE_TWO_VENUE_CANDIDATE_EVIDENCE' if ready else 'HOLD_PAIR_COMPLETE_STATE',
      'targeted_pairs':len(stage),'first_batch_accounts':len(first_addresses),'second_batch_accounts':len(second_addresses),
      'first_slot':first_slot,'second_slot':second_slot,'slot_gap':abs(second_slot-first_slot),'hydrated_pairs':len(ready),
      'pair_holds':dict(hydration_holds),'dependency_holds':dict(discovery_holds),
      'account_holds':{'first':dict(first_holds),'second':dict(second_holds)},'quote_rows':len(quotes),
      'quote_classifications':dict(stats),'gross_positive_candidates':stats['GROSS_POSITIVE_CANDIDATE'],
      'rpc_calls':2,'pricing_rpc_calls':0,'snapshot_atomic_same_slot':first_slot==second_slot,
      'net_profit_certified':False,'atomic_certified':False,'execution_admission':False,'signing':False,'broadcast':False}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE305_RESULT]',json.dumps(report,sort_keys=True),flush=True)
    for r in sorted((r for r in quotes if r[8]=='GROSS_POSITIVE_CANDIDATE'),key=lambda r:r[10],reverse=True)[:12]:
        print('[ORACLE305_CANDIDATE]',json.dumps({'token':r[3],'direction':r[6],'size_sol':r[7],'gross_bps':round(r[10],3),'slots':[r[1],r[2]]}),flush=True)
    print('[REPORT]',REPORT,flush=True)
    if getattr(q18,'_worker',None) is not None:q18._worker.close()

def test():
    token='t';pairs={'a':[(token,'PUMPSWAP_WS')],'b':[(token,'METEORA_WS')]}
    cache={'pools':{'b':{'historical_only':True,'token':token,'addresses':[{'address':'c','array_index':1}]}}}
    found=pairs_from_inventory(pairs,cache)
    assert len(found)==1 and selection(found)==['a','b','c']
    sample=lambda snap,size:[{'direction':'PUMP_TO_METEORA','local_end':round(size*1e9)+42},
          {'direction':'METEORA_TO_PUMP','local_end':round(size*1e9)-42}]
    class Fake:exact_snapshot_opportunities=staticmethod(sample)
    rows,stats=evaluate([(found[0],{})],Fake,(1,2))
    assert len(rows)==38 and stats['GROSS_POSITIVE_CANDIDATE']==19
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.1
    assert len(unpack_rpc({'result':{'context':{'slot':10},'value':[None]}},['a'])[1])==0
    print('[ORACLE305_TEST_PASS] prioritized_complete_pairs=TRUE two_batches=TRUE native_function=TRUE grid19=TRUE ledger=TRUE no_orders=TRUE')

def table():
    if not LEDGER.exists():print('[ORACLE305] NO_QUOTE_EVIDENCE');return
    con=ledger()
    for token,direction,size,bps,status in con.execute('SELECT token,direction,size_sol,gross_bps,status FROM quotes ORDER BY rowid DESC LIMIT 40'):
        print(f'{token[:12]:12} {direction:17} {size:.3f} {str(round(bps,3)) if bps is not None else "-":>9} {status}')
    print('[GATE] Historical two-slot candidate quotes only. Net fees, atomic simulation and execution NOT certified.')
    con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.run:run()
    elif a.table:table()
    else:p.error('Select --test, --run or --table')
