"""ORACLE-098: single authorized ALT setup transaction; no arbitrage execution."""
import argparse
import base64
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

from qseries_v2.oracle_execution.solana_atomic_executor import oracle_097_unsigned_alt_setup_preflight as o97

PLAN = Path('runtime_state/oracle/solana_atomic_executor/canonical_alt_plan.json')
CANONICAL = Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
TOKEN_REGISTRY = Path('runtime_state/qseries/qarb_execution_engineering/qarb_096_micro_alt.json')
PENDING = Path('runtime_state/oracle/solana_atomic_executor/alt_creation_pending.json')
MAX_SETUP_COST = 10_000_000  # cap: 0.010 SOL, including estimated rent and network fee
RESERVE = 3_000_000         # wallet remains funded after setup
MAX_WIRE = 1232
ALT_PROGRAM = 'AddressLookupTab1e1111111111111111111111111'


def rpc(method, params):
    url = os.environ.get('SOLANA_RPC_URL') or 'https://api.mainnet-beta.solana.com'
    if not url.startswith('https://') or '\n' in url or '\r' in url:
        raise RuntimeError('HTTPS_RPC_REQUIRED')
    body = json.dumps({'jsonrpc':'2.0','id':98,'method':method,'params':params}).encode()
    try:
        with urlopen(Request(url, data=body, headers={'Content-Type':'application/json'}),timeout=20) as r:
            response=json.load(r)
    except Exception as exc:
        raise RuntimeError('RPC_TRANSPORT_FAILED_'+type(exc).__name__) from None
    if not isinstance(response,dict) or response.get('error'):
        raise RuntimeError('RPC_FAILED_'+method)
    return response.get('result')


def atomic_json(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,sort_keys=True,indent=2),encoding='utf-8')
    temp.replace(path)


def load_plan():
    doc=json.loads(PLAN.read_text(encoding='utf-8'))
    payer, addrs=o97.validate_plan(doc)
    return doc,payer,addrs


def lookup_table_info(address):
    res=rpc('getAccountInfo',[address,{'encoding':'base64','commitment':'confirmed'}])
    return res.get('value') if isinstance(res,dict) else None


def verify_alt(table, addrs):
    from solders.pubkey import Pubkey
    info=lookup_table_info(table)
    if not isinstance(info,dict) or info.get('owner')!=ALT_PROGRAM:
        return False,'ALT_NOT_CONFIRMED'
    datum=info.get('data')
    if not isinstance(datum,list) or not datum:
        return False,'ALT_DATA_MISSING'
    try:
        raw=base64.b64decode(datum[0],validate=True)
        wanted=[bytes(Pubkey.from_string(a)) for a in addrs]
    except (ValueError,TypeError):
        return False,'ALT_DATA_DECODE_FAILURE'
    if len(raw)<56 or (len(raw)-56)%32 or raw[:4] != bytes([1,0,0,0]):
        return False,'ALT_LAYOUT_INVALID'
    onchain=[raw[i:i+32] for i in range(56,len(raw),32)]
    if onchain != wanted:
        return False,'ALT_ACCOUNTS_NOT_MATCHED'
    if int.from_bytes(raw[4:12],'little') != 2**64-1:
        return False,'ALT_DEACTIVATED'
    last_extended_slot=int.from_bytes(raw[12:20],'little')
    current=rpc('getSlot',[{'commitment':'confirmed'}])
    if type(current) is not int or current <= last_extended_slot:
        return False,'ALT_NOT_WARM_NEXT_SLOT'
    return True,'ALT_CONFIRMED'


