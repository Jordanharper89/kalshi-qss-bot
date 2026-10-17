from __future__ import annotations
import argparse, asyncio, base64, hashlib, json, os, sqlite3, time
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote

DEST=Path('qseries_v2/oracle_execution/oracle_live_pricing/oracle230a.py')
ROOT=Path('runtime_state/oracle/oracle_live_execution')
REPORT=ROOT/'ORACLE230A_RAW_WS_BRIDGE.json'
DB=ROOT/'ORACLE218_DISCOVERY.sqlite3'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def config(path=Path('.env')):
    names=(
        'SOLANA_WS_URL','HELIUS_WS_URL','QSB_SOLANA_WS_URL',
        'SOLANA_RPC_URL','HELIUS_RPC_URL','QSB_SOLANA_RPC_URL',
        'HELIUS_API_KEY','QSB_HELIUS_API_KEY'
    )
    values={}
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#'): continue
            if line.startswith('export '): line=line[7:].strip()
            if '=' not in line: continue
            key,value=line.split('=',1)
            key=key.strip()
            if key not in names: continue
            value=value.strip()
            if len(value)>=2 and value[0]==value[-1] and value[0] in ("'",'"'):
                value=value[1:-1]
            values[key]=value.strip()
    for name in names:
        if os.environ.get(name): values[name]=os.environ[name].strip()
    return values

def endpoint(values=None):
    e=config() if values is None else values
    names=(
        'SOLANA_WS_URL','HELIUS_WS_URL','QSB_SOLANA_WS_URL',
        'SOLANA_RPC_URL','HELIUS_RPC_URL','QSB_SOLANA_RPC_URL'
    )
    for name in names:
        value=e.get(name,'').strip()
        if not value: continue
        parsed=urlsplit(value)
        if parsed.scheme not in ('https','wss') or not parsed.hostname:
            raise RuntimeError('HOLD_INVALID_ENDPOINT_'+name)
        if parsed.username or parsed.password:
            raise RuntimeError('HOLD_ENDPOINT_USERINFO_REFUSED')
        host=parsed.hostname.lower()
        if not (host=='helius-rpc.com' or host.endswith('.helius-rpc.com')):
            raise RuntimeError('HOLD_NON_HELIUS_ENDPOINT_'+name)
        return urlunsplit(('wss',parsed.netloc,parsed.path,
                           parsed.query,'')),name
    for name in ('HELIUS_API_KEY','QSB_HELIUS_API_KEY'):
        key=e.get(name,'').strip()
        if key:
            return ('wss://mainnet.helius-rpc.com/?api-key='+
                    quote(key,safe='')),name
    raise RuntimeError('HOLD_NO_HELIUS_CREDENTIAL_IN_ENV_FILE')

