"""ORACLE-280: vetted bin-array account WebSocket capture; disarmed, zero REST."""
import argparse, base64, hashlib, json, os, socket, time
from collections import Counter
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
SOURCE = ROOT/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json'
STATE = ROOT/'ORACLE280_BIN_ARRAY_WS_STATES.json'
REPORT = ROOT/'ORACLE280_BIN_ARRAY_WS_REPORT.json'
OWNER = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
SIZES = [round(.01+.005*i,3) for i in range(19)]
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def decode58(value):
    if not isinstance(value,str) or not 32 <= len(value) <= 44:raise ValueError('BAD_ADDRESS')
    n=0
    for c in value:n=n*58+ALPHABET.index(c)
    data=n.to_bytes((n.bit_length()+7)//8,'big') if n else b''
    data=b'\0'*(len(value)-len(value.lstrip('1')))+data
    if len(data)!=32:raise ValueError('BAD_ADDRESS_SIZE')
    return data

def manifest(cache,max_accounts):
    if cache.get('build')!='ORACLE279' or not isinstance(cache.get('pools'),dict):raise RuntimeError('UNTRUSTED_CACHE')
    result={}
    for pool,info in sorted(cache['pools'].items()):
        try:pool_raw=decode58(pool)
        except (ValueError,TypeError):continue
        if info.get('historical_only') is not True or not isinstance(info.get('addresses'),list):continue
        for entry in info['addresses']:
            try:
                address=entry['address'];decode58(address)
                assert entry['owner']==OWNER
                assert type(entry['array_index']) is int
                assert type(entry['byte_count']) is int and entry['byte_count']>=56
                assert len(entry['sha256'])==64
            except (KeyError,ValueError,TypeError,AssertionError):continue
            if address in result and result[address]['pool']!=pool:raise RuntimeError('ARRAY_SHARED_ACROSS_POOLS')
            result[address]={'pool':pool,'pool_raw':pool_raw,'array_index':entry['array_index'],
                             'historical_sha256':entry['sha256'],'token':info.get('token','')}
    return dict(list(sorted(result.items()))[:max_accounts])

def decode(packet,subscriptions,selected,now):
    if not isinstance(packet,dict) or packet.get('method')!='accountNotification':return None
    params=packet.get('params')
    if not isinstance(params,dict):return None
    addr=subscriptions.get(params.get('subscription'))
    if addr not in selected:return None
    result=params.get('result');ctx=result.get('context') if isinstance(result,dict) else None
    value=result.get('value') if isinstance(result,dict) else None
    if not isinstance(ctx,dict) or not isinstance(value,dict) or type(ctx.get('slot')) is not int or ctx['slot']<=0:return None
    data=value.get('data')
    if value.get('owner')!=OWNER or not isinstance(data,list) or len(data)!=2 or data[1]!='base64':return None
    try:raw=base64.b64decode(data[0],validate=True)
    except (ValueError,TypeError):return None
    target=selected[addr]
    if not 56<=len(raw)<=240000 or raw[24:56]!=target['pool_raw']:return None
    index=int.from_bytes(raw[8:16],'little',signed=True)
    if index!=target['array_index']:return None
    return {'address':addr,'pool':target['pool'],'token':target['token'],'array_index':index,
            'slot':ctx['slot'],'owner':OWNER,'fingerprint':hashlib.sha256(raw).hexdigest(),
            'byte_count':len(raw),'data_b64':base64.b64encode(raw).decode(), 'received_epoch':now,
            'verified_pool_index_owner':True}

def accept(state,item):
    previous=state['accounts'].get(item['address'])
    if previous and item['slot']<previous['slot']:return 'OLDER_SLOT'
    if previous and item['slot']==previous['slot']:
        return 'DUPLICATE' if previous['fingerprint']==item['fingerprint'] else 'SAME_SLOT_CONFLICT'
    state['accounts'][item['address']]=item
    return 'CAPTURED'

def test():
    pool=OWNER;address='So11111111111111111111111111111111111111112'
    raw=b'Z'*8+(4).to_bytes(8,'little',signed=True)+b'X'*8+decode58(pool)+b'Q'*8
    cache={'build':'ORACLE279','pools':{pool:{'historical_only':True,'token':address,'addresses':[
        {'address':address,'owner':OWNER,'array_index':4,'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}}}
    selected=manifest(cache,30);assert len(selected)==1
    def packet(contents,slot=100):return {'method':'accountNotification','params':{'subscription':7,'result':{
        'context':{'slot':slot},'value':{'owner':OWNER,'data':[base64.b64encode(contents).decode(),'base64']}}}}
    entry=decode(packet(raw),{7:address},selected,123)
    assert entry and entry['array_index']==4
    state={'accounts':{}};assert accept(state,entry)=='CAPTURED' and accept(state,entry)=='DUPLICATE'
    assert decode(packet(raw[:24]+b'N'*32+raw[56:]),{7:address},selected,123) is None
    assert decode(packet(raw,99),{},selected,123) is None
    assert len(SIZES)==19 and SIZES[-1]==.1
    print('[ORACLE280_TEST_PASS] vetted_addresses=TRUE bin_identity=TRUE slot_dedup=TRUE zero_rest=TRUE no_execution=TRUE')

def run(seconds,maximum):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    url=os.getenv('SOLANA_WS_URL','')
    if not url.startswith('wss://'):raise RuntimeError('WS_URL_REQUIRED')
    if not SOURCE.is_file():raise RuntimeError('ORACLE279_CACHE_MISSING')
    selected=manifest(json.loads(SOURCE.read_text(encoding='utf-8')),maximum)
    if not selected:raise RuntimeError('NO_VETTED_ARRAYS')
    import websocket
    state={'build':'ORACLE280','schema':1,'accounts':{},'signing':False,'broadcast':False,'execution_admission':False}
    counts=Counter();pending={};subscribed={};ws=None
    try:
        ws=websocket.create_connection(url,timeout=8,enable_multithread=True);ws.settimeout(2)
        for i,address in enumerate(selected,1):
            pending[i]=address
            ws.send(json.dumps({'jsonrpc':'2.0','id':i,'method':'accountSubscribe','params':[address,{'encoding':'base64','commitment':'processed'}]}))
        stop=time.monotonic()+seconds
        while time.monotonic()<stop:
            try:raw=ws.recv()
            except (socket.timeout,websocket.WebSocketTimeoutException):continue
            except websocket.WebSocketConnectionClosedException:counts['WS_CLOSED']+=1;break
            try:packet=json.loads(raw)
            except (TypeError,ValueError):counts['BAD_JSON']+=1;continue
            if not isinstance(packet,dict):continue
            if type(packet.get('id')) is int and packet['id'] in pending:
                address=pending.pop(packet['id'])
                if type(packet.get('result')) is int:
                    subscribed[packet['result']]=address;counts['SUBSCRIBED']+=1
                else:counts['SUBSCRIBE_REJECTED']+=1
                continue
            if packet.get('method')!='accountNotification':continue
            counts['NOTIFICATIONS']+=1
            row=decode(packet,subscribed,selected,time.time())
            if row is None:counts['INVALID']+=1;continue
            counts[accept(state,row)]+=1
    finally:
        if ws is not None:
            try:ws.close()
            except Exception:pass
        ROOT.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(state,indent=2),encoding='utf-8')
    pools=Counter(e['pool'] for e in state['accounts'].values())
    report={'build':'ORACLE280','cached_arrays':len(selected),'subscribed':len(subscribed),
            'arrays_with_live_notifications':len(state['accounts']),'pools_with_live_array_updates':len(pools),
            'per_pool_live_arrays':dict(pools),'counters':dict(counts),'rest_rpc_calls':0,'size_grid':SIZES,
            'all_bins_hydrated':False,'fresh_canonical_state_certified':False,'net_profit_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,'status':'HOLD_COMPLETE_BIN_HYDRATION'}
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('[ORACLE280_RESULT]',json.dumps({k:v for k,v in report.items() if k!='size_grid'},sort_keys=True))
    print('[REPORT]',REPORT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--max-accounts',type=int,default=30)
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(10,min(180,a.seconds)),max(1,min(64,a.max_accounts)))
