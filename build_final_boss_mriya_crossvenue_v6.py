"""Complete V6 installer: read-only fresh-Mriya PumpSwap/DLMM pool discovery.

Does not replace or edit ORACLE-322, Q18/Q20/Q25, ORACLE-402, sockets,
subscriptions, or wallet/key surfaces. Provides untrusted pool prospects
for later native SDK verification; never forwards executable candidates.
"""
from __future__ import annotations
import argparse, ast, hashlib, os, tempfile
from pathlib import Path

ROOT=Path.cwd()
PACKAGE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
TARGET=PACKAGE/'final_boss_mriya_crossvenue_discovery.py'

SOURCE=r'''"""V6: Mriya confirmed mint -> indexed cross-venue prospects -> on-chain account-owner checks.

Indexer fields and token/pool association are NOT verified pool state.
Requires separate official SDK decode, fresh quote, simulation, security gate.
No new WebSockets, scanner edits, hot-path HTTP, signatures or transactions.
"""
from __future__ import annotations
import argparse, json, os, re, tempfile, time, urllib.request, urllib.error
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
MAX_MINTS=4
MAX_HTTP=4
MAX_RPC=1
FRESH_S=180
MAX_BYTES=1_500_000

class Hold(RuntimeError):pass

def valid(a):return isinstance(a,str) and bool(ADDR.fullmatch(a))

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
        seen.add(token);rows.append(dict(token=token,slot=slot,block_time=ts,
                                        witness=witness,age_s=round(now-ts,1)))
    return sorted(rows,key=lambda r:(r['age_s'],r['token']))[:MAX_MINTS]

def pair_parse(rows,token):
    """Indexer is a locator only; enforce token + WSOL and venue identity."""
    if not isinstance(rows,list):raise Hold('HOLD_INDEXER_SHAPE')
    pump={};meteora={};rejections={}
    for p in rows[:180]:
        if not isinstance(p,dict) or p.get('chainId')!='solana':continue
        a=p.get('pairAddress')
        if not valid(a):continue
        base=p.get('baseToken') or {};quote=p.get('quoteToken') or {}
        if not isinstance(base,dict) or not isinstance(quote,dict):continue
        b=base.get('address');q=quote.get('address')
        if not valid(b) or not valid(q) or {b,q}!={token,WSOL}:continue
        dex=str(p.get('dexId') or '').lower().replace('-','').replace('_','')
        labels=[str(z).lower() for z in (p.get('labels') or []) if isinstance(z,str)]
        # DLMM only; Meteora DAMM/DYN must NOT be represented as DLMM.
        if dex=='meteora' and any('dlmm' in z for z in labels):venue='M'
        elif dex=='pumpswap':venue='P'
        else:
            rejections['VENUE_OR_DLMM_UNSUPPORTED']=rejections.get('VENUE_OR_DLMM_UNSUPPORTED',0)+1
            continue
        raw_liq=(p.get('liquidity') or {}).get('usd') if isinstance(p.get('liquidity'),dict) else None
        liq=float(raw_liq) if type(raw_liq) in (int,float) and 0<=raw_liq<=1e12 else None
        # For ranking only; not a verified economic or price input.
        entry={'address':a,'liquidity_usd_indexer':liq}
        current=(pump if venue=='P' else meteora)
        if a not in current or (liq or 0)>(current[a]['liquidity_usd_indexer'] or 0):current[a]=entry
    pumps=sorted(pump.values(),key=lambda x:-(x['liquidity_usd_indexer'] or 0))[:3]
    mets=sorted(meteora.values(),key=lambda x:-(x['liquidity_usd_indexer'] or 0))[:3]
    # No fallback between venue families. Require same token and SOL on each venue.
    triples=[]
    for p in pumps:
        for m in mets:
            if p['address']==m['address']:continue
            triples.append({'token':token,'pump_pool':p['address'],'meteora_pool':m['address'],
              'pump_liquidity_usd_indexer':p['liquidity_usd_indexer'],
              'meteora_liquidity_usd_indexer':m['liquidity_usd_indexer']})
    return triples[:6],{'pump_sol_pools':len(pumps),'dlmm_sol_pools':len(mets),'excluded':rejections}

class PublicClient:
    def __init__(self,rpc_url):
        self._rpc=rpc_url
        self.http_calls=0;self.rpc_calls=0;self.retry_after_s=0
    def indexer(self,mint):
        if self.http_calls>=MAX_HTTP:raise Hold('HOLD_DISCOVERY_HTTP_BUDGET')
        if not valid(mint):raise Hold('HOLD_INVALID_MINT')
        self.http_calls+=1
        url='https://api.dexscreener.com/token-pairs/v1/solana/'+mint
        req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'OracleReadOnlyCrosslist/1.0'})
        try:
            with urllib.request.urlopen(req,timeout=12) as r:raw=r.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:raise Hold('HOLD_INDEXER_RESPONSE_TOO_LARGE')
            return json.loads(raw.decode('utf-8'))
        except urllib.error.HTTPError as exc:
            if exc.code==429:self.retry_after_s=90
            raise Hold('HOLD_INDEXER_HTTP_'+str(exc.code)) from None
        except (urllib.error.URLError,OSError,TimeoutError,UnicodeError,ValueError):
            raise Hold('HOLD_INDEXER_NETWORK_OR_FORMAT') from None
    def accounts(self,addresses):
        if not self._rpc.startswith('https://'):raise Hold('HOLD_RPC_NOT_CONFIGURED')
        if self.rpc_calls>=MAX_RPC:raise Hold('HOLD_RPC_BUDGET')
        if not addresses or len(addresses)>32 or any(not valid(a) for a in addresses):
            raise Hold('HOLD_ACCOUNT_BATCH_INVALID')
        self.rpc_calls+=1
        payload={'jsonrpc':'2.0','id':1,'method':'getMultipleAccounts',
                'params':[addresses,{'encoding':'jsonParsed','commitment':'confirmed'}]}
        req=urllib.request.Request(self._rpc,json.dumps(payload).encode('utf-8'),
                                   headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=15) as r:raw=r.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:raise Hold('HOLD_RPC_RESPONSE_TOO_LARGE')
            data=json.loads(raw.decode('utf-8'))
            err=data.get('error') or {}
            if err:
                code=err.get('code') if isinstance(err,dict) else None
                if code in (429,-32429):self.retry_after_s=90
                raise Hold('HOLD_RPC_CODE_'+str(code) if type(code) is int else 'HOLD_RPC_JSON_ERROR')
            result=data.get('result') or {}
            values=result.get('value') if isinstance(result,dict) else None
            if not isinstance(values,list) or len(values)!=len(addresses):
                raise Hold('HOLD_RPC_ACCOUNTS_LENGTH')
            return dict(zip(addresses,values))
        except urllib.error.HTTPError as exc:
            if exc.code==429:self.retry_after_s=90
            raise Hold('HOLD_RPC_HTTP_'+str(exc.code)) from None
        except (urllib.error.URLError,OSError,TimeoutError,UnicodeError,ValueError):
            raise Hold('HOLD_RPC_NETWORK_OR_FORMAT') from None

def mint_check(acc):
    if not isinstance(acc,dict):return 'HOLD_MINT_MISSING'
    owner=acc.get('owner')
    if owner==T22:return 'HOLD_TOKEN2022_EXTENSION_AUDIT'
    if owner!=SPL:return 'HOLD_MINT_OWNER_INVALID'
    data=acc.get('data') or {};p=data.get('parsed') if isinstance(data,dict) else None
    if not isinstance(p,dict) or p.get('type')!='mint':return 'HOLD_MINT_NOT_PARSED'
    info=p.get('info') or {}
    if not isinstance(info,dict) or not info.get('isInitialized'):return 'HOLD_MINT_NOT_INITIALIZED'
    if 'mintAuthority' not in info or 'freezeAuthority' not in info:return 'HOLD_AUTHORITY_FIELDS_MISSING'
    if info['mintAuthority'] is not None:return 'HOLD_MINT_AUTHORITY_PRESENT'
    if info['freezeAuthority'] is not None:return 'HOLD_FREEZE_AUTHORITY_PRESENT'
    return 'PROVISIONAL_SPL_MINT_ONLY'

def reconcile(sightings,client):
    metrics={'mriya_fresh_mints':len(sightings),'indexer_checked':0,'pool_triples_indexer':0,
      'owner_checked':0,'owner_verified_prospects':0,'risk_holds':{},'unmatched_mints':0,
      'http_calls':0,'rpc_calls':0}
    triples=[];unmatched=[];errors=[]
    for r in sightings:
        try:
            found,diagnostics=pair_parse(client.indexer(r['token']),r['token'])
            metrics['indexer_checked']+=1
            if not found:
                unmatched.append({'token':r['token'],'why':'NO_PUMPSWAP_AND_DLMM_SOL_PAIRS_INDEXED',
                                  'venue_counts':diagnostics});continue
            for item in found:
                item.update({'mriya_age_s':r['age_s'],'wallet_tx_witness':r['witness'],
                             'source':'MRIYA_V5_PLUS_DEXSCREENER_LOCATOR',
                             'onchain_pool_binding_verified':False,
                             'execution_eligible':False})
            triples.extend(found)
        except Hold as ex:
            errors.append({'token':r['token'],'code':str(ex)})
            if client.retry_after_s:break
    metrics['pool_triples_indexer']=len(triples)
    addresses=list(dict.fromkeys(a for r in triples for a in
      (r['token'],r['pump_pool'],r['meteora_pool'])))[:32]
    # Fail closed: if RPC errors, keep unverified prospects for diagnosis only.
    if addresses:
        try:
            account_map=client.accounts(addresses)
            for r in triples:
                token_ok=mint_check(account_map.get(r['token']))
                pump=account_map.get(r['pump_pool']);meteora=account_map.get(r['meteora_pool'])
                p_owner=isinstance(pump,dict) and pump.get('owner')==PUMP
                m_owner=isinstance(meteora,dict) and meteora.get('owner')==DLMM
                r['mint_check']=token_ok
                r['pump_program_owner_verified']=bool(p_owner)
                r['dlmm_program_owner_verified']=bool(m_owner)
                r['pool_program_owners_verified']=bool(p_owner and m_owner)
                r['status']=('PROSPECT_OWNERS_VERIFIED_NEEDS_NATIVE_POOL_MINT_DECODING'
                  if p_owner and m_owner and token_ok=='PROVISIONAL_SPL_MINT_ONLY'
                  else 'HOLD_MINT_OR_POOL_OWNER')
                metrics['owner_checked']+=1
                if r['status'].startswith('PROSPECT_'):
                    metrics['owner_verified_prospects']+=1
                else:
                    code=token_ok if token_ok!='PROVISIONAL_SPL_MINT_ONLY' else 'HOLD_POOL_OWNER'
                    metrics['risk_holds'][code]=metrics['risk_holds'].get(code,0)+1
        except Hold as ex:
            errors.append({'code':str(ex),'stage':'BATCH_ACCOUNT_OWNER_VERIFICATION'})
            for r in triples:r['status']='HOLD_RPC_ACCOUNT_VERIFICATION'
    metrics['unmatched_mints']=len(unmatched)
    metrics['http_calls']=client.http_calls;metrics['rpc_calls']=client.rpc_calls
    return {'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V6','observed_unix':time.time(),
       'source':'FRESH_MRIYA_INDEXED_POOL_PROSPECTS_UNTRUSTED','metrics':metrics,
       'prospects':triples,'unmatched':unmatched,'holds':errors,
       'status':('HOLD_NO_VERIFIED_ONCHAIN_POOL_OWNERS' if not metrics['owner_verified_prospects']
                 else 'PROSPECTS_OWNER_VERIFIED_NATIVE_DECODE_REQUIRED'),
       'trust_boundary':'Indexer SOL/token labeling plus program ownership only. Neither pool mint state nor quote economics decoded.',
       'scanner_modified':False,'subscription_rotation_applied':False,'additional_websockets':0,
       'read_only':True,'signing':False,'broadcast':False,'execution_authority':False}

def save(report,loc=OUT):
    loc.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=loc.parent,delete=False,suffix='.tmp') as f:
        json.dump(report,f,indent=2,sort_keys=True);name=f.name
    os.replace(name,loc)

def tests():
    import tempfile as tf
    t='A'*43;pp='B'*43;mm='C'*43
    row=lambda dex,addr,labels:dict(chainId='solana',dexId=dex,pairAddress=addr,
                 labels=labels,baseToken={'address':t},quoteToken={'address':WSOL},
                 liquidity={'usd':40000})
    found,d=pair_parse([row('pumpswap',pp,[]),row('meteora',mm,['DLMM']),
                        row('meteora','D'*43,['DYN'])],t)
    assert len(found)==1 and found[0]['pump_pool']==pp and found[0]['meteora_pool']==mm
    assert pair_parse([row('meteora',mm,['DYN'])],t)[0]==[]
    acc=lambda owner:{'owner':owner,'data':{'parsed':{'type':'mint','info':{
          'isInitialized':True,'mintAuthority':None,'freezeAuthority':None}}}}
    assert mint_check(acc(SPL))=='PROVISIONAL_SPL_MINT_ONLY'
    assert mint_check(acc(T22))=='HOLD_TOKEN2022_EXTENSION_AUDIT'
    class Fake:
        http_calls=0;rpc_calls=0;retry_after_s=0
        def indexer(self,m):
            self.http_calls+=1
            return [row('pumpswap',pp,[]),row('meteora',mm,['DLMM'])]
        def accounts(self,addresses):
            self.rpc_calls+=1
            assert set(addresses)=={t,pp,mm}
            return {t:acc(SPL),pp:{'owner':PUMP},mm:{'owner':DLMM}}
    fake=Fake()
    r=reconcile([{'token':t,'age_s':5,'witness':'c'*20}],fake)
    assert r['metrics']['owner_verified_prospects']==1 and fake.http_calls==1 and fake.rpc_calls==1
    assert r['prospects'][0]['onchain_pool_binding_verified'] is False
    assert r['prospects'][0]['execution_eligible'] is False and r['broadcast'] is False
    class Missing(Fake):
        def accounts(self,addresses):return {t:acc(T22),pp:{'owner':PUMP},mm:{'owner':DLMM}}
    assert reconcile([{'token':t,'age_s':5,'witness':'c'*20}],Missing())['metrics']['owner_verified_prospects']==0
    with tf.TemporaryDirectory() as td:
        fp=Path(td)/'s.json';now=1000
        fp.write_text(json.dumps({'source':'MRIYA_WALLET_CONFIRMED_TX','wallet':MRIYA,
          'status':'OBSERVED','updated_unix':now,'rows':[{'token':t,'slot':555,
          'block_time':999,'tx_witness_sha256':'a'*20}]}))
        assert load_sightings(now,fp)[0]['token']==t
        try:load_sightings(now+200,fp)
        except Hold as e:assert str(e)=='HOLD_MRIYA_REPORT_OLDER_THAN_90S'
        else:raise AssertionError('STALE_MRIYA_ADMITTED')
    assert MAX_HTTP==MAX_MINTS==4 and MAX_RPC==1
    print('[PASS] V6 fresh Mriya, exact SOL crosslist, DLMM-only, batch onchain owners, fail-closed safety')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--once',action='store_true')
    a=p.parse_args()
    if a.test:tests();return 0
    if not a.once:p.error('Use --test or --once')
    try:
        sightings=load_sightings()
        if not sightings:raise Hold('HOLD_NO_FRESH_MRIYA_MINTS')
        cli=PublicClient(os.environ.get('SOLANA_RPC_URL',''))
        report=reconcile(sightings,cli)
    except Hold as e:
        report={'build':'FINAL_BOSS_MRIYA_CROSSVENUE_V6','status':str(e),
          'read_only':True,'scanner_modified':False,'subscription_rotation_applied':False,
          'signing':False,'broadcast':False,'execution_authority':False}
    save(report)
    metrics=report.get('metrics',{})
    print('[MRIYA_CROSSVENUE_V6]',json.dumps({'status':report['status'],
        'fresh_mints':metrics.get('mriya_fresh_mints',0),
        'indexed_crossvenue':metrics.get('pool_triples_indexer',0),
        'owner_verified_prospects':metrics.get('owner_verified_prospects',0),
        'unmatched_mints':metrics.get('unmatched_mints',0),
        'http_calls':metrics.get('http_calls',0),'rpc_calls':metrics.get('rpc_calls',0),
        'hold_codes':[x.get('code') for x in report.get('holds',[])]},sort_keys=True),flush=True)
    print('[REPORT]',OUT.relative_to(ROOT),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
'''

