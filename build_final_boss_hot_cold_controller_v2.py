"""Full replacement installer: Final Boss hot/cold intake V2.
READ-ONLY advisory module. No scanner, sockets, or executor modification.
"""
from __future__ import annotations
import argparse, ast, hashlib, os, tempfile
from pathlib import Path

ROOT=Path.cwd()
TARGET=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_rotation_controller.py'
PREV_SHA256='60a039f7fa06929a77a1a2255031d113994c756a42134ab16e55de1384383609'
SOURCE = r'''

"""FINAL BOSS rotation intelligence: advisory only, never mutates frozen scanner.

Potential hot promotions MUST be separately enacted by verified scanner lifecycle.
The only authority for execution remains a fresh canonical scanner event and a
fully certified native simulation. This module never signs or broadcasts.
"""
from __future__ import annotations
import argparse, ast, collections, hashlib, json, os, re, tempfile, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'runtime_state/oracle/final_boss_dual'
OUTPUT = STATE / 'rotation_advisory.json'
BASE58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SPL = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
T22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
PATHS = (
 ('MRIYA_EXACT','runtime_state/qseries/qarb_clean_bot/mriya_dynamic_exact_bindings.json'),
 ('MRIYA_ACTIVE','runtime_state/qseries/qarb_clean_bot/mriya_dynamic_active_bindings.json'),
 ('MRIYA_ORIGINAL','runtime_state/qseries/qarb_clean_bot/mriya_exact_pump_meteora_bindings.json'),
 ('MRIYA_PRIORITY','runtime_state/oracle/solana_atomic_executor/mriya_replenishment_priority.json'),
 ('MRIYA_REGISTRY','runtime_state/qseries/qarb_clean_bot/mriya_dynamic_token_registry.json'),
 ('UNIVERSAL','runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json'),
 ('NATIVE_147','runtime_state/oracle/oracle_live_execution/ORACLE_147_WALLET_TEMPLATE_REPORT.json'),
 ('HYDRATION_025','runtime_state/oracle/oracle_live_execution/oracle_025_single_hydration_exact_live_reuse.json'),
)
SEARCH_DIRS = (
 'runtime_state/oracle/oracle_live_execution',
 'runtime_state/oracle/solana_atomic_executor',
 'runtime_state/qseries/qarb_clean_bot',
 'runtime_state/oracle/final_boss_dual',
)
SOURCE_NAME = re.compile(r'(?i)(mriya|crosslist|discover|inventory|warm.*pair|pair.*(list|registry|binding)|exact.*binding)')
EXCLUDE_NAME = re.compile(r'(?i)(secret|private|keystore|wallet|keypair|rotation_advisory|oracle_402_source_first_handoff)')
FRESH_WINDOW=600.0
MAX_PAIRS=28

def value(item, *keys):
    for k in keys:
        v=item.get(k)
        if isinstance(v,dict):
            v=next((v[q] for q in ('address','pubkey','pool_address','pool','mint','id')
                    if isinstance(v.get(q),str) and v.get(q)),None)
        if isinstance(v,str) and v:return v
    return None

def triples(data, limit=12000):
    """Never infer a pool identity from a token alone or a partial pubkey."""
    queue=[data];count=0
    while queue and count<limit:
        obj=queue.pop();count+=1
        if isinstance(obj,dict):
            t=value(obj,'token','mint','token_mint','token_address','mint_address')
            p=value(obj,'pump_pool','pumpswap_pool','pump','pump_address')
            m=value(obj,'meteora_pool','dlmm_pool','meteora','dlmm','meteora_address')
            if all(isinstance(x,str) and BASE58.fullmatch(x) for x in (t,p,m)):
                yield t,p,m,obj
            queue.extend(x for x in obj.values() if isinstance(x,(dict,list)))
        elif isinstance(obj,list):queue.extend(x for x in obj if isinstance(x,(dict,list)))

def public_inputs(root=ROOT):
    """Known source files plus bounded discovery of public inventory JSON.

    File discovery is intentionally shallow, does not inspect wallet/secrets files,
    and never treats an unknown JSON source as an executable authorization.
    """
    seen=set();inputs=[]
    for name,rel in PATHS:
        rel=Path(rel).as_posix()
        if rel not in seen:seen.add(rel);inputs.append((name,rel))
    for directory in SEARCH_DIRS:
        folder=root/directory
        if not folder.is_dir():continue
        found=[]
        try:
            for f in folder.glob('*.json'):
                if not SOURCE_NAME.search(f.name) or EXCLUDE_NAME.search(f.name):continue
                if f.is_symlink() or not f.is_file():continue
                if f.stat().st_size>8_000_000:continue
                found.append(f)
        except OSError:continue
        found.sort(key=lambda f:f.stat().st_mtime,reverse=True)
        for f in found[:40]:
            rel=f.relative_to(root).as_posix()
            if rel in seen:continue
            seen.add(rel);inputs.append(('AUTO_'+f.name[:48],rel))
    return inputs

def schema_of(obj):
    # Disclose schema keys and counts, never source values, credentials or RPC URLs.
    if isinstance(obj,dict):
        return {'type':'object','top_keys':sorted(str(k)[:60] for k in obj)[:28],
                'list_keys':{str(k)[:60]:len(v) for k,v in obj.items() if isinstance(v,list)}}
    if isinstance(obj,list):return {'type':'list','count':len(obj)}
    return {'type':type(obj).__name__}

def load_public_rows(root=ROOT, now=None):
    now=time.time() if now is None else now
    combined={};sources={};issues=[]
    for name,rel in public_inputs(root):
        f=root/rel
        if not f.is_file():
            sources[name]={'state':'MISSING','path':rel};continue
        try:
            if f.is_symlink():raise ValueError('SYMLINK_SOURCE_UNTRUSTED')
            size=f.stat().st_size
            if size>8_000_000:raise ValueError('SOURCE_TOO_LARGE')
            age=max(0.,now-f.stat().st_mtime)
            data=json.loads(f.read_text(encoding='utf-8-sig'))
            rows=list(triples(data))
            fresh=age<=FRESH_WINDOW
            sources[name]={'state':('FRESH' if fresh else 'STALE'),
                           'path':rel,'age_s':round(age,1),'triples':len(rows),
                           'schema':schema_of(data),
                           'note':('NO_COMPLETE_TRIPLES_IN_SOURCE' if not rows else 'COMPLETE_TRIPLES_PRESENT')}
            for t,p,m,r in rows:
                key=(t,p,m)
                cand=combined.setdefault(key,{'token':t,'pump_pool':p,'meteora_pool':m,
                                             'sources':set(),'fresh_sources':set(),
                                             'freshest_age_s':float('inf'),'activity_hint':0.0,
                                             'mriya_observed':False})
                cand['sources'].add(name)
                if fresh:
                    cand['fresh_sources'].add(name)
                    cand['freshest_age_s']=min(cand['freshest_age_s'],age)
                cand['mriya_observed']=cand['mriya_observed'] or 'MRIYA' in name.upper() or 'MRIYA' in str(r.get('source','')).upper()
                for field in ('pump_activity','activity','recent_transactions','touches'):
                    v=r.get(field)
                    if fresh and type(v) in (int,float):
                        cand['activity_hint']=max(cand['activity_hint'],max(0.,min(float(v),1e8)))
        except (OSError,ValueError,UnicodeError,TypeError) as exc:
            sources[name]={'state':'UNREADABLE','path':rel,'reason':type(exc).__name__}
            issues.append(name+'_UNREADABLE')
    out=list(combined.values())
    for r in out:
        r['sources']=sorted(r['sources']);r['fresh_sources']=sorted(r['fresh_sources'])
        if r['freshest_age_s']==float('inf'):r['freshest_age_s']=None
    return out,sources,issues

def mint_verdict(acc):
    if not isinstance(acc,dict):return 'HOLD_MINT_ACCOUNT_MISSING'
    owner=acc.get('owner')
    if owner==T22:return 'HOLD_TOKEN2022_EXTENSION_AUDIT_REQUIRED'
    if owner!=SPL:return 'HOLD_UNKNOWN_MINT_OWNER'
    d=acc.get('data')
    if not isinstance(d,dict):return 'HOLD_MINT_PARSING_UNAVAILABLE'
    parsed=d.get('parsed')
    if not isinstance(parsed,dict) or parsed.get('type')!='mint':return 'HOLD_NOT_PARSED_MINT'
    info=parsed.get('info')
    if not isinstance(info,dict) or info.get('isInitialized') is not True:return 'HOLD_UNINITIALIZED_MINT'
    if 'mintAuthority' not in info or 'freezeAuthority' not in info:return 'HOLD_AUTHORITY_FIELDS_MISSING'
    if info.get('mintAuthority') is not None:return 'HOLD_MINT_AUTHORITY_ACTIVE'
    if info.get('freezeAuthority') is not None:return 'HOLD_FREEZE_AUTHORITY_ACTIVE'
    return 'PROVISIONAL_MINT_AUTHORITY_PASS'

class PacedMintRPC:
    def __init__(self,url,interval_s=20):
        self.url=url;self.interval_s=max(10,int(interval_s));self.next_at=0.;self.cache={};self.stats=collections.Counter()
    def inspect(self,tokens,now=None):
        now=time.time() if now is None else now
        result={t:self.cache[t][1] for t in tokens if t in self.cache and self.cache[t][0]>now}
        pending=[t for t in tokens if t not in result]
        if not pending:return result
        if not self.url:
            for t in pending:result[t]='HOLD_RPC_NOT_CONFIGURED'
            return result
        if now<self.next_at:
            for t in pending:result[t]='HOLD_RPC_PACING_WINDOW'
            return result
        batch=pending[:min(40,len(pending))]
        self.next_at=now+self.interval_s
        packet=json.dumps({'jsonrpc':'2.0','id':1,'method':'getMultipleAccounts',
                           'params':[batch,{'encoding':'jsonParsed','commitment':'confirmed'}]}).encode()
        try:
            req=urllib.request.Request(self.url,packet,{'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req,timeout=8) as resp:
                body=resp.read(2_000_000)
            payload=json.loads(body)
            vals=(payload.get('result') or {}).get('value')
            if not isinstance(vals,list) or len(vals)!=len(batch):raise ValueError('RPC_RESPONSE_UNEXPECTED')
            for token,acc in zip(batch,vals):
                code=mint_verdict(acc)
                result[token]=code;self.cache[token]=(now+min(300,self.interval_s*8),code)
            self.stats['rpc_calls']+=1
        except urllib.error.HTTPError as exc:
            self.stats['http_'+str(exc.code)]+=1
            if exc.code==429:
                try:delay=int(exc.headers.get('Retry-After','30'))
                except ValueError:delay=30
                self.next_at=now+max(30,min(600,delay))
            for token in batch:result[token]='HOLD_RPC_RATE_LIMIT_OR_ERROR'
        except (OSError,ValueError,UnicodeError):
            self.stats['rpc_failure']+=1
            for token in batch:result[token]='HOLD_RPC_RATE_LIMIT_OR_ERROR'
        for token in pending[len(batch):]:result[token]='HOLD_RPC_BUDGET_DEFERRED'
        return result

def scanner_status(root=ROOT,now=None):
    now=time.time() if now is None else now
    path=root/'runtime_state/oracle/final_boss_dual/scanner_status.json'
    try:
        age=max(0.,now-path.stat().st_mtime)
        obj=json.loads(path.read_text(encoding='utf-8'))
        if type(obj)!=dict:raise ValueError('BAD_JSON')
        return {'live':age<=15 and obj.get('status')=='RUNNING',
                'status':str(obj.get('status','UNKNOWN'))[:50],
                'age_s':round(age,2),'admitted':obj.get('admitted'),
                'epoch':obj.get('epoch')}
    except (OSError,ValueError,UnicodeError):return {'live':False,'status':'MISSING_OR_UNREADABLE'}

def rank(rows,risks,scanner):
    items=[]
    for r in rows:
        x=dict(r)
        x['mint_risk']=risks.get(x['token'],'HOLD_NO_MINT_EVIDENCE')
        x['risk_screened']=x['mint_risk']=='PROVISIONAL_MINT_AUTHORITY_PASS'
        x['inventory_fresh']=bool(x['fresh_sources'])
        x['admission_basis_sufficient']=x['inventory_fresh'] and x['risk_screened']
        # Mriya is a signal to investigate, never authorization to execute.
        x['mriya_priority']=bool(x['mriya_observed'])
        age=x['freshest_age_s']
        x['priority_score']=round((60 if x['mriya_priority'] else 25)+
                  min(20,max(0,x['activity_hint'])**.25)+(max(0,20-age/30) if age is not None else 0),2)
        items.append(x)
    items.sort(key=lambda r:(not r['admission_basis_sufficient'],-r['priority_score'],r['token']))
    approved=[x for x in items if x['admission_basis_sufficient']][:MAX_PAIRS]
    for idx,x in enumerate(items):
        x['tier']='HOT_PROPOSAL' if x in approved else ('COLD_HOLD' if not x['admission_basis_sufficient'] else 'ACTIVE_RESERVE')
        x['live_subscription_confirmed']=False
        x['execution_authorized']=False
        # A separate exact scanner subscription+event witness is mandatory.
    return items

def scanner_source_probe(root=ROOT):
    """Static evidence only; never import/execute the scanner installer."""
    f=root/'build_oracle_322_scanner_isolated_discovery.py'
    if not f.is_file():return {'state':'SCANNER_INSTALLER_NOT_PRESENT'}
    try:
        s=f.read_text(encoding='utf-8')
        tree=ast.parse(s)
        bodies=[('installer',s)]
        # Installers in this repo may contain an embedded SOURCE or TARGET_SOURCE.
        for n in ast.walk(tree):
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
                if any(isinstance(t,ast.Name) and ('SOURCE' in t.id or 'SCANNER' in t.id) for t in n.targets):
                    if len(n.value.value)>500:bodies.append(('embedded_source',n.value.value))
        matches=[]
        for label,body in bodies:
            for i,line in enumerate(body.splitlines(),1):
                if any(t in line.lower() for t in ('discovery_staged','accountunsubscribe','accountsubscribe','subscription_changed','rotate_hot','rotate_cold')):
                    matches.append({'scope':label,'line':i,'signal':next(t for t in ('discovery_staged','accountunsubscribe','accountsubscribe','subscription_changed','rotate_hot','rotate_cold') if t in line.lower())})
        return {'state':'STATIC_PROBE_ONLY',
                'sha256':hashlib.sha256(s.encode()).hexdigest(),
                'embedded_sources':len(bodies)-1,
                'candidate_rotation_signals':matches[:40],
                'live_rotation_certified':False}
    except (OSError,SyntaxError,UnicodeError):return {'state':'SCANNER_INSTALLER_UNREADABLE'}

def snapshot(root=ROOT,rpc=None):
    rows,src,issues=load_public_rows(root)
    sc=scanner_status(root)
    mint_tokens=list(dict.fromkeys(x['token'] for x in sorted((r for r in rows if r['fresh_sources']), key=lambda x:x['freshest_age_s'])))
    codes=rpc.inspect(mint_tokens) if rpc else {t:'HOLD_RPC_NOT_CONFIGURED' for t in mint_tokens}
    ranked=rank(rows,codes,sc)
    return {'build':'FINAL_BOSS_HOT_COLD_ADVISORY','scanner':sc,'sources':src,
            'issues':issues,'scanner_source_probe':scanner_source_probe(root),
            'exact_discovered_triples':len(rows),
            'fresh_exact_triples':sum(bool(x['fresh_sources']) for x in rows),
            'stale_exact_triples':sum(not x['fresh_sources'] for x in rows),
            'mriya_sourced_triples':sum(x['mriya_priority'] for x in ranked),
            'input_files_present':sum(q.get('state') in ('FRESH','STALE') for q in src.values()),
            'input_files_missing':sum(q.get('state')=='MISSING' for q in src.values()),
            'input_files_with_triples':sum(q.get('triples',0)>0 for q in src.values()),
            'rpc_configured':bool(rpc and rpc.url),
            'provisional_mint_pass_count':sum(x['risk_screened'] for x in ranked),
            'hot_proposals':sum(x['tier']=='HOT_PROPOSAL' for x in ranked),
            'rpc_stats':dict(rpc.stats) if rpc else {},
            'rotation_applied':False,'subscriber_mutations':0,'additional_websockets':0,
            'scanner_source_modified':False,'private_key_used':False,
            'signing':False,'broadcast':False,'execution_authorized':False,
            'status':('HOLD_NO_COMPLETE_TRIPLES_IN_DISCOVERY_FILES' if not rows else 'HOLD_SCANNER_SUBSCRIPTION_ROTATION_NOT_WIRED'),
            'note':'Advisory only; scanner status contains counts, not verified identities. Never claim hot/cold rotation.',
            'rows':ranked[:100]}

def save(data,root=ROOT):
    target=root/'runtime_state/oracle/final_boss_dual/rotation_advisory.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=target.parent,encoding='utf-8',delete=False,suffix='.tmp') as f:
        name=f.name;json.dump(data,f,indent=2,sort_keys=True)
    os.replace(name,target)
    return target

def tests():
    good={'owner':SPL,'data':{'parsed':{'type':'mint','info':{'isInitialized':True,'mintAuthority':None,'freezeAuthority':None}}}}
    assert mint_verdict(good)=='PROVISIONAL_MINT_AUTHORITY_PASS'
    assert mint_verdict(dict(good,owner=T22))=='HOLD_TOKEN2022_EXTENSION_AUDIT_REQUIRED'
    incomplete=json.loads(json.dumps(good));del incomplete['data']['parsed']['info']['freezeAuthority']
    assert mint_verdict(incomplete)=='HOLD_AUTHORITY_FIELDS_MISSING'
    bad=json.loads(json.dumps(good));bad['data']['parsed']['info']['freezeAuthority']='test'
    assert mint_verdict(bad)=='HOLD_FREEZE_AUTHORITY_ACTIVE'
    token='A'*43;pump='B'*43;dlmm='C'*43
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);rel=PATHS[0][1];f=root/rel;f.parent.mkdir(parents=True)
        f.write_text(json.dumps({'rows':[{'token':token,'pump_pool':pump,'meteora_pool':dlmm,'source':'MRIYA_HOT'}]}))
        rows,sources,_=load_public_rows(root)
        assert len(rows)==1 and rows[0]['sources']==['MRIYA_EXACT']
        assert rank(rows,{token:'PROVISIONAL_MINT_AUTHORITY_PASS'},{})[0]['tier']=='HOT_PROPOSAL'
        assert rank(rows,{token:'HOLD_RPC_NOT_CONFIGURED'},{})[0]['tier']=='COLD_HOLD'
        assert list(triples({'token':token,'pump_pool':pump}))==[]
        assert scanner_status(root)['live'] is False
        assert scanner_source_probe(root)['state']=='SCANNER_INSTALLER_NOT_PRESENT'
        save(snapshot(root),root)
        assert json.loads((root/'runtime_state/oracle/final_boss_dual/rotation_advisory.json').read_text())['rotation_applied'] is False
        # Counterexample: an old file with valid keys cannot become HOT or get RPC screening.
        now=time.time()
        os.utime(f,(now-700,now-700))
        stale_rows,stale_src,_=load_public_rows(root,now=now)
        assert len(stale_rows)==1 and not stale_rows[0]['fresh_sources']
        assert stale_src['MRIYA_EXACT']['state']=='STALE'
        assert rank(stale_rows,{token:'PROVISIONAL_MINT_AUTHORITY_PASS'},{})[0]['tier']=='COLD_HOLD'
        # Extended nested Meteora envelope (seen in physical crosslisting).
        assert len(list(triples({'rows':[{'mint':token,'pump_pool':pump,'meteora':{'pool_address':dlmm}}]})))==1
    print('[PASS] HOT_COLD v2 source visibility, Mriya triples, stale holds, RPC screening, no scanner mutation')
    print('[SCOPE] Planner only. Live same-socket scanner rotation not yet certified.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--observe',action='store_true')
    ap.add_argument('--seconds',type=int,default=120);ap.add_argument('--rpc-risk',action='store_true');ap.add_argument('--interval',type=int,default=15)
    args=ap.parse_args()
    if args.test:tests();return 0
    if not args.observe:ap.error('Use --test or --observe')
    if not 1<=args.seconds<=3600 or not 10<=args.interval<=300:ap.error('invalid interval/seconds')
    url=os.environ.get('SOLANA_RPC_URL','') if args.rpc_risk else ''
    if url and not url.startswith('https://'):url=''
    rpc=PacedMintRPC(url,interval_s=max(20,args.interval))
    start=time.monotonic()
    while True:
        data=snapshot(ROOT,rpc)
        path=save(data)
        print('[FINAL_BOSS_ROTATION_ADVISORY]',json.dumps({k:data[k] for k in ('status','scanner','exact_discovered_triples','fresh_exact_triples','stale_exact_triples','mriya_sourced_triples','input_files_present','input_files_missing','input_files_with_triples','rpc_configured','provisional_mint_pass_count','hot_proposals','rotation_applied','rpc_stats')},sort_keys=True),flush=True)
        if time.monotonic()-start>=args.seconds:break
        time.sleep(min(args.interval,max(0,args.seconds-(time.monotonic()-start))))
    print('[REPORT]',path.relative_to(ROOT),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())

'''

