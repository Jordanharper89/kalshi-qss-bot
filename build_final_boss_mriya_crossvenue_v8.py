"""FULL V8 replacement: Mriya on-chain DLMM mint/status and Token-2022 audit.
Replaces only final_boss_mriya_crossvenue_discovery.py, requires exact V7 hash.
No scanner modification, signing, live orders, or subscriptions.
"""
from __future__ import annotations
import argparse,ast,hashlib,os,tempfile
from pathlib import Path
ROOT=Path.cwd()
PACKAGE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
TARGET=PACKAGE/'final_boss_mriya_crossvenue_discovery.py'
BACKUPS=ROOT/'runtime_state/oracle/final_boss_dual'
V7_SHA='9b7d5e28a41b3fa143ac4565331bb5e4ff99835529fdbef3230cdf358a3af476'
SOURCE=r'''"""V8: native DLMM pair identity + Token-2022 mint risk audit, read-only.

Indexer labels remain untrusted. Pool program owners, Pool discriminator, Pump mint
association, and Token2022 safety are separated. No execution or subscriptions.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
SIGHTINGS=BASE/'mriya_live_sightings.json'
OUT=BASE/'mriya_crossvenue_prospects.json'
MRIYA='MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X'
WSOL='So11111111111111111111111111111111111111112'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
SPL='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
T22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
ADDR=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
# Official Pump AMM Pool discriminator; official Meteora DLMM IDL LbPair header.
PUMP_POOL_DISC=bytes((241,154,109,4,17,177,109,188))
DLMM_PAIR_DISC=hashlib.sha256(b'account:LbPair').digest()[:8]
# Meteora official dlmm IDL LbPair: discriminator 8 + StaticParameters 32
# + VariableParameters 32 + leading scalar header 16 => token_x at 88,
# token_y at 120, reserve_x at 152. The scalar status lives at 82.
DLMM_TOKEN_X_OFFSET=88
DLMM_TOKEN_Y_OFFSET=120
DLMM_PAIR_TYPE_OFFSET=75
DLMM_BIN_STEP_OFFSET=80
DLMM_STATUS_OFFSET=82
MAX_MINTS=4
MAX_HTTP=4
MAX_RPC=1
FRESH_S=180
MAX_BYTES=1_500_000

class Hold(RuntimeError):pass

def valid(a):return isinstance(a,str) and bool(ADDR.fullmatch(a))

def base58_encode(raw):
    if not isinstance(raw,bytes):raise TypeError('EXPECTED_BYTES')
    n=int.from_bytes(raw,'big')
    out=''
    while n:
        n,rem=divmod(n,58)
        out=ALPHABET[rem]+out
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+out

def base58_decode(val):
    if not isinstance(val,str) or any(c not in ALPHABET for c in val):raise ValueError('BASE58_INVALID')
    num=0
    for c in val:num=num*58+ALPHABET.index(c)
    body=num.to_bytes((num.bit_length()+7)//8,'big') if num else b''
    return b'\0'*(len(val)-len(val.lstrip('1')))+body

def load_sightings(now=None,path=SIGHTINGS):
    now=time.time() if now is None else now
    if not path.is_file() or path.is_symlink():raise Hold('HOLD_MRIYA_REPORT_MISSING_OR_LINK')
    if path.stat().st_size>250_000:raise Hold('HOLD_MRIYA_REPORT_TOO_LARGE')
    try:x=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,OSError,UnicodeError):raise Hold('HOLD_MRIYA_REPORT_FORMAT') from None
    if x.get('source')!='MRIYA_WALLET_CONFIRMED_TX' or x.get('wallet')!=MRIYA or x.get('status')!='OBSERVED':
        raise Hold('HOLD_MRIYA_UNTRUSTED_OR_INACTIVE_REPORT')
    t=x.get('updated_unix')
    if type(t) not in (int,float) or not 0<=now-t<=90:raise Hold('HOLD_MRIYA_REPORT_OLDER_THAN_90S')
    rows=[];seen=set()
    for r in x.get('rows',[]):
        if not isinstance(r,dict):continue
        token=r.get('token');ts=r.get('block_time');slot=r.get('slot')
        if not valid(token) or token==WSOL or token in seen:continue
        if type(ts) is not int or not 0<=now-ts<=FRESH_S:continue
        if type(slot) is not int or slot<=0:continue
        witness=r.get('tx_witness_sha256')
        if not isinstance(witness,str) or not re.fullmatch('[0-9a-f]{20}',witness):continue
        seen.add(token);rows.append(dict(token=token,slot=slot,block_time=ts,witness=witness,age_s=round(now-ts,1)))
    return sorted(rows,key=lambda r:(r['age_s'],r['token']))[:MAX_MINTS]

def pair_parse(rows,token):
    if not isinstance(rows,list):raise Hold('HOLD_INDEXER_SHAPE')
    pumps={};mets={};reject={}
    for obj in rows[:180]:
        if not isinstance(obj,dict) or obj.get('chainId')!='solana':continue
        addr=obj.get('pairAddress')
        if not valid(addr):continue
        base=obj.get('baseToken') or {};quote=obj.get('quoteToken') or {}
        if not isinstance(base,dict) or not isinstance(quote,dict):continue
        b=base.get('address');q=quote.get('address')
        if not valid(b) or not valid(q) or {b,q}!={token,WSOL}:continue
        dex=str(obj.get('dexId') or '').lower().replace('-','').replace('_','')
        labels=[str(z).lower() for z in (obj.get('labels') or []) if isinstance(z,str)]
        if dex=='meteora' and any('dlmm' in z for z in labels):dest=mets
        elif dex=='pumpswap':dest=pumps
        else:
            reject['UNSUPPORTED_VENUE_OR_NON_DLMM']=reject.get('UNSUPPORTED_VENUE_OR_NON_DLMM',0)+1
            continue
        raw_liq=(obj.get('liquidity') or {}).get('usd') if isinstance(obj.get('liquidity'),dict) else None
        liq=float(raw_liq) if type(raw_liq) in (int,float) and 0<=raw_liq<=1e12 else None
        val={'address':addr,'liquidity_usd_indexer':liq}
        if addr not in dest or (liq or 0)>(dest[addr]['liquidity_usd_indexer'] or 0):dest[addr]=val
    p=sorted(pumps.values(),key=lambda x:-(x['liquidity_usd_indexer'] or 0))[:3]
    m=sorted(mets.values(),key=lambda x:-(x['liquidity_usd_indexer'] or 0))[:3]
    out=[{'token':token,'pump_pool':x['address'],'meteora_pool':y['address'],
           'pump_liquidity_usd_indexer':x['liquidity_usd_indexer'],
           'meteora_liquidity_usd_indexer':y['liquidity_usd_indexer']}
         for x in p for y in m if x['address']!=y['address']]
    return out[:6],{'pump_sol_pools':len(p),'dlmm_sol_pools':len(m),'excluded':reject}

class PublicClient:
    def __init__(self,url):
        self._rpc=url;self.http_calls=0;self.rpc_calls=0;self.retry_after_s=0
    def indexer(self,mint):
        if self.http_calls>=MAX_HTTP:raise Hold('HOLD_DISCOVERY_HTTP_BUDGET')
        if not valid(mint):raise Hold('HOLD_INVALID_MINT')
        self.http_calls+=1
        req=urllib.request.Request('https://api.dexscreener.com/token-pairs/v1/solana/'+mint,
          headers={'Accept':'application/json','User-Agent':'OracleReadonlyPoolVerify/1.0'})
        try:
            with urllib.request.urlopen(req,timeout=12) as response:raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:raise Hold('HOLD_INDEXER_TOO_LARGE')
            return json.loads(raw.decode('utf-8'))
        except urllib.error.HTTPError as ex:
            if ex.code==429:self.retry_after_s=90
            raise Hold('HOLD_INDEXER_HTTP_'+str(ex.code)) from None
        except (urllib.error.URLError,OSError,TimeoutError,UnicodeError,ValueError):
            raise Hold('HOLD_INDEXER_NETWORK_OR_FORMAT') from None
    def accounts(self,addresses):
        if not isinstance(self._rpc,str) or not self._rpc.startswith('https://'):raise Hold('HOLD_RPC_NOT_CONFIGURED')
        if self.rpc_calls>=MAX_RPC:raise Hold('HOLD_RPC_BUDGET')
        if not addresses or len(addresses)>32 or any(not valid(x) for x in addresses):raise Hold('HOLD_ACCOUNT_BATCH_INVALID')
        self.rpc_calls+=1
        # jsonParsed keeps SPL mint fields readable and unknown pool programs as base64.
        payload={'jsonrpc':'2.0','id':1,'method':'getMultipleAccounts',
                 'params':[addresses,{'encoding':'jsonParsed','commitment':'confirmed'}]}
        req=urllib.request.Request(self._rpc,json.dumps(payload).encode(),
            headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=15) as response:raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:raise Hold('HOLD_RPC_TOO_LARGE')
            x=json.loads(raw.decode('utf-8'))
            err=x.get('error') or {}
            if err:
                code=err.get('code') if isinstance(err,dict) else None
                if code in (429,-32429):self.retry_after_s=90
                raise Hold('HOLD_RPC_CODE_'+str(code) if type(code) is int else 'HOLD_RPC_JSON_ERROR')
            result=x.get('result') or {}
            vals=result.get('value') if isinstance(result,dict) else None
            if not isinstance(vals,list) or len(vals)!=len(addresses):raise Hold('HOLD_RPC_ACCOUNTS_LENGTH')
            return dict(zip(addresses,vals))
        except urllib.error.HTTPError as ex:
            if ex.code==429:self.retry_after_s=90
            raise Hold('HOLD_RPC_HTTP_'+str(ex.code)) from None
        except (urllib.error.URLError,OSError,TimeoutError,UnicodeError,ValueError):
            raise Hold('HOLD_RPC_NETWORK_OR_FORMAT') from None

def mint_check(acc):
    if not isinstance(acc,dict):return 'HOLD_MINT_MISSING'
    owner=acc.get('owner')
    if owner==T22:return 'HOLD_TOKEN2022_EXTENSION_AUDIT_REQUIRED'
    if owner!=SPL:return 'HOLD_MINT_OWNER_INVALID'
    data=acc.get('data') or {}
    parsed=data.get('parsed') if isinstance(data,dict) else None
    if not isinstance(parsed,dict) or parsed.get('type')!='mint':return 'HOLD_MINT_NOT_PARSED'
    info=parsed.get('info') or {}
    if not isinstance(info,dict) or not info.get('isInitialized'):return 'HOLD_MINT_NOT_INITIALIZED'
    if 'mintAuthority' not in info or 'freezeAuthority' not in info:return 'HOLD_AUTHORITY_FIELDS_MISSING'
    if info['mintAuthority'] is not None:return 'HOLD_MINT_AUTHORITY_PRESENT'
    if info['freezeAuthority'] is not None:return 'HOLD_FREEZE_AUTHORITY_PRESENT'
    return 'PROVISIONAL_SPL_MINT_ONLY'

# Avoid calling Token-2022 safe merely because an RPC returns a mint account.
# The actual extension list is required and any unrecognized extension is held.
DANGEROUS_EXTENSIONS={
    'transferfeeconfig','transferhook','transferhookaccount','permanentdelegate',
    'confidentialtransfermint','confidentialtransferfeeconfig',
    'nontransferable','defaultaccountstate','pausable','scaleduimount',
    'scaleduiamount','interestbearingconfig','cpiguard','memoTransfer'.lower(),
}
REVIEW_EXTENSIONS={'metadatapointer','tokenmetadata','groupmemberpointer','groupmember',
                   'grouppointer','tokengroup'}

def token2022_audit(acc):
    out={'status':'HOLD_TOKEN2022_UNVERIFIED','extensions':[],
         'hazardous_extensions':[],'unknown_extensions':[],'mint_authority_absent':False,
         'freeze_authority_absent':False}
    if not isinstance(acc,dict) or acc.get('owner')!=T22:
        out['status']='HOLD_TOKEN2022_OWNER_MISSING';return out
    data=acc.get('data') or {}
    parsed=data.get('parsed') if isinstance(data,dict) else None
    info=parsed.get('info') if isinstance(parsed,dict) else None
    if not isinstance(info,dict) or parsed.get('type')!='mint' or not info.get('isInitialized'):
        out['status']='HOLD_TOKEN2022_MINT_FORMAT';return out
    if 'mintAuthority' not in info or 'freezeAuthority' not in info:
        out['status']='HOLD_TOKEN2022_AUTHORITY_NOT_VISIBLE';return out
    out['mint_authority_absent']=info['mintAuthority'] is None
    out['freeze_authority_absent']=info['freezeAuthority'] is None
    if not out['mint_authority_absent'] or not out['freeze_authority_absent']:
        out['status']='HOLD_TOKEN2022_MINT_OR_FREEZE_AUTHORITY';return out
    ext=info.get('extensions')
    if not isinstance(ext,list):
        out['status']='HOLD_TOKEN2022_EXTENSIONS_NOT_VISIBLE';return out
    names=[]
    for row in ext:
        name=row.get('extension') if isinstance(row,dict) else None
        if not isinstance(name,str) or not name:
            out['status']='HOLD_TOKEN2022_EXTENSION_UNREADABLE';return out
        names.append(name)
    out['extensions']=names
    normalized={n.lower().replace('_','').replace('-','') for n in names}
    out['hazardous_extensions']=sorted(normalized & DANGEROUS_EXTENSIONS)
    out['unknown_extensions']=sorted(normalized - DANGEROUS_EXTENSIONS - REVIEW_EXTENSIONS)
    if out['hazardous_extensions']:
        out['status']='HOLD_TOKEN2022_RESTRICTIVE_EXTENSIONS'
    elif out['unknown_extensions']:
        out['status']='HOLD_TOKEN2022_UNKNOWN_EXTENSIONS'
    else:
        # Even metadata-only / empty lists require the two-venue official SDK
        # instruction compatibility and protected signed atomic simulation.
        out['status']='HOLD_TOKEN2022_FULL_NATIVE_EXECUTION_SIM_REQUIRED'
    return out

def dlmm_native_witness(raw,token):
    result={'pair_mints_match':False,'status':'UNKNOWN','pair_type':None,'bin_step':None}
    if raw is None or len(raw)<DLMM_TOKEN_Y_OFFSET+32:
        result['reason']='HOLD_DLMM_HEADER_TRUNCATED';return result
    x=base58_encode(bytes(raw[DLMM_TOKEN_X_OFFSET:DLMM_TOKEN_X_OFFSET+32]))
    y=base58_encode(bytes(raw[DLMM_TOKEN_Y_OFFSET:DLMM_TOKEN_Y_OFFSET+32]))
    result.update(token_x_mint=x,token_y_mint=y,
                  pair_mints_match=({x,y}=={token,WSOL}),
                  pair_type=raw[DLMM_PAIR_TYPE_OFFSET],
                  status=raw[DLMM_STATUS_OFFSET],
                  bin_step=int.from_bytes(raw[DLMM_BIN_STEP_OFFSET:DLMM_BIN_STEP_OFFSET+2],'little'))
    if not result['pair_mints_match']:
        result['reason']='HOLD_DLMM_NATIVE_MINT_MISMATCH'
    elif result['bin_step']<=0:
        result['reason']='HOLD_DLMM_ZERO_BIN_STEP'
    elif result['status']!=0:
        result['reason']='HOLD_DLMM_POOL_DISABLED'
    elif result['pair_type'] not in (0,2,3):
        result['reason']='HOLD_DLMM_RESTRICTED_PAIR_TYPE'
    else:
        result['reason']='DLMM_POOL_MINTS_VERIFIED'
    return result

def raw_pool_bytes(acc):
    if not isinstance(acc,dict):return None
    data=acc.get('data')
    if isinstance(data,list) and len(data)==2 and data[1]=='base64' and isinstance(data[0],str):
        try:return base64.b64decode(data[0],validate=True)
        except (ValueError,base64.binascii.Error):return None
    return None

def pool_witness(acc,expected,kind,token):
    if not isinstance(acc,dict):return {'owner_match':False,'reason':'HOLD_POOL_ACCOUNT_MISSING','owner_category':'MISSING'}
    owner=acc.get('owner')
    match=(owner==expected)
    cat='EXPECTED' if match else ('TOKEN_PROGRAM' if owner in (SPL,T22) else 'OTHER')
    result={'owner_match':match,'owner_category':cat,
            'owner_pubkey':owner if valid(owner) else None}
    if not match:
        result['reason']='HOLD_POOL_PROGRAM_OWNER_MISMATCH';return result
    raw=raw_pool_bytes(acc)
    result['byte_length']=len(raw) if raw is not None else None
    if raw is None or len(raw)<8:
        result['reason']='HOLD_POOL_BINARY_UNAVAILABLE';return result
    disc=PUMP_POOL_DISC if kind=='PUMP' else DLMM_PAIR_DISC
    result['discriminator_match']=raw[:8]==disc
    if not result['discriminator_match']:
        result['reason']='HOLD_POOL_DISCRIMINATOR_MISMATCH';return result
    if kind=='PUMP':
        # Pump IDL Pool: discriminator[0:8], bump[8], index[9:11], creator[11:43],
        # base_mint[43:75], quote_mint[75:107]. Only this fixed header is read.
        if len(raw)<107:
            result['reason']='HOLD_PUMP_POOL_TOO_SHORT';return result
        base=base58_encode(raw[43:75]);quote=base58_encode(raw[75:107])
        result['base_mint']=base;result['quote_mint']=quote
        result['pair_mints_match']={base,quote}=={token,WSOL}
        result['reason']='PUMP_POOL_HEADER_VERIFIED' if result['pair_mints_match'] else 'HOLD_PUMP_POOL_MINT_MISMATCH'
    else:
        # Official Meteora DLMM bytemuck LbPair layout, never string-search the
        # account or trust indexer metadata. The on-chain header is authoritative.
        result.update(dlmm_native_witness(raw,token))
    return result

def reconcile(sightings,client):
    metrics={'mriya_fresh_mints':len(sightings),'indexer_checked':0,'pool_triples_indexer':0,
       'owners_both_verified':0,'pump_pool_headers_verified':0,'dlmm_discriminators_verified':0,
       'mint_provisional_pass':0,'token2022_extension_holds':0,
       'native_binding_certified':0,'execution_eligible':0,
       'pool_owner_mismatch':0,'owner_account_missing':0,'other_holds':{},
       'unmatched_mints':0,'http_calls':0,'rpc_calls':0}
    triples=[];unmatched=[];errors=[]
    for r in sightings:
        try:
            found,d=pair_parse(client.indexer(r['token']),r['token'])
            metrics['indexer_checked']+=1
            if not found:
                unmatched.append({'token':r['token'],'why':'NO_PUMPSWAP_AND_DLMM_SOL_PAIRS_INDEXED','venue_counts':d})
                continue
            for item in found:
                item.update({'mriya_age_s':r['age_s'],'wallet_tx_witness':r['witness'],
                    'source':'MRIYA_V5_PLUS_DEXSCREENER_LOCATOR',
                    'onchain_pool_binding_verified':False,'execution_eligible':False,
                    'status':'HOLD_OWNER_AUDIT_PENDING'})
            triples.extend(found)
        except Hold as ex:
            errors.append({'token':r['token'],'code':str(ex)})
            if client.retry_after_s:break
    metrics['pool_triples_indexer']=len(triples)
    addresses=list(dict.fromkeys(a for r in triples for a in
      (r['token'],r['pump_pool'],r['meteora_pool'])))[:32]
    if addresses:
        try:
            acct=client.accounts(addresses)
            for r in triples:
                p=pool_witness(acct.get(r['pump_pool']),PUMP,'PUMP',r['token'])
                m=pool_witness(acct.get(r['meteora_pool']),DLMM,'DLMM',r['token'])
                token_acc=acct.get(r['token'])
                t22_audit=token2022_audit(token_acc) if isinstance(token_acc,dict) and token_acc.get('owner')==T22 else None
                mint=t22_audit['status'] if t22_audit else mint_check(token_acc)
                r['token2022_audit']=t22_audit
                r['mint_check']=mint
                r['pump_witness']=p;r['dlmm_witness']=m
                r['pump_program_owner_verified']=p['owner_match']
                r['dlmm_program_owner_verified']=m['owner_match']
                both=p['owner_match'] and m['owner_match']
                r['pool_program_owners_verified']=both
                if both:metrics['owners_both_verified']+=1
                if p.get('reason')=='PUMP_POOL_HEADER_VERIFIED':metrics['pump_pool_headers_verified']+=1
                if m.get('discriminator_match'):metrics['dlmm_discriminators_verified']+=1
                if mint=='PROVISIONAL_SPL_MINT_ONLY':metrics['mint_provisional_pass']+=1
                if t22_audit is not None:metrics['token2022_extension_holds']+=1
                for w in (p,m):
                    if w['reason']=='HOLD_POOL_ACCOUNT_MISSING':metrics['owner_account_missing']+=1
                    if w['reason']=='HOLD_POOL_PROGRAM_OWNER_MISMATCH':metrics['pool_owner_mismatch']+=1
                # Physical mint-to-pool verification is independent of token
                # safety, SDK hydration and executable net-profit simulation.
                exact=(both and p.get('reason')=='PUMP_POOL_HEADER_VERIFIED'
                    and m.get('reason')=='DLMM_POOL_MINTS_VERIFIED')
                r['onchain_pool_binding_verified']=bool(exact)
                if exact:metrics['native_binding_certified']+=1
                if not both:status='HOLD_POOL_PROGRAM_OWNER'
                elif p.get('reason')!='PUMP_POOL_HEADER_VERIFIED':status=p['reason']
                elif m.get('reason')!='DLMM_POOL_MINTS_VERIFIED':status=m['reason']
                elif mint!='PROVISIONAL_SPL_MINT_ONLY':status=mint
                else:status='HOLD_NATIVE_SDK_HYDRATION_SIGNED_SIM_AND_NET_PROFIT'
                r['status']=status
                metrics['other_holds'][status]=metrics['other_holds'].get(status,0)+1
        except Hold as ex:
            errors.append({'code':str(ex),'stage':'BATCH_ACCOUNT_OWNER_VERIFICATION'})
            for r in triples:r['status']='HOLD_RPC_ACCOUNT_VERIFICATION'
    metrics['unmatched_mints']=len(unmatched)
    metrics['http_calls']=client.http_calls;metrics['rpc_calls']=client.rpc_calls
    return {'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V8','observed_unix':time.time(),
        'source':'FRESH_MRIYA_INDEXED_POOL_PROSPECTS_UNTRUSTED','metrics':metrics,
        'prospects':triples,'unmatched':unmatched,'holds':errors,
        'status':('HOLD_NO_ONCHAIN_OWNER_PAIR' if not metrics['owners_both_verified']
          else 'HOLD_NO_EXACT_NATIVE_DLMM_MINT_BINDINGS' if not metrics['native_binding_certified']
          else 'HOLD_TOKEN_SAFETY_AND_EXECUTION_SIMULATION'),
        'trust_boundary':'Official zero-copy DLMM pool header mints and status independently verified; Token2022 extension observations are not a trading authorization. Native SDK hydration, exact economics, and protected signed atomic simulation remain separate. Indexer prices never authorize execution.',
        'scanner_modified':False,'subscription_rotation_applied':False,'additional_websockets':0,
        'read_only':True,'signing':False,'broadcast':False,'execution_authority':False}

def save(report,path=OUT):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False,suffix='.tmp') as f:
        json.dump(report,f,indent=2,sort_keys=True);name=f.name
    os.replace(name,path)

def tests():
    import tempfile as tf
    t=base58_encode(bytes([3])*32);pp=base58_encode(bytes([4])*32);mm=base58_encode(bytes([5])*32)
    assert base58_decode(t)==bytes([3])*32
    assert base58_encode(b'\0'*32)=='1'*32
    row=lambda dex,addr,labels:{'chainId':'solana','dexId':dex,'pairAddress':addr,
        'labels':labels,'baseToken':{'address':t},'quoteToken':{'address':WSOL},
        'liquidity':{'usd':44000}}
    pidx=[row('pumpswap',pp,[]),row('meteora',mm,['DLMM']),row('meteora',base58_encode(bytes([6])*32),['DYN'])]
    found,d=pair_parse(pidx,t)
    assert len(found)==1 and d['excluded']['UNSUPPORTED_VENUE_OR_NON_DLMM']==1
    parsed_mint=lambda owner:{'owner':owner,'data':{'parsed':{'type':'mint','info':{
        'isInitialized':True,'mintAuthority':None,'freezeAuthority':None}}}}
    def pool(owner,kind):
        if kind=='P':
            b=bytearray(220);b[:8]=PUMP_POOL_DISC;b[43:75]=base58_decode(t);b[75:107]=base58_decode(WSOL)
        else:
            b=bytearray(900);b[:8]=DLMM_PAIR_DISC;b[DLMM_TOKEN_X_OFFSET:DLMM_TOKEN_X_OFFSET+32]=base58_decode(t);b[DLMM_TOKEN_Y_OFFSET:DLMM_TOKEN_Y_OFFSET+32]=base58_decode(WSOL);b[DLMM_BIN_STEP_OFFSET:DLMM_BIN_STEP_OFFSET+2]=(25).to_bytes(2,'little');b[DLMM_PAIR_TYPE_OFFSET]=3;b[DLMM_STATUS_OFFSET]=0
        return {'owner':owner,'data':[base64.b64encode(b).decode(),'base64']}
    assert pool_witness(pool(PUMP,'P'),PUMP,'PUMP',t)['reason']=='PUMP_POOL_HEADER_VERIFIED'
    assert pool_witness(pool(DLMM,'M'),DLMM,'DLMM',t)['reason']=='DLMM_POOL_MINTS_VERIFIED'
    assert pool_witness(pool(SPL,'P'),PUMP,'PUMP',t)['reason']=='HOLD_POOL_PROGRAM_OWNER_MISMATCH'
    class Fake:
        http_calls=0;rpc_calls=0;retry_after_s=0
        def __init__(self,mint_owner=SPL,pump_owner=PUMP):self.mint_owner=mint_owner;self.pump_owner=pump_owner
        def indexer(self,m):self.http_calls+=1;return pidx
        def accounts(self,addresses):
            self.rpc_calls+=1
            assert set(addresses)=={t,pp,mm}
            return {t:parsed_mint(self.mint_owner),pp:pool(self.pump_owner,'P'),mm:pool(DLMM,'M')}
    sight=[{'token':t,'age_s':2,'witness':'f'*20}]
    good=reconcile(sight,Fake())
    assert good['metrics']['owners_both_verified']==1
    assert good['metrics']['pump_pool_headers_verified']==1
    assert good['metrics']['execution_eligible']==0
    assert good['prospects'][0]['status']=='HOLD_NATIVE_SDK_HYDRATION_SIGNED_SIM_AND_NET_PROFIT'
    assert good['metrics']['native_binding_certified']==1
    assert good['prospects'][0]['onchain_pool_binding_verified'] is True
    t22=reconcile(sight,Fake(T22))
    assert t22['metrics']['owners_both_verified']==1 and t22['metrics']['token2022_extension_holds']==1
    assert t22['prospects'][0]['status']=='HOLD_TOKEN2022_EXTENSIONS_NOT_VISIBLE'
    wrong=reconcile(sight,Fake(SPL,SPL))
    assert wrong['metrics']['owners_both_verified']==0 and wrong['metrics']['pool_owner_mismatch']==1
    assert wrong['status']=='HOLD_NO_ONCHAIN_OWNER_PAIR'
    with tf.TemporaryDirectory() as d:
        path=Path(d)/'test.json';now=1000
        path.write_text(json.dumps({'source':'MRIYA_WALLET_CONFIRMED_TX','wallet':MRIYA,
        'status':'OBSERVED','updated_unix':now,'rows':[{'token':t,'slot':555,
          'block_time':999,'tx_witness_sha256':'a'*20}]}))
        assert load_sightings(now,path)[0]['token']==t
        try:load_sightings(now+200,path)
        except Hold as e:assert str(e)=='HOLD_MRIYA_REPORT_OLDER_THAN_90S'
        else:raise AssertionError('ACCEPTED_STALE')
    # Official IDL alignment and negative identity/disabled pool tests.
    assert DLMM_TOKEN_X_OFFSET==8+32+32+16 and DLMM_TOKEN_Y_OFFSET==120
    d=pool(DLMM,'M');raw=bytearray(base64.b64decode(d['data'][0]));raw[DLMM_TOKEN_Y_OFFSET:DLMM_TOKEN_Y_OFFSET+32]=bytes([12])*32
    assert dlmm_native_witness(raw,t)['reason']=='HOLD_DLMM_NATIVE_MINT_MISMATCH'
    raw[DLMM_TOKEN_Y_OFFSET:DLMM_TOKEN_Y_OFFSET+32]=base58_decode(WSOL)
    raw[DLMM_STATUS_OFFSET]=1
    assert dlmm_native_witness(raw,t)['reason']=='HOLD_DLMM_POOL_DISABLED'
    tx={'owner':T22,'data':{'parsed':{'type':'mint','info':{'isInitialized':True,'mintAuthority':None,'freezeAuthority':None,'extensions':[{'extension':'transferFeeConfig'}]}}}}
    assert token2022_audit(tx)['status']=='HOLD_TOKEN2022_RESTRICTIVE_EXTENSIONS'
    tx['data']['parsed']['info']['extensions']=[{'extension':'metadataPointer'}]
    assert token2022_audit(tx)['status']=='HOLD_TOKEN2022_FULL_NATIVE_EXECUTION_SIM_REQUIRED'
    tx['data']['parsed']['info'].pop('extensions')
    assert token2022_audit(tx)['status']=='HOLD_TOKEN2022_EXTENSIONS_NOT_VISIBLE'
    assert MAX_HTTP==MAX_MINTS==4 and MAX_RPC==1
    print('[PASS] V8 DLMM official header mint/status, T22 extension fail-closed, mismatch fixtures, RPC cap, no execution')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--once',action='store_true')
    a=p.parse_args()
    if a.test:tests();return 0
    if not a.once:p.error('Use --test or --once')
    try:
        rows=load_sightings()
        if not rows:raise Hold('HOLD_NO_FRESH_MRIYA_MINTS')
        result=reconcile(rows,PublicClient(os.environ.get('SOLANA_RPC_URL','')))
    except Hold as ex:
        result={'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V8','status':str(ex),
                'read_only':True,'scanner_modified':False,'subscription_rotation_applied':False,
                'signing':False,'broadcast':False,'execution_authority':False}
    save(result)
    m=result.get('metrics',{})
    summary={'status':result['status'],'fresh_mints':m.get('mriya_fresh_mints',0),
       'indexed_crossvenue':m.get('pool_triples_indexer',0),
       'owners_both_verified':m.get('owners_both_verified',0),
       'pump_pool_headers_verified':m.get('pump_pool_headers_verified',0),
       'dlmm_discriminators_verified':m.get('dlmm_discriminators_verified',0),
       'token2022_extension_holds':m.get('token2022_extension_holds',0),
       'native_binding_certified':m.get('native_binding_certified',0),
       'pool_owner_mismatch':m.get('pool_owner_mismatch',0),
       'owner_account_missing':m.get('owner_account_missing',0),
       'unmatched_mints':m.get('unmatched_mints',0),
       'http_calls':m.get('http_calls',0),'rpc_calls':m.get('rpc_calls',0),
       'holds':[x.get('code') for x in result.get('holds',[])]}
    print('[MRIYA_CROSSVENUE_V8]',json.dumps(summary,sort_keys=True),flush=True)
    for r in result.get('prospects',[]):
        print('[V8_POOL_AUDIT]',json.dumps({'token':r['token'],
          'pump_pool':r['pump_pool'],'dlmm_pool':r['meteora_pool'],
          'pump_owner':r.get('pump_witness',{}).get('owner_category'),
          'dlmm_owner':r.get('dlmm_witness',{}).get('owner_category'),
          'pump_header':r.get('pump_witness',{}).get('reason'),
          'dlmm_header':r.get('dlmm_witness',{}).get('reason'),
          'dlmm_mint_x':r.get('dlmm_witness',{}).get('token_x_mint'),
          'dlmm_mint_y':r.get('dlmm_witness',{}).get('token_y_mint'),
          'dlmm_pool_status':r.get('dlmm_witness',{}).get('status'),
          'native_identity_verified':r.get('onchain_pool_binding_verified',False),
          'token2022_extensions':(r.get('token2022_audit') or {}).get('extensions',[]),
          'mint_risk':r.get('mint_check'),
          'status':r.get('status')},sort_keys=True),flush=True)
    print('[REPORT]',OUT.relative_to(ROOT),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
'''

