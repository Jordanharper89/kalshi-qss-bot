

"""FINAL BOSS rotation intelligence V3: source provenance and interface certification.

This observer never mutates the frozen scanner.

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
                                             'mriya_observed':False,
                                             'fresh_mriya_sources':set(),'historical_mriya_sources':set()})
                cand['sources'].add(name)
                if fresh:
                    cand['fresh_sources'].add(name)
                    cand['freshest_age_s']=min(cand['freshest_age_s'],age)
                is_mriya=('MRIYA' in name.upper() or 'MRIYA' in str(r.get('source','')).upper())
                cand['mriya_observed']=cand['mriya_observed'] or is_mriya
                if is_mriya:
                    cand['historical_mriya_sources'].add(name)
                    if fresh:cand['fresh_mriya_sources'].add(name)
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
        r['fresh_mriya_sources']=sorted(r['fresh_mriya_sources'])
        r['historical_mriya_sources']=sorted(r['historical_mriya_sources'])
        if r['freshest_age_s']==float('inf'):r['freshest_age_s']=None
    return out,sources,issues

def mriya_live_evidence(root=ROOT,now=None):
    """Correlate actual recent wallet tx tokens to fresh exact-pair identities.

    Never make a historical pool fresh merely because the tracked wallet touched
    its mint: complete pool freshness comes from a different trusted source.
    """
    now=time.time() if now is None else now
    path=root/'runtime_state/oracle/final_boss_dual/mriya_live_sightings.json'
    status={'source':'MRIYA_RPC_PUBLIC_TX','report_present':path.is_file(),
            'verified_recent_mints':0,'fresh_matched_triples':0,
            'unmatched_recent_mints':0,'reason':'MISSING_REPORT'}
    try:
        if path.is_symlink() or path.stat().st_size>2_000_000:raise ValueError('UNTRUSTED_SIGHTINGS_REPORT')
        x=json.loads(path.read_text(encoding='utf-8'))
        if x.get('source')!='MRIYA_WALLET_CONFIRMED_TX' or x.get('wallet')!='MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X':
            raise ValueError('UNTRUSTED_SIGHTINGS_PRODUCER')
        if not 0<=now-float(x['updated_unix'])<=90:raise ValueError('SIGHTINGS_REPORT_STALE')
        rows=x.get('rows') or []
        recent={r['token'] for r in rows if isinstance(r,dict)
                and isinstance(r.get('token'),str) and BASE58.fullmatch(r['token'])
                and type(r.get('slot')) is int and r['slot']>0
                and type(r.get('block_time')) in (int,float)
                and 0<=now-r['block_time']<=180}
        status.update(verified_recent_mints=len(recent),reason='FRESH_EVIDENCE' if recent else 'NO_FRESH_WALLET_MINT_ACTIVITY')
        return recent,status
    except (OSError,KeyError,ValueError,UnicodeError,TypeError) as exc:
        status['reason']='HOLD_'+type(exc).__name__
        return set(),status

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
        x['mriya_priority']=bool(x.get('fresh_mriya_sources'))
        x['historical_mriya_only']=bool(x['mriya_observed']) and not x['mriya_priority']
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

def scanner_interface_audit(root=ROOT):
    """Static AST-only read of original installer; NEVER import or execute scanner.

    Gives function names and line numbers, not source text or environment values.
    Scanner socket lifecycle stays unchanged until real interface is inspected.
    """
    path=root/'build_oracle_322_scanner_isolated_discovery.py'
    if not path.is_file():return {'state':'SCANNER_INSTALLER_MISSING','interfaces':[]}
    try:
        content=path.read_text(encoding='utf-8-sig')
        root_ast=ast.parse(content)
        bodies=[('installer',content)]
        for node in ast.walk(root_ast):
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                if len(node.value.value)<1000:continue
                if any(isinstance(target,ast.Name) and any(token in target.id.upper() for token in ('SOURCE','SCRIPT','CONTENT')) for target in node.targets):
                    bodies.append(('embedded_'+str(len(bodies)),node.value.value))
        markers={'accountSubscribe':'ACCOUNT_SUBSCRIBE',
                 'accountUnsubscribe':'ACCOUNT_UNSUBSCRIBE',
                 'programSubscribe':'PROGRAM_SUBSCRIBE',
                 'programUnsubscribe':'PROGRAM_UNSUBSCRIBE',
                 'live_subscriptions_changed':'SUBSCRIPTION_CHANGE_FLAG',
                 'DISCOVERY_STAGED':'STAGED_DISCOVERY',
                 'subscribe':'SUBSCRIBE_REFERENCE',
                 'unsubscribe':'UNSUBSCRIBE_REFERENCE',
                 'rotate':'ROTATION_REFERENCE',
                 'promote':'PROMOTION_REFERENCE',
                 'scanner.lock':'SINGLE_OWNER_LOCK',
                 'create_task':'TASK_SPAWN'}
        findings=[];functions=[]
        for label,body in bodies:
            try:
                node=ast.parse(body)
                func_nodes=[n for n in ast.walk(node) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
                for fn in func_nodes:
                    if any(x in fn.name.lower() for x in ('discover','candidate','subscribe','unsubscribe','staged','rotate','promot','replenish','refresh','ws','scanner','shard','status')):
                        functions.append({'scope':label,'name':fn.name,'line':fn.lineno,'end':fn.end_lineno})
            except SyntaxError:func_nodes=[]
            for line_no,line in enumerate(body.splitlines(),1):
                # Marker-only output, preventing accidental exposure of source credentials.
                sigs=[v for token,v in markers.items() if token.lower() in line.lower()]
                if not sigs:continue
                containing=[fn for fn in func_nodes if fn.lineno<=line_no<=fn.end_lineno]
                parent=min(containing,key=lambda f:f.end_lineno-f.lineno).name if containing else 'module'
                findings.append({'scope':label,'line':line_no,'function':parent,'signals':sigs[:5]})
        return {'state':'STATIC_SCANNER_INTERFACE_EVIDENCE',
                'scanner_source_sha256':hashlib.sha256(content.encode()).hexdigest(),
                'embedded_bodies':len(bodies)-1,
                'interfaces':findings[:100],'functions':functions[:100],
                'subscribe_references':sum(any('SUBSCRIBE' in s for s in item['signals']) for item in findings),
                'live_subscription_rotation_certified':False}
    except (UnicodeError,OSError,SyntaxError):return {'state':'SCANNER_SOURCE_UNREADABLE','interfaces':[]}

def canonical_bus_health():
    """Read-only check of producer epoch health, independent of status JSON mtime."""
    db=None
    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as m
        db=m.bus()
        status=m.validate_scanner(db)
        return {'checked':True,'ok':status.get('ok') is True,
                'epoch':status.get('epoch'),
                'producer_prefix':str(status.get('producer',''))[:12],
                'reason':str(status.get('reason',''))[:100]}
    except Exception as exc:
        # Only error *types*, never values: exception messages may include RPC secrets.
        return {'checked':False,'ok':False,'reason':'CANONICAL_CHECK_'+type(exc).__name__}
    finally:
        if db is not None:
            try:db.close()
            except Exception:pass

def snapshot(root=ROOT,rpc=None):
    rows,src,issues=load_public_rows(root)
    mriya_mints,mriya_status=mriya_live_evidence(root)
    matched=set()
    for row in rows:
        if row['fresh_sources'] and row['token'] in mriya_mints:
            if 'MRIYA_LIVE_RPC_EVIDENCE' not in row['fresh_mriya_sources']:
                row['fresh_mriya_sources'].append('MRIYA_LIVE_RPC_EVIDENCE')
            row['mriya_observed']=True
            matched.add(row['token'])
    mriya_status['fresh_matched_triples']=sum(bool(r['fresh_sources']) and r['token'] in mriya_mints for r in rows)
    mriya_status['unmatched_recent_mints']=len(mriya_mints-matched)
    sc=scanner_status(root)
    mint_tokens=list(dict.fromkeys(x['token'] for x in sorted((r for r in rows if r['fresh_sources']), key=lambda x:x['freshest_age_s'])))
    codes=rpc.inspect(mint_tokens) if rpc else {t:'HOLD_RPC_NOT_CONFIGURED' for t in mint_tokens}
    ranked=rank(rows,codes,sc)
    return {'build':'FINAL_BOSS_HOT_COLD_ADVISORY_V4','scanner':sc,'sources':src,'mriya_live_evidence':mriya_status,
            'issues':issues,'scanner_source_probe':scanner_source_probe(root),
            'scanner_interface_audit':scanner_interface_audit(root),
            'canonical_bus_health':canonical_bus_health() if root==ROOT else {'checked':False,'ok':False},
            'exact_discovered_triples':len(rows),
            'fresh_exact_triples':sum(bool(x['fresh_sources']) for x in rows),
            'stale_exact_triples':sum(not x['fresh_sources'] for x in rows),
            'mriya_sourced_triples':sum(x['mriya_observed'] for x in ranked),
            'fresh_mriya_triples':sum(x['mriya_priority'] for x in ranked),
            'historical_mriya_only_triples':sum(x['historical_mriya_only'] for x in ranked),
            'fresh_source_files_with_triples':[(k,v.get('triples',0),v.get('age_s')) for k,v in src.items() if v.get('state')=='FRESH' and v.get('triples',0)>0][:20],
            'mriya_source_files':[(k,v.get('state'),v.get('age_s'),v.get('triples',0)) for k,v in src.items() if 'MRIYA' in k.upper() and v.get('triples',0)>0][:20],
            'input_files_present':sum(q.get('state') in ('FRESH','STALE') for q in src.values()),
            'input_files_missing':sum(q.get('state')=='MISSING' for q in src.values()),
            'input_files_with_triples':sum(q.get('triples',0)>0 for q in src.values()),
            'rpc_configured':bool(rpc and rpc.url),
            'provisional_mint_pass_count':sum(x['risk_screened'] for x in ranked),
            'fresh_risk_holds':{code:sum(x['mint_risk']==code and x['inventory_fresh'] for x in ranked) for code in sorted({x['mint_risk'] for x in ranked if x['inventory_fresh']})},
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
        assert rank(rows,{token:'PROVISIONAL_MINT_AUTHORITY_PASS'},{})[0]['mriya_priority'] is True
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
        # An old Mriya record must not grant Mriya priority even if another source is fresh.
        fresh_other=root/'runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json'
        fresh_other.parent.mkdir(parents=True,exist_ok=True)
        fresh_other.write_text(json.dumps({'rows':[{'token':token,'pump_pool':pump,'meteora_pool':dlmm}]}),encoding='utf-8')
        merged,_,_=load_public_rows(root,now=now)
        assert len(merged)==1 and len(merged[0]['fresh_sources'])==1
        witness=rank(merged,{token:'PROVISIONAL_MINT_AUTHORITY_PASS'},{})[0]
        assert witness['mriya_priority'] is False and witness['historical_mriya_only'] is True
        assert witness['admission_basis_sufficient'] is True
        assert scanner_interface_audit(root)['state']=='SCANNER_INSTALLER_MISSING'
        # Extended nested Meteora envelope (seen in physical crosslisting).
        assert len(list(triples({'rows':[{'mint':token,'pump_pool':pump,'meteora':{'pool_address':dlmm}}]})))==1
    # Mriya activity can prioritize a known fresh triple, never renew a stale pool.
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);f=root/'runtime_state/oracle/final_boss_dual/mriya_live_sightings.json';f.parent.mkdir(parents=True)
        now=time.time();token='A'*43
        f.write_text(json.dumps({'source':'MRIYA_WALLET_CONFIRMED_TX',
                  'wallet':'MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X',
                  'updated_unix':now,'rows':[{'token':token,'slot':123,'block_time':now-20}]}))
        mints,status=mriya_live_evidence(root,now)
        assert token in mints and status['verified_recent_mints']==1
        old,hold=mriya_live_evidence(root,now+200)
        assert not old and hold['reason'].startswith('HOLD_')
        other=root/'runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json';other.parent.mkdir(parents=True)
        other.write_text(json.dumps({'rows':[{'token':token,'pump_pool':'B'*43,'meteora_pool':'C'*43}]}))
        live=snapshot(root)
        assert live['fresh_mriya_triples']==1 and live['mriya_live_evidence']['fresh_matched_triples']==1
        os.utime(other,(now-700,now-700))
        old=snapshot(root)
        assert old['fresh_mriya_triples']==0
    print('[PASS] HOT_COLD V4 recent wallet provenance, no stale identity renewal, canonical health, no scanner mutation')
    print('[SCOPE] Planner only. Live same-socket scanner rotation not yet certified.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--observe',action='store_true')
    ap.add_argument('--seconds',type=int,default=120);ap.add_argument('--rpc-risk',action='store_true');ap.add_argument('--interval',type=int,default=15);ap.add_argument('--interface',action='store_true')
    args=ap.parse_args()
    if args.test:tests();return 0
    if args.interface:
        report=scanner_interface_audit(ROOT)
        p=STATE/'scanner_interface_audit.json';STATE.mkdir(parents=True,exist_ok=True)
        save_report=report.copy()
        with tempfile.NamedTemporaryFile('w',dir=STATE,encoding='utf-8',delete=False,suffix='.tmp') as f:
            temp=f.name;json.dump(save_report,f,indent=2,sort_keys=True)
        os.replace(temp,p)
        print('[SCANNER_INTERFACE_AUDIT]',json.dumps(report,sort_keys=True),flush=True)
        print('[REPORT]',p.relative_to(ROOT),flush=True);return 0
    if not args.observe:ap.error('Use --test, --interface, or --observe')
    if not 1<=args.seconds<=3600 or not 10<=args.interval<=300:ap.error('invalid interval/seconds')
    url=os.environ.get('SOLANA_RPC_URL','') if args.rpc_risk else ''
    if url and not url.startswith('https://'):url=''
    rpc=PacedMintRPC(url,interval_s=max(20,args.interval))
    start=time.monotonic()
    while True:
        data=snapshot(ROOT,rpc)
        path=save(data)
        print('[FINAL_BOSS_ROTATION_ADVISORY]',json.dumps({k:data[k] for k in ('status','scanner','exact_discovered_triples','fresh_exact_triples','stale_exact_triples','mriya_sourced_triples','fresh_mriya_triples','historical_mriya_only_triples','mriya_live_evidence','fresh_source_files_with_triples','canonical_bus_health','input_files_present','input_files_missing','input_files_with_triples','rpc_configured','provisional_mint_pass_count','fresh_risk_holds','hot_proposals','rotation_applied','rpc_stats')},sort_keys=True),flush=True)
        if time.monotonic()-start>=args.seconds:break
        time.sleep(min(args.interval,max(0,args.seconds-(time.monotonic()-start))))
    print('[REPORT]',path.relative_to(ROOT),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())