def normalized(data):
    return data.replace(b'\r\n',b'\n')

def digest(data):
    return hashlib.sha256(normalized(data)).hexdigest()

def test():
    ast.parse(SOURCE)
    safe="'rotation_applied':False" in SOURCE and "'subscriber_mutations':0" in SOURCE
    assert safe and "'additional_websockets':0" in SOURCE
    assert "'signing':False" in SOURCE and "'broadcast':False" in SOURCE
    assert 'def public_inputs(' in SOURCE and 'getMultipleAccounts' in SOURCE
    assert not any(s in SOURCE for s in ('sendTransaction','sendRawTransaction','send_raw_transaction'))
    print('[PASS] ROTATION_V2_INSTALLER syntax, source diagnostics, stale holds, no scanner mutation')

def install():
    test()
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    desired=SOURCE.encode('utf-8')
    if TARGET.exists():
        raw=TARGET.read_bytes()
        existing=digest(raw)
        if existing==digest(desired):
            print('[PASS] ROTATION_V2_ALREADY_INSTALLED');return
        if existing!=PREV_SHA256:
            raise SystemExit('[HOLD] UNRECOGNIZED_CONTROLLER_SOURCE_NOT_OVERWRITTEN sha256='+existing)
        folder=ROOT/'runtime_state/oracle/final_boss_dual'
        folder.mkdir(parents=True,exist_ok=True)
        backup=folder/('rotation_controller_before_v2_'+existing[:16]+'.bak')
        if backup.exists() and backup.read_bytes()!=raw:
            raise SystemExit('[HOLD] BACKUP_COLLISION_NOT_OVERWRITTEN')
        if not backup.exists():
            with backup.open('xb') as fh:fh.write(raw)
        assert backup.read_bytes()==raw
        print('[EXACT_BACKUP]',backup.relative_to(ROOT))
    with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False,suffix='.tmp') as f:
        tmp=Path(f.name);f.write(desired)
    try:os.replace(tmp,TARGET)
    finally:tmp.unlink(missing_ok=True)
    assert digest(TARGET.read_bytes())==digest(desired)
    print('[REPLACED_CONTROLLER]',TARGET.relative_to(ROOT))
    print('[SHA256]',digest(desired))
    print('[PRESERVED] ORACLE-322, Q18/Q20/Q25, ORACLE-402, scanner lock, WebSockets')
    print('[MODE] SAFE_DISCOVERY_EVIDENCE_ONLY, NO_SUBSCRIPTION_ROTATION, NO_SIGNING_OR_BROADCAST')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    action=ap.add_mutually_exclusive_group(required=True)
    action.add_argument('--test',action='store_true')
    action.add_argument('--install',action='store_true')
    args=ap.parse_args()
    if args.test:test()
    else:install()