def norm(raw):
    return hashlib.sha256(raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n')).hexdigest()
NEW_SHA=norm(SOURCE.encode('utf-8'))

def test():
    ast.parse(SOURCE)
    for forbidden in ('sendTransaction','accountSubscribe','QSB_SOLANA_PRIVATE_KEY',
                      'signTransaction','private_key','create_subprocess'):
        assert forbidden not in SOURCE, 'HOLD_FORBIDDEN_BOUNDARY_'+forbidden
    assert SOURCE.count('maxSupportedTransactionVersion')==0
    assert "'execution_authority':False" in SOURCE
    assert 'DLMM_TOKEN_X_OFFSET=88' in SOURCE
    assert 'def token2022_audit' in SOURCE
    scope={'__name__':'v8_full_installer_test','__file__':str(TARGET)}
    exec(compile(SOURCE,str(TARGET),'exec'),scope)
    scope['tests']()
    print('[PASS] V8_INSTALLER guarded V7->V8 full replacement, exact DLMM/T22 audits, read-only')

def install():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    new=SOURCE.encode('utf-8')
    if TARGET.exists():
        if TARGET.is_symlink():raise RuntimeError('HOLD_TARGET_SYMLINK')
        old=TARGET.read_bytes();old_hash=norm(old)
        if old_hash==NEW_SHA:
            print('[PASS] V8_ALREADY_INSTALLED');return
        if old_hash!=V7_SHA:
            raise RuntimeError('HOLD_EXISTING_V7_SOURCE_UNRECOGNIZED_'+old_hash[:12])
        BACKUPS.mkdir(parents=True,exist_ok=True)
        backup=BACKUPS/('mriya_crossvenue_pre_v8_'+old_hash[:16]+'.bak')
        if backup.exists() and backup.read_bytes()!=old:
            raise RuntimeError('HOLD_BACKUP_PATH_COLLISION')
        if not backup.exists():
            with tempfile.NamedTemporaryFile('wb',dir=BACKUPS,delete=False,suffix='.tmp') as f:
                f.write(old);temp=Path(f.name)
            os.replace(temp,backup)
        if backup.read_bytes()!=old:raise RuntimeError('HOLD_BACKUP_READBACK')
        print('[EXACT_BACKUP]',backup.relative_to(ROOT))
    with tempfile.NamedTemporaryFile('wb',dir=PACKAGE,delete=False,suffix='.tmp') as f:
        f.write(new);temp=Path(f.name)
    os.replace(temp,TARGET)
    if norm(TARGET.read_bytes())!=NEW_SHA:raise RuntimeError('HOLD_INSTALL_READBACK')
    print('[REPLACED_FULL_V8]',TARGET.relative_to(ROOT))
    print('[SHA256]',NEW_SHA)
    print('[PRESERVED] ORACLE-322, active WS, Q18/Q20/Q25, ORACLE-402, Mriya V5, V4 controller')
    print('[AUTHORITY] NO_ROTATION; NO_SIGNING; NO_BROADCAST; NOT_EXECUTION_ELIGIBLE')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--install',action='store_true')
    a=p.parse_args()
    if not a.test and not a.install:p.error('Select --test or --install')
    if a.test:test()
    if a.install:install()
if __name__=='__main__':main()
