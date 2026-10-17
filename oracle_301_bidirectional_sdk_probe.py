"""ORACLE-301: real SDK bidirectional Meteora quote coverage, not cross-venue arbitrage."""
import argparse,hashlib,json,os,socket,sqlite3,tempfile,time
from collections import Counter
from pathlib import Path
ROOT=Path('runtime_state/oracle/oracle_live_execution')
OUT=ROOT/'ORACLE301_BIDIRECTIONAL_SDK_EVIDENCE.json'
GRID=tuple(round(.010+i*.005,3) for i in range(19))
OWNER='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def network_block():
    def blocked(*args,**kwargs):raise RuntimeError('PRICING_NETWORK_FORBIDDEN')
    socket.create_connection=blocked
    socket.socket.connect=blocked
    socket.socket.connect_ex=blocked

def classify(q,asked):
    left=int(getattr(q,'remaining_in',asked))
    got=int(getattr(q,'amount_out',0))
    if left<0 or left>asked or got<0:return 'INVALID_QUOTE',got,left
    if left>0:return 'PARTIAL_FILL',got,left
    if getattr(q,'complete',False) is not True:return 'INCOMPLETE_NO_REMAINDER',got,left
    if got<=0:return 'ZERO_OUTPUT',got,left
    return 'FULL_FILL',got,0

def two_quotes(pool_bytes,bin_bytes,now,lamports,quote_fn=None,pool_type=None):
    from oracle_300_canonical_mint_quote import lb_pair_mints,WSOL
    x,y=lb_pair_mints(pool_bytes)
    if quote_fn is None:
        from meteora_dlmm import PoolState,quote
        quote_fn=quote;pool_type=PoolState
    state=pool_type.from_accounts(pool_bytes,bin_bytes,decimals_x=9,decimals_y=9)
    spend_x=(x==WSOL)
    try:a=quote_fn(state,amount_in=lamports,swap_for_y=spend_x,timestamp=int(now),strict=False)
    except Exception as exc:return {'forward':'SDK_'+type(exc).__name__,'reverse':'NOT_ATTEMPTED'}
    first,tokens,left=classify(a,lamports)
    row={'forward':first,'forward_token_out_raw':tokens,'forward_remaining_lamports':left,'reverse':'NOT_ATTEMPTED'}
    if first!='FULL_FILL':return row
    try:b=quote_fn(state,amount_in=tokens,swap_for_y=not spend_x,timestamp=int(now),strict=False)
    except Exception as exc:row['reverse']='SDK_'+type(exc).__name__;return row
    second,returned,remaining=classify(b,tokens)
    row.update(reverse=second,reverse_sol_out_lamports=returned,reverse_remaining_token_raw=remaining)
    if second=='FULL_FILL':
        row['same_venue_roundtrip_delta_lamports']=returned-lamports
        row['same_venue_roundtrip_bps']=(returned-lamports)*10000/lamports
    return row

