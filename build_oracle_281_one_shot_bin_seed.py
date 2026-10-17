"""ORACLE-281: single getMultipleAccounts bootstrap for vetted DLMM arrays; no orders."""
import argparse, base64, hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path
import build_oracle_280_bin_array_ws_capture as prior

ROOT=Path('runtime_state/oracle/oracle_live_execution')
SOURCE=ROOT/'ORACLE279_BIN_ARRAY_ADDRESS_CACHE.json'
STATE=ROOT/'ORACLE281_BIN_ARRAY_SEED_STATES.json'
REPORT=ROOT/'ORACLE281_BIN_ARRAY_SEED_REPORT.json'
GRID=[round(.010+.005*i,3) for i in range(19)]

def validate(value,address,target,slot,received):
    if not isinstance(value,dict) or value.get('owner')!=prior.OWNER:return None
    data=value.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':return None
    try: raw=base64.b64decode(data[0],validate=True)
    except (ValueError,TypeError):return None
    if not 56<=len(raw)<=240000 or raw[24:56]!=target['pool_raw']:return None
    index=int.from_bytes(raw[8:16],'little',signed=True)
    if index!=target['array_index']:return None
    return {'address':address,'pool':target['pool'],'token':target['token'],
            'array_index':index,'slot':slot,'owner':prior.OWNER,
            'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),
            'data_b64':base64.b64encode(raw).decode(),'received_epoch':received,
            'verified_pool_index_owner':True,'source':'BOOTSTRAP_GET_MULTIPLE_ACCOUNTS'}

def parse(response,selected,now):
    if not isinstance(response,dict) or 'error' in response:raise RuntimeError('RPC_ERROR')
    result=response.get('result')
    if not isinstance(result,dict):raise RuntimeError('RPC_RESULT_MISSING')
    context=result.get('context');values=result.get('value')
    if not isinstance(context,dict) or type(context.get('slot')) is not int or context['slot']<=0:raise RuntimeError('INVALID_CONTEXT_SLOT')
    if not isinstance(values,list) or len(values)!=len(selected):raise RuntimeError('ACCOUNT_CARDINALITY_MISMATCH')
    slot=context['slot'];accepted={};holds={}
    for (address,target),value in zip(selected.items(),values):
        row=validate(value,address,target,slot,now)
        if row is None:holds[address]='MISSING_OR_ACCOUNT_VALIDATION_FAILED'
        else:accepted[address]=row
    return accepted,holds,slot

def request_once(url,selected,timeout):
    payload={'jsonrpc':'2.0','id':281,'method':'getMultipleAccounts',
             'params':[list(selected),{'encoding':'base64','commitment':'processed'}]}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),
                               headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as conn:
        if conn.status!=200:raise RuntimeError('UNEXPECTED_HTTP_STATUS')
        raw=conn.read(12_000_001)
    if len(raw)>12_000_000:raise RuntimeError('RPC_RESPONSE_TOO_LARGE')
    return json.loads(raw)

def test():
    addr='So11111111111111111111111111111111111111112';pool=prior.OWNER
    raw=b'X'*8+(2).to_bytes(8,'little',signed=True)+b'Y'*8+prior.decode58(pool)+b'R'*8
    target={'pool':pool,'pool_raw':prior.decode58(pool),'token':addr,'array_index':2}
    selected={addr:target}
    response={'result':{'context':{'slot':23},'value':[{'owner':prior.OWNER,
              'data':[base64.b64encode(raw).decode(),'base64']}]}}
    rows,holds,slot=parse(response,selected,1000)
    assert len(rows)==1 and not holds and slot==23 and rows[addr]['verified_pool_index_owner']
    assert parse({'result':{'context':{'slot':23},'value':[None]}},selected,1000)[1]
    try:parse({'result':{'context':{'slot':23},'value':[]}},selected,1000)
    except RuntimeError:pass
    else:raise AssertionError('CARDINALITY_UNCHECKED')
    assert len(GRID)==19 and GRID[-1]==.1
    print('[ORACLE281_TEST_PASS] sdk_layout=TRUE account_identity=TRUE bounded_batch=TRUE no_orders=TRUE')

def run(max_accounts,timeout):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    cache=json.loads(SOURCE.read_text(encoding='utf-8'))
    selected=prior.manifest(cache,max_accounts)
    if not selected:raise RuntimeError('NO_VETTED_BIN_ARRAYS')
    ROOT.mkdir(parents=True,exist_ok=True)
    calls=0;rows={};holds={};slot=None;status='HOLD_NO_INITIAL_BIN_BYTES'
    try:
        calls=1
        rows,holds,slot=parse(request_once(url,selected,timeout),selected,time.time())
        status='BIN_BYTES_SEEDED_NOT_CANONICAL_HYDRATION' if rows else status
    except urllib.error.HTTPError as exc:
        status='HOLD_HTTP_'+str(exc.code)
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,RuntimeError) as exc:
        status='HOLD_'+type(exc).__name__
    state={'build':'ORACLE281','schema':1,'accounts':rows,'signing':False,'broadcast':False,'execution_admission':False}
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2),encoding='utf-8');os.replace(tmp,STATE)
    counts={}
    for row in rows.values():counts[row['pool']]=counts.get(row['pool'],0)+1
    report={'build':'ORACLE281','discovered_addresses':len(selected),'accounts_seeded':len(rows),
            'per_pool_seeded':counts,'account_holds':len(holds),'rpc_calls':calls,'max_rpc_calls':1,
            'rpc_batch_only':True,'slot':slot,'size_grid':GRID,
            'websocket_updates_still_required':True,'full_hydration':False,
            'local_pricing_connected':False,'net_profit_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,'status':status}
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('[ORACLE281_RESULT]',json.dumps({k:v for k,v in report.items() if k!='size_grid'},sort_keys=True))
    print('[REPORT]',REPORT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--max-accounts',type=int,default=30);p.add_argument('--timeout',type=int,default=15)
    a=p.parse_args()
    if not(a.test or a.run):p.error('specify --test or --run')
    if a.test:test()
    if a.run:run(max(1,min(30,a.max_accounts)),max(5,min(30,a.timeout)))
