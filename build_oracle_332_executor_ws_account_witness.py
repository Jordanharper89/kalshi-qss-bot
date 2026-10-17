"""ORACLE-332 complete sidecar installer. Does not replace running scanner or executor.
Windows CMD; installer and launcher only, never signs or broadcasts.
"""
from __future__ import annotations
import argparse,hashlib,os,pathlib,py_compile,subprocess,sys
from urllib.parse import quote
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.boss_ws_state_witness'
TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_ws_state_witness.py')
SOURCE=r'''"""ORACLE-332 executor-only WebSocket state witness.
Mirrors actual pool-account bytes, context slots and receipt time into its own SQLite WAL.
Read-only. NOT an executable quote, not a coherent all-accounts snapshot, not authorization.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, pathlib, random, re, sqlite3, time, urllib.request, urllib.error
from collections import Counter

ROOT = pathlib.Path('runtime_state/oracle/final_boss_dual')
BUS = ROOT/'candidate_bus.sqlite3'
INVENTORY = ROOT/'scanner_inventory.json'
OUT = ROOT/'executor_account_witness.sqlite3'
STATUS = ROOT/'executor_account_witness_status.json'
BASE58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


def emit(event, record):
    print('['+event+'] '+json.dumps(record,sort_keys=True,default=str),flush=True)

def redacted(error):
    result=type(error).__name__+':'+str(error)
    result=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',result)
    result=re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',r'\1=[REDACTED]',result)
    return result[:180]

def pubkey(value):
    return isinstance(value,str) and BASE58.fullmatch(value) is not None

def inventory_pairs(limit=24):
    # Read only original scanner inventory. Do not import, patch, launch or alter scanner.
    obj=json.loads(INVENTORY.read_text(encoding='utf-8'))
    pairs=[];seen=set()
    for x in obj.get('pairs',[]):
        if not isinstance(x,dict):continue
        token,pump,meteora=(x.get(k) for k in ('token','pump_pool','meteora_pool'))
        if not all(map(pubkey,(token,pump,meteora))):continue
        k=(token,pump,meteora)
        if k in seen:continue
        pairs.append(dict(token=token,pump_pool=pump,meteora_pool=meteora))
        seen.add(k)
        if len(pairs)>=limit:break
    if not pairs:raise RuntimeError('NO_VALID_FROZEN_SCANNER_INVENTORY_PAIRS')
    return pairs

def watch_addresses(pairs):
    # These are only the two pool accounts per pair, not the vault/bin-array set.
    return list(dict.fromkeys(a for p in pairs for a in (p['pump_pool'],p['meteora_pool'])))

def storage():
    ROOT.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(OUT),timeout=5,isolation_level=None)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=NORMAL')
    c.execute('CREATE TABLE IF NOT EXISTS latest(pubkey TEXT PRIMARY KEY,slot INTEGER NOT NULL,received_ns INTEGER NOT NULL,owner TEXT NOT NULL,lamports INTEGER NOT NULL,data_b64 TEXT NOT NULL,content_sha256 TEXT NOT NULL,source TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT,started_ns INTEGER NOT NULL,ends_ns INTEGER,subscriptions INTEGER DEFAULT 0,notifications INTEGER DEFAULT 0,read_only INTEGER NOT NULL DEFAULT 1)')
    return c

def normalize(pub, value, slot, received_ns, source):
    if not pubkey(pub) or not isinstance(value,dict):raise ValueError('BAD_ACCOUNT_VALUE')
    if int(slot)<=0 or int(received_ns)<=0:raise ValueError('BAD_ACCOUNT_TIME_OR_SLOT')
    data=value.get('data')
    if not isinstance(data,(list,tuple)) or len(data)<2 or data[1]!='base64':
        raise ValueError('ACCOUNT_NOT_BASE64')
    raw=base64.b64decode(data[0],validate=True)
    if len(raw)>524288:raise ValueError('ACCOUNT_DATA_TOO_LARGE')
    owner=value.get('owner')
    if not pubkey(owner):raise ValueError('ACCOUNT_OWNER_UNRECOGNIZED')
    return dict(pubkey=pub,slot=int(slot),received_ns=int(received_ns),owner=owner,
                lamports=int(value.get('lamports',0)),data_b64=data[0],
                content_sha256=hashlib.sha256(raw).hexdigest(),source=source)

def upsert(conn,row):
    old=conn.execute('SELECT slot FROM latest WHERE pubkey=?',(row['pubkey'],)).fetchone()
    if old and row['slot']<int(old[0]):return False
    conn.execute('INSERT INTO latest(pubkey,slot,received_ns,owner,lamports,data_b64,content_sha256,source) VALUES(:pubkey,:slot,:received_ns,:owner,:lamports,:data_b64,:content_sha256,:source) ON CONFLICT(pubkey) DO UPDATE SET slot=excluded.slot,received_ns=excluded.received_ns,owner=excluded.owner,lamports=excluded.lamports,data_b64=excluded.data_b64,content_sha256=excluded.content_sha256,source=excluded.source WHERE excluded.slot>=latest.slot',row)
    return True

def pair_witness(conn,p):
    rows=[]
    for addr in (p['pump_pool'],p['meteora_pool']):
        row=conn.execute('SELECT slot,received_ns,content_sha256,source FROM latest WHERE pubkey=?',(addr,)).fetchone()
        rows.append(row)
    if any(x is None for x in rows):
        return {'gate':'POOL_ACCOUNT_WITNESS_INCOMPLETE','pool_accounts_present':sum(x is not None for x in rows),
                'price_freshness_certified':False,'execution_admission':False}
    ages=[round((time.time_ns()-x[1])/1e6,2) for x in rows]
    return {'gate':'POOL_ACCOUNT_LINEAGE_ONLY','slot_pump':int(rows[0][0]),'slot_meteora':int(rows[1][0]),
            'slot_delta':abs(int(rows[0][0])-int(rows[1][0])),
            'age_ms':ages,'price_freshness_certified':False,
            'all_swap_accounts_witnessed':False,'execution_admission':False}

def bootstrap(rpc_url,addresses,conn,stats):
    # One batched RPC request per <=100 addresses, never one request per nomination.
    for start in range(0,len(addresses),80):
        batch=addresses[start:start+80]
        params=[batch,{'encoding':'base64','commitment':'processed'}]
        body=json.dumps({'jsonrpc':'2.0','id':7,'method':'getMultipleAccounts','params':params}).encode()
        request=urllib.request.Request(rpc_url,data=body,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request,timeout=15) as rsp:obj=json.load(rsp)
        if 'error' in obj:raise RuntimeError('RPC_BATCH_BOOTSTRAP_ERROR')
        value=obj.get('result') or {}
        slot=int((value.get('context') or {}).get('slot',0))
        rows=value.get('value') or []
        if len(rows)!=len(batch) or slot<=0:raise ValueError('MALFORMED_BATCH_BOOTSTRAP')
        for address,account in zip(batch,rows):
            if account is None:stats['missing_accounts']+=1;continue
            row=normalize(address,account,slot,time.time_ns(),'RPC_BATCH_BOOTSTRAP')
            if upsert(conn,row):stats['bootstrap_accounts']+=1
        stats['bootstrap_batches']+=1
        if start+80<len(addresses):time.sleep(1.25)

def websocket_client(url):
    try:
        import websocket
        w=websocket.create_connection(url,timeout=12,enable_multithread=True)
        w.settimeout(1)
        return w
    except ImportError:
        from websockets.sync.client import connect
        return connect(url,open_timeout=12,close_timeout=3)

def ingest_notification(message,subs,conn,stats):
    if message.get('method')!='accountNotification':return False
    params=message.get('params') or {}
    addr=subs.get(params.get('subscription'))
    if not addr:stats['unknown_subscription']+=1;return False
    result=params.get('result') or {}
    slot=int((result.get('context') or {}).get('slot',0))
    row=normalize(addr,result.get('value'),slot,time.time_ns(),'WEBSOCKET_NOTIFICATION')
    if upsert(conn,row):stats['updates']+=1;return True
    stats['out_of_order_ignored']+=1;return False

def run(seconds=0,limit=24,pacing=.12):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        # Launcher scrubs the subprocess; guard direct runs to prevent accidental secret inheritance.
        raise RuntimeError('PRIVATE_KEY_PRESENT_IN_WITNESS_PROCESS_REFUSED')
    url=os.getenv('SOLANA_WS_URL','')
    rpc=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('wss://') or not rpc.startswith('https://'):
        raise RuntimeError('SOLANA_WS_URL_WSS_AND_RPC_HTTPS_REQUIRED')
    pairs=inventory_pairs(limit)
    addresses=watch_addresses(pairs)
    stats=Counter();conn=storage();first=time.monotonic();backoff=2.;booted=False
    conn.execute('INSERT INTO runs(started_ns) VALUES(?)',(time.time_ns(),))
    emit('BOSS332_START',{'pairs':len(pairs),'watch_pool_accounts':len(addresses),
         'scanner_modified':False,'executor_modified':False,'execution_authority':False,
         'signing':False,'broadcast':False,'all_swap_accounts_witnessed':False})
    while seconds<=0 or time.monotonic()-first<seconds:
        sock=None
        try:
            sock=websocket_client(url);pending={};subs={}
            # Pace subscription requests to avoid a large burst on reconnect.
            for i,addr in enumerate(addresses,100):
                req={'jsonrpc':'2.0','id':i,'method':'accountSubscribe','params':[addr,{'encoding':'base64','commitment':'processed'}]}
                sock.send(json.dumps(req));pending[i]=addr;time.sleep(max(.05,float(pacing)))
            acks_deadline=time.monotonic()+max(20.,len(addresses)*1.5)
            while pending and time.monotonic()<acks_deadline:
                try:raw=sock.recv()
                except Exception as e:
                    if 'timed out' in str(e).lower() or 'timeout' in type(e).__name__.lower():continue
                    raise
                if isinstance(raw,bytes):raw=raw.decode()
                if not raw:raise RuntimeError('WS_CLOSED_DURING_SUBSCRIBE')
                msg=json.loads(raw)
                if msg.get('id') in pending:
                    request_id=msg['id'];addr=pending.pop(request_id)
                    if 'error' in msg:stats['subscription_errors']+=1;continue
                    subs[msg['result']]=addr;stats['subscribed']+=1
                else:ingest_notification(msg,subs,conn,stats)
            if pending:raise RuntimeError('WS_SUBSCRIBE_ACK_INCOMPLETE')
            # Optional single batch bootstrap after live subscription is established;
            # received notifications with newer slots cannot be overwritten by older RPC state.
            if not booted:
                try:bootstrap(rpc,addresses,conn,stats);booted=True
                except Exception as e:
                    stats['bootstrap_errors']+=1
                    emit('BOSS332_BOOTSTRAP_HOLD',{'reason':redacted(e),'retry_after_reconnect':True})
            emit('BOSS332_SUBSCRIBED',{'active':len(subs),'bootstrap_accounts':stats['bootstrap_accounts'],
                'updates':stats['updates'],'price_freshness_certified':False})
            backoff=2.;last=time.monotonic()
            while seconds<=0 or time.monotonic()-first<seconds:
                try:raw=sock.recv()
                except Exception as e:
                    if 'timed out' in str(e).lower() or 'timeout' in type(e).__name__.lower():raw=None
                    else:raise
                if raw == '' or raw == b'':raise RuntimeError('WS_CLOSED_AFTER_SUBSCRIBE')
                if raw:
                    if isinstance(raw,bytes):raw=raw.decode()
                    ingest_notification(json.loads(raw),subs,conn,stats)
                if time.monotonic()-last>=5:
                    reports=[pair_witness(conn,p) for p in pairs]
                    observed=conn.execute('SELECT count(*) FROM latest').fetchone()[0]
                    report={'pool_accounts':len(addresses),'observed':observed,'updates':stats['updates'],
                       'bootstrap_batches':stats['bootstrap_batches'],
                       'pairs_two_pool_accounts_observed':sum(r['gate']=='POOL_ACCOUNT_LINEAGE_ONLY' for r in reports),
                       'ws_connected':True,'signing':False,'broadcast':False,
                       'account_bytes_cached_in_sqlite':True,'price_freshness_certified':False,
                       'bin_arrays_and_vaults_not_yet_mirrored':True,
                       'next_gate':'ADD_VAULT_AND_BIN_ARRAY_APPLY_ACCOUNT_EVENT'}
                    temp=STATUS.with_name(STATUS.name+'.tmp');temp.write_text(json.dumps(report,indent=2),encoding='utf-8');os.replace(temp,STATUS)
                    emit('BOSS332_WITNESS_HEARTBEAT',report);last=time.monotonic()
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            stats['disconnects']+=1
            reason=redacted(e)
            if '429' in reason or 'too many requests' in reason.lower():stats['rpc_429']+=1
            emit('BOSS332_RECONNECT',{'reason':reason,'backoff_seconds':round(backoff,2),'429_count':stats['rpc_429'],
                'will_retry':True,'trading_authority':False})
            time.sleep(backoff+random.uniform(0,.5));backoff=min(60.,backoff*2)
        finally:
            if sock:
                try:sock.close()
                except Exception:pass
    conn.close();emit('BOSS332_EXIT',{'stats':dict(stats),'signing':False,'broadcast':False})
    return 0

def tests():
    import unittest,tempfile
    class Test(unittest.TestCase):
        def setUp(self):
            self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
            self.c=sqlite3.connect(':memory:');self.c.execute('CREATE TABLE latest(pubkey TEXT PRIMARY KEY,slot INTEGER,received_ns INTEGER,owner TEXT,lamports INTEGER,data_b64 TEXT,content_sha256 TEXT,source TEXT)')
            self.a='1'*32;self.b='2'*32
            self.value={'data':[base64.b64encode(b'live-state').decode(),'base64'],'owner':'1'*32,'lamports':44}
        def test_base64_content_sha(self):
            x=normalize(self.a,self.value,200,1000,'WEBSOCKET_NOTIFICATION');self.assertEqual(x['content_sha256'],hashlib.sha256(b'live-state').hexdigest())
        def test_invalid_base64_fails_closed(self):
            with self.assertRaises(ValueError):normalize(self.a,{'data':['%%','base64'],'owner':self.b},3,100,'WS')
        def test_jsonparsed_not_silently_accepted(self):
            with self.assertRaises(ValueError):normalize(self.a,{'data':{'parsed':True},'owner':self.b},3,100,'WS')
        def test_out_of_order_slot_guard(self):
            upsert(self.c,normalize(self.a,self.value,300,1000,'WS'));self.assertFalse(upsert(self.c,normalize(self.a,self.value,299,2000,'WS')))
        def test_same_slot_allowed(self):
            upsert(self.c,normalize(self.a,self.value,300,1000,'WS'));self.assertTrue(upsert(self.c,normalize(self.a,self.value,300,2000,'WS')))
        def test_pubkey_check(self):
            self.assertTrue(pubkey(self.a));self.assertFalse(pubkey('API?KEY=abc'))
        def test_watch_dedup(self):
            self.assertEqual(watch_addresses([dict(pump_pool=self.a,meteora_pool=self.b),dict(pump_pool=self.a,meteora_pool=self.b)]),[self.a,self.b])
        def test_missing_account_never_price_certified(self):
            r=pair_witness(self.c,dict(pump_pool=self.a,meteora_pool=self.b));self.assertFalse(r['price_freshness_certified'])
        def test_complete_pool_accounts_still_no_quote(self):
            for a in (self.a,self.b):upsert(self.c,normalize(a,self.value,500,1000,'WS'))
            r=pair_witness(self.c,dict(pump_pool=self.a,meteora_pool=self.b));self.assertEqual(r['gate'],'POOL_ACCOUNT_LINEAGE_ONLY');self.assertFalse(r['all_swap_accounts_witnessed'])
        def test_notification_parsing_and_slot(self):
            msg={'method':'accountNotification','params':{'subscription':5,'result':{'context':{'slot':808},'value':self.value}}}
            stats=Counter();self.assertTrue(ingest_notification(msg,{5:self.a},self.c,stats));self.assertEqual(self.c.execute('SELECT slot FROM latest').fetchone()[0],808)
        def test_unknown_subscription_discarded(self):
            stats=Counter();self.assertFalse(ingest_notification({'method':'accountNotification','params':{'subscription':4}}, {},self.c,stats));self.assertEqual(stats['unknown_subscription'],1)
        def test_sensitive_rpc_url_redaction(self):
            self.assertNotIn('foobar123',redacted(Exception('https://rpc.test/?api-key=foobar123')))
        def test_no_private_key_api_in_source(self):
            s=pathlib.Path(__file__).read_text(encoding='utf-8');self.assertNotIn('send'+'Transaction',s);self.assertNotIn('sign_'+'transaction(',s)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Test))
    if not result.wasSuccessful():return 1
    emit('BOSS332_TEST_PASS',{'tests':result.testsRun,'scope':'DETERMINISTIC_FIXTURES_ONLY'})
    return 0

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    for name in ('run','test','audit','status'):m.add_argument('--'+name,action='store_true')
    p.add_argument('--seconds',type=int,default=120);p.add_argument('--pairs',type=int,default=24)
    a=p.parse_args()
    if a.test:return tests()
    if a.audit:
        try:import websocket;driver='websocket-client'
        except ImportError:
            try:from websockets.sync.client import connect;driver='websockets.sync'
            except ImportError:driver='UNAVAILABLE_INSTALL_WEBSOCKET_CLIENT'
        emit('BOSS332_AUDIT',{'websocket_driver':driver,'scanner_untouched':True,
            'executor_untouched':True,'private_key_not_used':True,
            'price_freshness_certified':False,'signing':False,'broadcast':False});return 0
    if a.status:
        emit('BOSS332_STATUS',json.loads(STATUS.read_text()) if STATUS.exists() else {'gate':'NOT_YET_RUNNING'})
        return 0
    return run(a.seconds,a.pairs)
if __name__=='__main__':raise SystemExit(main())
'''
EXPECTED='f0c968a907b38078b2a6a9ce468212ace66b6b45d0929475c2759d04fb731c7c'
def install():
    raw=SOURCE.encode('utf-8')
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise RuntimeError('SOURCE_HASH_MISMATCH')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    temp=TARGET.with_name(TARGET.name+'.332.installing')
    temp.write_bytes(raw)
    check=TARGET.with_name('oracle332check.pyc')
    try:py_compile.compile(str(temp),cfile=str(check),doraise=True)
    finally:
        if check.exists():check.unlink()
    os.replace(temp,TARGET)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:raise RuntimeError('BYTE_HASH_MISMATCH')
    print('[ORACLE332_INSTALLED]',TARGET)
    print('[ORACLE332_SHA256_PASS]',EXPECTED)