def targets(limit=100):
    if not DB.is_file(): raise RuntimeError('HOLD_MISSING_REGISTRY')
    with closing(sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        rows=db.execute(
            'SELECT mint,pump_pool,meteora_pool FROM universal_routes '
            'ORDER BY last_seen DESC LIMIT ?', (limit,)
        ).fetchall()
    owners={}
    for mint,p,m in rows:
        if p==m: raise RuntimeError('HOLD_AMBIGUOUS_POOL_IDENTITY')
        for address,owner in ((p,PUMP),(m,DLMM)):
            if address in owners and owners[address]!=owner:
                raise RuntimeError('HOLD_OWNER_COLLISION')
            owners[address]=owner
    return owners,len(rows)

def extract(msg,subs,owners):
    if not isinstance(msg,dict) or msg.get('method')!='accountNotification':
        return None
    p=msg.get('params')
    if not isinstance(p,dict): return None
    address=subs.get(p.get('subscription'))
    result=p.get('result')
    if address not in owners or not isinstance(result,dict): return None
    ctx=result.get('context')
    value=result.get('value')
    slot=ctx.get('slot') if isinstance(ctx,dict) else None
    if type(slot)!=int or slot<=0 or not isinstance(value,dict): return None
    if value.get('owner')!=owners[address]:
        raise ValueError('OWNER_PROGRAM_MISMATCH')
    if value.get('executable') is not False:
        raise ValueError('EXECUTABLE_ACCOUNT_REJECTED')
    data=value.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':
        raise ValueError('NON_BASE64_DATA')
    raw=base64.b64decode(data[0],validate=True)
    if not 1<=len(raw)<=1048576: raise ValueError('INVALID_LENGTH')
    if 'space' in value and value['space']!=len(raw):
        raise ValueError('SPACE_MISMATCH')
    return address,slot,value['owner'],data[0],hashlib.sha256(raw).hexdigest()

def install():
    source=Path(__file__).read_bytes()
    if DEST.exists() and DEST.read_bytes()!=source:
        old=DEST.read_text(encoding='utf-8-sig')
        if 'ORACLE230A_INSTALLED' not in old:
            raise RuntimeError('REFUSE_UNKNOWN_ORACLE230A_OVERWRITE')
    DEST.parent.mkdir(parents=True,exist_ok=True)
    init=DEST.parent/'__init__.py'
    if not init.exists(): init.write_text('',encoding='utf-8')
    DEST.write_bytes(source)
    print('[ORACLE230A_INSTALLED]',DEST)

def test():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        path=Path(td)/'.env'
        path.write_text(
            'HELIUS_API_KEY=fixture_only\n'
            'QSB_SOLANA_PRIVATE_KEY=NEVER_USE_THIS\n',
            encoding='utf-8'
        )
        result=config(path)
        assert 'QSB_SOLANA_PRIVATE_KEY' not in result
        assert result['HELIUS_API_KEY']=='fixture_only'
        url,source=endpoint(result)
        assert source=='HELIUS_API_KEY' and url.startswith('wss://')
        assert endpoint({'SOLANA_RPC_URL':
            'https://mainnet.helius-rpc.com/?api-key=fixture'})[0].startswith('wss:')
    msg={'method':'accountNotification','params':{'subscription':7,'result':{
        'context':{'slot':42},'value':{'data':['YWJj','base64'],
        'owner':PUMP,'executable':False,'space':3}}}}
    assert extract(msg,{7:'pump'},{'pump':PUMP})[:3]==('pump',42,PUMP)
    bad=json.loads(json.dumps(msg))
    bad['params']['result']['value']['owner']=DLMM
    try: extract(bad,{7:'pump'},{'pump':PUMP})
    except ValueError: pass
    else: raise AssertionError('BAD_OWNER_ACCEPTED')
    print('[ORACLE230A_V3_TEST_PASS] dotenv=TRUE secret_isolation=TRUE owner_guard=TRUE')

async def observe(url,seconds=40):
    import websockets
    from qseries_v2.oracle_execution.oracle_live_pricing import oracle226
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ARMED_REFUSED')
    owners,n=targets()
    if not owners: raise RuntimeError('HOLD_NO_POOLS')
    stats=Counter(); subs={}; pending={}; seen=set()
    end=time.monotonic()+seconds
    try:
        async with websockets.connect(url,max_size=8*1024*1024,
                                      ping_interval=20,open_timeout=15) as ws:
            for i,address in enumerate(owners,1):
                pending[i]=address
                await ws.send(json.dumps({
                    'jsonrpc':'2.0','id':i,'method':'accountSubscribe',
                    'params':[address,{'encoding':'base64','commitment':'confirmed'}]
                }))
            print('[ORACLE230A_SUBMITTED]',len(owners),flush=True)
            while time.monotonic()<end:
                try:
                    raw=await asyncio.wait_for(
                        ws.recv(),min(5,max(.01,end-time.monotonic()))
                    )
                    msg=json.loads(raw)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(msg,dict): continue
                if type(msg.get('id'))==int and msg['id'] in pending:
                    if type(msg.get('result'))==int:
                        subs[msg['result']]=pending.pop(msg['id'])
                        stats['ack']+=1
                    else:
                        pending.pop(msg['id'])
                        stats['reject']+=1
                    continue
                try:
                    event=extract(msg,subs,owners)
                except (ValueError,TypeError) as exc:
                    stats['invalid_'+type(exc).__name__]+=1
                    continue
                if event is None: continue
                address,slot,owner,data64,digest=event
                identity=(address,slot,digest)
                if identity in seen:
                    stats['duplicate']+=1
                    continue
                seen.add(identity)
                try:
                    oracle226.ingest(
                        address,slot,owner,data64,
                        datetime.now(timezone.utc).isoformat()
                    )
                    stats['stored']+=1
                    if stats['stored']<=5 or stats['stored']%20==0:
                        print('[ORACLE230A_RAW_STORED]',
                              stats['stored'],'slot',slot,flush=True)
                except (ValueError,RuntimeError,sqlite3.Error) as exc:
                    stats['store_rejected_'+type(exc).__name__]+=1
    finally:
        result={
            'build':'ORACLE230A_V3','routes':n,'accounts':len(owners),
            'stats':dict(stats),'raw_handoff_connected':stats['stored']>0,
            'official_exact_pricing_connected':False,
            'profit_certified':False,'signing':False,'broadcast':False
        }
        ROOT.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('[ORACLE230A_RESULT]',json.dumps(result,sort_keys=True))
        print('[REPORT]',REPORT)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--install',action='store_true')
    ap.add_argument('--test',action='store_true')
    ap.add_argument('--live',action='store_true')
    ap.add_argument('--seconds',type=int,default=40)
    args=ap.parse_args()
    if args.install: install()
    if args.test: test()
    if args.live:
        url,source=endpoint()
        print('[ORACLE230A_CONFIG_LOADED]',source,'secret_hidden=TRUE')
        try:
            asyncio.run(observe(url,args.seconds))
        except Exception as exc:
            print('[ORACLE230A_LIVE_HOLD]',type(exc).__name__)
            raise SystemExit(1)
    if not (args.install or args.test or args.live):
        ap.print_help()

if __name__=='__main__':
    main()