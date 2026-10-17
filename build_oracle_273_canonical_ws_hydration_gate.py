"""ORACLE-273: verify WS account bytes against canonical pool identity; fail closed."""
import argparse
import base64
import hashlib
import json
import os
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge
import build_oracle_272_ws_account_state_capture as capture

BASE = Path('runtime_state/oracle/oracle_live_execution')
OUT = BASE / 'ORACLE273_CANONICAL_WS_HYDRATION_GATE.json'
GRID = [round(.010 + .005*i, 3) for i in range(19)]


def check_account(address, entry, inventory, now, max_age=30):
    if not bridge.valid_address(address) or not isinstance(entry, dict):
        return 'BAD_IDENTITY'
    if entry.get('address') != address or address not in inventory:
        return 'UNKNOWN_ACCOUNT'
    if type(entry.get('slot')) is not int or entry['slot'] <= 0:
        return 'INVALID_SLOT'
    age = entry.get('received_epoch')
    if type(age) not in (float,int) or not 0 <= now-age <= max_age:
        return 'STALE_ACCOUNT'
    if not bridge.valid_address(entry.get('owner')):
        return 'INVALID_OWNER_FORMAT'
    encoded = entry.get('data_b64')
    if not isinstance(encoded,str) or len(encoded)>capture.MAX_BYTES*2:
        return 'INVALID_BASE64'
    try: raw=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):return 'INVALID_BASE64'
    if not 0<len(raw)<=capture.MAX_BYTES or len(raw)!=entry.get('byte_count'):
        return 'INVALID_LENGTH'
    if hashlib.sha256(raw).hexdigest()!=entry.get('fingerprint'):
        return 'HASH_MISMATCH'
    refs=entry.get('refs')
    if not isinstance(refs,list) or not refs or any(
        not isinstance(x,list) or len(x)!=2 or tuple(x) not in inventory[address]
        for x in refs):
        return 'UNTRUSTED_REFS'
    if not set(inventory[address]).issubset({tuple(x) for x in refs}):
        return 'INCOMPLETE_REFS'
    return 'VALID_CAPTURED_BYTES'


def evaluate(state,inventory,now,max_age=30,max_slot_delta=150):
    if (state.get('build')!='ORACLE272' or state.get('schema')!=1 or
        any(state.get(k) is not False for k in ('signing','broadcast','execution_admission')) or
        not isinstance(state.get('accounts'),dict)):
        raise RuntimeError('UNTRUSTED_CAPTURE_STATE')
    by_token=defaultdict(lambda:defaultdict(list));counts=Counter()
    for address,entry in state['accounts'].items():
        label=check_account(address,entry,inventory,now,max_age)
        counts[label]+=1
        if label!='VALID_CAPTURED_BYTES':continue
        for mint,venue in inventory[address]:
            by_token[mint][venue].append({'address':address,'slot':entry['slot'],
                'fingerprint':entry['fingerprint'],'owner':entry['owner'],
                'byte_count':entry['byte_count'],'age_seconds':round(now-entry['received_epoch'],2)})
    candidates=[]
    for token,venues in sorted(by_token.items()):
        pump=venues.get('PUMPSWAP_WS',[]);meteora=venues.get('METEORA_WS',[])
        if not pump or not meteora:
            counts['ONLY_ONE_VENUE']+=1;continue
        a=max(pump,key=lambda x:x['slot']);b=max(meteora,key=lambda x:x['slot'])
        if abs(a['slot']-b['slot'])>max_slot_delta:
            counts['SLOT_DISTANCE_HOLD']+=1;continue
        # The pool account alone does not include all PumpSwap reserves or DLMM bin arrays.
        candidates.append({'token':token,'pump_pool':a,'meteora_pool':b,
            'slot_delta':abs(a['slot']-b['slot']), 'pool_bytes_verified':True,
            'canonical_full_hydration':False,'ready_to_price':False,
            'missing':['PUMP_VAULT_ACCOUNT_STATES','METEORA_BIN_ARRAY_STATES',
                       'OWNER_PROGRAM_VERIFICATION','SAME_EPOCH_TWO_VENUE_SNAPSHOT']})
    return {'build':'ORACLE273','size_grid':GRID,'captured_account_count':len(state['accounts']),
        'account_checks':dict(counts),'verified_pair_candidates':len(candidates),
        'candidates':candidates,'owner_program_certified':False,
        'canonical_full_hydration':False,'local_pricing_connected':False,
        'fee_adjusted_net_certified':False,'atomic_simulation_certified':False,
        'execution_admission':False,'signing':False,'broadcast':False,
        'status':'HOLD_REQUIRED_VAULT_BIN_AND_SNAPSHOT_ACCOUNTS' if candidates
          else 'HOLD_NO_FRESH_TWO_VENUE_POOL_BYTES'}


def test():
    mint='A'*32;a='B'*32;b='C'*32;owner='D'*32;now=1000
    inv={a:[(mint,'PUMPSWAP_WS')],b:[(mint,'METEORA_WS')]}
    def entry(addr,slot,venue):
        raw=(addr+venue).encode()
        return {'address':addr,'slot':slot,'received_epoch':now,'owner':owner,
            'data_b64':base64.b64encode(raw).decode(),'fingerprint':hashlib.sha256(raw).hexdigest(),
            'byte_count':len(raw),'refs':[[mint,venue]]}
    db=capture.empty();db['accounts']={a:entry(a,100,'PUMPSWAP_WS'),b:entry(b,102,'METEORA_WS')}
    r=evaluate(db,inv,now+1)
    assert r['verified_pair_candidates']==1 and not r['candidates'][0]['ready_to_price']
    assert len(r['size_grid'])==19 and r['size_grid'][-1]==.1
    db['accounts'][a]['data_b64']=base64.b64encode(b'changed').decode()
    assert evaluate(db,inv,now+1)['account_checks']['INVALID_LENGTH']==1
    db['accounts'][a]=entry(a,100,'PUMPSWAP_WS')
    assert evaluate(db,inv,now+100)['verified_pair_candidates']==0
    db['signing']=True
    try:evaluate(db,inv,now+1)
    except RuntimeError:pass
    else:raise AssertionError('ARMED_SOURCE_ACCEPTED')
    print('[ORACLE273_TEST_PASS] hash=TRUE provenance=TRUE 19_sizes=TRUE stale_hold=TRUE no_orders=TRUE')


def run(max_age):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    state=capture.load(capture.STATE)
    lifecycle=life.load(life.DB)
    inventory=bridge.inventory(bridge.INPUTS,set(lifecycle['tokens']))
    if not inventory:raise RuntimeError('CANONICAL_POOL_INVENTORY_MISSING')
    report=evaluate(state,inventory,time.time(),max_age=max_age)
    report['watched_inventory_accounts']=len(inventory)
    BASE.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.oracle273_',suffix='.tmp',dir=BASE)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,OUT)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print('[ORACLE273_RESULT]',json.dumps({k:v for k,v in report.items() if k!='candidates'},sort_keys=True))
    for row in report['candidates'][:12]:
        print('[ORACLE273_POOL_PAIR]',json.dumps({'token':row['token'][:12],
            'pump_slot':row['pump_pool']['slot'],'meteora_slot':row['meteora_pool']['slot'],
            'missing':row['missing'],'ready_to_price':False},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--max-age',type=int,default=120)
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(5,min(a.max_age,600)))
