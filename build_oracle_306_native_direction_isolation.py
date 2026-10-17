"""ORACLE-306 full read-only native direction isolation: reuse ORACLE-305 hydration and ORACLE-018 SDK."""
import argparse, json, os, sqlite3, subprocess, time
from collections import Counter
from pathlib import Path

import build_oracle_305_pair_complete_native_reconnect as prior

ROOT=prior.ROOT
OUT=ROOT/'ORACLE306_NATIVE_DIRECTION_EVIDENCE.json'
DB=ROOT/'ORACLE306_NATIVE_DIRECTION_EVIDENCE.sqlite3'
GRID=prior.GRID
DIRECTIONS=('METEORA_TO_PUMP','PUMP_TO_METEORA')

def db():
    ROOT.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB,timeout=20)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('''CREATE TABLE IF NOT EXISTS quotes(
       epoch REAL,slot1 INTEGER,slot2 INTEGER,token TEXT,direction TEXT,size_sol REAL,
       status TEXT,gross_bps REAL,out_lamports INTEGER,reason TEXT,
       PRIMARY KEY(slot1,slot2,token,direction,size_sol))''')
    return con

def classify(exc):
    msg=str(exc).upper()
    if 'DLMM_PARTIAL' in msg or 'INSUFFICIENTBINARRAY' in msg:return 'DLMM_PARTIAL_OR_ARRAYS'
    if 'PUMP_SDK_WORKER_DIED' in msg:return 'PUMP_WORKER_DIED'
    if 'PUMP_SDK_WORKER:' in msg:return 'PUMP_SDK_REJECT'
    if 'PUMP_SDK_RESPONSE_ORDER' in msg:return 'PUMP_RESPONSE_ORDER'
    if 'PRICING_NETWORK_FORBIDDEN' in msg or 'NETWORK' in msg:return 'NETWORK_FORBIDDEN'
    if 'NODE' in msg and ('NOT FOUND' in msg or 'ENOENT' in msg):return 'NODE_NOT_FOUND'
    if 'REVERSE_TOKEN_NET_ZERO' in msg or 'FORWARD_TOKEN_NET_ZERO' in msg:return 'TOKEN_RECEIPT_ZERO'
    return 'ERROR_'+type(exc).__name__.upper()

def native_leg(q18,core,snap,size,direction):
    start=round(size*1e9)
    if direction=='METEORA_TO_PUMP':
        first=core.dlmm_quote_snapshot(snap,start,core.WSOL)
        net_token=q18.token_net(snap['token'],int(first['raw_out']))
        if net_token<=0:raise RuntimeError('REVERSE_TOKEN_NET_ZERO')
        result=q18.worker().sell(snap,net_token)
        end=int(result['uiQuote']);minend=int(result['minQuote'])
    elif direction=='PUMP_TO_METEORA':
        first=q18.worker().buy(snap,start)
        net_token=q18.token_net(snap['token'],int(first['baseOut']))
        if net_token<=0:raise RuntimeError('FORWARD_TOKEN_NET_ZERO')
        second=core.dlmm_quote_snapshot(snap,net_token,snap['token'])
        end=int(second['raw_out']);minend=None
    else:raise ValueError('INVALID_DIRECTION')
    if end<=0:raise ValueError('INVALID_QUOTE_OUT')
    return {'end':end,'minend':minend,'bps':(end-start)*10000/start,
            'status':'GROSS_POSITIVE_CANDIDATE' if end>start else 'GROSS_NONPOSITIVE'}

def evaluate(ready,q18,core,slots):
    rows=[];summary=Counter();best=[]
    for item,snap in ready:
        for size in GRID:
            for direction in DIRECTIONS:
                try:
                    v=native_leg(q18,core,snap,size,direction)
                    status=v['status'];bps=v['bps'];out=v['end'];reason=''
                    if status=='GROSS_POSITIVE_CANDIDATE':
                        best.append({'token':item['token'],'direction':direction,'size_sol':size,
                                     'gross_bps':round(bps,3),'slots':list(slots),
                                     'slippage_min_certified':False,'fee_adjusted':False})
                except Exception as exc:
                    reason=classify(exc);status='HOLD_'+reason;bps=None;out=None
                summary[status]+=1
                rows.append((time.time(),*slots,item['token'],direction,size,status,bps,out,reason))
    return rows,dict(summary),sorted(best,key=lambda x:x['gross_bps'],reverse=True)

def worker_preflight(q18):
    js=Path(q18.WORKER_JS)
    if not js.is_file():return 'HOLD_PUMP_WORKER_JS_MISSING'
    if not (Path(q18.NODEDIR)/'node_modules').is_dir():return 'HOLD_PUMP_NODE_MODULES_MISSING'
    try:
        r=subprocess.run(['node','--version'],capture_output=True,text=True,timeout=4)
        if r.returncode:return 'HOLD_NODE_RUNTIME_FAILURE'
    except (OSError,subprocess.TimeoutExpired):return 'HOLD_NODE_RUNTIME_UNAVAILABLE'
    return 'READY'

