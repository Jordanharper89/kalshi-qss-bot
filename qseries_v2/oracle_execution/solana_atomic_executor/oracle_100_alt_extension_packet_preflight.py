"""Build and quote unsigned extension packet; no key access or submission."""
import base64,json,os,urllib.request
from pathlib import Path
from solders.pubkey import Pubkey
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
ROOT=Path('runtime_state/oracle/solana_atomic_executor')
ALT_PROGRAM='AddressLookupTab1e1111111111111111111111111'
SYSTEM='11111111111111111111111111111111'
MAX_WIRE=1232

def rpc(method,params):
    url=os.environ.get('SOLANA_RPC_URL') or 'https://api.mainnet-beta.solana.com'
    if not url.startswith('https://') or '\n' in url or '\r' in url: raise RuntimeError('HTTPS_RPC_REQUIRED')
    request=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':100,'method':method,'params':params}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=20) as response: result=json.load(response)
    if not isinstance(result,dict) or result.get('error') or 'result' not in result: raise RuntimeError('RPC_ERROR_'+method)
    return result['result']

def inspect(info,table,wanted,payer):
    if not isinstance(info,dict) or info.get('owner')!=ALT_PROGRAM: raise RuntimeError('ALT_NOT_FOUND_OR_BAD_OWNER')
    raw=base64.b64decode(info['data'][0],validate=True)
    if len(raw)<56 or (len(raw)-56)%32 or raw[:4]!=b'\x01\x00\x00\x00': raise RuntimeError('BAD_ALT_LAYOUT')
    if int.from_bytes(raw[4:12],'little')!=(1<<64)-1 or raw[21]!=1: raise RuntimeError('ALT_NOT_ACTIVE_OR_FROZEN')
    authority=str(Pubkey.from_bytes(raw[22:54]))
    if authority!=payer: raise RuntimeError('ALT_AUTHORITY_PAYER_MISMATCH')
    existing=[str(Pubkey.from_bytes(raw[i:i+32])) for i in range(56,len(raw),32)]
    if len(existing)!=len(set(existing)) or len(existing)>256: raise RuntimeError('INVALID_ALT_ADDRESS_SET')
    missing=[a for a in wanted if a not in existing]
    if len(existing)+len(missing)>256: raise RuntimeError('ALT_FULL')
    return existing,missing

def instruction(table,payer,missing):
    if not missing: raise RuntimeError('NO_EXTENSION_NEEDED')
    # Address Lookup Table Program ExtendLookupTable: variant u32(2), vector len u64, pubkeys
    data=(2).to_bytes(4,'little')+len(missing).to_bytes(8,'little')+b''.join(bytes(Pubkey.from_string(a)) for a in missing)
    return {'programId':ALT_PROGRAM,'accounts':[{'pubkey':table,'isSigner':False,'isWritable':True},
      {'pubkey':payer,'isSigner':True,'isWritable':False},
      {'pubkey':payer,'isSigner':True,'isWritable':True},
      {'pubkey':SYSTEM,'isSigner':False,'isWritable':False}],
      'data':base64.b64encode(data).decode(),'dataEncoding':'base64'}

def main():
    plan=json.loads((ROOT/'canonical_alt_plan.json').read_text(encoding='utf-8'))
    reg=json.loads((ROOT/'canonical_alt.json').read_text(encoding='utf-8'))
    payer=plan.get('public_payer'); wanted=plan.get('selected_addresses'); table=reg.get('address')
    if not isinstance(payer,str) or not isinstance(table,str) or not isinstance(wanted,list) or len(wanted)!=8 or len(set(wanted))!=8: raise RuntimeError('INVALID_CANONICAL_INPUT')
    for a in [payer,table,*wanted]: Pubkey.from_string(a)
    if str(r.q87.c.sim_identity()[1])!=payer: raise RuntimeError('RUNTIME_PUBLIC_IDENTITY_MISMATCH')
    res=rpc('getAccountInfo',[table,{'encoding':'base64','commitment':'confirmed'}]); info=res.get('value')
    existing,missing=inspect(info,table,wanted,payer)
    if not missing:
        print('[PASS] ORACLE100_ALT_ALREADY_COVERS_PLAN'); return
    ix=instruction(table,payer,missing)
    bh=rpc('getLatestBlockhash',[{'commitment':'confirmed'}])['value']['blockhash']
    msg,packet=r.q87.c.compile_v0(payer,[ix],[],bh)
    if not isinstance(packet,(bytes,bytearray)) or len(packet)>MAX_WIRE or len(packet)<66: raise RuntimeError('UNSIGNED_EXTENSION_PACKET_ILLEGAL')
    if packet[0]!=1 or packet[1:65]!=bytes(64): raise RuntimeError('UNSIGNED_SHAPE_UNEXPECTED')
    fee=rpc('getFeeForMessage',[base64.b64encode(packet[65:]).decode(),{'commitment':'confirmed'}])['value']
    rent=rpc('getMinimumBalanceForRentExemption',[56+32*(len(existing)+len(missing)),{'commitment':'confirmed'}])
    if type(fee)!=int or type(rent)!=int: raise RuntimeError('COST_QUOTE_MISSING')
    rent_delta=max(0,rent-int(info['lamports']))
    balance=rpc('getBalance',[payer,{'commitment':'confirmed'}])['value']
    if type(balance)!=int or balance<fee+rent_delta+3000000: raise RuntimeError('BALANCE_BELOW_QUOTE_PLUS_RESERVE')
    report={'table':table,'authority':payer,'existing':len(existing),'missing':missing,'missing_count':len(missing),
      'wire_bytes':len(packet),'fee_lamports':fee,'additional_rent_lamports':rent_delta,
      'estimated_total_lamports':fee+rent_delta,'balance_lamports':balance,
      'extension_instruction':ix,'signing':False,'broadcast':False,'trade_authority':False,'status':'UNSIGNED_PACKET_PREFLIGHT_ONLY'}
    path=ROOT/'oracle100_unsigned_extension_packet.json'; temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8');temp.replace(path)
    print('[ORACLE100_UNSIGNED_EXTENSION] '+json.dumps({k:v for k,v in report.items() if k not in ('extension_instruction','missing')},sort_keys=True))
    print('[REPORT]',path)
    print('[HOLD] NO_SIGNER_LOADED_NO_SIGNATURE_NO_BROADCAST')

if __name__=='__main__': main()
