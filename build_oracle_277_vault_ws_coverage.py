"""ORACLE-277: bounded verified pool/vault WS capture; no RPC polling or trades."""
import argparse, base64, hashlib, json, os, socket, time
from collections import Counter
from pathlib import Path
import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge
import build_oracle_272_ws_account_state_capture as capture

BASE = Path('runtime_state/oracle/oracle_live_execution')
DEPENDENCIES = BASE/'ORACLE276_RESOLVED_DEPENDENCIES.json'
STATE = BASE/'ORACLE277_ACCOUNT_BYTES.json'
REPORT = BASE/'ORACLE277_VAULT_WS_COVERAGE.json'
TOKEN_PROGRAMS = {'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
                  'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}
WSOL = 'So11111111111111111111111111111111111111112'
GRID = [round(.010+.005*i,3) for i in range(19)]

def b58(raw):
    abc='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    n=int.from_bytes(raw,'big'); s=''
    while n: n,r=divmod(n,58); s=abc[r]+s
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+(s or '')

def manifest(deps,pools):
    if deps.get('build')!='ORACLE276' or any(deps.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_DEPENDENCIES')
    result={a:[{'role':'POOL','mint':m,'venue':v} for m,v in refs] for a,refs in pools.items()}
    for row in deps.get('tokens',[]):
        if row.get('status')!='PUMP_VAULT_ADDRESSES_RESOLVED_UNVERIFIED':continue
        if row.get('pump_pool') not in pools:continue
        mint=row.get('token')
        if (mint,'PUMPSWAP_WS') not in pools[row['pump_pool']]:continue
        for key,role,expected in [('pump_base_vault','BASE_VAULT',mint),('pump_quote_vault','QUOTE_VAULT',WSOL)]:
            addr=row.get(key)
            if not bridge.valid_address(addr) or not bridge.valid_address(expected):continue
            result.setdefault(addr,[]).append({'role':role,'mint':mint,'expected_token_mint':expected,'venue':'PUMPSWAP_WS'})
    return dict(sorted(result.items()))

def decode(packet,subscribed,selected,now):
    if not isinstance(packet,dict) or packet.get('method')!='accountNotification':return None
    params=packet.get('params',{})
    if not isinstance(params,dict):return None
    addr=subscribed.get(params.get('subscription'))
    if addr not in selected:return None
    result=params.get('result',{});ctx=result.get('context',{}) if isinstance(result,dict) else {}
    val=result.get('value',{}) if isinstance(result,dict) else {}
    if not isinstance(ctx,dict) or not isinstance(val,dict) or type(ctx.get('slot')) is not int or ctx['slot']<=0:return None
    data=val.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':return None
    try:raw=base64.b64decode(data[0],validate=True)
    except (ValueError,TypeError):return None
    owner=val.get('owner')
    if not raw or len(raw)>capture.MAX_BYTES or not bridge.valid_address(owner):return None
    entry={'address':addr,'slot':ctx['slot'],'owner':owner,'data_b64':base64.b64encode(raw).decode(),
           'byte_count':len(raw),'fingerprint':hashlib.sha256(raw).hexdigest(),
           'received_epoch':now,'refs':selected[addr]}
    vault_refs=[x for x in selected[addr] if x['role']!='POOL']
    if vault_refs:
        if owner not in TOKEN_PROGRAMS or len(raw)<72:
            entry['vault_validation']='HOLD_TOKEN_ACCOUNT_LAYOUT_OR_OWNER'
        else:
            mint=b58(raw[:32]);entry['token_mint']=mint
            entry['balance_raw']=int.from_bytes(raw[64:72],'little')
            entry['vault_validation']='MINT_MATCH' if all(x['expected_token_mint']==mint for x in vault_refs) else 'HOLD_MINT_MISMATCH'
    return entry

def accept(state,item):
    prior=state['accounts'].get(item['address'])
    if prior and item['slot']<prior['slot']:return 'OLDER_SLOT'
    if prior and item['slot']==prior['slot']:
        return 'DUPLICATE' if item['fingerprint']==prior['fingerprint'] else 'SAME_SLOT_CONFLICT'
    state['accounts'][item['address']]=item
    return 'CAPTURED'

def test():
    mint='A'*32;pool='B'*32;vault='C'*32
    d={'build':'ORACLE276','signing':False,'broadcast':False,'execution_admission':False,
       'tokens':[{'token':mint,'pump_pool':pool,'pump_base_vault':vault,'pump_quote_vault':'D'*32,
                  'status':'PUMP_VAULT_ADDRESSES_RESOLVED_UNVERIFIED'}]}
    m=manifest(d,{pool:[(mint,'PUMPSWAP_WS')]})
    assert len(m)==3 and m[vault][0]['role']=='BASE_VAULT'
    raw=b'\0'*32+b'\0'*32+(123).to_bytes(8,'little')
    packet={'method':'accountNotification','params':{'subscription':8,'result':{'context':{'slot':40},
        'value':{'owner':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','data':[base64.b64encode(raw).decode(),'base64']}}}}
    e=decode(packet,{8:vault},m,1000);assert e['balance_raw']==123 and e['vault_validation']=='HOLD_MINT_MISMATCH'
    state={'accounts':{}};assert accept(state,e)=='CAPTURED' and accept(state,e)=='DUPLICATE'
    assert decode(packet,{},m,1000) is None
    assert len(GRID)==19 and GRID[0]==.01 and GRID[-1]==.1
    d['signing']=True
    try:manifest(d,{})
    except RuntimeError:pass
    else:raise AssertionError('ARMED_INPUT_ACCEPTED')
    print('[ORACLE277_TEST_PASS] manifest=TRUE ws_provenance=TRUE mint_guard=TRUE 19_sizes=TRUE no_execution=TRUE')

def run(seconds,maximum):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    url=os.getenv('SOLANA_WS_URL','')
    if not url.startswith('wss://'):raise RuntimeError('WSS_REQUIRED')
    import websocket
    db=life.load(life.DB)
    pools=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    deps=json.loads(DEPENDENCIES.read_text(encoding='utf-8'))
    selected=dict(list(manifest(deps,pools).items())[:maximum])
    if not selected:raise RuntimeError('NO_VERIFIED_ADDRESSES')
    state={'build':'ORACLE277','schema':1,'accounts':{},'signing':False,'broadcast':False,'execution_admission':False}
    counts=Counter();pending={};subscribed={};ws=None
    try:
        ws=websocket.create_connection(url,timeout=7,enable_multithread=True);ws.settimeout(2)
        for i,address in enumerate(selected,1):
            pending[i]=address
            ws.send(json.dumps({'jsonrpc':'2.0','id':i,'method':'accountSubscribe','params':[address,{'encoding':'base64','commitment':'processed'}]}))
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            try:raw=ws.recv()
            except (socket.timeout,websocket.WebSocketTimeoutException):continue
            except websocket.WebSocketConnectionClosedException:counts['WS_CLOSED']+=1;break
            try:packet=json.loads(raw)
            except (ValueError,TypeError):counts['BAD_JSON']+=1;continue
            if not isinstance(packet,dict):continue
            req=packet.get('id')
            if type(req) is int and req in pending:
                addr=pending.pop(req)
                if type(packet.get('result')) is int:
                    subscribed[packet['result']]=addr;counts['SUBSCRIBED']+=1
                else:counts['SUBSCRIBE_REJECTED']+=1
                continue
            if packet.get('method')!='accountNotification':continue
            counts['NOTIFICATIONS']+=1
            item=decode(packet,subscribed,selected,time.time())
            if item is None:counts['INVALID']+=1;continue
            counts[accept(state,item)]+=1
    finally:
        if ws is not None:
            try:ws.close()
            except Exception:pass
        capture.save(STATE,state)
    vaults=[e for e in state['accounts'].values() if any(r['role']!='POOL' for r in e['refs'])]
    report={'build':'ORACLE277','subscribed':len(subscribed),'watched_addresses':len(selected),
        'planned_vault_addresses':sum(any(r['role']!='POOL' for r in refs) for refs in selected.values()),
        'vault_accounts_captured':len(vaults),'verified_token_mint_vaults':sum(e.get('vault_validation')=='MINT_MATCH' for e in vaults),
        'counters':dict(counts),'unresolved':['METEORA_BIN_ARRAYS','METEORA_VAULTS','COMPLETE_CANONICAL_STATE'],
        'rpc_poll_calls':0,'local_pricing_connected':False,'full_hydration':False,
        'execution_admission':False,'signing':False,'broadcast':False,'status':'HOLD_FULL_ACCOUNT_COVERAGE'}
    capture.save(REPORT,report)
    print('[ORACLE277_RESULT]',json.dumps(report,sort_keys=True))
    print('[REPORT]',REPORT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--max-accounts',type=int,default=64)
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(10,min(180,a.seconds)),max(1,min(64,a.max_accounts)))