def run():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    import oracle_283_287_milestone_a_runtime as market
    import oracle_294_298_local_quote_evidence as old
    import build_oracle_299_fresh_quote_activation as batch
    from urllib.parse import urlsplit
    selected=market.targets()
    if not 1<=len(selected)<=100:raise RuntimeError('ACCOUNT_COUNT_NOT_BATCHABLE')
    url=os.environ.get('SOLANA_RPC_URL','')
    if urlsplit(url).scheme!='https':raise RuntimeError('HTTPS_RPC_REQUIRED')
    payload=batch.perform_rpc(url,list(selected))
    rows,holds,slot=batch.decode_response(payload,selected,market.validate,time.time())
    # The only network boundary is above: all SDK work below is offline.
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    network_block()
    indexed={r[0]:{'slot':r[1],'owner':r[2],'sha':r[3],'raw':r[4]} for r in rows}
    _,pools=old.load_targets();stats=Counter();data=[]
    for pool,info in sorted(pools.items()):
        p=indexed.get(pool);bins=[];reason=None
        if p is None:reason='POOL_MISSING'
        elif p['owner']!=OWNER:reason='POOL_OWNER_INVALID'
        for address,index in sorted(info['bins'],key=lambda a:a[1]):
            b=indexed.get(address)
            if b is None:reason=reason or 'BIN_MISSING'
            elif b['owner']!=OWNER:reason=reason or 'BIN_OWNER_INVALID'
            elif p and abs(p['slot']-b['slot'])>250:reason=reason or 'SLOT_DISTANCE_HOLD'
            else:bins.append(b['raw'])
        if len(bins)!=len(info['bins']):reason=reason or 'INCOMPLETE_BIN_WINDOW'
        for size in GRID:
            row={'token':info['token'],'pool':pool,'size_sol':size,'snapshot_slot':slot}
            if reason:row['forward']=reason;row['reverse']='NOT_ATTEMPTED'
            else:
                try:row.update(two_quotes(p['raw'],bins,time.time(),round(size*1e9)))
                except Exception as exc:row.update(forward='SDK_'+type(exc).__name__,reverse='NOT_ATTEMPTED')
            stats['FORWARD_'+row['forward']]+=1;stats['REVERSE_'+row['reverse']]+=1
            data.append(row)
    report={'build':'ORACLE301','status':'LOCAL_BIDIRECTIONAL_METEORA_EVIDENCE',
        'snapshot_slot':slot,'account_batch_count':len(selected),'valid_accounts':len(rows),
        'account_holds':holds,'meteora_pools':len(pools),'size_grid':list(GRID),
        'sdk_quote_classifications':dict(stats),'observations':data,'rpc_calls':1,
        'pricing_rpc_calls':0,'cross_venue_opportunities_certified':0,
        'profit_after_fees_certified':False,'atomic_certified':False,
        'execution_admission':False,'signing':False,'broadcast':False}
    ROOT.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE301_RESULT]',json.dumps({k:v for k,v in report.items() if k not in ('observations','size_grid')},sort_keys=True),flush=True)
    for r in data:
        if r.get('forward')=='FULL_FILL':
            print('[ORACLE301_QUOTE]',json.dumps(r,sort_keys=True),flush=True)
    print('[REPORT]',OUT)

def test():
    import sys,types
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.1
    assert classify(types.SimpleNamespace(remaining_in=0,amount_out=42,complete=True),100)==('FULL_FILL',42,0)
    assert classify(types.SimpleNamespace(remaining_in=8,amount_out=42,complete=True),100)[0]=='PARTIAL_FILL'
    assert classify(types.SimpleNamespace(remaining_in=0,amount_out=42,complete=False),100)[0]=='INCOMPLETE_NO_REMAINDER'
    from oracle_300_canonical_mint_quote import WSOL,ALPHABET
    v=0
    for c in WSOL:v=v*58+ALPHABET.index(c)
    raw=bytearray(904);raw[88:120]=v.to_bytes(32,'big');raw[120:152]=bytes([7])*32
    calls=[]
    class P:
        @staticmethod
        def from_accounts(*args,**kwargs):return 'pool'
    def quote(state,amount_in,swap_for_y,timestamp,strict):
        calls.append((amount_in,swap_for_y))
        return types.SimpleNamespace(amount_out=amount_in*2 if len(calls)==1 else amount_in//3,
                                     remaining_in=0,complete=True)
    result=two_quotes(bytes(raw),[b'array'],100,100,quote,P)
    assert result['forward']=='FULL_FILL' and result['reverse']=='FULL_FILL'
    assert calls==[(100,True),(200,False)]
    assert result['same_venue_roundtrip_delta_lamports']==-34
    calls.clear()
    def partial(*args,**kwargs):return types.SimpleNamespace(amount_out=50,remaining_in=1,complete=True)
    assert two_quotes(bytes(raw),[],100,100,partial,P)['reverse']=='NOT_ATTEMPTED'
    print('[ORACLE301_TEST_PASS] real_token_input_sizing=TRUE mint_direction=TRUE partial_separated=TRUE 19_sizes=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.run:run()
    else:p.error('Choose --test or --run')
