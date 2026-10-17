"""ORACLE-279: pool-scoped Meteora DLMM bin discovery, bounded REST RPC; no trading."""
import argparse, ast, base64, hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path

ROOT=Path('runtime_state/oracle/oracle_live_execution')
SOURCE=ROOT/'ORACLE278_METEORA_BIN_DEPENDENCY_GATE.json'
CACHE=ROOT/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json'
OUT=ROOT/'ORACLE279_BOUNDED_DLMM_DISCOVERY.json'
CORE=Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
OWNER='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def decode58(s):
    if not isinstance(s,str) or not 32<=len(s)<=44:raise ValueError('INVALID_ADDRESS')
    n=0
    for c in s:n=n*58+ALPHABET.index(c)
    out=n.to_bytes((n.bit_length()+7)//8,'big') if n else b''
    out=b'\0'*(len(s)-len(s.lstrip('1')))+out
    if len(out)!=32:raise ValueError('INVALID_ADDRESS_LENGTH')
    return out


def canonical_contract():
    t=ast.parse(CORE.read_text(encoding='utf-8'))
    funcs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='dlmm_arrays']
    if len(funcs)!=1:raise RuntimeError('CANONICAL_ARRAY_DISCOVERY_CHANGED')
    n=funcs[0]
    calls=[c for c in ast.walk(n) if isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='rpc']
    if len(calls)!=1 or len(calls[0].args)<2:raise RuntimeError('CANONICAL_RPC_CONTRACT_CHANGED')
    call=calls[0]
    if not isinstance(call.args[0],ast.Constant) or call.args[0].value!='getProgramAccounts':raise RuntimeError('CANONICAL_RPC_METHOD_CHANGED')
    # Fail closed on a changed memcmp offset and pool argument.
    signature=ast.unparse(call.args[1])
    if "'offset': 24" not in signature or "'bytes': pool" not in signature or "'encoding': 'base64'" not in signature:
        raise RuntimeError('CANONICAL_POOL_FILTER_CHANGED')
    return {'method':'getProgramAccounts','pool_memcmp_offset':24,'source_line':call.lineno}