def quote_cost(payer, setup_ixs, blockhash, addrs):
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    msg, unsigned = r.q87.c.compile_v0(payer,setup_ixs,[],blockhash)
    if not isinstance(unsigned,(bytes,bytearray)) or len(unsigned)>MAX_WIRE or len(unsigned)<66:
        raise RuntimeError('ALT_SETUP_WIRE_ILLEGAL')
    # Packet signature prefix: 1 compact count + 64 zeroed signature bytes.
    if unsigned[0] != 1 or unsigned[1:65] != bytes(64):
        raise RuntimeError('UNSIGNED_PACKET_SHAPE_INVALID')
    fee=rpc('getFeeForMessage',[base64.b64encode(unsigned[65:]).decode(),{'commitment':'confirmed'}])
    lamports=fee.get('value') if isinstance(fee,dict) else None
    if type(lamports) is not int or lamports < 0:
        raise RuntimeError('NETWORK_FEE_UNAVAILABLE')
    rent=rpc('getMinimumBalanceForRentExemption',[56+32*len(addrs),{'commitment':'confirmed'}])
    if type(rent) is not int or rent < 0:
        raise RuntimeError('ALT_RENT_UNAVAILABLE')
    total=lamports+rent
    if total > MAX_SETUP_COST:
        raise RuntimeError('ALT_SETUP_COST_EXCEEDS_0_010_SOL_CAP')
    bal=rpc('getBalance',[payer,{'commitment':'confirmed'}])
    balance=bal.get('value') if isinstance(bal,dict) else None
    if type(balance) is not int or balance < total + RESERVE:
        raise RuntimeError('INSUFFICIENT_BALANCE_FOR_ALT_AND_RESERVE')
    return msg,bytes(unsigned),{'rent_lamports':rent,'fee_lamports':lamports,'total_lamports':total,'balance_lamports':balance,'wire_bytes':len(unsigned)}


def prepare():
    if PENDING.exists():
        raise RuntimeError('PENDING_ALT_SEND_REQUIRES_RECONCILIATION')
    if CANONICAL.exists():
        raise RuntimeError('CANONICAL_ALT_ALREADY_REGISTERED_REFUSE_DUPLICATE')
    doc,payer,addrs=load_plan()
    slot=o97.finalized_slot(os.environ.get('SOLANA_RPC_URL') or 'https://api.mainnet-beta.solana.com')
    setup=o97.build_public_setup(payer,addrs,slot)
    table=setup['lookupTable']
    if lookup_table_info(table) is not None:
        raise RuntimeError('DERIVED_ALT_ADDRESS_ALREADY_EXISTS')
    bh=rpc('getLatestBlockhash',[{'commitment':'confirmed'}])
    blockhash=(bh or {}).get('value',{}).get('blockhash')
    if not isinstance(blockhash,str):
        raise RuntimeError('BLOCKHASH_UNAVAILABLE')
    msg, unsigned, costs=quote_cost(payer,setup['instructions'],blockhash,addrs)
    payload={'table':table,'payer':payer,'token':doc['capture_token'],
             'slot':slot,'addresses':addrs,'setup_ixs':setup['instructions'],
             'msg':msg,'unsigned':unsigned,'costs':costs}
    print('[ORACLE098_SETUP_QUOTE] '+json.dumps({'table':table,'addresses':len(addrs),
          'slot':slot,'estimated_cost_lamports':costs['total_lamports'],
          'rent_lamports':costs['rent_lamports'],'fee_lamports':costs['fee_lamports'],
          'wire_bytes':costs['wire_bytes'],'max_cost_lamports':MAX_SETUP_COST},sort_keys=True),flush=True)
    return payload


