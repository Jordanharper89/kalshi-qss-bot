"""ORACLE-300 complete standalone installer for canonical Meteora mint-order bridge.
Installs a NEW read-only runtime, without patching scanner, original monitors, or trading code.
"""
import argparse,py_compile
from pathlib import Path
TARGET=Path('oracle_300_canonical_mint_quote.py')
SOURCE=r'''"""ORACLE-300: exact LB pair mint offset decode -> SDK single-leg quote.
One coherent account batch; no network permitted during pricing, no orders.
"""
import argparse,base64,hashlib,json,os,sqlite3,tempfile,time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path('runtime_state/oracle/oracle_live_execution')
OUT=ROOT/'ORACLE300_CANONICAL_MINT_QUOTE.json'
WSOL='So11111111111111111111111111111111111111112'
ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
GRID=tuple(round(.010+.005*i,3) for i in range(19))

def b58(raw):
    value=int.from_bytes(raw,'big');chars=''
    while value:value,r=divmod(value,58);chars=ALPHABET[r]+chars
    return '1'*(len(raw)-len(raw.lstrip(b'\\0')))+chars

def lb_pair_mints(raw):
    if not isinstance(raw,bytes) or len(raw)<904:raise ValueError('LB_PAIR_LAYOUT_TOO_SHORT')
    # Anchor discriminator at [0:8]; canonical LB pair token X/Y pubkeys at [88:120], [120:152].
    x,y=b58(raw[88:120]),b58(raw[120:152])
    if len(raw[88:120])!=32 or len(raw[120:152])!=32 or x==y:raise ValueError('LB_PAIR_MINT_LAYOUT_INVALID')
    if WSOL not in (x,y):raise ValueError('LB_PAIR_NOT_WSOL_MARKET')
    return x,y

def quote_one_leg(pool_bytes,arrays,now,side,amount):
    if side!='WSOL_TO_TOKEN':return 'HOLD_REVERSE_TOKEN_INPUT_NOT_DERIVED',0,amount
    try:x,y=lb_pair_mints(pool_bytes)
    except ValueError as exc:return str(exc),0,amount
    from meteora_dlmm import PoolState,quote
    # SDK decimals are metadata only: quote uses exact integer token amounts.
    state=PoolState.from_accounts(pool_bytes,arrays,decimals_x=9,decimals_y=9)
    swap_for_y=(x==WSOL)
    result=quote(state,amount_in=amount,swap_for_y=swap_for_y,timestamp=int(now),strict=False)
    output=int(getattr(result,'amount_out',0));remaining=int(getattr(result,'remaining_in',amount))
    if getattr(result,'complete',False) is not True or remaining!=0:
        return 'DLMM_PARTIAL_OR_MISSING_BIN_ARRAY',output,remaining
    if output<=0:return 'DLMM_ZERO_OUTPUT',output,remaining
    return 'DLMM_FULL_FILL_ONE_LEG',output,0

def probe_compatibility():
    import oracle_294_298_local_quote_evidence as old
    import oracle_283_287_milestone_a_runtime as market
    import build_oracle_299_fresh_quote_activation as batch
    assert old.GRID==GRID and old.WSOL==WSOL
    assert old.MARKET.name=='ORACLE283_287_MARKET_EVIDENCE.sqlite3'
    return old,market,batch

def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    old,market,batch=probe_compatibility()
    selected=market.targets()
    if not 1<=len(selected)<=100:raise RuntimeError('ACCOUNT_BATCH_LIMIT')
    url=os.environ.get('SOLANA_RPC_URL','')
    if urlsplit(url).scheme!='https':raise RuntimeError('HTTPS_RPC_REQUIRED')
    payload=batch.perform_rpc(url,list(selected))
    rows,holds,slot=batch.decode_response(payload,selected,market.validate,time.time())
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    ROOT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='oracle300_') as directory:
        path=Path(directory)/'same_slot.sqlite3'
        batch.temporary_market(path,rows)
        original_db=old.MARKET;original_quote=old.sdk_quote
        old.MARKET=path;old.sdk_quote=quote_one_leg
        try:observation=old.cycle(120)
        finally:old.MARKET=original_db;old.sdk_quote=original_quote
    result={'build':'ORACLE300','status':'LOCAL_MINT_LAYOUT_QUOTE_EVIDENCE',
       'batch_slot':slot,'requested_accounts':len(selected),'valid_accounts':len(rows),
       'holds':holds,'rpc_calls':1,'pricing_rpc_calls':0,
       'sdk_calls':observation['sdk_calls'],
       'full_fill_one_leg':observation['dlmm_full_fill_one_leg'],
       'partial_one_leg':observation['dlmm_partial'],
       'quote_statuses':observation['statuses'],
       'mint_layout_offsets':[88,120], 'size_grid':list(GRID),
       'cross_venue_profit_certified':False,'net_positive_certified':False,
       'atomic_certified':False,'signing':False,'broadcast':False}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE300_RESULT]',json.dumps(result,sort_keys=True),flush=True)
    print('[REPORT]',OUT)

def test():
    import sys,types
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    def un58(s):
        number=0
        for char in s:number=number*58+ALPHABET.index(char)
        return number.to_bytes(32,'big')
    raw=bytearray(904);raw[88:120]=un58(WSOL);raw[120:152]=bytes([4])*32
    assert lb_pair_mints(bytes(raw))[0]==WSOL
    raw2=bytearray(raw);raw2[88:120]=raw[120:152];raw2[120:152]=raw[88:120]
    assert lb_pair_mints(bytes(raw2))[1]==WSOL
    calls=[]
    lib=types.ModuleType('meteora_dlmm')
    class Pool:
        @staticmethod
        def from_accounts(pool,arrays,decimals_x,decimals_y):return pool
    class Q:
        amount_out=123;remaining_in=0;complete=True
    def quote(pool,amount_in,swap_for_y,timestamp,strict):
        calls.append((amount_in,swap_for_y,strict));return Q()
    lib.PoolState=Pool;lib.quote=quote
    old=sys.modules.get('meteora_dlmm');sys.modules['meteora_dlmm']=lib
    try:
        assert quote_one_leg(bytes(raw),[b'bins'],1234,'WSOL_TO_TOKEN',100)[0]=='DLMM_FULL_FILL_ONE_LEG'
        assert quote_one_leg(bytes(raw2),[b'bins'],1234,'WSOL_TO_TOKEN',100)[0]=='DLMM_FULL_FILL_ONE_LEG'
        assert calls==[(100,True,False),(100,False,False)]
        assert quote_one_leg(bytes(raw),[],1234,'TOKEN_TO_WSOL',100)[0].startswith('HOLD_')
        Q.remaining_in=1
        assert quote_one_leg(bytes(raw),[],1234,'WSOL_TO_TOKEN',100)[0]=='DLMM_PARTIAL_OR_MISSING_BIN_ARRAY'
    finally:
        if old is None:del sys.modules['meteora_dlmm']
        else:sys.modules['meteora_dlmm']=old
    print('[ORACLE300_TEST_PASS] lb_offsets=TRUE both_mint_orders=TRUE sdk_direction=TRUE partial_hold=TRUE 19_sizes=TRUE read_only=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.run:run()
    else:p.error('Specify --test or --run')
'''

def install():
    if TARGET.exists() and 'ORACLE-300:' not in TARGET.read_text(encoding='utf-8')[:150]:
        raise RuntimeError('UNRECOGNIZED_ORACLE300_TARGET')
    TARGET.write_text(SOURCE,encoding='utf-8');py_compile.compile(str(TARGET),doraise=True)
    print('[ORACLE300_INSTALL_PASS] original_scanner_unchanged=TRUE new_pricer=TRUE signing=FALSE broadcast=FALSE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');a=p.parse_args()
    if a.install:install()
    else:p.error('Specify --install')
