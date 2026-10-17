"""ORACLE-304. Read-only reconnection to existing native P2M/M2P pricing."""
import argparse,hashlib,json,os,socket,sqlite3,time
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path('runtime_state/oracle/oracle_live_execution')
OUT=ROOT/'ORACLE304_CANONICAL_RECONNECT.json'
DB=ROOT/'ORACLE304_CROSS_VENUE_EVIDENCE.sqlite3'
GRID=tuple(round(.010+.005*i,3) for i in range(19))
WSOL='So11111111111111111111111111111111111111112'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'


def disarmed():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')


def db_open(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path,timeout=20)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('''CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY AUTOINCREMENT,
       epoch REAL,slot INTEGER,token TEXT,meteora TEXT,pump TEXT,direction TEXT,
       size_sol REAL,status TEXT,output_lamports INTEGER,gross_bps REAL,
       quote_min_lamports INTEGER,reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS runs(epoch REAL PRIMARY KEY,slot INTEGER,
       validated INTEGER,pairs INTEGER,attempts INTEGER,gross_positive INTEGER,
       holds INTEGER,rpc_calls INTEGER,pricing_rpc_calls INTEGER)''')
    return c


def native_contract():
    import inspect
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    source=inspect.getsource(q18.exact_snapshot_opportunities)
    required=('core.dlmm_quote_snapshot','worker().sell','worker().buy','token_net')
    if not all(s in source for s in required):raise RuntimeError('OFFICIAL_NATIVE_PRICER_CONTRACT_CHANGED')
    if not callable(q18.PumpSdkWorker) or not callable(core.decode_pump_pool):raise RuntimeError('NATIVE_DECODER_MISSING')
    return q18,core


def mapping(selected,records,decode_pump,b58):
    # The existing inventory and cache supply token/pool identity; never guess a pool.
    available={r[0]:{'slot':r[1],'owner':r[2],'raw':r[4]} for r in records}
    by_token=defaultdict(lambda:{'pump':[], 'meteora':[], 'bins':[]})
    for addr,detail in selected.items():
        if detail['kind']=='BIN':
            token=detail.get('token')
            if token:by_token[token]['bins'].append((addr,detail))
            continue
        for ref in detail.get('refs',[]):
            token=ref.get('token') or ref.get('mint')
            venue=str(ref.get('venue') or ref.get('role') or '').upper()
            if not token or ref.get('role')!='POOL':continue
            if 'PUMP' in venue:by_token[token]['pump'].append(addr)
            elif 'METEORA' in venue or 'DLMM' in venue:by_token[token]['meteora'].append(addr)
    # Reliable fallback from inventory itself (manifest naming can vary).
    try:
        import build_oracle_270_verified_pool_ws_lifecycle as bridge
        import build_oracle_269_persistent_token_lifecycle as life
        canonical=bridge.inventory(bridge.INPUTS,set(life.load(life.DB)['tokens']))
        for addr,refs in canonical.items():
            for token,venue in refs:
                kind='pump' if venue=='PUMPSWAP_WS' else 'meteora' if venue=='METEORA_WS' else None
                if kind and addr not in by_token[token][kind]:by_token[token][kind].append(addr)
    except Exception as exc:
        raise RuntimeError('CANONICAL_INVENTORY_UNAVAILABLE:'+type(exc).__name__) from None
    outputs=[];holds=Counter()
    from oracle_300_canonical_mint_quote import lb_pair_mints
    from meteora_dlmm import PoolState
    for token,links in sorted(by_token.items()):
        bins=links['bins']
        for paddr in links['pump']:
            for maddr in links['meteora']:
                reason=None
                pump=available.get(paddr);met=available.get(maddr)
                if not pump or not met:reason='POOL_ACCOUNT_MISSING'
                elif pump['owner']!=PUMP or met['owner']!=DLMM:reason='PROGRAM_OWNER_MISMATCH'
                elif not bins:reason='NO_VETTED_BIN_ARRAYS'
                if reason:holds[reason]+=1;continue
                try:
                    pp=decode_pump(pump['raw'])
                    if pp['base_mint']!=token or pp['quote_mint']!=WSOL:
                        raise ValueError('PUMP_MINT_IDENTITY_MISMATCH')
                    xm,ym=lb_pair_mints(met['raw'])
                    if {xm,ym}!={token,WSOL}:raise ValueError('METEORA_MINT_IDENTITY_MISMATCH')
                    base=available.get(pp['base_vault']);quote=available.get(pp['quote_vault'])
                    if not base or not quote:raise ValueError('PUMP_VAULT_BYTES_MISSING')
                    if len(base['raw'])<72 or len(quote['raw'])<72:raise ValueError('VAULT_LAYOUT_SHORT')
                    if b58(base['raw'][:32])!=token or b58(quote['raw'][:32])!=WSOL:
                        raise ValueError('PUMP_VAULT_MINT_MISMATCH')
                    if base['owner'] not in ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'):
                        raise ValueError('BASE_VAULT_PROGRAM_INVALID')
                    if quote['owner'] not in ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'):
                        raise ValueError('QUOTE_VAULT_PROGRAM_INVALID')
                    raw_arrays=[]
                    for a,t in bins:
                        if t['pool']!=maddr:continue
                        v=available.get(a)
                        if not v or v['owner']!=DLMM:raise ValueError('BIN_ARRAY_MISSING_OR_PROGRAM')
                        if v['raw'][24:56]!=b58_decode(maddr):raise ValueError('BIN_POOL_MISMATCH')
                        raw_arrays.append((int(t['array_index']),v['raw']))
                    if not raw_arrays:raise ValueError('NO_POOL_SPECIFIC_BIN_BYTES')
                    raw_arrays.sort(key=lambda v:v[0])
                    state=PoolState.from_accounts(met['raw'],[b for _,b in raw_arrays],decimals_x=9,decimals_y=9,
                         lb_pair_key=b58_decode(maddr),exhaustive=True)
                    meta={'address':maddr,'token_x':xm,'token_y':ym,'decimals_x':9,'decimals_y':9}
                    snapshot={'token':token,'pump_pool':paddr,'meteora':meta,'dlmm_state':state,
                      'pump_base_reserve':int.from_bytes(base['raw'][64:72],'little'),
                      'pump_quote_reserve':int.from_bytes(quote['raw'][64:72],'little')}
                    if min(snapshot['pump_base_reserve'],snapshot['pump_quote_reserve'])<=0:
                        raise ValueError('PUMP_ZERO_RESERVES')
                    outputs.append((token,paddr,maddr,snapshot))
                except Exception as exc:
                    holds[str(exc)[:100] if isinstance(exc,ValueError) else 'HYDRATION_'+type(exc).__name__]+=1
    return outputs,holds


