"""ORACLE-282: offline bootstrap/WS bin-state reconciliation; no RPC or orders."""
import argparse, base64, hashlib, json, os, time
from collections import Counter
from pathlib import Path
import build_oracle_280_bin_array_ws_capture as ws

ROOT = Path('runtime_state/oracle/oracle_live_execution')
CACHE = ROOT/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json'
SEED = ROOT/'ORACLE281_BIN_ARRAY_SEED_STATES.json'
UPDATES = ROOT/'ORACLE280_BIN_ARRAY_WS_STATES.json'
OUT = ROOT/'ORACLE282_BIN_STATE_RECONCILIATION.json'
GRID = [round(.010+i*.005, 3) for i in range(19)]


def load(path, expected, optional=False):
    if optional and not path.exists():
        return {'build':expected, 'accounts':{}, 'signing':False, 'broadcast':False, 'execution_admission':False}
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,dict) or obj.get('build')!=expected or any(obj.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_'+expected)
    if not isinstance(obj.get('accounts'),dict):raise RuntimeError('INVALID_ACCOUNTS_'+expected)
    return obj


def verify(row, addr, target):
    if not isinstance(row,dict) or row.get('address')!=addr or row.get('owner')!=ws.OWNER:return 'INVALID_IDENTITY'
    if type(row.get('slot')) is not int or row['slot']<=0:return 'INVALID_SLOT'
    if type(row.get('received_epoch')) not in (float,int) or row['received_epoch']<=0:return 'INVALID_TIME'
    if row.get('pool')!=target['pool'] or row.get('array_index')!=target['array_index']:return 'INVALID_POOL_OR_INDEX'
    try:raw=base64.b64decode(row['data_b64'],validate=True)
    except (KeyError,ValueError,TypeError):return 'INVALID_BASE64'
    if not 56<=len(raw)<=240000 or row.get('byte_count')!=len(raw):return 'INVALID_LENGTH'
    if hashlib.sha256(raw).hexdigest()!=row.get('fingerprint'):return 'INVALID_HASH'
    if raw[24:56]!=target['pool_raw'] or int.from_bytes(raw[8:16],'little',signed=True)!=target['array_index']:
        return 'INVALID_ONCHAIN_IDENTITY'
    return 'VALID'


def reconcile(cache, seed, updates, now, max_age=120):
    if type(max_age) not in (int,float) or max_age<=0:raise RuntimeError('INVALID_MAX_AGE')
    targets=ws.manifest(cache,10000)
    if not targets:raise RuntimeError('NO_VETTED_TARGETS')
    chosen={}; counts=Counter(); per_pool={}; examples=[]
    for address,target in targets.items():
        candidates=[]
        for label,obj in [('BOOTSTRAP',seed),('WS_UPDATE',updates)]:
            row=obj['accounts'].get(address)
            if row is None:continue
            status=verify(row,address,target)
            counts[label+'_'+status]+=1
            if status=='VALID':candidates.append((row['slot'],row['received_epoch'],label,row))
        if not candidates:
            counts['MISSING_VALID_ACCOUNT']+=1
            continue
        candidates.sort(key=lambda x:(x[0],x[1]))
        best=candidates[-1]
        if len(candidates)>1 and candidates[-1][0]==candidates[-2][0] and candidates[-1][3]['fingerprint']!=candidates[-2][3]['fingerprint']:
            counts['SAME_SLOT_CONFLICT']+=1
            continue
        age=now-best[1]
        if age<0 or age>max_age:
            counts['STALE_OR_CLOCK_INVALID']+=1
            freshness='STALE'
        else:
            counts['RECENT_OBSERVATION']+=1
            freshness='RECENT_OBSERVATION_ONLY'
        chosen[address]={'pool':target['pool'],'slot':best[0],'source':best[2],
                         'observed_age_seconds':round(age,2),'freshness':freshness}
        info=per_pool.setdefault(target['pool'],{'expected':0,'valid':0,'recent':0,'bootstrap':0,'ws':0})
        info['valid']+=1
        info['recent']+=freshness=='RECENT_OBSERVATION_ONLY'
        info['bootstrap']+=best[2]=='BOOTSTRAP'
        info['ws']+=best[2]=='WS_UPDATE'
        if len(examples)<8:examples.append({'account':address[:12],**chosen[address]})
    for target in targets.values():per_pool.setdefault(target['pool'],{'expected':0,'valid':0,'recent':0,'bootstrap':0,'ws':0})['expected']+=1
    return {'build':'ORACLE282','expected_arrays':len(targets),'valid_reconciled_arrays':len(chosen),
            'recent_observation_arrays':counts['RECENT_OBSERVATION'],'per_pool':per_pool,
            'counts':dict(counts),'examples':examples,'size_grid':GRID,
            'rpc_calls':0,'ws_required_for_ongoing_freshness':True,
            'pool_state_hydrated':False,'vaults_all_verified':False,'full_canonical_state':False,
            'local_pricing_connected':False,'net_profit_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,
            'status':'HOLD_CANONICAL_POOL_VAULT_AND_FRESH_STATE'}


def test():
    p=ws.OWNER;a='So11111111111111111111111111111111111111112'
    raw=b'Z'*8+(5).to_bytes(8,'little',signed=True)+b'X'*8+ws.decode58(p)+b'Q'*8
    target={'address':a,'owner':ws.OWNER,'array_index':5,'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    cache={'build':'ORACLE279','pools':{p:{'historical_only':True,'token':a,'addresses':[target]}}}
    row={'address':a,'pool':p,'array_index':5,'slot':100,'owner':ws.OWNER,
         'received_epoch':1000.,'byte_count':len(raw),'fingerprint':hashlib.sha256(raw).hexdigest(),
         'data_b64':base64.b64encode(raw).decode()}
    r=reconcile(cache,{'accounts':{a:row}},{'accounts':{}},1005)
    assert r['valid_reconciled_arrays']==1 and r['recent_observation_arrays']==1 and r['rpc_calls']==0
    r=reconcile(cache,{'accounts':{a:row}},{'accounts':{}},1400)
    assert r['recent_observation_arrays']==0
    newer=dict(row,slot=101,received_epoch=1010.)
    r=reconcile(cache,{'accounts':{a:row}},{'accounts':{a:newer}},1015)
    assert r['per_pool'][p]['ws']==1
    corrupt=dict(row,fingerprint='0'*64)
    assert reconcile(cache,{'accounts':{a:corrupt}},{'accounts':{}},1005)['valid_reconciled_arrays']==0
    print('[ORACLE282_TEST_PASS] canonical_identity=TRUE slot_merge=TRUE expiry=TRUE hash_hold=TRUE no_rpc=TRUE')


def run(max_age):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    cache=json.loads(CACHE.read_text(encoding='utf-8'))
    result=reconcile(cache,load(SEED,'ORACLE281'),load(UPDATES,'ORACLE280',True),time.time(),max_age)
    ROOT.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf-8');os.replace(tmp,OUT)
    print('[ORACLE282_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('size_grid','per_pool','examples')},sort_keys=True))
    for pool,item in result['per_pool'].items():print('[ORACLE282_POOL]',json.dumps({'pool':pool,**item},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--max-age',type=int,default=120)
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(1,min(a.max_age,3600)))