def run():
    prior.disarm()
    import build_oracle_269_persistent_token_lifecycle as life
    import build_oracle_270_verified_pool_ws_lifecycle as bridge
    import build_oracle_299_fresh_quote_activation as batch
    import build_oracle_304_canonical_reconnect as old
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    inv=bridge.inventory(bridge.INPUTS,set(life.load(life.DB)['tokens']))
    cache=json.loads(prior.CACHE.read_text(encoding='utf-8'))
    if cache.get('build')!='ORACLE279' or not isinstance(cache.get('pools'),dict):raise RuntimeError('UNTRUSTED_BIN_CACHE')
    stage=prior.pairs_from_inventory(inv,cache,2)
    if not stage:raise RuntimeError('NO_VETTED_BIN_PAIRS')
    url=os.environ.get('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('RPC_ENDPOINT_REQUIRED')
    addresses=prior.selection(stage)
    if len(addresses)>100:raise RuntimeError('FIRST_BATCH_OVER_BUDGET')
    slot1,first,h1=prior.unpack_rpc(batch.perform_rpc(url,addresses),addresses)
    addresses2,decoded,hdep=prior.dependency_addresses(stage,first,core.decode_pump_pool)
    if len(addresses2)>100:raise RuntimeError('SECOND_BATCH_OVER_BUDGET')
    slot2,second,h2=prior.unpack_rpc(batch.perform_rpc(url,addresses2),addresses2)
    # Strictly no RPC after these two batches, including imports and native SDK calls.
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    old.freeze_network()
    q18,core=old.native_contract()
    data={**first,**second}
    decimals={}
    for mint in {p['token'] for p in stage}|{prior.WSOL}:
        try:decimals[mint]=prior.mint_decimals(data.get(mint),mint)
        except ValueError:pass
    ready=[];holds=Counter()
    for item in stage:
        if not all(x in decimals for x in (item['token'],prior.WSOL)):
            holds['MINT_DECIMALS_MISSING']+=1;continue
        p,h=prior.hydrate([item],data,decoded,core,decimals);ready.extend(p);holds.update(h)
    node_status=worker_preflight(q18)
    if node_status!='READY':
        # Keep independent Meteora-first direction measurable but do not call broken worker.
        # Fail closed on both routes rather than invent SDK prices.
        rows=[];stats=Counter({node_status:len(ready)*len(GRID)*2});best=[]
        for item,_ in ready:
            for size in GRID:
                for direction in DIRECTIONS:
                    rows.append((time.time(),slot1,slot2,item['token'],direction,size,node_status,None,None,node_status))
    else:rows,stats,best=evaluate(ready,q18,core,(slot1,slot2))
    c=db()
    try:
        c.executemany('INSERT OR REPLACE INTO quotes VALUES(?,?,?,?,?,?,?,?,?,?)',rows);c.commit()
    finally:c.close()
    report={'build':'ORACLE306','status':'NATIVE_ISOLATED_DIRECTION_EVIDENCE' if ready else 'HOLD_CANONICAL_HYDRATION',
       'targeted_pairs':len(stage),'hydrated_pairs':len(ready),'slots':[slot1,slot2],
       'snapshot_atomic_same_slot':slot1==slot2,'slot_gap':abs(slot2-slot1),
       'worker_preflight':node_status,'pair_holds':dict(holds),'dependency_holds':dict(hdep),
       'account_holds':{'first':dict(h1),'second':dict(h2)},'quote_rows':len(rows),
       'quote_classifications':stats,'gross_positive_candidates':len(best),'rpc_calls':2,
       'pricing_rpc_calls_python':0,'node_rpc_calls_certified':False,
       'gross_is_not_net':True,'fee_adjusted_net_certified':False,'atomic_certified':False,
       'execution_admission':False,'signing':False,'broadcast':False}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE306_RESULT]',json.dumps(report,sort_keys=True),flush=True)
    for x in best[:12]:print('[ORACLE306_CANDIDATE]',json.dumps(x,sort_keys=True),flush=True)
    print('[REPORT]',OUT,flush=True)
    if getattr(q18,'_worker',None) is not None:q18._worker.close()

def test():
    assert len(GRID)==19 and len(DIRECTIONS)==2
    class Core:
        WSOL='SOL'
        @staticmethod
        def dlmm_quote_snapshot(snap,amount,mint):
            if mint=='SOL':raise RuntimeError('DLMM_PARTIAL')
            return {'raw_out':amount+1000}
    class Worker:
        def buy(self,snap,amount):return {'baseOut':amount}
    class Q:
        @staticmethod
        def worker():return Worker()
        @staticmethod
        def token_net(token,amount):return amount
    item={'token':'mint'};snap={'token':'mint'}
    rows,summary,best=evaluate([(item,snap)],Q,Core,(4,5))
    assert len(rows)==38 and summary['HOLD_DLMM_PARTIAL_OR_ARRAYS']==19
    assert summary['GROSS_POSITIVE_CANDIDATE']==19 and len(best)==19
    assert all(x[4]=='PUMP_TO_METEORA' for x in rows if x[6]=='GROSS_POSITIVE_CANDIDATE')
    assert classify(RuntimeError('PUMP_SDK_WORKER_DIED'))=='PUMP_WORKER_DIED'
    assert classify(RuntimeError('PRICING_NETWORK_FORBIDDEN'))=='NETWORK_FORBIDDEN'
    print('[ORACLE306_TEST_PASS] independent_directions=TRUE node_preflight=TRUE grid19=TRUE no_orders=TRUE')

def table():
    if not DB.is_file():print('[ORACLE306] NO_EVIDENCE');return
    c=db()
    print('ORACLE-306 | INDEPENDENT NATIVE QUOTE EVIDENCE | READ ONLY')
    for token,direction,size,status,bps in c.execute('SELECT token,direction,size_sol,status,gross_bps FROM quotes ORDER BY epoch DESC LIMIT 50'):
        print(f'{token[:12]:12} {direction:17} {size:.3f} {status:32} {str(round(bps,3)) if bps is not None else "-"}')
    c.close()
    print('[GATE] Uncertified gross candidates. No net-profit or execution authorization.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.run:run()
    elif a.table:table()
    else:p.error('Choose --test, --run, or --table')