def normalized_sha(data):
    return hashlib.sha256(data.replace(b'\r\n',b'\n').replace(b'\r',b'\n')).hexdigest()

SHA=normalized_sha(SOURCE.encode('utf-8'))

def test():
    ast.parse(SOURCE)
    assert 'sendTransaction' not in SOURCE and 'accountSubscribe' not in SOURCE
    assert 'private_key' not in SOURCE.lower() and 'signTransaction' not in SOURCE
    assert 'maxSupportedTransactionVersion' not in SOURCE # V5 owns tx parsing
    assert 'execution_eligible\':False' in SOURCE
    env={'__name__':'v6_installer_selftest','__file__':str(TARGET)}
    exec(compile(SOURCE,str(TARGET),'exec'),env)
    env['tests']()
    print('[PASS] V6_FULL_INSTALLER syntax, physical module fixtures, no scanner mutation')

def install():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    new=SOURCE.encode('utf-8')
    if TARGET.exists():
        old=TARGET.read_bytes()
        if normalized_sha(old)==SHA:
            print('[PASS] V6_ALREADY_INSTALLED');return
        raise RuntimeError('HOLD_EXISTING_V6_MODULE_UNRECOGNIZED')
    with tempfile.NamedTemporaryFile('wb',dir=PACKAGE,delete=False,suffix='.tmp') as tmp:
        tmp.write(new);tmp_name=tmp.name
    os.replace(tmp_name,TARGET)
    if normalized_sha(TARGET.read_bytes())!=SHA:raise RuntimeError('INSTALL_READBACK_FAILED')
    print('[INSTALLED]',TARGET.relative_to(ROOT))
    print('[SHA256]',SHA)
    print('[PRESERVED] scanner 322 / original Q18,Q20,Q25 / 402 / Mriya worker V5')
    print('[BOUNDARY] Indexed prospects only; SDK pool-mint state decoding pending, no automatic admission')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--install',action='store_true');a=p.parse_args()
    if not (a.test or a.install):p.error('Select --test and/or --install')
    if a.test:test()
    if a.install:install()
if __name__=='__main__':main()
