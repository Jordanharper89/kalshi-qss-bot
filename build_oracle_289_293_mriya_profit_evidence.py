"""ORACLE-289..293: complete standalone read-only Mriya discovery + evidence sidecar installer.
Does not replace scanner or price engine; creates a self-contained running evidence service.
"""
from pathlib import Path
import argparse, py_compile

TARGET=Path('oracle_289_293_mriya_evidence_runtime.py')
SOURCE=r'''"""ORACLE 289-293 persistent read-only Mriya trade-observation evidence.
Mriya wallet activity is NOT an atomic arbitrage opportunity or executable profit.
"""
import argparse, base64, hashlib, json, os, sqlite3, time, urllib.request, urllib.error
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone

ROOT=Path('runtime_state/oracle/oracle_live_execution')
DB=ROOT/'ORACLE289_293_MRIYA_EVIDENCE.sqlite3'
MARKET_DB=ROOT/'ORACLE283_287_MARKET_EVIDENCE.sqlite3'
MRIYA='MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X'
WSOL='So11111111111111111111111111111111111111112'
GRID=tuple(round(.010+i*.005,3) for i in range(19))


def disarmed():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('RESEARCH_CHILD_MUST_BE_DISARMED')

def connect(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path,timeout=15)
    c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA busy_timeout=15000')
    c.executescript("""CREATE TABLE IF NOT EXISTS signatures(sig TEXT PRIMARY KEY,slot INTEGER,block_time INTEGER,status TEXT,first_seen INTEGER);
CREATE TABLE IF NOT EXISTS transactions(sig TEXT PRIMARY KEY,slot INTEGER,block_time INTEGER,fee_lamports INTEGER,sol_delta_lamports INTEGER,tokens_json TEXT,source TEXT);
CREATE TABLE IF NOT EXISTS tokens(mint TEXT PRIMARY KEY,first_seen INTEGER,last_seen INTEGER,events INTEGER,tracked INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cycles(epoch INTEGER PRIMARY KEY,rpc_calls INTEGER,discovered INTEGER,decoded INTEGER,new_tokens INTEGER,tracked_tokens INTEGER,market_bytes INTEGER,fresh_market_bytes INTEGER,quote_count INTEGER,net_positive INTEGER,readiness TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
""")
    return c

def rpc(url,method,params,timeout=14):
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as resp:data=resp.read(4000001)
    if len(data)>4000000:raise RuntimeError('RPC_REPLY_OVERSIZE')
    val=json.loads(data)
    if not isinstance(val,dict) or 'error' in val:raise RuntimeError('RPC_RESULT_REJECTED')
    return val.get('result')

def signature_rows(payload):
    if not isinstance(payload,list):raise ValueError('SIGNATURE_RESPONSE_NOT_LIST')
    result=[]
    for r in payload:
        if not isinstance(r,dict):continue
        sig=r.get('signature');slot=r.get('slot');bt=r.get('blockTime')
        if not isinstance(sig,str) or not 64<=len(sig)<=100 or type(slot)!=int or slot<=0:continue
        if bt is not None and (type(bt)!=int or bt<0):continue
        result.append((sig,slot,bt,'ERR' if r.get('err') is not None else 'OK'))
    return result

def wallet_deltas(tx):
    """Public transaction deltas for one exact wallet. Not wallet's realized profit."""
    if not isinstance(tx,dict):raise ValueError('TX_NOT_FOUND')
    meta=tx.get('meta');tr=tx.get('transaction')
    if not isinstance(meta,dict) or not isinstance(tr,dict):raise ValueError('TX_META_MISSING')
    message=tr.get('message',{})
    accounts=message.get('accountKeys',[])
    keys=[x if isinstance(x,str) else x.get('pubkey') if isinstance(x,dict) else None for x in accounts]
    if MRIYA not in keys:raise ValueError('WALLET_KEY_NOT_IN_TRANSACTION')
    i=keys.index(MRIYA);pre=meta.get('preBalances',[]);post=meta.get('postBalances',[])
    if i>=len(pre) or i>=len(post):raise ValueError('SOL_BALANCE_MISSING')
    sol_delta=int(post[i])-int(pre[i]);fee=meta.get('fee',0)
    def balances(k):
        out={}
        for t in meta.get(k,[]):
            if not isinstance(t,dict) or t.get('owner')!=MRIYA:continue
            mint=t.get('mint');amount=t.get('uiTokenAmount',{}).get('amount')
            if not isinstance(mint,str) or not isinstance(amount,str):continue
            try:amt=int(amount)
            except ValueError:continue
            out[mint]=out.get(mint,0)+amt
        return out
    a=balances('preTokenBalances');b=balances('postTokenBalances')
    diffs={m:b.get(m,0)-a.get(m,0) for m in sorted(a.keys()|b.keys()) if b.get(m,0)!=a.get(m,0)}
    return {'slot':tx.get('slot'),'block_time':tx.get('blockTime'),'fee_lamports':int(fee),
            'sol_delta_lamports':sol_delta,'tokens':diffs,'transaction_error':meta.get('err') is not None}

def inspected_market(db=MARKET_DB,max_age=120):
    if not db.is_file():return (0,0)
    con=sqlite3.connect('file:'+str(db.resolve())+'?mode=ro',uri=True,timeout=4)
    try:
        records=con.execute('SELECT raw,sha,received FROM account_bytes').fetchall()
        now=time.time()
        valid=[(raw,received) for raw,sha,received in records if isinstance(raw,bytes) and hashlib.sha256(raw).hexdigest()==sha]
        return len(valid),sum(0<=now-t<=max_age for _,t in valid)
    except sqlite3.OperationalError:return (0,0)
    finally:con.close()

def tracked_mints():
    """Optional discovery signal, no market universe or scanner mutation."""
    try:
        import build_oracle_269_persistent_token_lifecycle as m
        db=m.load(m.DB)
        return {str(t) for t in db.get('tokens',{})}
    except (ImportError,KeyError,OSError,ValueError,TypeError):return set()

def one_cycle(c,url,max_rpc=3,fetch_limit=2):
    if not 1<=max_rpc<=3 or not 0<=fetch_limit<=2:raise ValueError('RPC_BUDGET_VIOLATION')
    now=int(time.time());calls=0;new=0;decoded=0;new_tokens=0
    calls+=1
    entries=signature_rows(rpc(url,'getSignaturesForAddress',[MRIYA,{'limit':15,'commitment':'confirmed'}]))
    prior={r[0] for r in c.execute('SELECT sig FROM signatures')}
    # Newer first for discovery, fetch only unprocessed signatures.
    for sig,slot,bt,status in entries:
        if sig not in prior:
            c.execute('INSERT OR IGNORE INTO signatures VALUES(?,?,?,?,?)',(sig,slot,bt,status,now));new+=1
    for sig,slot,bt,status in entries:
        if calls>=max_rpc or decoded>=fetch_limit:break
        if status!='OK' or c.execute('SELECT 1 FROM transactions WHERE sig=?',(sig,)).fetchone():continue
        calls+=1
        try:
            tx=rpc(url,'getTransaction',[sig,{'encoding':'jsonParsed','commitment':'confirmed','maxSupportedTransactionVersion':0}])
            event=wallet_deltas(tx)
        except (ValueError,TypeError,KeyError,RuntimeError):continue
        c.execute('INSERT OR IGNORE INTO transactions VALUES(?,?,?,?,?,?,?)',
                  (sig,event['slot'],event['block_time'],event['fee_lamports'],event['sol_delta_lamports'],
                   json.dumps(event['tokens'],sort_keys=True),'HELIUS_PUBLIC_PARSED'))
        decoded+=1
        for mint,delta in event['tokens'].items():
            if delta==0 or mint==WSOL:continue
            prior_token=c.execute('SELECT events FROM tokens WHERE mint=?',(mint,)).fetchone()
            if prior_token is None:new_tokens+=1
            c.execute('INSERT INTO tokens(mint,first_seen,last_seen,events) VALUES(?,?,?,1) ON CONFLICT(mint) DO UPDATE SET last_seen=excluded.last_seen,events=events+1',(mint,now,now))
    watched=tracked_mints()
    c.execute('UPDATE tokens SET tracked=0')
    for mint in watched:c.execute('UPDATE tokens SET tracked=1 WHERE mint=?',(mint,))
    tracked=c.execute('SELECT count(*) FROM tokens WHERE tracked=1').fetchone()[0]
    valid,fresh=inspected_market()
    # No quote and no opportunity can be certified merely from wallet deltas.
    status='HOLD_NO_CANONICAL_SYNCHRONIZED_LOCAL_QUOTES'
    c.execute('INSERT OR REPLACE INTO cycles VALUES(?,?,?,?,?,?,?,?,?,?,?)',
              (now,calls,new,decoded,new_tokens,tracked,valid,fresh,0,0,status))
    c.commit()
    return {'rpc_calls':calls,'new_signatures':new,'decoded_transactions':decoded,
            'new_mints':new_tokens,'watched_mints_matched':tracked,
            'market_verified_bytes':valid,'market_fresh_bytes':fresh,
            'local_quotes':0,'net_positive_certified':0,'status':status,
            'signing':False,'broadcast':False}

def table(c):
    print('ORACLE 289-293 | PUBLIC MRIYA DISCOVERY + MARKET EVIDENCE (READ ONLY)')
    print('TIME        RPC  NEW SIG  TX READ  NEW MINTS  TRACKED  BYTES  FRESH  QUOTES  NET+')
    for r in c.execute('SELECT epoch,rpc_calls,discovered,decoded,new_tokens,tracked_tokens,market_bytes,fresh_market_bytes,quote_count,net_positive FROM cycles ORDER BY epoch DESC LIMIT 20'):
        print(f'{r[0]:10} {r[1]:4} {r[2]:8} {r[3]:8} {r[4]:10} {r[5]:8} {r[6]:6} {r[7]:6} {r[8]:7} {r[9]:5}')
    print('MINT (public)                                     EVENTS  TRACKED  LAST SEEN')
    for m,e,t,last in c.execute('SELECT mint,events,tracked,last_seen FROM tokens ORDER BY last_seen DESC,events DESC LIMIT 15'):
        print(f'{m:48} {e:6} {t:8} {last:11}')
    print('[GATE] Wallet trading history is NOT proof of same-slot arbitrage, PnL, or execution readiness.')

def monitor(seconds,interval,max_rpc):
    disarmed()
    if interval<60:raise RuntimeError('MINIMUM_INTERVAL_60_SECONDS')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('SOLANA_RPC_URL_REQUIRED')
    c=connect();end=time.monotonic()+seconds if seconds else float('inf')
    print('[ORACLE289_293_START] mriya_discovery=TRUE rpc_budget_per_cycle='+str(max_rpc)+' signing=FALSE broadcast=FALSE',flush=True)
    try:
        while time.monotonic()<end:
            start=time.monotonic()
            try:result=one_cycle(c,url,max_rpc)
            except urllib.error.HTTPError as exc:
                # Immediately stop on 429 rather than hot-looping or printing credential-bearing URLs.
                if exc.code==429:print('[ORACLE289_293_429] STOP_THROTTLED',flush=True);break
                print('[ORACLE289_293_RPC_HTTP] status='+str(exc.code),flush=True);result=None
            except (urllib.error.URLError,TimeoutError,OSError,RuntimeError,ValueError) as exc:
                print('[ORACLE289_293_RPC_HOLD] '+type(exc).__name__,flush=True);result=None
            if result:print('[ORACLE289_293_HEARTBEAT]',json.dumps(result,sort_keys=True),flush=True)
            while time.monotonic()<end and time.monotonic()-start<interval:
                time.sleep(min(1,interval-(time.monotonic()-start),end-time.monotonic()))
    except KeyboardInterrupt:print('[ORACLE289_293_STOP] KeyboardInterrupt',flush=True)
    finally:c.close()

def test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        c=connect(Path(d)/'test.sqlite')
        s='s'*88
        assert signature_rows([{'signature':s,'slot':12,'blockTime':10,'err':None}])==[(s,12,10,'OK')]
        tx={'slot':12,'blockTime':10,'transaction':{'message':{'accountKeys':[MRIYA]}},
            'meta':{'preBalances':[10000],'postBalances':[8000],'fee':500,
            'preTokenBalances':[{'owner':MRIYA,'mint':'X','uiTokenAmount':{'amount':'100'}}],
            'postTokenBalances':[{'owner':MRIYA,'mint':'X','uiTokenAmount':{'amount':'150'}}], 'err':None}}
        result=wallet_deltas(tx)
        assert result['tokens']=={'X':50} and result['sol_delta_lamports']==-2000
        try:wallet_deltas(dict(tx,transaction={'message':{'accountKeys':['some-other-wallet']}}))
        except ValueError:pass
        else:raise AssertionError('WALLET_ATTRIBUTION_BYPASS')
        c.execute('INSERT INTO cycles VALUES(?,?,?,?,?,?,?,?,?,?,?)',(1,1,1,1,1,0,0,0,0,0,'HOLD'))
        c.commit();assert c.execute('SELECT count(*) FROM cycles').fetchone()[0]==1
        c.close()
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.1
    print('[ORACLE289_293_TEST_PASS] signature_validation=TRUE wallet_attribution=TRUE token_deltas=TRUE sqlite=TRUE no_trades=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true')
    p.add_argument('--seconds',type=int,default=0);p.add_argument('--interval',type=int,default=90)
    p.add_argument('--max-rpc',type=int,default=3)
    a=p.parse_args()
    if a.test:test()
    elif a.table:c=connect();table(c);c.close()
    elif a.run:monitor(max(0,a.seconds),a.interval,a.max_rpc)
    else:p.error('--test, --table or --run required')
'''

def install():
    compile(SOURCE,str(TARGET),'exec')
    if TARGET.exists():
        existing=TARGET.read_text(encoding='utf-8')
        if not existing.startswith('"""ORACLE 289-293 persistent read-only Mriya trade-observation evidence.'):
            raise RuntimeError('REFUSE_UNKNOWN_RUNTIME_OVERWRITE')
    tmp=TARGET.with_suffix('.tmp');tmp.write_text(SOURCE,encoding='utf-8');tmp.replace(TARGET)
    py_compile.compile(str(TARGET),doraise=True)
    print('[ORACLE289_293_INSTALL_PASS] 5_stages=TRUE scanner_unchanged=TRUE mriya_public=TRUE signing=FALSE broadcast=FALSE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');a=p.parse_args()
    if not a.install:p.error('Specify --install')
    install()
