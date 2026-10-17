"""ORACLE-272: authenticated WS pool bytes -> restart-safe, bounded hydration staging."""
import argparse
import base64
import hashlib
import json
import os
import socket
import tempfile
import time
from collections import Counter
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge

BASE = Path('runtime_state/oracle/oracle_live_execution')
STATE = BASE / 'ORACLE272_WS_ACCOUNT_STATES.json'
REPORT = BASE / 'ORACLE272_CAPTURE_RESULT.json'
MAX_BYTES = 240000


def empty():
    return {'build':'ORACLE272','schema':1,'accounts':{},'signing':False,
            'broadcast':False,'execution_admission':False}


def load(path):
    if not path.exists():return empty()
    d=json.loads(path.read_text(encoding='utf-8'))
    if (d.get('build')!='ORACLE272' or d.get('schema')!=1 or
        any(d.get(k) is not False for k in ('signing','broadcast','execution_admission')) or
        not isinstance(d.get('accounts'),dict)):
        raise RuntimeError('UNTRUSTED_STAGING_STATE')
    return d


def save(path,d):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.oracle272_',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(d,f,sort_keys=True,separators=(',',':'))
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def extract(packet,subscribed,inventory,now):
    if not isinstance(packet,dict) or packet.get('method')!='accountNotification':return None
    params=packet.get('params')
    if not isinstance(params,dict) or type(params.get('subscription')) is not int:return None
    address=subscribed.get(params['subscription'])
    if address not in inventory:return None
    result=params.get('result')
    if not isinstance(result,dict):return None
    context,value=result.get('context'),result.get('value')
    if not isinstance(context,dict) or type(context.get('slot')) is not int or context['slot']<=0:return None
    if not isinstance(value,dict):return None
    encoded=value.get('data')
    if not isinstance(encoded,list) or len(encoded)!=2 or encoded[1]!='base64' or not isinstance(encoded[0],str):return None
    try:raw=base64.b64decode(encoded[0],validate=True)
    except (ValueError,TypeError):return None
    if not 0<len(raw)<=MAX_BYTES:return None
    # Account owner is part of the account context and must remain available to the hydrator.
    owner=value.get('owner')
    if not bridge.valid_address(owner):return None
    return {'address':address,'slot':context['slot'],'fingerprint':hashlib.sha256(raw).hexdigest(),
            'data_b64':base64.b64encode(raw).decode('ascii'),'byte_count':len(raw),
            'owner':owner,'received_epoch':now,'refs':[[mint,venue] for mint,venue in inventory[address]]}


def accept(state,item):
    address=item['address'];prev=state['accounts'].get(address)
    if prev and item['slot']<prev['slot']:return 'OLD_SLOT'
    if prev and item['slot']==prev['slot']:
        if item['fingerprint']==prev['fingerprint']:return 'DUPLICATE'
        return 'SAME_SLOT_CONFLICT'
    state['accounts'][address]=item
    return 'CAPTURED_NEW_ACCOUNT_STATE'


def candidates(state,now,age=30,slot_distance=150):
    by_token={}
    for address,entry in state['accounts'].items():
        if (type(entry.get('received_epoch')) not in (int,float) or
            not 0<=now-entry['received_epoch']<=age or
            not bridge.valid_address(address)):
            continue
        for mint,venue in entry.get('refs',[]):
            if venue not in ('PUMPSWAP_WS','METEORA_WS'):continue
            by_token.setdefault(mint,{}).setdefault(venue,[]).append(entry)
    output=[]
    for mint,venues in by_token.items():
        if not {'PUMPSWAP_WS','METEORA_WS'}.issubset(venues):continue
        pump=max(venues['PUMPSWAP_WS'],key=lambda e:e['slot'])
        meteora=max(venues['METEORA_WS'],key=lambda e:e['slot'])
        if abs(pump['slot']-meteora['slot'])>slot_distance:continue
        output.append({'token':mint,'pump_address':pump['address'],
            'meteora_address':meteora['address'],'pump_slot':pump['slot'],
            'meteora_slot':meteora['slot'],'hydration_candidate_only':True,
            'canonical_snapshot_certified':False})
    return sorted(output,key=lambda x:x['token'])