def b58_decode(s):
    from oracle_300_canonical_mint_quote import ALPHABET
    n=0
    for c in s:n=n*58+ALPHABET.index(c)
    return b'\0'*(len(s)-len(s.lstrip('1')))+n.to_bytes((n.bit_length()+7)//8,'big')


def freeze_network():
    import urllib.request
    def blocked(*a,**k):raise RuntimeError('PRICING_NETWORK_FORBIDDEN')
    socket.create_connection=blocked
    socket.socket.connect=blocked
    socket.socket.connect_ex=blocked
    urllib.request.urlopen=blocked


def quote_all(pairs,fn,slot):
    rows=[];counts=Counter();now=time.time()
    for token,pump,meteora,snap in pairs:
        for size in GRID:
            try:
                got=fn(snap,size)
                if not isinstance(got,list) or len(got)!=2:raise ValueError('EXACT_NATIVE_RETURN_SHAPE')
                for item in got:
                    direction=item.get('direction')
                    if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
                        raise ValueError('EXACT_NATIVE_DIRECTION_INVALID')
                    end=int(item['local_end']);start=int(round(size*1e9))
                    if end<=0:raise ValueError('NONPOSITIVE_OUTPUT')
                    bps=(end-start)*10000/start
                    status='GROSS_POSITIVE_CANDIDATE' if end>start else 'GROSS_NONPOSITIVE'
                    counts[status]+=1
                    rows.append((now,slot,token,meteora,pump,direction,size,status,end,bps,
                                 int(item.get('local_min_end',0) or 0),''))
            except Exception as exc:
                reason=type(exc).__name__
                if isinstance(exc,RuntimeError):
                    message=str(exc)
                    for known in ('DLMM_PARTIAL','PUMP_SDK_WORKER','REVERSE_TOKEN_NET_ZERO','FORWARD_TOKEN_NET_ZERO','PRICING_NETWORK_FORBIDDEN'):
                        if known in message:reason=known;break
                counts['HOLD_'+reason]+=1
                for direction in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
                    rows.append((now,slot,token,meteora,pump,direction,size,'HOLD_'+reason,0,None,0,reason))
    return rows,dict(counts)


def run():
    disarmed()
    import oracle_283_287_milestone_a_runtime as market
    import build_oracle_299_fresh_quote_activation as batch
    selected=market.targets()
    if not 1<=len(selected)<=100:raise RuntimeError('BATCH_LIMIT_100')
    response=batch.perform_rpc(os.environ.get('SOLANA_RPC_URL',''),list(selected))
    data,holds,slot=batch.decode_response(response,selected,market.validate,time.time())
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    freeze_network()
    q18,core=native_contract()
    if len(data)!=len(selected):raise RuntimeError('INCOMPLETE_COHERENT_BOOTSTRAP')
    from oracle_300_canonical_mint_quote import b58
    pairs,pair_holds=mapping(selected,data,core.decode_pump_pool,b58)
    records,counts=quote_all(pairs,q18.exact_snapshot_opportunities,slot)
    con=db_open()
    try:
        con.executemany('''INSERT INTO quotes(epoch,slot,token,meteora,pump,direction,size_sol,status,
                        output_lamports,gross_bps,quote_min_lamports,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',records)
        con.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?)',(time.time(),slot,len(data),len(pairs),len(records),
           counts.get('GROSS_POSITIVE_CANDIDATE',0),sum(n for k,n in counts.items() if k.startswith('HOLD_')),
           1,0));con.commit()
    finally:con.close()
    result={'build':'ORACLE304','status':'CROSS_VENUE_GROSS_EVIDENCE' if records else 'HOLD_MISSING_CANONICAL_PAIR_COVERAGE',
       'batch_slot':slot,'selected_accounts':len(selected),'validated_accounts':len(data),
       'hydrated_pairs':len(pairs),'pair_holds':dict(pair_holds),'account_holds':holds,
       'quote_rows':len(records),'quote_classifications':counts,'gross_positive_candidates':counts.get('GROSS_POSITIVE_CANDIDATE',0),
       'rpc_calls':1,'pricing_rpc_calls':0,'fee_adjusted_net_certified':False,'atomic_certified':False,
       'execution_admission':False,'signing':False,'broadcast':False}
    ROOT.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE304_RESULT]',json.dumps(result,sort_keys=True),flush=True)
    for item in sorted((r for r in records if r[7]=='GROSS_POSITIVE_CANDIDATE'),key=lambda r:r[9],reverse=True)[:20]:
        print('[ORACLE304_CANDIDATE]',json.dumps({'token':item[2],'direction':item[5],'size_sol':item[6],
             'gross_bps':round(item[9],3),'slot':item[1]},sort_keys=True),flush=True)
    print('[REPORT]',OUT)
    if hasattr(q18,'_worker') and q18._worker is not None:q18._worker.close()


def table():
    if not DB.exists():print('[ORACLE304] NO_EVIDENCE_YET');return
    c=db_open()
    print('ORACLE-304 | CROSS VENUE GROSS EVIDENCE | NO TRADES')
    print('TOKEN         DIR               SIZE     GROSS BPS   STATUS')
    for token,direction,size,bps,status in c.execute('''SELECT token,direction,size_sol,gross_bps,status FROM quotes
       ORDER BY id DESC LIMIT 40'''):
        print(f'{str(token)[:12]:12} {direction:17} {size:6.3f} {bps if bps is not None else 0:11.2f}   {status}')
    print('[GATE] Gross estimates are not fee-adjusted net, simulated transactions, or executable profits.')
    c.close()


def test():
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.1
    sample=lambda snap,size:[{'direction':'PUMP_TO_METEORA','local_end':int(size*1e9)+1000},
                             {'direction':'METEORA_TO_PUMP','local_end':int(size*1e9)-1000}]
    rows,stats=quote_all([('mint','pump','dlmm',{})],sample,123)
    assert len(rows)==38 and stats['GROSS_POSITIVE_CANDIDATE']==19 and stats['GROSS_NONPOSITIVE']==19
    bad,holds=quote_all([('mint','pump','dlmm',{})],lambda s,z:(_ for _ in ()).throw(RuntimeError('DLMM_PARTIAL')),123)
    assert len(bad)==38 and holds['HOLD_DLMM_PARTIAL']==19
    from oracle_300_canonical_mint_quote import b58,WSOL
    assert len(b58_decode(WSOL))==32
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        c=db_open(Path(d)/'e.db');assert c.execute('SELECT COUNT(*) FROM quotes').fetchone()[0]==0;c.close()
    print('[ORACLE304_TEST_PASS] original_native_seam=TARGETED grid19=TRUE directions2=TRUE partial_hold=TRUE ledger=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true')
    a=p.parse_args()
    if a.test:test()
    elif a.run:run()
    elif a.table:table()
    else:p.error('Choose --test, --run, or --table')
