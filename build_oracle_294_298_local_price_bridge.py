"""ORACLE-294..298 full installer: audited, offline SDK evidence bridge. No scanner modification."""
import argparse, py_compile
from pathlib import Path
TARGET=Path('oracle_294_298_local_quote_evidence.py')
SOURCE=r'''"""ORACLE294-298: persisted raw-byte -> Meteora exact-in SDK quote evidence.
No network, trading, signing, broadcast, or claims of cross-venue profit.
"""
import argparse, hashlib, json, os, sqlite3, time
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path('runtime_state/oracle/oracle_live_execution')
MARKET=ROOT/'ORACLE283_287_MARKET_EVIDENCE.sqlite3'
MRIYA=ROOT/'ORACLE289_293_MRIYA_EVIDENCE.sqlite3'
DB=ROOT/'ORACLE294_298_LOCAL_PRICE_EVIDENCE.sqlite3'
OWNER='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
WSOL='So11111111111111111111111111111111111111112'
GRID=tuple(round(.010+.005*i,3) for i in range(19))

def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_PROCESS_REQUIRED')
    # Protect from accidental hidden network in quoted SDK or imported modules.
    import socket
    def no_connection(*args,**kwargs):raise RuntimeError('LOCAL_PRICER_NETWORK_FORBIDDEN')
    socket.create_connection=no_connection
    socket.socket.connect=no_connection
    socket.socket.connect_ex=no_connection

def database(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path,timeout=15)
    c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA busy_timeout=15000')
    c.executescript("""CREATE TABLE IF NOT EXISTS observations(
      run_id INTEGER,pool TEXT,token TEXT,direction TEXT,size_sol REAL,source_slot INTEGER,
      status TEXT,amount_in_raw INTEGER,amount_out_raw INTEGER,remaining_in_raw INTEGER,
      evidence_age REAL,reason TEXT,PRIMARY KEY(run_id,pool,direction,size_sol));
    CREATE TABLE IF NOT EXISTS runs(run_id INTEGER PRIMARY KEY,epoch REAL,pools INTEGER,
      available_bins INTEGER,quotes_attempted INTEGER,full_fill INTEGER,partial_fill INTEGER,
      mriya_matches INTEGER,rest_calls INTEGER,net_positive_certified INTEGER,readiness TEXT);
    CREATE TABLE IF NOT EXISTS token_admission(mint TEXT PRIMARY KEY,first_seen REAL,
      matched_inventory INTEGER,market_bytes_available INTEGER,last_seen REAL);
    """)
    return c

def load_targets():
    import oracle_283_287_milestone_a_runtime as m
    selected=m.targets()
    by_pool=defaultdict(lambda:{'bins':[],'pool_address':None,'token':None})
    for address,t in selected.items():
        if t['kind']=='BIN':
            p=by_pool[t['pool']];p['bins'].append((address,t['array_index']));p['pool_address']=t['pool']
            if t.get('token'):p['token']=t['token']
    return selected,dict(by_pool)

def fetch_account(con,address,now,max_age):
    row=con.execute('SELECT slot,owner,sha,raw,source,received FROM account_bytes WHERE address=?',(address,)).fetchone()
    if not row:return None,'ACCOUNT_MISSING'
    slot,owner,digest,raw,source,epoch=row
    if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=digest:return None,'HASH_MISMATCH'
    if not isinstance(slot,int) or slot<=0:return None,'INVALID_SLOT'
    age=now-epoch
    if not 0<=age<=max_age:return None,'STALE_ACCOUNT'
    return {'slot':slot,'owner':owner,'raw':raw,'source':source,'age':age},None

def mriya_mints():
    if not MRIYA.exists():return set()
    con=sqlite3.connect('file:'+str(MRIYA.resolve()).replace('\\','/')+'?mode=ro',uri=True)
    try:return {r[0] for r in con.execute('SELECT mint FROM tokens')}
    except sqlite3.OperationalError:return set()
    finally:con.close()

def inspect_pool(state):
    # SDK field names can change between pinned versions. Refuse to infer mint order from token name.
    for a,b in (('token_x_mint','token_y_mint'),('mint_x','mint_y'),('token_x','token_y')):
        x=getattr(state,a,None);y=getattr(state,b,None)
        if x is None or y is None:continue
        def string(v):
            if isinstance(v,(str,bytes)):return str(v)
            for attr in ('mint','address','pubkey'):
                item=getattr(v,attr,None)
                if item is not None:return str(item)
            return str(v)
        sx,sy=string(x),string(y)
        if WSOL in (sx,sy) and sx!=sy:return sx,sy
    return None,None

def sdk_quote(pool_bytes,arrays,now,side,amount):
    from meteora_dlmm import PoolState,quote
    state=PoolState.from_accounts(pool_bytes,arrays,decimals_x=9,decimals_y=9)
    x,y=inspect_pool(state)
    if not x:return 'HOLD_MINT_ORDER_NOT_CERTIFIED',0,amount
    swap_for_y=(x==WSOL) if side=='WSOL_TO_TOKEN' else (y==WSOL)
    # TOKEN_TO_WSOL cannot express trade size in SOL without a preliminary token sizing quote.
    if side=='TOKEN_TO_WSOL':return 'HOLD_TOKEN_INPUT_SIZE_NOT_DERIVED',0,amount
    result=quote(state,amount_in=amount,swap_for_y=swap_for_y,timestamp=int(now),strict=False)
    remaining=int(getattr(result,'remaining_in',0))
    output=int(getattr(result,'amount_out',0))
    complete=getattr(result,'complete',False) is True
    if not complete or remaining:return 'PARTIAL_OR_MISSING_LIQUIDITY',output,remaining
    if output<=0:return 'ZERO_OUTPUT',output,remaining
    return 'DLMM_FULL_FILL_ONE_LEG',output,0

def cycle(max_age):
    disarm();selected,pools=load_targets();now=time.time();run_id=time.time_ns()
    out=database(); market=sqlite3.connect('file:'+str(MARKET.resolve()).replace('\\','/')+'?mode=ro',uri=True)
    matches=mriya_mints();counts=Counter();rows=[];seen_tokens=set();available_bins=0
    try:
        for pool,info in sorted(pools.items()):
            token=info['token'];seen_tokens.add(token)
            account,reason=fetch_account(market,pool,now,max_age)
            bins=[];states=[]
            for address,index in sorted(info['bins'],key=lambda pair:pair[1]):
                bin_account,hold=fetch_account(market,address,now,max_age)
                if bin_account and bin_account['owner']==OWNER:
                    bins.append(bin_account['raw']);states.append(bin_account)
                else:counts['BIN_'+(hold or 'OWNER_MISMATCH')]+=1
            available_bins+=len(bins)
            hold=None
            if not account:hold='POOL_'+reason
            elif account['owner']!=OWNER:hold='POOL_OWNER_MISMATCH'
            elif len(bins)!=len(info['bins']):hold='INCOMPLETE_BIN_WINDOW'
            elif any(abs(a['slot']-account['slot'])>250 for a in states):hold='SLOT_DISTANCE_HOLD'
            elif not token:hold='TOKEN_IDENTITY_MISSING'
            for size in GRID:
                for direction in ('WSOL_TO_TOKEN','TOKEN_TO_WSOL'):
                    amount=round(size*1_000_000_000)
                    status=hold or ('HOLD_TOKEN_INPUT_SIZE_NOT_DERIVED' if direction=='TOKEN_TO_WSOL' else None)
                    output=remaining=0
                    if status is None:
                        counts['SDK_CALLS']+=1
                        try:status,output,remaining=sdk_quote(account['raw'],bins,now,direction,amount)
                        except Exception as exc:
                            status='SDK_REJECTED_'+type(exc).__name__
                    counts[status]+=1
                    rows.append((run_id,pool,token,direction,size,account['slot'] if account else 0,
                                 status,amount,output,remaining,max([account['age']]+[b['age'] for b in states]) if account else -1,status))
            out.execute('INSERT INTO token_admission VALUES(?,?,?,?,?) ON CONFLICT(mint) DO UPDATE SET matched_inventory=excluded.matched_inventory,market_bytes_available=excluded.market_bytes_available,last_seen=excluded.last_seen',
                        (token,now,int(token in matches),int(account is not None),now))
        for new_mint in sorted(matches-seen_tokens):
            out.execute('INSERT INTO token_admission VALUES(?,?,?,?,?) ON CONFLICT(mint) DO UPDATE SET last_seen=excluded.last_seen',
                        (new_mint,now,0,0,now))
        out.executemany('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',rows)
        out.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(
            run_id,now,len(pools),available_bins,counts['SDK_CALLS'],counts['DLMM_FULL_FILL_ONE_LEG'],
            counts['PARTIAL_OR_MISSING_LIQUIDITY'],len(matches & seen_tokens),0,0,
            'HOLD_SECOND_VENUE_EXACT_QUOTE_AND_FEES'))
        out.commit()
        report={'build':'ORACLE294_298','pools':len(pools),'bins_fresh':available_bins,
           'observation_rows':len(rows),'sdk_calls':counts['SDK_CALLS'],
           'dlmm_full_fill_one_leg':counts['DLMM_FULL_FILL_ONE_LEG'],
           'dlmm_partial':counts['PARTIAL_OR_MISSING_LIQUIDITY'],
           'mriya_discovered_mints':len(matches),'mriya_inventory_overlap':len(matches & seen_tokens),
           'statuses':dict(counts),'price_evidence_type':'METEORA_SINGLE_LEG_ONLY',
           'cross_venue_profit_certified':False,'rpc_calls':0,'signing':False,'broadcast':False}
        print('[ORACLE294_298_RESULT]',json.dumps(report,sort_keys=True),flush=True)
        return report
    finally:market.close();out.close()

def table():
    c=database()
    print('ORACLE LOCAL QUOTE EVIDENCE | METEORA ONE-LEG ONLY | NO TRADES')
    print('RUN ID              POOLS  BINS   SDK QUOTES  FULL FILL  PARTIAL  MRIYA MATCH')
    for r in c.execute('SELECT run_id,pools,available_bins,quotes_attempted,full_fill,partial_fill,mriya_matches FROM runs ORDER BY run_id DESC LIMIT 15'):
        print(f'{r[0]:19} {r[1]:6} {r[2]:5} {r[3]:11} {r[4]:10} {r[5]:8} {r[6]:12}')
    print('[GATE] PumpSwap second leg, executable sizing, transaction fees, net profit and atomic test NOT certified.')
    c.close()

def test():
    import tempfile
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.1
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'x.db';c=sqlite3.connect(p);c.execute('CREATE TABLE account_bytes(address TEXT,slot INTEGER,owner TEXT,sha TEXT,raw BLOB,source TEXT,received REAL)')
        raw=b'abc';h=hashlib.sha256(raw).hexdigest()
        c.execute('INSERT INTO account_bytes VALUES(?,?,?,?,?,?,?)',('A',42,OWNER,h,raw,'BATCH',1000.));c.commit()
        val,err=fetch_account(c,'A',1010.,120);assert err is None and val['raw']==raw
        assert fetch_account(c,'A',1200.,120)[1]=='STALE_ACCOUNT'
        c.execute('UPDATE account_bytes SET sha=?',('f'*64,));c.commit()
        assert fetch_account(c,'A',1010.,120)[1]=='HASH_MISMATCH';c.close()
        ledger=database(Path(d)/'ledger.db');assert ledger.execute('SELECT count(*) FROM runs').fetchone()[0]==0;ledger.close()
    class S:mint_x=WSOL;mint_y='token'
    assert inspect_pool(S())==(WSOL,'token')
    print('[ORACLE294_298_TEST_PASS] local_bytes=TRUE sha=TRUE stale_hold=TRUE mint_direction=TRUE grid19=TRUE ledger=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true')
    p.add_argument('--max-age',type=int,default=120);p.add_argument('--interval',type=int,default=30);p.add_argument('--cycles',type=int,default=1)
    a=p.parse_args()
    if a.test:test()
    elif a.table:table()
    elif a.run:
        for i in range(max(1,a.cycles)):
            cycle(max(1,a.max_age))
            if i+1<a.cycles:time.sleep(max(1,a.interval))
    else:p.error('Specify --test, --run, --table')
'''

def install():
    if TARGET.exists():
        head=TARGET.read_text(encoding='utf-8')[:160]
        if 'ORACLE294-298' not in head:raise RuntimeError('UNRECOGNIZED_FILE_REFUSE_OVERWRITE')
    TARGET.write_text(SOURCE,encoding='utf-8')
    py_compile.compile(str(TARGET),doraise=True)
    print('[ORACLE294_298_INSTALL_PASS] scanner_unchanged=TRUE market_db_read_only=TRUE signing=FALSE broadcast=FALSE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');a=p.parse_args()
    if not a.install:p.error('Specify --install')
    install()
