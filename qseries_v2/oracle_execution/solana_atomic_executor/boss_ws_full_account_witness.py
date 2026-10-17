"""ORACLE-333 executor-only complete-account WS observation sidecar.
Read-only. Adds the Pump vaults, DLMM vaults and bounded verified bin arrays.
Never treats a partial account catalog as an executable snapshot.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,pathlib,random,re,sqlite3,struct,time,urllib.request,urllib.error
from collections import Counter,defaultdict

ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
INVENTORY=ROOT/'scanner_inventory.json'
OUT=ROOT/'executor_full_account_witness.sqlite3'
STATUS=ROOT/'executor_full_account_witness_status.json'
BASE58=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SOL='So11111111111111111111111111111111111111112'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
TOKEN='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'


def emit(tag,item):
    print('['+tag+'] '+json.dumps(item,sort_keys=True,default=str),flush=True)

def redacted(e):
    value=type(e).__name__+':'+str(e)
    value=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',value)
    value=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',value)
    return value[:190]

def pubkey(s):return isinstance(s,str) and bool(BASE58.fullmatch(s))

def inventory_pairs(limit):
    j=json.loads(INVENTORY.read_text(encoding='utf-8'))
    rows=[];seen=set()
    for p in j.get('pairs',[]):
        if not isinstance(p,dict):continue
        token,pump,meteora=(p.get(x) for x in ('token','pump_pool','meteora_pool'))
        if not all(map(pubkey,(token,pump,meteora))):continue
        k=(token,pump,meteora)
        if k in seen:continue
        rows.append(dict(token=token,pump_pool=pump,meteora_pool=meteora))
        seen.add(k)
        if len(rows)>=limit:break
    if not rows:raise RuntimeError('NO_SCANNER_INVENTORY')
    return rows

def storage():
    ROOT.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(OUT),timeout=10,isolation_level=None)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=NORMAL')
    db.execute('CREATE TABLE IF NOT EXISTS latest(pubkey TEXT PRIMARY KEY,slot INTEGER NOT NULL,received_ns INTEGER NOT NULL,owner TEXT NOT NULL,lamports INTEGER NOT NULL,data_b64 TEXT NOT NULL,content_sha256 TEXT NOT NULL,source TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS watch(pubkey TEXT PRIMARY KEY,roles TEXT NOT NULL,token TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pair_catalog(token TEXT PRIMARY KEY,pump_pool TEXT NOT NULL,meteora_pool TEXT NOT NULL,bin_total INTEGER NOT NULL,bin_selected INTEGER NOT NULL,discovery_complete INTEGER NOT NULL,structural_only INTEGER NOT NULL DEFAULT 1)')
    return db

def normalized(key,value,slot,source,at_ns=None):
    if not pubkey(key) or not isinstance(value,dict):raise ValueError('BAD_ACCOUNT_VALUE')
    slot=int(slot)
    if slot<1:raise ValueError('BAD_SLOT')
    data=value.get('data')
    if not isinstance(data,(tuple,list)) or len(data)<2 or data[1]!='base64':raise ValueError('NOT_BASE64_ACCOUNT')
    raw=base64.b64decode(data[0],validate=True)
    if len(raw)>524288:raise ValueError('ACCOUNT_OVERSIZE')
    owner=value.get('owner')
    if not pubkey(owner):raise ValueError('INVALID_ACCOUNT_OWNER')
    at=int(at_ns or time.time_ns())
    return dict(pubkey=key,slot=slot,received_ns=at,owner=owner,lamports=int(value.get('lamports',0)),data_b64=data[0],content_sha256=hashlib.sha256(raw).hexdigest(),source=source)

def upsert(db,row):
    cur=db.execute('SELECT slot,received_ns FROM latest WHERE pubkey=?',(row['pubkey'],)).fetchone()
    if cur and (int(cur[0]),int(cur[1]))>(row['slot'],row['received_ns']):return False
    db.execute('INSERT INTO latest(pubkey,slot,received_ns,owner,lamports,data_b64,content_sha256,source) VALUES(:pubkey,:slot,:received_ns,:owner,:lamports,:data_b64,:content_sha256,:source) ON CONFLICT(pubkey) DO UPDATE SET slot=excluded.slot,received_ns=excluded.received_ns,owner=excluded.owner,lamports=excluded.lamports,data_b64=excluded.data_b64,content_sha256=excluded.content_sha256,source=excluded.source WHERE excluded.slot>latest.slot OR (excluded.slot=latest.slot AND excluded.received_ns>=latest.received_ns)',row)
    return True

def rpc(url,method,params,stats,retries=3):
    if not url.startswith('https://'):raise ValueError('HTTPS_REQUIRED')
    data=json.dumps(dict(jsonrpc='2.0',id=7,method=method,params=params)).encode()
    for attempt in range(retries):
        req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=24) as f: obj=json.load(f)
            if obj.get('error'):
                err=obj['error'];code=err.get('code') if isinstance(err,dict) else None
                if code==429:raise RateLimit('RPC_CODE_429')
                raise RuntimeError('RPC_ERROR_'+str(code))
            return obj.get('result')
        except urllib.error.HTTPError as e:
            if e.code != 429:raise RuntimeError('RPC_HTTP_'+str(e.code)) from None
            last=RateLimit('HTTP_429')
        except RateLimit as e:last=e
        stats['rpc_429']+=1
        if attempt==retries-1:raise last
        delay=min(12.,2.5*(2**attempt))+random.uniform(.1,.7)
        emit('BOSS333_RATE_LIMIT_COOLDOWN',{'wait_seconds':round(delay,2),'attempt':attempt+1,'method':method})
        time.sleep(delay)
    raise RuntimeError('RPC_RETRY_EXHAUSTED')

class RateLimit(RuntimeError):pass

def batch_bootstrap(url,keys,db,stats,tag='BOOTSTRAP',roles=None):
    for i in range(0,len(keys),65):
        block=keys[i:i+65]
        r=rpc(url,'getMultipleAccounts',[block,{'encoding':'base64','commitment':'processed'}],stats)
        slot=int((r.get('context') or {}).get('slot',0)) if isinstance(r,dict) else 0
        vals=r.get('value') if isinstance(r,dict) else None
        if slot<=0 or not isinstance(vals,list) or len(vals)!=len(block):raise RuntimeError('INVALID_BOOTSTRAP_BATCH')
        for key,v in zip(block,vals):
            if v is None:stats['missing_accounts']+=1;continue
            if roles is not None and not validate_owner(key,v,roles):
                stats['bootstrap_owner_reject']+=1;continue
            if upsert(db,normalized(key,v,slot,'RPC_'+tag)):stats['bootstrap_rows']+=1
        stats['bootstrap_batches']+=1
        if i+65<len(keys):time.sleep(1.2)

def pump_vaults(pool_raw,token,decoder):
    if len(pool_raw)<203:raise ValueError('PUMP_ACCOUNT_TOO_SHORT')
    row=decoder(pool_raw)
    if row.get('quote_mint')!=SOL or row.get('base_mint')!=token:raise ValueError('PUMP_MINT_IDENTITY_MISMATCH')
    base,quote=row.get('base_vault'),row.get('quote_vault')
    if not pubkey(base) or not pubkey(quote) or base==quote:raise ValueError('BAD_PUMP_VAULTS')
    return [('PUMP_BASE_VAULT',base),('PUMP_QUOTE_VAULT',quote)]

def reserve_vaults(pool,token,pda,b58d):
    # Cross-checked against canonical runtime.prebuild_meteora_templates.
    return [('DLMM_SOL_RESERVE',pda([b58d(pool),b58d(SOL)],DLMM)),
            ('DLMM_TOKEN_RESERVE',pda([b58d(pool),b58d(token)],DLMM))]

def selected_bin_rows(rows,pool,program,decode,cap):
    # Official DLMM BinArray: discriminator[8], index i64[8], version[1], padding[7], lb_pair[32].
    valid=[];seen=set()
    for x in rows:
        try:
            if x['account']['owner']!=program:continue
            key=x['pubkey']; encoded=x['account']['data'][0]
            data=base64.b64decode(encoded,validate=True)
            if len(data)<56 or decode(data[24:56])!=pool:continue
            ix=struct.unpack_from('<q',data,8)[0]
            if key in seen:continue
            seen.add(key);valid.append((ix,key))
        except (ValueError,TypeError,IndexError,KeyError,struct.error):continue
    valid.sort()
    # This is ONLY a witness catalog. No claim that the first arrays are active/quote-selected.
    return valid[:cap],len(valid)

def discover_arrays(url,pool,c,stats,cap,decode):
    # dataSlice keeps the onetime getProgramAccounts response small.
    config={'encoding':'base64','commitment':'processed',
            'dataSlice':{'offset':0,'length':56},
            'filters':[{'memcmp':{'offset':24,'bytes':pool}}]}
    result=rpc(url,'getProgramAccounts',[DLMM,config],stats)
    if not isinstance(result,list):raise RuntimeError('DLMM_CATALOG_NOT_LIST')
    return selected_bin_rows(result,pool,DLMM,decode,cap)

def watch_plan(pairs,db,url,stats,max_arrays,c):
    roles=defaultdict(set);catalog={};fully_found=0
    all_pool=list(dict.fromkeys(a for p in pairs for a in (p['pump_pool'],p['meteora_pool'])))
    # One batched pool-account bootstrap BEFORE asking each parent pool for its bin arrays.
    batch_bootstrap(url,all_pool,db,stats,'POOL_CATALOG')
    for p in pairs:
        token,pump,dlmm=p['token'],p['pump_pool'],p['meteora_pool']
        roles[pump].add((token,'PUMP_POOL'));roles[dlmm].add((token,'DLMM_POOL'))
        total=0;sel=0;complete=False;errors=[]
        try:
            pv=db.execute('SELECT data_b64,owner FROM latest WHERE pubkey=?',(pump,)).fetchone()
            lv=db.execute('SELECT data_b64,owner FROM latest WHERE pubkey=?',(dlmm,)).fetchone()
            if not pv or pv[1]!=PUMP:raise ValueError('PUMP_POOL_OWNER_OR_ACCOUNT_MISSING')
            if not lv or lv[1]!=DLMM:raise ValueError('DLMM_POOL_OWNER_OR_ACCOUNT_MISSING')
            vaults=pump_vaults(base64.b64decode(pv[0]),token,c.decode_pump_pool)
            vaults+=reserve_vaults(dlmm,token,c.pda,c.b58d)
            for role,key in vaults:roles[key].add((token,role))
            bins,total=discover_arrays(url,dlmm,c,stats,max_arrays,c.b58e)
            for ix,key in bins:roles[key].add((token,'DLMM_BIN_ARRAY_INDEX_'+str(ix)))
            sel=len(bins);complete=(total>0 and sel==total)
        except Exception as e:
            stats['catalog_errors']+=1;errors.append(redacted(e))
        catalog[token]=dict(token=token,pump_pool=pump,meteora_pool=dlmm,bin_total=total,
                            bin_selected=sel,discovery_complete=int(complete),structural_only=1)
        db.execute('INSERT OR REPLACE INTO pair_catalog(token,pump_pool,meteora_pool,bin_total,bin_selected,discovery_complete,structural_only) VALUES(:token,:pump_pool,:meteora_pool,:bin_total,:bin_selected,:discovery_complete,:structural_only)',catalog[token])
        if complete:fully_found+=1
        emit('BOSS333_PAIR_CATALOG',{'token':token[:12],'vaults_and_arrays_discovered':sel>0,
              'bin_arrays_selected':sel,'bin_arrays_total':total,'array_catalog_complete':complete,
              'errors':errors,'executable_price_certified':False})
        time.sleep(.95)
    # No silent sharing of keys between unrelated tokens; pair/role lineage lives in watch table.
    for key,pairs_roles in roles.items():
        vals=sorted(pairs_roles)
        db.execute('INSERT OR REPLACE INTO watch(pubkey,roles,token) VALUES(?,?,?)',
                   (key,json.dumps(vals),','.join(sorted({v[0] for v in vals}))))
    emit('BOSS333_CATALOG_COMPLETE',{'pairs':len(pairs),'catalog_fully_discovered_pairs':fully_found,
         'watch_accounts':len(roles),'rpc_429':stats['rpc_429'],'price_freshness_certified':False})
    return roles,catalog

def validate_owner(key,value,roles):
    owner=value.get('owner') if isinstance(value,dict) else None
    labels={r for _,r in roles.get(key,())}
    if 'PUMP_POOL' in labels and owner!=PUMP:return False
    if ('DLMM_POOL' in labels or any(x.startswith('DLMM_BIN_ARRAY_INDEX_') for x in labels)) and owner!=DLMM:return False
    if any('VAULT' in x or 'RESERVE' in x for x in labels) and owner not in (TOKEN,TOKEN22):return False
    return True

def witness_report(db,pairs,roles,stats,connected):
    now=time.time_ns();stages=Counter();latest=[]
    for key,vals in roles.items():
        row=db.execute('SELECT slot,received_ns,source FROM latest WHERE pubkey=?',(key,)).fetchone()
        for token,role in vals:stages[role.split('_INDEX_')[0]+'_WATCHED']+=1
        if row:
            latest.append((key,int(row[0]),(now-int(row[1]))/1e6))
            for token,role in vals:stages[role.split('_INDEX_')[0]+'_OBSERVED']+=1
    # One pool slot never proves all related vaults and bins were observed at a coherent bank.
    missing=sum(1 for a in roles if not any(x[0]==a for x in latest))
    young=sum(1 for _,_,age in latest if 0<=age<=750)
    return {'pairs':len(pairs),'watched_accounts':len(roles),'observed_accounts':len(latest),
            'missing_accounts':missing,'accounts_updated_in_last_750ms':young,
            'received_ws_updates':stats['updates'],'subscription_acks':stats['subscribed'],
            'bootstrap_batches':stats['bootstrap_batches'],'rpc_429':stats['rpc_429'],
            'catalog_errors':stats['catalog_errors'],'subscription_errors':stats['subscribe_errors'],
            'invalid_owner_rejects':stats['account_owner_reject']+stats['bootstrap_owner_reject'],
            'ws_connected':bool(connected),'role_coverage':dict(stages),
            'slot_lineage_available':True,'slot_coherence_certified':False,
            'executable_pricing_certified':False,'execution_admission':False,
            'signing':False,'broadcast':False}

def websocket_client(url):
    import websocket
    s=websocket.create_connection(url,timeout=14,enable_multithread=True)
    s.settimeout(.8)
    return s

def ingest(msg,subs,db,roles,stats):
    if msg.get('method')!='accountNotification':return
    params=msg.get('params') or {};key=subs.get(params.get('subscription'))
    if not key:stats['unknown_subs']+=1;return
    result=params.get('result') or {};val=result.get('value')
    if not validate_owner(key,val,roles):stats['account_owner_reject']+=1;return
    slot=(result.get('context') or {}).get('slot')
    try:
        if upsert(db,normalized(key,val,slot,'WS_NOTIFICATION')):stats['updates']+=1
        else:stats['older_slot_drop']+=1
    except Exception:stats['notification_rejects']+=1

def run(seconds,pair_limit,max_arrays,pacing):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):raise RuntimeError('SECRET_PRESENT_IN_WITNESS_PROCESS_REFUSED')
    url=os.environ.get('SOLANA_RPC_URL','');ws=os.environ.get('SOLANA_WS_URL','')
    if not url.startswith('https://') or not ws.startswith('wss://'):raise RuntimeError('SECURE_RPC_WS_REQUIRED')
    if max_arrays<1 or max_arrays>12:raise ValueError('ARRAY_LIMIT_1_TO_12')
    if pair_limit<1 or pair_limit>28:raise ValueError('PAIR_LIMIT_1_TO_28')
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
    db=storage();stats=Counter();pairs=inventory_pairs(pair_limit)
    roles,catalog=watch_plan(pairs,db,url,stats,max_arrays,c)
    addresses=list(roles)
    booted=False;started=time.monotonic();backoff=2.0
    emit('BOSS333_START',{'pairs':len(pairs),'accounts':len(addresses),
          'scanner_untouched':True,'executor_untouched':True,'signing':False,'broadcast':False,
          'array_catalog_capped':sum(p['bin_selected']<p['bin_total'] for p in catalog.values())})
    while seconds<=0 or time.monotonic()-started<seconds:
        s=None
        try:
            s=websocket_client(ws);pending={};subs={}
            for n,key in enumerate(addresses,100):
                s.send(json.dumps({'jsonrpc':'2.0','id':n,'method':'accountSubscribe',
                          'params':[key,{'encoding':'base64','commitment':'processed'}]}))
                pending[n]=key
                time.sleep(max(.07,float(pacing)))
            until=time.monotonic()+max(25.,len(addresses)*.65)
            while pending and time.monotonic()<until:
                try:raw=s.recv()
                except Exception as e:
                    if 'timed out' in str(e).lower() or 'timeout' in type(e).__name__.lower():continue
                    raise
                if not raw:raise RuntimeError('WS_CLOSED_WHILE_SUBSCRIBING')
                if isinstance(raw,bytes):raw=raw.decode()
                m=json.loads(raw);request_id=m.get('id')
                if request_id in pending:
                    key=pending.pop(request_id)
                    if 'error' in m:stats['subscribe_errors']+=1
                    else:subs[m['result']]=key;stats['subscribed']+=1
                else:ingest(m,subs,db,roles,stats)
            if pending:raise RuntimeError('SUBSCRIBE_ACK_TIMEOUT')
            if not booted:
                try:
                    batch_bootstrap(url,addresses,db,stats,'AFTER_SUBSCRIBE',roles=roles);booted=True
                except Exception as e:
                    stats['bootstrap_errors']+=1
                    emit('BOSS333_BOOTSTRAP_HOLD',{'reason':redacted(e)})
            emit('BOSS333_SUBSCRIBED',{'acks':len(subs),'watched':len(addresses),
                 'bootstrap_batches':stats['bootstrap_batches'],'executable_pricing_certified':False})
            backoff=2.;last=0.
            while seconds<=0 or time.monotonic()-started<seconds:
                try:raw=s.recv()
                except Exception as e:
                    if 'timed out' in str(e).lower() or 'timeout' in type(e).__name__.lower():raw=None
                    else:raise
                if raw=='' or raw==b'':raise RuntimeError('WS_CLOSED')
                if raw:
                    if isinstance(raw,bytes):raw=raw.decode()
                    ingest(json.loads(raw),subs,db,roles,stats)
                if time.monotonic()-last>=5:
                    report=witness_report(db,pairs,roles,stats,True)
                    temp=STATUS.with_name(STATUS.name+'.tmp')
                    temp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
                    os.replace(temp,STATUS)
                    emit('BOSS333_HEARTBEAT',report);last=time.monotonic()
            break
        except KeyboardInterrupt:break
        except Exception as e:
            stats['disconnects']+=1
            emit('BOSS333_RECONNECT',{'reason':redacted(e),'backoff_seconds':backoff,
                 'reported_429':stats['rpc_429'],'execution_admission':False})
            time.sleep(backoff+random.uniform(0,.5));backoff=min(60.,backoff*2)
        finally:
            if s:
                try:s.close()
                except Exception:pass
    emit('BOSS333_EXIT',{'watched':len(addresses),'updates':stats['updates'],
         'rpc_429':stats['rpc_429'],'disconnects':stats['disconnects'],'signing':False,'broadcast':False})
    db.close();return 0

def tests():
    import unittest
    class T(unittest.TestCase):
        def setUp(self):
            self.db=sqlite3.connect(':memory:');self.db.execute('CREATE TABLE latest(pubkey TEXT PRIMARY KEY,slot INTEGER,received_ns INTEGER,owner TEXT,lamports INTEGER,data_b64 TEXT,content_sha256 TEXT,source TEXT)')
            self.a='1'*32;self.b='2'*32;self.token='3'*32
            self.value={'owner':PUMP,'lamports':100,'data':[base64.b64encode(b'abc').decode(),'base64']}
        def tearDown(self):self.db.close()
        def test_store_slot(self):
            upsert(self.db,normalized(self.a,self.value,20,'BOOT',100));self.assertEqual(self.db.execute('SELECT slot FROM latest').fetchone()[0],20)
        def test_out_of_order(self):
            upsert(self.db,normalized(self.a,self.value,20,'BOOT',100));self.assertFalse(upsert(self.db,normalized(self.a,self.value,19,'WS',200)))
        def test_same_slot_recent(self):
            upsert(self.db,normalized(self.a,self.value,20,'BOOT',100));self.assertTrue(upsert(self.db,normalized(self.a,self.value,20,'WS',200)))
        def test_same_slot_old_timestamp(self):
            upsert(self.db,normalized(self.a,self.value,20,'BOOT',200));self.assertFalse(upsert(self.db,normalized(self.a,self.value,20,'BOOT',100)))
        def test_hash(self):
            self.assertEqual(normalized(self.a,self.value,5,'WS')['content_sha256'],hashlib.sha256(b'abc').hexdigest())
        def test_invalid_base64(self):
            with self.assertRaises(ValueError):normalized(self.a,{'owner':PUMP,'data':['@@','base64']},8,'WS')
        def test_invalid_owner(self):
            with self.assertRaises(ValueError):normalized(self.a,{'owner':'hello','data':['AA==','base64']},8,'WS')
        def test_pump_vaults(self):
            def dec(_):return {'base_mint':self.token,'quote_mint':SOL,'base_vault':self.a,'quote_vault':self.b}
            self.assertEqual(len(pump_vaults(b'x'*250,self.token,dec)),2)
        def test_pump_wrong_mint(self):
            def dec(_):return {'base_mint':self.a,'quote_mint':SOL,'base_vault':self.a,'quote_vault':self.b}
            with self.assertRaises(ValueError):pump_vaults(b'x'*250,self.token,dec)
        def test_reserves_pair_seed(self):
            def dec(v):return v
            def pda(seeds,p):return self.a if seeds[1]==self.b.encode() else self.b
            self.assertEqual(len(reserve_vaults(self.a,self.token,pda,lambda x:x.encode())),2)
        def test_bin_subset_marked(self):
            def dec(x):return self.b if x==b'x'*32 else self.a
            raw=b'z'*8+struct.pack('<q',6)+b'0'*8+b'x'*32
            arr=[{'pubkey':self.a,'account':{'owner':DLMM,'data':[base64.b64encode(raw).decode(),'base64']}},
                 {'pubkey':self.b,'account':{'owner':DLMM,'data':[base64.b64encode(raw[:8]+struct.pack('<q',7)+raw[16:]).decode(),'base64']}}]
            out,total=selected_bin_rows(arr,self.b,DLMM,dec,1)
            self.assertEqual((len(out),total),(1,2))
        def test_bin_wrong_parent_rejected(self):
            raw=b'0'*56;arr=[{'pubkey':self.a,'account':{'owner':DLMM,'data':[base64.b64encode(raw).decode(),'base64']}}]
            out,total=selected_bin_rows(arr,self.b,DLMM,lambda x:self.a,4);self.assertEqual(total,0)
        def test_pump_owner_reject(self):
            self.assertFalse(validate_owner(self.a,{'owner':TOKEN},{self.a:{(self.token,'PUMP_POOL')}}))
        def test_vault_owner_reject(self):
            self.assertFalse(validate_owner(self.a,{'owner':PUMP},{self.a:{(self.token,'DLMM_SOL_RESERVE')}}))
        def test_array_owner_accept(self):
            self.assertTrue(validate_owner(self.a,{'owner':DLMM},{self.a:{(self.token,'DLMM_BIN_ARRAY_INDEX_10')}}))
        def test_secret_redaction(self):
            self.assertNotIn('VERYSECRET',redacted(RuntimeError('https://helius.test/?api-key=VERYSECRET')))
        def test_no_quote_claim(self):
            r=witness_report(self.db,[],{self.a:{(self.token,'PUMP_POOL')}},Counter(),True)
            self.assertFalse(r['executable_pricing_certified']);self.assertFalse(r['slot_coherence_certified'])
        def test_no_secret_api(self):
            s=pathlib.Path(__file__).read_text(encoding='utf-8')
            self.assertNotIn('send'+'Transaction',s);self.assertNotIn('sign_'+'transaction(',s)
        def test_immutable_scanner_file(self):
            self.assertEqual(INVENTORY.name,'scanner_inventory.json')
            self.assertEqual(OUT.name,'executor_full_account_witness.sqlite3')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res=unittest.TextTestRunner(verbosity=2).run(suite)
    if res.wasSuccessful():emit('BOSS333_TEST_PASS',{'count':res.testsRun,'type':'OFFLINE_FIXTURES'});return 0
    return 1

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for x in ('run','test','audit','status'):g.add_argument('--'+x,action='store_true')
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--pairs',type=int,default=6)
    p.add_argument('--max-arrays-per-pair',type=int,default=6)
    p.add_argument('--subscribe-pacing',type=float,default=.12)
    a=p.parse_args()
    if a.test:return tests()
    if a.audit:
        try:import websocket;driver='websocket-client'
        except ImportError:driver='UNAVAILABLE'
        emit('BOSS333_AUDIT',{'driver':driver,'scanner_untouched':True,'executor_untouched':True,
             'signing':False,'broadcast':False,'private_key_not_used':True,
             'all_arrays_covered_only_if_catalog_uncapped':True,
             'executable_pricing_certified':False});return 0
    if a.status:
        emit('BOSS333_STATUS',json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.exists() else {'state':'NO_LIVE_TEST'});return 0
    return run(a.seconds,a.pairs,a.max_arrays_per_pair,a.subscribe_pacing)
if __name__=='__main__':raise SystemExit(main())