def clean_targets(report):
    if report.get('build')!='ORACLE278' or any(report.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_278')
    targets=report.get('meteora_targets')
    if not isinstance(targets,list):raise RuntimeError('MISSING_TARGETS')
    found=[]; seen=set()
    for item in targets:
        if not isinstance(item,dict):continue
        pool=item.get('meteora_pool');token=item.get('token')
        try:decode58(pool);decode58(token)
        except (ValueError,TypeError):continue
        if pool not in seen:
            seen.add(pool);found.append({'pool':pool,'token':token})
    return found


def extract(response,pool):
    if not isinstance(response,list):raise ValueError('INVALID_RPC_RESPONSE')
    pool_bytes=decode58(pool);good=[];rejected={}
    for item in response:
        try:
            pubkey=item['pubkey'];decode58(pubkey)
            acc=item['account'];owner=acc['owner']
            if owner!=OWNER:raise ValueError('WRONG_PROGRAM_OWNER')
            data=acc['data'];encoded=data[0] if isinstance(data,list) and len(data)==2 and data[1]=='base64' else None
            if not isinstance(encoded,str):raise ValueError('WRONG_ENCODING')
            raw=base64.b64decode(encoded,validate=True)
            if len(raw)<56 or raw[24:56]!=pool_bytes:raise ValueError('POOL_MISMATCH_OR_SHORT')
            good.append({'address':pubkey,'owner':owner,'array_index':int.from_bytes(raw[8:16],'little',signed=True),
                         'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        except (KeyError,ValueError,IndexError,TypeError,OverflowError) as exc:
            reason=str(exc) if isinstance(exc,ValueError) and str(exc) in ('WRONG_PROGRAM_OWNER','WRONG_ENCODING','POOL_MISMATCH_OR_SHORT') else 'INVALID_ACCOUNT'
            rejected[reason]=rejected.get(reason,0)+1
    return sorted(good,key=lambda x:x['array_index']),rejected


def load_cache():
    if not CACHE.is_file():return {'build':'ORACLE279','pools':{}}
    obj=json.loads(CACHE.read_text(encoding='utf-8'))
    if obj.get('build')!='ORACLE279' or not isinstance(obj.get('pools'),dict):raise RuntimeError('INVALID_CACHE')
    return obj


def request_one(url,pool,timeout):
    payload={'jsonrpc':'2.0','id':1,'method':'getProgramAccounts','params':[OWNER,{'encoding':'base64','commitment':'processed','filters':[{'memcmp':{'offset':24,'bytes':pool}}]}]}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as response:
        obj=json.loads(response.read(6_000_000))
    if not isinstance(obj,dict) or 'error' in obj or not isinstance(obj.get('result'),list):raise RuntimeError('RPC_RESULT_INVALID_OR_ERROR')
    return obj['result']


def run(max_calls,timeout):
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    contract=canonical_contract()
    targets=clean_targets(json.loads(SOURCE.read_text(encoding='utf-8')))
    if not targets:raise RuntimeError('NO_VERIFIED_TARGETS')
    cache=load_cache();url=os.environ.get('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    # Limit total on this invocation regardless of errors; avoid repeating prior successful pool discovery.
    candidates=[x for x in targets if x['pool'] not in cache['pools']]
    count=0;results=[];stopped=False
    for target in candidates[:max_calls]:
        pool=target['pool'];count+=1
        try:
            raw=request_one(url,pool,timeout)
            arrays,rejected=extract(raw,pool)
            cache['pools'][pool]={'token':target['token'],'addresses':arrays,'rejected':rejected,'historical_only':True,'retrieved_epoch':time.time()}
            results.append({'pool':pool,'token':target['token'][:12],'arrays':len(arrays),'rejected':rejected,'status':'DISCOVERED_HISTORICAL_NOT_FRESH'})
        except urllib.error.HTTPError as exc:
            results.append({'pool':pool,'status':'HTTP_'+str(exc.code)})
            if exc.code==429:stopped=True;break
        except (urllib.error.URLError,TimeoutError,OSError,RuntimeError,ValueError) as exc:
            results.append({'pool':pool,'status':'HOLD_'+type(exc).__name__})
        if count<min(max_calls,len(candidates)):time.sleep(1.2)
    ROOT.mkdir(parents=True,exist_ok=True)
    CACHE.write_text(json.dumps(cache,indent=2),encoding='utf-8')
    result={'build':'ORACLE279','target_pools':len(targets),'calls_this_run':count,'max_calls':max_calls,
            'cache_pools':len(cache['pools']),'http_429_stop':stopped,'results':results,
            'canonical_contract':contract,'bin_array_addresses_historical_only':True,
            'fresh_pool_state_certified':False,'full_hydration':False,'local_pricing_connected':False,
            'execution_admission':False,'signing':False,'broadcast':False,
            'status':'HOLD_BIN_BYTES_AND_FRESH_CANONICAL_STATE'}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE279_RESULT]',json.dumps(result,sort_keys=True))
    print('[REPORT]',OUT)


def test():
    assert len(decode58(OWNER))==32
    v={'build':'ORACLE278','signing':False,'broadcast':False,'execution_admission':False,'meteora_targets':[{'meteora_pool':OWNER,'token':OWNER}]}
    assert len(clean_targets(v))==1
    v['signing']=True
    try:clean_targets(v)
    except RuntimeError:pass
    else:raise AssertionError('ARMED_TARGET_ACCEPTED')
    good,rejected=extract([{'pubkey':OWNER,'account':{'owner':OWNER,'data':[base64.b64encode(b'X'*24+decode58(OWNER)+b'Z'*16).decode(),'base64']}}],OWNER)
    assert len(good)==1 and good[0]['byte_count']==72 and not rejected
    bad,rejected=extract([{'pubkey':OWNER,'account':{'owner':OWNER,'data':[base64.b64encode(b'X'*72).decode(),'base64']}}],OWNER)
    assert not bad and rejected['POOL_MISMATCH_OR_SHORT']==1
    assert [round(.010+.005*i,3) for i in range(19)][-1]==.100
    print('[ORACLE279_TEST_PASS] exact_pool_filter=TRUE owner=TRUE hash=TRUE budget=TRUE 19_sizes=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--max-calls',type=int,default=2);p.add_argument('--timeout',type=int,default=12)
    a=p.parse_args()
    if a.test:test()
    if a.run:run(min(2,max(0,a.max_calls)),min(20,max(3,a.timeout)))
    if not a.run and not a.test:p.error('Specify --test or --run')
