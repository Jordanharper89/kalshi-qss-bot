
from pathlib import Path
import ast, os

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_509_exact_pair_qualification.py')
CORE=Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
SOURCE=r'''
from __future__ import annotations
import argparse, base64, collections, json, math, os, re, time, urllib.error, urllib.parse
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

ROOT=Path('runtime_state/oracle/oracle_live_execution')
SOURCE=ROOT/'oracle_508_mriya_tokens.json'
STATE=ROOT/'oracle_509_checks.json'
REPORT=ROOT/'oracle_509_report.json'
QUALIFIED=ROOT/'oracle_509_qualified_pairs.json'
EXCLUDE={c.WSOL,c.USDC,c.USDT,c.PUMP,c.DLMM,c.TOKEN,c.TOKEN22,c.SYSTEM}
DIRECTIONS=('PUMP_TO_METEORA','METEORA_TO_PUMP')

class PoolSearchHold(ValueError): pass

def load(path):
    if not path.exists():return {}
    obj=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,dict):raise ValueError('INVALID_STATE_JSON')
    return obj

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    try:
        tmp.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding='utf-8')
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def universe(tokens,tape):
    out={}
    for t,v in tokens.items():
        if isinstance(t,str) and len(t)>=32 and isinstance(v,dict):
            out[t]={'token':t,'sources':['MRIYA_COVERAGE']}
    for t,p in tape:
        if not isinstance(t,str) or len(t)<32:continue
        row=out.setdefault(t,{'token':t,'sources':[]})
        if 'LIVE_TAPE' not in row['sources']:row['sources'].append('LIVE_TAPE')
        if isinstance(p,str):row['tape_pool']=p
    return out

def choose(rows,checks,limit,retry=False):
    items=list(rows.values())
    if retry:
        items=[r for r in items if checks.get(r['token'],{}).get('retry') or checks.get(r['token'],{}).get('reason')=='PROBE_HOLD']
    return sorted(items,key=lambda r:(
        float(checks.get(r['token'],{}).get('checked_at',0)),r['token']))[:limit]

def mint(obj):
    if isinstance(obj,str):return obj
    if isinstance(obj,dict):
        return obj.get('address') or obj.get('mint') or obj.get('token_address')
    return None

def pool_candidates(token,fetch,min_tvl,page_size=200,max_pages=6):
    if not 1<=page_size<=1000 or not 1<=max_pages<=12:
        raise ValueError('INVALID_PAGE_BOUNDS')
    found={}
    exhausted=False
    pages_read=0
    for page in range(1,max_pages+1):
        url='https://dlmm.datapi.meteora.ag/pools?'+urllib.parse.urlencode({
            'page':page,'page_size':page_size,'query':token})
        data=fetch(url)
        entries=data.get('data') if isinstance(data,dict) else data
        if not isinstance(entries,list):
            raise PoolSearchHold('METEORA_RESPONSE_SCHEMA_INVALID')
        pages_read+=1
        for item in entries:
            if not isinstance(item,dict):continue
            tx=mint(item.get('token_x') or item.get('tokenX'))
            ty=mint(item.get('token_y') or item.get('tokenY'))
            if {tx,ty}!={token,c.WSOL}:continue
            addr=item.get('address') or item.get('pool_address') or item.get('pubkey')
            if not isinstance(addr,str):continue
            value=item.get('tvl',item.get('liquidity_usd'))
            try:tvl=float(value) if value is not None else None
            except (ValueError,TypeError):tvl=None
            if tvl is not None and (not math.isfinite(tvl) or tvl<0):
                tvl=None
            found[addr]={'address':addr,'token_x':tx,'token_y':ty,'tvl_usd':tvl}
        if len(entries)<page_size:
            exhausted=True
            break
        if any(x['tvl_usd'] is not None and x['tvl_usd']>=min_tvl for x in found.values()):
            break
    ranked=sorted(found.values(),key=lambda x:(
        x['tvl_usd'] is not None,x['tvl_usd'] or 0),reverse=True)
    valid=[x for x in ranked if x['tvl_usd'] is not None and x['tvl_usd']>=min_tvl]
    if valid:return valid[:3],'OK',pages_read
    if not exhausted:
        raise PoolSearchHold('METEORA_SEARCH_PAGE_CAP_INCOMPLETE')
    return [],('LIQUIDITY_METADATA_HOLD' if ranked else 'NO_DLMM_PAIR'),pages_read

def pump_pda(token):
    from solders.pubkey import Pubkey
    base=Pubkey.from_string(token)
    creator,_=Pubkey.find_program_address(
        [b'pool-authority',bytes(base)],Pubkey.from_string(c.PUMP_FUN))
    pool,_=Pubkey.find_program_address(
        [b'pool',(0).to_bytes(2,'little'),bytes(creator),
         bytes(base),bytes(Pubkey.from_string(c.WSOL))],
        Pubkey.from_string(c.PUMP))
    return str(pool)

def verify(token,pump,options,rpc,decode):
    packet=rpc('getMultipleAccounts',[
        [pump]+[x['address'] for x in options],
        {'encoding':'base64','commitment':'confirmed'}])
    vals=packet.get('value') if isinstance(packet,dict) else None
    if not isinstance(vals,list) or len(vals)!=len(options)+1:
        raise ValueError('ACCOUNT_RESPONSE_INVALID')
    p=vals[0]
    if not isinstance(p,dict):return None,'NO_CANONICAL_PUMP_POOL'
    if p.get('owner')!=c.PUMP:return None,'PUMP_OWNER_MISMATCH'
    if p.get('executable'):return None,'PUMP_EXECUTABLE_INVALID'
    try:
        blob=base64.b64decode(p['data'][0],validate=True)
        if len(blob)<203:raise ValueError('PUMP_DATA_SHORT')
        info=decode(blob)
    except (ValueError,TypeError,KeyError,IndexError):
        return None,'PUMP_STATE_INVALID'
    if info.get('base_mint')!=token or info.get('quote_mint')!=c.WSOL:
        return None,'PUMP_TOKEN_MISMATCH'
    for meta,account in zip(options,vals[1:]):
        if not isinstance(account,dict) or account.get('owner')!=c.DLMM or account.get('executable'):
            continue
        try:raw=base64.b64decode(account['data'][0],validate=True)
        except (ValueError,TypeError,KeyError,IndexError):
            continue
        if len(raw)>=8:return meta,'OK'
    return None,'DLMM_OWNER_OR_ACCOUNT_INVALID'

def classify(exc,stage):
    if isinstance(exc,PoolSearchHold):
        return {'reason':str(exc),'retry':True}
    if isinstance(exc,urllib.error.HTTPError):
        code=int(exc.code)
        return {'reason':stage+'_HTTP_'+str(code),
            'http_code':code,'retry':code in (429,500,502,503,504)}
    if isinstance(exc,(TimeoutError,ConnectionError,urllib.error.URLError)):
        return {'reason':stage+'_NETWORK_RETRY','retry':True,
                'error_type':type(exc).__name__}
    m=re.search(r'"code"\s*:\s*(-?\d+)',str(exc))
    if m:
        code=int(m.group(1))
        return {'reason':stage+'_RPC_'+str(code),
                'rpc_code':code,'retry':code in (-32005,-32004,-32016,429)}
    msg=str(exc)
    known=('METEORA_RESPONSE_SCHEMA_INVALID',
           'METEORA_SEARCH_PAGE_CAP_INCOMPLETE','ACCOUNT_RESPONSE_INVALID')
    if msg in known:return {'reason':msg,'retry':True}
    return {'reason':stage+'_ERROR_HOLD',
            'error_type':type(exc).__name__,'retry':True}

def qualify(row,fetch,rpc,derive,decode,min_tvl,validate=None):
    token=row['token']
    if token in EXCLUDE:
        return {'reason':'EXCLUDED_EXACT_ASSET',
                'qualified':False,'retry':False}
    if validate is None:
        from solders.pubkey import Pubkey
        validate=Pubkey.from_string
    try:validate(token)
    except (TypeError,ValueError):
        return {'reason':'INVALID_TOKEN','qualified':False,'retry':False}
    try:options,reason,pages=pool_candidates(token,fetch,min_tvl)
    except Exception as exc:
        return dict(qualified=False,**classify(exc,'METEORA'))
    if not options:
        return {'reason':reason,'qualified':False,
                'retry':False,'pages_checked':pages}
    try:
        for opt in options:validate(opt['address'])
        pump=derive(token)
    except Exception as exc:
        return dict(qualified=False,**classify(exc,'PUMP_DERIVATION'))
    try:selected,reason=verify(token,pump,options,rpc,decode)
    except Exception as exc:
        return dict(qualified=False,**classify(exc,'ACCOUNT'))
    if not selected:
        return {'reason':reason,'qualified':False,'retry':False}
    return {'reason':'API_MATCH_OWNER_VERIFIED','qualified':True,'retry':False,
        'token':token,'pump_pool':pump,
        'meteora_pool':selected['address'],
        'token_x':selected['token_x'],'token_y':selected['token_y'],
        'tvl_usd':selected['tvl_usd'],'sources':row['sources'],
        'pages_checked':pages,
        'source_status':'TAPE_POOL_DIFFERS' if row.get('tape_pool') and row['tape_pool']!=pump else 'OK',
        'directions':list(DIRECTIONS),
        'stage':'API_PAIR_AND_ONCHAIN_OWNERS_ONLY',
        'scanner_admitted':False,'execution_authority':False}

def audit(limit,min_tvl,retry_holds):
    if not SOURCE.exists():raise RuntimeError('ORACLE508_TOKENS_REQUIRED')
    tokens=load(SOURCE)
    tape=c.tape_candidates(Path.cwd())
    current=universe(tokens,tape)
    checks=load(STATE)
    items=choose(current,checks,limit,retry_holds)
    results=[]
    now=time.time()
    for row in items:
        result=qualify(row,c.http,c.rpc,pump_pda,c.decode_pump_pool,min_tvl)
        result.update(token=row['token'],checked_at=time.time())
        checks[row['token']]=result
        results.append(result)
        print('[ORACLE509_CHECK]',json.dumps({
            k:result[k] for k in (
                'token','reason','qualified','retry','rpc_code',
                'http_code','pages_checked') if k in result
        },sort_keys=True),flush=True)
        time.sleep(.2)
    save(STATE,checks)
    live=[v for t,v in checks.items() if t in current and
          v.get('qualified') and now-float(v.get('checked_at',0))<=600]
    save(QUALIFIED,{
        'generated_at':now,'ttl_seconds':600,
        'read_only':True,'signing':False,'broadcast':False,
        'scanner_admitted':False,'qualified_pairs':live})
    reasons=dict(collections.Counter(x['reason'] for x in results))
    holds=sum(bool(x.get('retry')) for x in results)
    outcome={
        'status':'HOLD_TRANSIENT_REQUESTS' if holds else 'PASS_AUDIT',
        'source_mriya_tokens':len(tokens),'source_tape_pairs':len(tape),
        'unique_candidates':len(current),'checked_this_run':len(results),
        'qualified_this_run':sum(bool(x.get('qualified')) for x in results),
        'qualified_fresh_registry':len(live),
        'pending_unchecked':sum(t not in checks for t in current),
        'retry_pending':sum(bool(v.get('retry')) for t,v in checks.items()
                            if t in current),
        'reasons':reasons,
        'read_only':True,'signing':False,'broadcast':False,
        'scanner_admitted':False}
    save(REPORT,outcome)
    print('[ORACLE509]',json.dumps(outcome,sort_keys=True),flush=True)
    print('[REPORT]',REPORT,flush=True)
    if holds:raise SystemExit(2)

def tests():
    x='X'*32
    y='Y'*32
    rows=universe({x:{}},[(x,'P'*32),(y,'Q'*32)])
    assert len(rows)==2 and len(rows[x]['sources'])==2
    assert choose(rows,{x:{'retry':True}},8,True)[0]['token']==x
    def longpage(url):
        page=int(urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query)['page'][0])
        if page==1:
            return {'data':[{'token_x':x,'token_y':y}]*200}
        return {'data':[{'token_x':c.WSOL,'token_y':x,
                        'address':'P'*32,'tvl':500}]}
    result,why,pages=pool_candidates(x,longpage,100)
    assert why=='OK' and pages==2 and result[0]['address']=='P'*32
    assert pool_candidates(x,lambda _: {'data':[]},100)[1]=='NO_DLMM_PAIR'
    try:
        pool_candidates(x,lambda _: {'data':[{}]*200},100,max_pages=2)
    except PoolSearchHold as exc:
        assert str(exc)=='METEORA_SEARCH_PAGE_CAP_INCOMPLETE'
    else:raise AssertionError('UNEXHAUSTED_PAGE_MUST_HOLD')
    try:pool_candidates(x,lambda _: {'unknown':[]},100)
    except PoolSearchHold as exc:
        assert str(exc)=='METEORA_RESPONSE_SCHEMA_INVALID'
    else:raise AssertionError('BAD_SCHEMA_MUST_HOLD')
    assert 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB' not in EXCLUDE
    assert qualify({'token':c.USDT},None,None,None,None,100)['reason']=='EXCLUDED_EXACT_ASSET'
    fake={'owner':c.PUMP,'executable':False,
          'data':[base64.b64encode(bytes(203)).decode(),'base64']}
    dlmm={'owner':c.DLMM,'executable':False,
          'data':['eHh4eHh4eHh4eA==','base64']}
    rpc=lambda *_:{'value':[fake,dlmm]}
    selected,why=verify(
        x,'Z'*32,[{'address':'P'*32}],rpc,
        lambda _:{'base_mint':x,'quote_mint':c.WSOL})
    assert selected is not None and why=='OK'
    selected,why=verify(
        x,'Z'*32,[{'address':'P'*32}],
        lambda *_:{'value':[fake,dict(dlmm,owner='bad')]},
        lambda _:{'base_mint':x,'quote_mint':c.WSOL})
    assert selected is None and why=='DLMM_OWNER_OR_ACCOUNT_INVALID'
    print('[PASS] ORACLE509_V3 pagination exact-mints owner checks failclosed diagnostics')

def main():
    p=argparse.ArgumentParser()
    act=p.add_mutually_exclusive_group(required=True)
    act.add_argument('--test',action='store_true')
    act.add_argument('--audit',action='store_true')
    p.add_argument('--limit',type=int,default=8)
    p.add_argument('--min-tvl-usd',type=float,default=100)
    p.add_argument('--retry-holds',action='store_true')
    args=p.parse_args()
    if args.test:tests();return
    if not 1<=args.limit<=28 or not math.isfinite(args.min_tvl_usd) or args.min_tvl_usd<0:
        p.error('INVALID_BOUNDS')
    audit(args.limit,args.min_tvl_usd,args.retry_holds)

if __name__=='__main__':main()
'''

def main():
    if not TARGET.parent.is_dir() or not CORE.is_file():
        raise SystemExit('HOLD_REPOSITORY_PATH_MISSING')
    text=CORE.read_text(encoding='utf-8')
    if any(v not in text for v in (
        'def decode_pump_pool(', 'def tape_candidates(', 'DLMM=', 'PUMP=')):
        raise SystemExit('HOLD_CORE_CONTRACT_CHANGED')
    ast.parse(SOURCE)
    temp=TARGET.with_name(TARGET.name+'.'+str(os.getpid())+'.tmp')
    try:
        temp.write_text(SOURCE,encoding='utf-8')
        os.replace(temp,TARGET)
    finally:
        if temp.exists():temp.unlink()
    print('[PASS] ORACLE509_V3_FULL_INSTALL SCANNER_UNCHANGED NO_SIGNING NO_BROADCAST')
    print('[INSTALLED]',TARGET)

if __name__=='__main__':main()