def create():
    if os.environ.get('ORACLE_ALT_SETUP_ARM') != 'CREATE_ALT_ONLY':
        raise RuntimeError('EXPLICIT_ALT_ONLY_ARM_REQUIRED')
    p=prepare()
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    kp=r.q87.c.keypair()    # Secret accessed only in the specifically armed --create path
    if str(kp.pubkey()) != p['payer']:
        raise RuntimeError('WALLET_PAYER_MISMATCH_NO_SEND')
    raw=r.q87.c.signed_tx(p['msg'],kp)
    if not isinstance(raw,(bytes,bytearray)) or len(raw)>MAX_WIRE or len(raw)!=len(p['unsigned']):
        raise RuntimeError('SIGNED_ALT_PACKET_SIZE_OR_SHAPE_INVALID')
    sim=rpc('simulateTransaction',[base64.b64encode(raw).decode(),{
        'encoding':'base64','sigVerify':True,'commitment':'processed',
        'replaceRecentBlockhash':False}])
    value=sim.get('value') if isinstance(sim,dict) else None
    if not isinstance(value,dict) or value.get('err') is not None:
        print('[HOLD] ALT_SIGNED_SIMULATION_FAILED_NO_SEND',flush=True)
        raise RuntimeError('ALT_SETUP_SIMULATION_NOT_SUCCESSFUL')
    print('[ORACLE098_ALT_SIM_PASS] units=%s wire_bytes=%d' % (value.get('unitsConsumed'),len(raw)),flush=True)
    # Write a journal BEFORE invoking the send; on ambiguous network results refuse reruns.
    journal={'status':'SEND_ATTEMPTED_CONFIRMATION_PENDING','table':p['table'],'token':p['token'],
             'payer':p['payer'],'addresses':p['addresses'],'slot':p['slot'],
             'created_unix':time.time(),'estimate':p['costs']}
    atomic_json(PENDING,journal)
    tx=rpc('sendTransaction',[base64.b64encode(raw).decode(),{
        'encoding':'base64','skipPreflight':False,
        'preflightCommitment':'processed','maxRetries':0}])
    if not isinstance(tx,str) or not tx:
        raise RuntimeError('SEND_RESPONSE_UNKNOWN_PENDING_JOURNAL_RETAINED')
    journal['signature']=tx
    atomic_json(PENDING,journal)
    print('[ORACLE098_ALT_SENT] signature=%s table=%s' % (tx,p['table']),flush=True)
    confirmed=False
    for _ in range(25):
        statuses=rpc('getSignatureStatuses',[[tx],{'searchTransactionHistory':True}])
        values=statuses.get('value') if isinstance(statuses,dict) else None
        info=values[0] if isinstance(values,list) and values else None
        if isinstance(info,dict):
            if info.get('err') is not None:
                raise RuntimeError('ALT_CONFIRMED_TRANSACTION_ERROR')
            if info.get('confirmationStatus') in ('confirmed','finalized'):
                confirmed=True
                break
        time.sleep(2)
    if not confirmed:
        raise RuntimeError('ALT_CONFIRMATION_PENDING_JOURNAL_RETAINED')
    for _ in range(12):
        ok,why=verify_alt(p['table'],p['addresses'])
        if ok:
            break
        time.sleep(2)
    else:
        raise RuntimeError('ALT_READBACK_FAILED_'+why)
    # Do not register table until it is usable in a later bank slot.
    current=rpc('getSlot',[{'commitment':'confirmed'}])
    if type(current) is not int or current <= p['slot']:
        raise RuntimeError('ALT_NOT_YET_SLOT_READY_JOURNAL_RETAINED')
    state={'address':p['table'],'addresses':p['addresses'],'signature':tx,
           'token':p['token'],'slot':current,'created_unix':time.time(),
           'confirmed':True,'source':'ORACLE098_VERIFIED_MAINNET_ALT'}
    atomic_json(CANONICAL,state)
    # Only update token-scoped lookup registry after confirmation and readback.
    registry={'tables':{}}
    if TOKEN_REGISTRY.exists():
        registry=json.loads(TOKEN_REGISTRY.read_text(encoding='utf-8'))
        if not isinstance(registry,dict) or not isinstance(registry.get('tables'),dict):
            raise RuntimeError('TOKEN_REGISTRY_UNEXPECTED_SCHEMA')
    existing=registry['tables'].get(p['token'])
    if existing and existing.get('address') != p['table']:
        raise RuntimeError('TOKEN_ALREADY_HAS_DIFFERENT_ALT')
    registry['tables'][p['token']]={'address':p['table'],'covered_accounts':len(p['addresses']),
                                  'created_by':'ORACLE098','verified':True}
    atomic_json(TOKEN_REGISTRY,registry)
    PENDING.unlink()
    print('[PASS] ORACLE098_MAINNET_ALT_VERIFIED_AND_REGISTERED',flush=True)
    print('[ALT_ADDRESS]',p['table'],flush=True)
    print('[HOLD] NO_ATOMIC_TRADE_SIMULATION_OR_TRADE_AUTHORIZATION',flush=True)


def main():
    ap=argparse.ArgumentParser()
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument('--preflight',action='store_true')
    flags.add_argument('--create',action='store_true')
    args=ap.parse_args()
    if args.create:
        create()
    else:
        prepare()
        print('[BOUNDARY] READ_ONLY_PREFLIGHT_NO_KEY_NO_SIGNING_NO_BROADCAST',flush=True)

if __name__=='__main__':
    main()