def test():
    mint='A'*32;a='B'*32;b='C'*32;owner='D'*32
    inventory={a:[(mint,'PUMPSWAP_WS')],b:[(mint,'METEORA_WS')]}
    def packet(subscription,slot,raw):
        return {'method':'accountNotification','params':{'subscription':subscription,
            'result':{'context':{'slot':slot},'value':{'owner':owner,
            'data':[base64.b64encode(raw).decode(),'base64']}}}}
    state=empty();t=1000
    first=extract(packet(1,200,b'pump'),{1:a,2:b},inventory,t)
    second=extract(packet(2,202,b'meteora'),{1:a,2:b},inventory,t+1)
    assert first['byte_count']==4 and accept(state,first)=='CAPTURED_NEW_ACCOUNT_STATE'
    assert accept(state,first)=='DUPLICATE'
    assert accept(state,second)=='CAPTURED_NEW_ACCOUNT_STATE'
    assert len(candidates(state,t+2))==1 and not candidates(state,t+100)
    assert not extract(packet(3,203,b'fake'),{1:a,2:b},inventory,t)
    assert accept(state,dict(first,slot=199))=='OLD_SLOT'
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'data.json';save(path,state)
        assert load(path)['accounts'][a]['data_b64']==first['data_b64']
    assert len(life.GRID)==19 and life.GRID[0]==.01 and life.GRID[-1]==.1
    print('[ORACLE272_TEST_PASS] ws_provenance=TRUE raw_bytes=TRUE restart=TRUE age_guard=TRUE 19_sizes=TRUE no_execution=TRUE')


def run(seconds,maximum):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    url=os.getenv('SOLANA_WS_URL','')
    if not url.startswith('wss://'):raise RuntimeError('WSS_REQUIRED')
    import websocket
    db=life.load(life.DB)
    inventory=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    selected=dict(list(inventory.items())[:maximum])
    if not selected:raise RuntimeError('NO_WATCHABLE_ACCOUNTS')
    state=load(STATE);counts=Counter();pending={};subscribed={};ws=None
    deadline=time.monotonic()+seconds
    try:
        ws=websocket.create_connection(url,timeout=7,enable_multithread=True)
        ws.settimeout(2)
        for i,address in enumerate(selected,1):
            pending[i]=address
            ws.send(json.dumps({'jsonrpc':'2.0','id':i,'method':'accountSubscribe',
                'params':[address,{'encoding':'base64','commitment':'processed'}]}))
        while time.monotonic()<deadline:
            try:raw=ws.recv()
            except (socket.timeout,websocket.WebSocketTimeoutException):continue
            except websocket.WebSocketConnectionClosedException:
                counts['WS_CLOSED']+=1;break
            try:msg=json.loads(raw)
            except (ValueError,TypeError):counts['BAD_JSON']+=1;continue
            if not isinstance(msg,dict):continue
            req=msg.get('id')
            if type(req) is int and req in pending:
                address=pending.pop(req)
                if type(msg.get('result')) is int:
                    subscribed[msg['result']]=address;counts['SUBSCRIBED']+=1
                else:counts['SUBSCRIBE_REJECTED']+=1
                continue
            if msg.get('method')!='accountNotification':continue
            counts['NOTIFICATIONS']+=1
            item=extract(msg,subscribed,selected,time.time())
            if item is None:counts['REJECTED']+=1;continue
            counts[accept(state,item)]+=1
            if counts['NOTIFICATIONS']%25==0:save(STATE,state)
    finally:
        if ws is not None:
            try:ws.close()
            except Exception:pass
        save(STATE,state)
        ready=candidates(state,time.time())
        report={'build':'ORACLE272','subscriptions_confirmed':len(subscribed),
            'watched_accounts':len(selected),'account_states_retained':len(state['accounts']),
            'two_venue_hydration_candidates':len(ready),'candidates':ready[:20],
            'counters':dict(counts),'rpc_poll_calls':0,'local_pricing_connected':False,
            'canonical_snapshot_certified':False,'net_profit_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,
            'status':'WS_PAYLOADS_STAGED_AWAITING_CANONICAL_HYDRATION'}
        save(REPORT,report)
        print('[ORACLE272_RESULT]',json.dumps({k:v for k,v in report.items() if k!='candidates'},sort_keys=True))
        for item in ready[:12]:
            print('[ORACLE272_HYDRATION_CANDIDATE]',json.dumps({**item,'token':item['token'][:12]},sort_keys=True))
        print('[REPORT]',REPORT)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--max-accounts',type=int,default=30)
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(10,min(a.seconds,180)),max(1,min(a.max_accounts,64)))
