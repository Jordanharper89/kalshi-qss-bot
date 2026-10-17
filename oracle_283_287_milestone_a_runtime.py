"""ORACLE-283..287 Milestone A: long-running, disarmed market evidence service.
One capped initial getMultipleAccounts request; incremental accountSubscribe updates;
SQLite restart-safe observations; no trade instructions, simulation or local quote claims.
"""
import argparse, base64, hashlib, json, os, socket, sqlite3, time, urllib.request, urllib.error
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path('runtime_state/oracle/oracle_live_execution')
DB=ROOT/'ORACLE283_287_MARKET_EVIDENCE.sqlite3'
REPORT=ROOT/'ORACLE283_287_READINESS.json'
GRID=[round(.010+.005*i,3) for i in range(19)]
OWNER_DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
TOKEN_PROGRAMS={'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}
WSOL='So11111111111111111111111111111111111111112'
ABC='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58decode(s):
    if not isinstance(s,str):raise ValueError('BAD_BASE58')
    n=0
    for c in s:n=n*58+ABC.index(c)
    result=n.to_bytes((n.bit_length()+7)//8,'big') if n else b''
    result=b'\0'*(len(s)-len(s.lstrip('1')))+result
    if len(result)!=32:raise ValueError('BAD_ADDRESS')
    return result

def b58encode(raw):
    n=int.from_bytes(raw,'big');s=''
    while n:n,r=divmod(n,58);s=ABC[r]+s
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+s

def disarmed():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('FAIL_CLOSED_DISARMED_CHILD_REQUIRED')

def verified_json(path,build):
    obj=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,dict) or obj.get('build')!=build:
        raise RuntimeError('UNTRUSTED_'+build)
    if build=='ORACLE279':
        # ORACLE-279 caches are address manifests, NOT execution reports.
        # Their documented schema has build+pools, without authority flags.
        # Reject any authority fields if present and not explicitly False.
        if not isinstance(obj.get('pools'),dict):raise RuntimeError('UNTRUSTED_ORACLE279_CACHE_SCHEMA')
        if any(k in obj and obj[k] is not False for k in ('signing','broadcast','execution_admission')):
            raise RuntimeError('UNTRUSTED_ORACLE279_AUTHORITY')
    elif any(obj.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_'+build)
    return obj

def targets(root=ROOT):
    import build_oracle_269_persistent_token_lifecycle as life
    import build_oracle_270_verified_pool_ws_lifecycle as bridge
    import build_oracle_277_vault_ws_coverage as v277
    import build_oracle_280_bin_array_ws_capture as b280
    db=life.load(life.DB)
    pools=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    manifest=v277.manifest(verified_json(root/'ORACLE276_RESOLVED_DEPENDENCIES.json','ORACLE276'),pools)
    selected={}
    for addr,refs in manifest.items():
        b58decode(addr)
        selected[addr]={'kind':'VAULT' if any(r['role']!='POOL' for r in refs) else 'POOL','refs':refs}
    bin_targets=b280.manifest(verified_json(root/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json','ORACLE279'),2000)
    for addr,item in bin_targets.items():
        if addr in selected:raise RuntimeError('DUPLICATE_ACCOUNT_ROLE')
        selected[addr]={'kind':'BIN','pool':item['pool'],'array_index':item['array_index'],
                        'token':item['token'],'pool_raw':item['pool_raw']}
    return dict(sorted(selected.items()))

def validate(addr,target,owner,raw,slot,epoch):
    if not isinstance(raw,bytes) or not raw or len(raw)>240000 or type(slot) is not int or slot<=0:return None
    try:b58decode(addr);b58decode(owner)
    except (ValueError,TypeError):return None
    kind=target['kind'];detail={}
    if kind=='BIN':
        if owner!=OWNER_DLMM or len(raw)<56:return None
        if raw[24:56]!=target['pool_raw'] or int.from_bytes(raw[8:16],'little',signed=True)!=target['array_index']:return None
        detail={'pool':target['pool'],'array_index':target['array_index']}
    elif kind=='VAULT':
        if owner not in TOKEN_PROGRAMS or len(raw)<72:return None
        mint=b58encode(raw[:32]);expect=[r['expected_token_mint'] for r in target['refs'] if r['role']!='POOL']
        if not expect or any(x!=mint for x in expect):return None
        detail={'mint':mint,'amount_raw':int.from_bytes(raw[64:72],'little')}
    elif kind=='POOL':
        if len(raw)<64:return None
        # Identity and owner-program certification is not available for every pool type here.
        # Keep owner as observed evidence; do NOT call this canonical hydration.
    else:return None
    return {'address':addr,'kind':kind,'slot':slot,'received_epoch':epoch,'owner':owner,
            'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),
            'verified_account_identity':True,'canonical_hydrated':False,'detail':detail,'raw':raw}

def parse_rpc(payload,selected,epoch):
    obj=payload.get('result') if isinstance(payload,dict) and 'error' not in payload else None
    if not isinstance(obj,dict):raise RuntimeError('RPC_RESPONSE_INVALID')
    slot=obj.get('context',{}).get('slot');vals=obj.get('value')
    if type(slot) is not int or slot<=0 or not isinstance(vals,list) or len(vals)!=len(selected):raise RuntimeError('RPC_CARDINALITY_OR_SLOT')
    rows=[]
    for (addr,t),v in zip(selected.items(),vals):
        if not isinstance(v,dict):continue
        data=v.get('data')
        if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':continue
        try:raw=base64.b64decode(data[0],validate=True)
        except (TypeError,ValueError):continue
        row=validate(addr,t,v.get('owner'),raw,slot,epoch)
        if row:rows.append(row)
    return rows

def bootstrap(url,selected,timeout=12):
    if not url.startswith('https://'):raise RuntimeError('HTTPS_REQUIRED')
    if len(selected)>100:raise RuntimeError('RPC_BUDGET_100_ACCOUNTS_MAX')
    payload={'jsonrpc':'2.0','id':283287,'method':'getMultipleAccounts',
             'params':[list(selected),{'encoding':'base64','commitment':'processed'}]}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as res:raw=res.read(28_000_001)
    if len(raw)>28_000_000:raise RuntimeError('RPC_OVERSIZE')
    return parse_rpc(json.loads(raw),selected,time.time())

def connect_db(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=15)
    con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA busy_timeout=15000')
    con.executescript('''CREATE TABLE IF NOT EXISTS account_state(address TEXT PRIMARY KEY,kind TEXT,slot INTEGER,received REAL,owner TEXT,sha TEXT,byte_count INTEGER,detail_json TEXT,source TEXT);
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,epoch REAL,address TEXT,kind TEXT,slot INTEGER,source TEXT,decision TEXT);
CREATE TABLE IF NOT EXISTS metrics(epoch INTEGER PRIMARY KEY,tracked INTEGER,fresh INTEGER,missing INTEGER,stale INTEGER,conflicts INTEGER,ws_notifications INTEGER,rpc_calls INTEGER,pricing_events INTEGER,positive_net INTEGER,atomic_ready INTEGER);
CREATE TABLE IF NOT EXISTS checkpoint(name TEXT PRIMARY KEY,value TEXT);
CREATE TABLE IF NOT EXISTS account_bytes(address TEXT PRIMARY KEY,slot INTEGER,owner TEXT,sha TEXT,raw BLOB,source TEXT,received REAL);
CREATE TABLE IF NOT EXISTS coverage_history(epoch INTEGER PRIMARY KEY,ready_pool_pairs INTEGER,tracked_tokens INTEGER,complete_bytes INTEGER,age_fresh INTEGER,missing INTEGER,stale INTEGER,unverified INTEGER,pump_pool_fresh INTEGER,meteora_pool_fresh INTEGER,vault_fresh INTEGER,bin_fresh INTEGER,price_verified INTEGER);

''')
    return con

def ingest(con,row,source):
    before=con.execute('SELECT slot,sha FROM account_state WHERE address=?',(row['address'],)).fetchone()
    if before:
        if row['slot']<before[0]:return 'OLDER_SLOT'
        if row['slot']==before[0]:return 'DUPLICATE' if before[1]==row['fingerprint'] else 'SAME_SLOT_CONFLICT'
    con.execute('INSERT OR REPLACE INTO account_state VALUES(?,?,?,?,?,?,?,?,?)',(
        row['address'],row['kind'],row['slot'],row['received_epoch'],row['owner'],row['fingerprint'],row['byte_count'],json.dumps(row['detail']),source))
    raw=row.get('raw')
    if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=row['fingerprint'] or len(raw)!=row['byte_count']:
        raise RuntimeError('RAW_BYTES_MISSING_OR_CORRUPTED')
    con.execute('INSERT OR REPLACE INTO account_bytes VALUES(?,?,?,?,?,?,?)',(
        row['address'],row['slot'],row['owner'],row['fingerprint'],sqlite3.Binary(raw),source,row['received_epoch']))
    con.execute('INSERT INTO events(epoch,address,kind,slot,source,decision) VALUES(?,?,?,?,?,?)',
                (row['received_epoch'],row['address'],row['kind'],row['slot'],source,'ACCEPTED'))
    return 'ACCEPTED'

def decode_ws(packet,subs,selected,epoch):
    if not isinstance(packet,dict) or packet.get('method')!='accountNotification':return None
    args=packet.get('params',{});addr=subs.get(args.get('subscription')) if isinstance(args,dict) else None
    if addr not in selected:return None
    result=args.get('result',{});ctx=result.get('context',{}) if isinstance(result,dict) else {}
    val=result.get('value',{}) if isinstance(result,dict) else {}
    if not isinstance(val,dict):return None
    data=val.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':return None
    try:raw=base64.b64decode(data[0],validate=True)
    except (TypeError,ValueError):return None
    return validate(addr,selected[addr],val.get('owner'),raw,ctx.get('slot'),epoch)

def snapshot(con,selected,counts,now,max_age,rpc_calls):
    rows={r[0]:r for r in con.execute('SELECT address,kind,slot,received,owner,sha,byte_count,detail_json,source FROM account_state')}
    live=[];stale=[];missing=[];coverage=defaultdict(lambda:Counter())
    for addr,t in selected.items():
        record=rows.get(addr)
        if record is None:missing.append(addr);coverage[t['kind']]['missing']+=1
        elif 0<=now-record[3]<=max_age:
            live.append(addr);coverage[t['kind']]['fresh']+=1
        else:stale.append(addr);coverage[t['kind']]['stale']+=1
    # There is no synchronized canonical Pump/Meteora state or verified local-only optimizer connection.
    # Never infer quotes/profitability from unsynchronized account notifications.
    return {'build':'ORACLE283_287','epoch':round(now,3),'tracked_accounts':len(selected),
            'fresh_accounts':len(live),'stale_accounts':len(stale),'missing_accounts':len(missing),
            'fresh_by_kind':{k:dict(v) for k,v in coverage.items()},'size_grid_sol':GRID,
            'counters':dict(counts),'rpc_calls_this_session':rpc_calls,
            'local_19_size_pricing_verified':False,'canonical_full_hydration':False,
            'atomic_simulation_certified':False,'net_profit_certified':False,
            'net_positive_opportunities':0,'atomic_ready_candidates':0,
            'readiness':'HOLD_CANONICAL_FULL_STATE_AND_LOCAL_PRICING',
            'scanner_modified':False,'execution_admission':False,'signing':False,'broadcast':False,
            'note':'Read-only account-state evidence. No claimed quotes, PnL, or executable opportunities.'}

def coverage_audit(con,selected,now,max_age):
    """Integrity-check persisted public account bytes, and measure actual dependencies.
    Fresh observation means a recent *changed state*, not guaranteed unchanged current state.
    """
    data={r[0]:r for r in con.execute('SELECT address,slot,owner,sha,raw,source,received FROM account_bytes')}
    token_roles=defaultdict(set); categories=Counter(); valid=0;fresh=0;unverified=0
    for addr,target in selected.items():
        kind=target['kind']; item=data.get(addr)
        if item is None:continue
        raw=item[4]
        if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=item[3]:
            unverified+=1;continue
        valid+=1
        if not 0<=now-item[6]<=max_age:continue
        fresh+=1;categories[kind]+=1
        if kind=='POOL':
            for ref in target.get('refs',[]):
                mint=ref.get('token') or ref.get('mint') or ref.get('expected_token_mint')
                venue=str(ref.get('venue','')).upper()
                if mint and venue:token_roles[mint].add(venue)
        elif kind=='BIN':
            token_roles[target['token']].add('BIN')
        elif kind=='VAULT':
            for ref in target.get('refs',[]):
                token=ref.get('token') or ref.get('mint') or ref.get('expected_token_mint')
                if token:token_roles[token].add('VAULT')
    # Inspect the source inventory to avoid assuming the v277 manifest's refs include token labels.
    # Counts below are byte freshness and provenance only, NOT synchronized canonical pair readiness.
    all_tokens={t['token'] for t in selected.values() if t['kind']=='BIN'}
    for t in selected.values():
        for r in t.get('refs',[]):
            mint=r.get('token') or r.get('mint')
            if mint:all_tokens.add(mint)
    return {'complete_account_bytes':valid,'fresh_verified_bytes':fresh,
       'identity_unverified_accounts':unverified,'fresh_pump_pool_bytes':0,
       'fresh_meteora_pool_bytes':0,'fresh_vault_bytes':categories['VAULT'],
       'fresh_bin_bytes':categories['BIN'],'tracked_tokens':len(all_tokens),
       'two_venue_pool_pairs_with_fresh_bytes':0,
       'pool_pair_verification_hold':'POOL_OWNER_AND_TOKEN_VENUE_MAPPING_NOT_CANONICALLY_CERTIFIED',
       'quote_events':0,'full_fill_quotes':0,'net_positive_opportunities':0,
       'local_19_size_pricing_verified':False,'canonical_full_hydration':False,
       'net_profit_certified':False,'atomic_simulation_certified':False}

def persist(con,selected,counts,max_age,rpc_calls):
    report=snapshot(con,selected,counts,time.time(),max_age,rpc_calls)
    report.update(coverage_audit(con,selected,report['epoch'],max_age))
    con.execute('INSERT OR REPLACE INTO coverage_history VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (int(report['epoch']),report['two_venue_pool_pairs_with_fresh_bytes'],report['tracked_tokens'],
        report['complete_account_bytes'],report['fresh_verified_bytes'],report['missing_accounts'],
        report['stale_accounts'],report['identity_unverified_accounts'],
        report['fresh_pump_pool_bytes'],report['fresh_meteora_pool_bytes'],
        report['fresh_vault_bytes'],report['fresh_bin_bytes'],0))
    con.execute('INSERT OR REPLACE INTO metrics VALUES(?,?,?,?,?,?,?,?,?,?,?)',(
        int(report['epoch']),report['tracked_accounts'],report['fresh_accounts'],report['missing_accounts'],
        report['stale_accounts'],counts['SAME_SLOT_CONFLICT'],counts['NOTIFICATIONS'],rpc_calls,0,0,0))
    con.commit()
    tmp=REPORT.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2),encoding='utf-8');os.replace(tmp,REPORT)
    return report

def show_table(con,limit=15):
    print('ORACLE MILESTONE A | READ-ONLY EVIDENCE TABLE')
    print('TIME (epoch)  FRESH  MISSING  STALE  WS NOTIFY  RPC  PRICE  NET+  ATOMIC')
    for r in con.execute('SELECT * FROM metrics ORDER BY epoch DESC LIMIT ?',(limit,)):
        print(f'{r[0]:12} {r[2]:6} {r[3]:8} {r[4]:6} {r[6]:10} {r[7]:4} {r[8]:6} {r[9]:5} {r[10]:7}')
    print('ACCOUNT BYTES | VERIFIED  FRESH  VAULT  BIN  PRICE')
    for x in con.execute('SELECT epoch,complete_bytes,age_fresh,vault_fresh,bin_fresh,price_verified FROM coverage_history ORDER BY epoch DESC LIMIT ?',(limit,)):
        print(f'{x[0]:12} {x[1]:9} {x[2]:6} {x[3]:6} {x[4]:4} {x[5]:6}')
    print('[GATE] Live public account bytes retained. Canonical pricing, net profit and atomic admission NOT certified. No trades attempted.')

def monitor(seconds,max_age,interval,max_accounts):
    disarmed()
    url=os.getenv('SOLANA_WS_URL','');rpc=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('wss://') or not rpc.startswith('https://'):raise RuntimeError('RPC_AND_WS_URL_REQUIRED')
    selected_all=targets()
    if not selected_all:raise RuntimeError('NO_VETTED_TARGETS')
    selected=dict(list(selected_all.items())[:max_accounts])
    if len(selected)>100:raise RuntimeError('MAX_ACCOUNTS_100')
    con=connect_db();counts=Counter();rpc_calls=0
    # One initial bootstrap per run, never periodic REST polling.
    try:
        rpc_calls=1
        rows=bootstrap(rpc,selected)
        for row in rows:counts['BOOTSTRAP_'+ingest(con,row,'BATCH_INIT')]+=1
        con.commit()
    except urllib.error.HTTPError as exc:
        counts['RPC_HTTP_'+str(exc.code)]+=1
        if exc.code==429:counts['RPC_429_STOP']+=1
    except (urllib.error.URLError,OSError,ValueError,RuntimeError,TimeoutError):
        counts['RPC_BOOTSTRAP_FAILED']+=1
    report=persist(con,selected,counts,max_age,rpc_calls)
    print('[ORACLE283_287_BOOTSTRAP]',json.dumps({'tracked':len(selected),'fresh':report['fresh_accounts'],'rpc_calls':rpc_calls,'holds':report['readiness']},sort_keys=True),flush=True)
    import websocket
    stop=time.monotonic()+seconds if seconds>0 else float('inf')
    retry_delay=1
    try:
        while time.monotonic()<stop:
            ws=None;pending={};subs={}
            try:
                ws=websocket.create_connection(url,timeout=12,enable_multithread=True);ws.settimeout(2)
                for i,addr in enumerate(selected,1):
                    pending[i]=addr
                    ws.send(json.dumps({'jsonrpc':'2.0','id':i,'method':'accountSubscribe',
                                        'params':[addr,{'encoding':'base64','commitment':'processed'}]}))
                counts['WS_CONNECTIONS']+=1;retry_delay=1
                last_save=time.monotonic()
                while time.monotonic()<stop:
                    try:raw=ws.recv()
                    except (socket.timeout,websocket.WebSocketTimeoutException):raw=None
                    if raw is not None:
                        try:pkt=json.loads(raw)
                        except (ValueError,TypeError):pkt=None
                        if isinstance(pkt,dict):
                            req=pkt.get('id')
                            if type(req) is int and req in pending:
                                addr=pending.pop(req)
                                if type(pkt.get('result')) is int:subs[pkt['result']]=addr;counts['SUBSCRIBED']+=1
                                else:counts['SUBSCRIBE_REJECTED']+=1
                            elif pkt.get('method')=='accountNotification':
                                counts['NOTIFICATIONS']+=1
                                row=decode_ws(pkt,subs,selected,time.time())
                                counts[ingest(con,row,'WS') if row is not None else 'INVALID_WS_RECORD']+=1
                    if time.monotonic()-last_save>=interval:
                        report=persist(con,selected,counts,max_age,rpc_calls)
                        print('[ORACLE283_287_HEARTBEAT]',json.dumps({'fresh':report['fresh_accounts'],'missing':report['missing_accounts'],
                          'stale':report['stale_accounts'],'notifications':counts['NOTIFICATIONS'],'rpc_calls':rpc_calls,
                          'net_positive_certified':False,'execution':False,
                          'verified_bytes':report['complete_account_bytes'],'fresh_bytes':report['fresh_verified_bytes'],
                          'vault_fresh':report['fresh_vault_bytes'],'bin_fresh':report['fresh_bin_bytes']},sort_keys=True),flush=True)
                        last_save=time.monotonic()
            except (websocket.WebSocketException,OSError,TimeoutError) as exc:
                counts['WS_RECONNECTS']+=1
                print('[ORACLE283_287_WS_RECONNECT]',type(exc).__name__,flush=True)
            finally:
                if ws is not None:
                    try:ws.close()
                    except Exception:pass
                persist(con,selected,counts,max_age,rpc_calls)
            if time.monotonic()<stop:time.sleep(min(retry_delay,stop-time.monotonic()));retry_delay=min(retry_delay*2,30)
    except KeyboardInterrupt:print('[ORACLE283_287_STOP] keyboard interrupt',flush=True)
    finally:
        report=persist(con,selected,counts,max_age,rpc_calls)
        print('[ORACLE283_287_RESULT]',json.dumps({k:v for k,v in report.items() if k!='size_grid_sol'},sort_keys=True),flush=True)
        print('[REPORT]',REPORT,flush=True)
        con.close()

def test():
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        con=connect_db(Path(folder)/'test.sqlite')
        pool=WSOL;raw=b'Z'*8+(7).to_bytes(8,'little',signed=True)+b'X'*8+b58decode(pool)+b'Q'*16
        address='11111111111111111111111111111111'
        selected={address:{'kind':'BIN','pool':pool,'pool_raw':b58decode(pool),'array_index':7}}
        row=validate(address,selected[address],OWNER_DLMM,raw,42,1000.)
        assert row and ingest(con,row,'BATCH_INIT')=='ACCEPTED'
        assert ingest(con,row,'WS')=='DUPLICATE'
        assert ingest(con,dict(row,slot=41),'WS')=='OLDER_SLOT'
        assert ingest(con,dict(row,slot=42,fingerprint='f'*64),'WS')=='SAME_SLOT_CONFLICT'
        assert ingest(con,dict(row,slot=43,received_epoch=1001.),'WS')=='ACCEPTED'
        assert snapshot(con,selected,Counter(),1002,120,1)['fresh_accounts']==1
        assert snapshot(con,selected,Counter(),1400,120,1)['stale_accounts']==1
        payload={'result':{'context':{'slot':55},'value':[{'owner':OWNER_DLMM,'data':[base64.b64encode(raw).decode(),'base64']}]}}
        assert len(parse_rpc(payload,selected,1003))==1
        try:parse_rpc({'result':{'context':{'slot':55},'value':[]}},selected,1003)
        except RuntimeError:pass
        else:raise AssertionError('RPC_CARDINALITY_CHECK_MISSING')
        con.close()
    # Regression: the production ORACLE279 address cache has no authority flags.
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'cache.json'
        path.write_text(json.dumps({'build':'ORACLE279','pools':{}}),encoding='utf-8')
        assert verified_json(path,'ORACLE279')['pools']=={}
        path.write_text(json.dumps({'build':'ORACLE279','pools':{},'signing':True}),encoding='utf-8')
        try:verified_json(path,'ORACLE279')
        except RuntimeError:pass
        else:raise AssertionError('ARMED_CACHE_ACCEPTED')
        path.write_text(json.dumps({'build':'ORACLE279','pools':[]}),encoding='utf-8')
        try:verified_json(path,'ORACLE279')
        except RuntimeError:pass
        else:raise AssertionError('INVALID_CACHE_ACCEPTED')
    with tempfile.TemporaryDirectory() as folder:
        con=connect_db(Path(folder)/'rawtest.sqlite')
        a='11111111111111111111111111111111'; raw=b'public-state-bytes'
        row={'address':a,'kind':'POOL','slot':80,'received_epoch':1000.,'owner':WSOL,
             'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),'detail':{},'raw':raw}
        assert ingest(con,row,'BATCH_INIT')=='ACCEPTED'
        assert con.execute('SELECT raw FROM account_bytes WHERE address=?',(a,)).fetchone()[0]==raw
        assert ingest(con,row,'WS')=='DUPLICATE'
        audit=coverage_audit(con,{a:{'kind':'POOL','refs':[]}},1001,120)
        assert audit['complete_account_bytes']==1 and audit['fresh_verified_bytes']==1
        assert audit['two_venue_pool_pairs_with_fresh_bytes']==0
        assert coverage_audit(con,{a:{'kind':'POOL','refs':[]}},1201,120)['fresh_verified_bytes']==0
        try:ingest(con,dict(row,slot=81,raw=b'tampered'),'WS')
        except RuntimeError:pass
        else:raise AssertionError('CORRUPT_RAW_ACCEPTED')
        con.close()
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    print('[ORACLE283_287_TEST_PASS] bootstrap=TRUE identity=TRUE slots=TRUE replay=TRUE expiry=TRUE ledger=TRUE size_policy=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true')
    p.add_argument('--seconds',type=int,default=3600,help='0 means continuous until Ctrl+C')
    p.add_argument('--interval',type=int,default=30);p.add_argument('--max-age',type=int,default=120);p.add_argument('--max-accounts',type=int,default=100)
    a=p.parse_args()
    if a.test:test()
    elif a.table:con=connect_db();show_table(con);con.close()
    elif a.run:monitor(max(0,a.seconds),max(5,a.max_age),max(5,a.interval),max(1,min(100,a.max_accounts)))
    else:p.error('Specify --test, --run or --table')
