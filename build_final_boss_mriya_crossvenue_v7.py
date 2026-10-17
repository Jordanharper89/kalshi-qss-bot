"""Final Boss Mriya Cross-Venue V7 COMPLETE replacement installer.

Fixes V6's conflation of token security with on-chain pool ownership, adds
safe header checks, and reports actual reasons for each hold. Read-only.
Requires the installed V6 SHA or an identical V7 copy. Preserves scanner.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import os
import tempfile
from pathlib import Path

ROOT=Path.cwd()
PACKAGE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
TARGET=PACKAGE/'final_boss_mriya_crossvenue_discovery.py'
BACKUPS=ROOT/'runtime_state/oracle/final_boss_dual'
V6_SHA='5ace2e758eca9c83eefe32de58c2cbea9849d279d6fc5c6bc25c4cded939489f'

SOURCE=r'''"""V7: fresh Mriya wallet mints to indexed cross-venue prospects with independent onchain audits.

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
# Official Pump AMM Pool discriminator; Anchor LbPair discriminator.
PUMP_POOL_DISC=bytes((241,154,109,4,17,177,109,188))
DLMM_PAIR_DISC=hashlib.sha256(b'account:LbPair').digest()[:8]
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
        # Meteora uses an LbPair zero-copy struct. A matching owner + discriminator
        # IS NOT a certificate that its token_x_mint/token_y_mint match token and WSOL.
        result['pair_mints_match']=False
        result['reason']='HOLD_DLMM_NATIVE_MINT_DECODER_REQUIRED'
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
                mint=mint_check(acct.get(r['token']))
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
                if mint=='HOLD_TOKEN2022_EXTENSION_AUDIT_REQUIRED':metrics['token2022_extension_holds']+=1
                for w in (p,m):
                    if w['reason']=='HOLD_POOL_ACCOUNT_MISSING':metrics['owner_account_missing']+=1
                    if w['reason']=='HOLD_POOL_PROGRAM_OWNER_MISMATCH':metrics['pool_owner_mismatch']+=1
                # Strongest possible read-only state: both owners, Pump mint header,
                # and DLMM discriminator. DLMM mint binding requires official SDK.
                if not both:status='HOLD_POOL_PROGRAM_OWNER'
                elif p.get('reason')!='PUMP_POOL_HEADER_VERIFIED':status=p['reason']
                elif not m.get('discriminator_match'):status=m['reason']
                elif mint!='PROVISIONAL_SPL_MINT_ONLY':status=mint
                else:status='HOLD_DLMM_NATIVE_MINT_DECODER_REQUIRED'
                r['status']=status
                metrics['other_holds'][status]=metrics['other_holds'].get(status,0)+1
        except Hold as ex:
            errors.append({'code':str(ex),'stage':'BATCH_ACCOUNT_OWNER_VERIFICATION'})
            for r in triples:r['status']='HOLD_RPC_ACCOUNT_VERIFICATION'
    metrics['unmatched_mints']=len(unmatched)
    metrics['http_calls']=client.http_calls;metrics['rpc_calls']=client.rpc_calls
    return {'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V7','observed_unix':time.time(),
        'source':'FRESH_MRIYA_INDEXED_POOL_PROSPECTS_UNTRUSTED','metrics':metrics,
        'prospects':triples,'unmatched':unmatched,'holds':errors,
        'status':('HOLD_NO_ONCHAIN_OWNER_PAIR' if not metrics['owners_both_verified']
          else 'HOLD_NATIVE_DLMM_POOL_MINT_AND_TOKEN_RISK_REVIEW'),
        'trust_boundary':'Owners are independent of token risk. Pump header and DLMM discriminator do not certify full DLMM pool mint state. Indexer prices are never used for execution.',
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
            b=bytearray(160);b[:8]=DLMM_PAIR_DISC
        return {'owner':owner,'data':[base64.b64encode(b).decode(),'base64']}
    assert pool_witness(pool(PUMP,'P'),PUMP,'PUMP',t)['reason']=='PUMP_POOL_HEADER_VERIFIED'
    assert pool_witness(pool(DLMM,'M'),DLMM,'DLMM',t)['reason']=='HOLD_DLMM_NATIVE_MINT_DECODER_REQUIRED'
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
    assert good['prospects'][0]['status']=='HOLD_DLMM_NATIVE_MINT_DECODER_REQUIRED'
    t22=reconcile(sight,Fake(T22))
    assert t22['metrics']['owners_both_verified']==1 and t22['metrics']['token2022_extension_holds']==1
    assert t22['prospects'][0]['status']=='HOLD_TOKEN2022_EXTENSION_AUDIT_REQUIRED'
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
    assert MAX_HTTP==MAX_MINTS==4 and MAX_RPC==1
    print('[PASS] V7 independent owner/mint audits, Pump header, DLMM discriminator, Token2022 holds, RPC cap, no execution')

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
        result={'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V7','status':str(ex),
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
       'pool_owner_mismatch':m.get('pool_owner_mismatch',0),
       'owner_account_missing':m.get('owner_account_missing',0),
       'unmatched_mints':m.get('unmatched_mints',0),
       'http_calls':m.get('http_calls',0),'rpc_calls':m.get('rpc_calls',0),
       'holds':[x.get('code') for x in result.get('holds',[])]}
    print('[MRIYA_CROSSVENUE_V7]',json.dumps(summary,sort_keys=True),flush=True)
    for r in result.get('prospects',[]):
        print('[V7_POOL_AUDIT]',json.dumps({'token':r['token'],
          'pump_pool':r['pump_pool'],'dlmm_pool':r['meteora_pool'],
          'pump_owner':r.get('pump_witness',{}).get('owner_category'),
          'dlmm_owner':r.get('dlmm_witness',{}).get('owner_category'),
          'pump_header':r.get('pump_witness',{}).get('reason'),
          'dlmm_header':r.get('dlmm_witness',{}).get('reason'),
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
    assert 'sendTransaction' not in SOURCE and 'accountSubscribe' not in SOURCE
    assert 'signTransaction' not in SOURCE and 'QSB_SOLANA_PRIVATE_KEY' not in SOURCE
    assert 'execution_eligible' in SOURCE and "'signing':False" in SOURCE
    env={'__name__':'v7_installer_test','__file__':str(TARGET)}
    exec(compile(SOURCE,str(TARGET),'exec'),env)
    env['tests']()
    print('[PASS] FULL_V7_INSTALLER exact V6 guard, no scanner mutation, read-only safety')

def install():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    new=SOURCE.encode('utf-8')
    if TARGET.is_file():
        previous=TARGET.read_bytes()
        old_sha=norm(previous)
        if old_sha==NEW_SHA:
            print('[PASS] CROSSVENUE_V7_ALREADY_INSTALLED');return
        if old_sha!=V6_SHA:
            raise RuntimeError('HOLD_EXISTING_CROSSVENUE_MODULE_UNRECOGNIZED_'+old_sha[:12])
        BACKUPS.mkdir(parents=True,exist_ok=True)
        backup=BACKUPS/('mriya_crossvenue_pre_v7_'+old_sha[:16]+'.bak')
        if backup.exists() and backup.read_bytes()!=previous:
            raise RuntimeError('HOLD_BACKUP_PATH_COLLISION')
        if not backup.exists():
            with tempfile.NamedTemporaryFile('wb',dir=BACKUPS,delete=False,suffix='.tmp') as f:
                f.write(previous);temp=Path(f.name)
            os.replace(temp,backup)
        if backup.read_bytes()!=previous:raise RuntimeError('HOLD_BACKUP_READBACK')
        print('[EXACT_BACKUP]',backup.relative_to(ROOT))
    with tempfile.NamedTemporaryFile('wb',dir=PACKAGE,delete=False,suffix='.tmp') as f:
        f.write(new);temp=Path(f.name)
    os.replace(temp,TARGET)
    if norm(TARGET.read_bytes())!=NEW_SHA:raise RuntimeError('HOLD_INSTALL_READBACK')
    print('[REPLACED_FULL_V7]',TARGET.relative_to(ROOT))
    print('[SHA256]',NEW_SHA)
    print('[PRESERVED] ORACLE-322 scanner, active WS, Q18/Q20/Q25, ORACLE-402, Mriya V5, risk controller')
    print('[SCOPE] Read-only pool auditing, no new WebSockets, no signing or broadcast, no rotation')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--install',action='store_true')
    a=p.parse_args()
    if not (a.test or a.install):p.error('Select --test or --install')
    if a.test:test()
    if a.install:install()
if __name__=='__main__':main()
