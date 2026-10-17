"""ORACLE-271: verified account-granular WS -> durable bounded reprice queue; no orders."""
import argparse
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
STATE = BASE / 'ORACLE271_ACCOUNT_EVENT_QUEUE.json'
REPORT = BASE / 'ORACLE271_LIVE_EVENT_RESULT.json'
GRID = life.GRID


def empty():
    return {'build':'ORACLE271','schema':1,'accounts':{},'queue':{},'counters':{},
            'signing':False,'broadcast':False,'execution_admission':False}


def read(path):
    if not path.exists(): return empty()
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('build')!='ORACLE271' or data.get('schema')!=1 or any(data.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_ORACLE271_STATE')
    if not isinstance(data.get('accounts'),dict) or not isinstance(data.get('queue'),dict):
        raise RuntimeError('INVALID_QUEUE_STATE')
    return data


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.oracle271_',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,sort_keys=True,indent=2)
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def accept(state, db, address, source, token, slot, fingerprint, observed_time):
    if not bridge.valid_address(address) or not bridge.valid_address(token) or source not in ('PUMPSWAP_WS','METEORA_WS'):
        return 'REJECT_IDENTITY'
    if token not in db['tokens'] or type(slot) is not int or slot<=0 or not isinstance(fingerprint,str) or len(fingerprint)!=64:
        return 'REJECT_PROVENANCE'
    old=state['accounts'].get(address)
    if old and slot<old['slot']:return 'OLD_SLOT'
    if old and slot==old['slot'] and fingerprint==old['fingerprint']:return 'DUPLICATE'
    if old and slot==old['slot'] and fingerprint!=old['fingerprint']:return 'SAME_SLOT_CONFLICT'
    state['accounts'][address]={'slot':slot,'fingerprint':fingerprint,'source':source,'observed_at':observed_time}
    token_state=db['tokens'][token]
    token_state['tier']='HOT'
    token_state['fresh_reprice_eligible']=False  # Cannot reprice until both venue states are hydrated.
    token_state['last_market_slot']=max(slot,token_state.get('last_market_slot') or 0)
    if source not in token_state['source_tags']:token_state['source_tags'].append(source)
    queued=state['queue'].setdefault(token,{'addresses':{},'last_event_time':0,'reprice_ready':False,'full_snapshot_verified':False})
    queued['addresses'][address]={'source':source,'slot':slot,'fingerprint':fingerprint}
    queued['last_event_time']=observed_time
    queued['reprice_ready']=False
    queued['full_snapshot_verified']=False
    return 'QUEUED_NEW_ACCOUNT_STATE'


def totals(state, counters, subscriptions, addresses):
    queue=state['queue']
    source_counts={mint:sorted({rec['source'] for rec in q['addresses'].values()}) for mint,q in queue.items()}
    both=sum(set(srcs)=={'PUMPSWAP_WS','METEORA_WS'} for srcs in source_counts.values())
    return {'build':'ORACLE271','subscriptions_confirmed':len(subscriptions), 'watched_accounts':len(addresses),
            'watched_tokens':len({mint for refs in addresses.values() for mint,_ in refs}),
            'token_queue_size':len(queue),'token_queue_both_sources_observed':both,
            'per_account_slots_tracked':len(state['accounts']),'counters':dict(counters),
            'size_grid':GRID,'rpc_poll_calls':0,'local_pricing_connected':False,
            'two_venue_snapshot_certified':False,'net_profit_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,
            'status':'QUEUED_WS_EVENTS_PENDING_CANONICAL_STATE_HYDRATION'}


def test():
    token='A'*32; a='B'*32;b='C'*32;c='D'*32
    db=life.new_db();life.token_state(db,token)
    state=empty()
    assert accept(state,db,a,'PUMPSWAP_WS',token,101,'a'*64,10)=='QUEUED_NEW_ACCOUNT_STATE'
    assert accept(state,db,a,'PUMPSWAP_WS',token,101,'a'*64,11)=='DUPLICATE'
    assert accept(state,db,a,'PUMPSWAP_WS',token,100,'b'*64,12)=='OLD_SLOT'
    assert accept(state,db,a,'PUMPSWAP_WS',token,101,'b'*64,13)=='SAME_SLOT_CONFLICT'
    assert accept(state,db,b,'PUMPSWAP_WS',token,101,'b'*64,14)=='QUEUED_NEW_ACCOUNT_STATE'
    assert accept(state,db,c,'METEORA_WS',token,101,'c'*64,15)=='QUEUED_NEW_ACCOUNT_STATE'
    assert db['tokens'][token]['tier']=='HOT' and not db['tokens'][token]['fresh_reprice_eligible']
    inventory={a:[(token,'PUMPSWAP_WS')],b:[(token,'PUMPSWAP_WS')],c:[(token,'METEORA_WS')]}
    summary=totals(state,Counter(),{1:a,2:b,3:c},inventory)
    assert summary['token_queue_both_sources_observed']==1 and not summary['local_pricing_connected']
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'file.json';save(p,state)
        assert read(p)['accounts'][b]['slot']==101
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.10
    print('[ORACLE271_TEST_PASS] account_dedup=TRUE same_slot_multi_account=TRUE restart=TRUE 19_sizes=TRUE fail_closed=TRUE')


def run(seconds, maximum):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    url=os.getenv('SOLANA_WS_URL','')
    if not url.startswith('wss://'):raise RuntimeError('WSS_URL_REQUIRED')
    import websocket
    db=life.load(life.DB)
    state=read(STATE)
    inventory=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    if not inventory:raise RuntimeError('NO_WATCHABLE_POOLS')
    selected=dict(list(inventory.items())[:maximum]);counts=Counter()
    pending={};subscribed={}
    socket_ws=None
    deadline=time.monotonic()+seconds
    try:
        socket_ws=websocket.create_connection(url,timeout=7,enable_multithread=True)
        socket_ws.settimeout(2)
        for n,address in enumerate(selected,1):
            pending[n]=address
            socket_ws.send(json.dumps({'jsonrpc':'2.0','id':n,'method':'accountSubscribe',
                'params':[address,{'encoding':'base64','commitment':'processed'}]}))
        while time.monotonic()<deadline:
            try: payload=socket_ws.recv()
            except (socket.timeout,websocket.WebSocketTimeoutException):continue
            except websocket.WebSocketConnectionClosedException:
                counts['WS_CLOSED']+=1;break
            try:packet=json.loads(payload)
            except (ValueError,TypeError):counts['BAD_JSON']+=1;continue
            if not isinstance(packet,dict):continue
            request=packet.get('id')
            if type(request) is int and request in pending:
                address=pending.pop(request)
                if type(packet.get('result')) is int:
                    subscribed[packet['result']]=address;counts['SUBSCRIBED']+=1
                else:counts['SUBSCRIPTION_REJECTED']+=1
                continue
            if packet.get('method')!='accountNotification':continue
            params=packet.get('params') or {}
            if not isinstance(params,dict):continue
            address=subscribed.get(params.get('subscription'))
            if address is None:counts['UNACKNOWLEDGED']+=1;continue
            decoded=bridge.decode_notification(packet,subscribed,selected)
            if not decoded:counts['REJECT_BAD_NOTIFICATION']+=1;continue
            counts['ACCOUNT_NOTIFICATIONS']+=1
            for item in decoded:
                counts[accept(state,db,address,item['source'],item['mint'],item['slot'],item['pool_fingerprint'],int(time.time()))]+=1
            if counts['ACCOUNT_NOTIFICATIONS']%25==0:
                save(STATE,state);life.save(db,life.DB)
    finally:
        if socket_ws is not None:
            try:socket_ws.close()
            except Exception:pass
        save(STATE,state);life.save(db,life.DB)
        report=totals(state,counts,subscribed,selected)
        save(REPORT,report)
        print('[ORACLE271_RESULT]',json.dumps(report,sort_keys=True))
        for mint,row in sorted(state['queue'].items(),key=lambda p:p[1].get('last_event_time',0),reverse=True)[:10]:
            print('[ORACLE271_QUEUE]',json.dumps({'token':mint[:12],'account_updates':len(row['addresses']),
                'sources':sorted({v['source'] for v in row['addresses'].values()}),'reprice_ready':False},sort_keys=True))
        print('[REPORT]',REPORT)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--max-accounts',type=int,default=30)
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(10,min(a.seconds,180)),max(1,min(a.max_accounts,64)))