def call(args,env=None):
    if not TARGET.is_file() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError('INSTALL_ORACLE332_FIRST')
    return subprocess.call([sys.executable,'-m',MODULE,*args],env=env)
def launch(args):
    from build_oracle_182_secure_windows_credentials import load,api,HELIUS
    key=load(api(),HELIUS)
    if not key:raise RuntimeError('HELIUS_CREDENTIAL_UNAVAILABLE')
    env=os.environ.copy()
    env.pop('QSB_SOLANA_PRIVATE_KEY',None)
    env['QSB_LIVE_ARM']='NO'
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+quote(key,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+quote(key,safe='')
    del key
    return call(args,env=env)
def main():
    p=argparse.ArgumentParser(description='ORACLE332 executor WS independent account witness')
    modes=p.add_mutually_exclusive_group(required=True)
    for mode in ('install','test','audit','status','launch'):modes.add_argument('--'+mode,action='store_true')
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--pairs',type=int,default=24)
    a=p.parse_args()
    if a.install:install();return 0
    if a.test:return call(['--test'])
    if a.audit:return call(['--audit'])
    if a.status:return call(['--status'])
    if a.launch:return launch(['--run','--seconds',str(a.seconds),'--pairs',str(a.pairs)])
    return 1
if __name__=='__main__':raise SystemExit(main())
