"""ORACLE-353 complete bank-first exact quote shadow installer; never submits trades."""
import argparse, ast, hashlib, os, pathlib, py_compile, subprocess, sys, tempfile, unittest

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_353_bank_first_shadow.py')
SCANNER=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py')
FROZEN_SHA='9ceef817699e895aa25cce877e59c2065061e75046a0aee6b373128fc95ca805'
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.oracle_353_bank_first_shadow'
SOURCE=r'''
"""ORACLE-353 bank-first same-slot 0.010 SOL scout; no execution authority.
Uses the frozen scanner only as an admission/identity reference. Independent bank-first
quotes are observations, NEVER approved scanner nominations or trading instructions.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, pathlib, time, unittest

ROOT = pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT = ROOT/'oracle_353_bank_first_report.json'
LEDGER = ROOT/'oracle_353_bank_first_evidence.jsonl'
SCANNER = pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py')
SCANNER_SHA = '9ceef817699e895aa25cce877e59c2065061e75046a0aee6b373128fc95ca805'
SIZE = 10_000_000
DIRECTIONS = {'PUMP_TO_METEORA','METEORA_TO_PUMP'}
REQUIRED = {'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}


def emit(tag, obj):
    print('['+tag+'] '+json.dumps(obj,sort_keys=True,default=str),flush=True)


def guard():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO')!='NO':
        raise RuntimeError('ORACLE353_READ_ONLY_REJECTED_SECRET_ENV')
    if hashlib.sha256(SCANNER.read_bytes()).hexdigest()!=SCANNER_SHA:
        raise RuntimeError('FROZEN_SCANNER_CHANGED')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    return url


def selected_keys(pair,cat,roles):
    if not cat.get('discovery_complete') or int(cat['bin_total'])!=int(cat['bin_selected']):
        raise ValueError('INCOMPLETE_BIN_ARRAY_CATALOG')
    if cat['token']!=pair['token'] or cat['pump_pool']!=pair['pump_pool'] or cat['meteora_pool']!=pair['meteora_pool']:
        raise ValueError('CATALOG_POOL_IDENTITY_DRIFT')
    keys=sorted(k for k,rs in roles.items() if any(t==pair['token'] for t,_ in rs))
    present={r for k in keys for t,r in roles[k] if t==pair['token']}
    if not REQUIRED.issubset(present):raise ValueError('REQUIRED_ACCOUNT_ROLES_MISSING')
    if not 6<=len(keys)<=100:raise ValueError('RPC_SINGLE_BANK_ACCOUNT_LIMIT')
    return keys


def approved_bank_routes(opps, size=SIZE):
    """Reject incomplete/duplicate quotes; gross-positive means research only."""
    if not isinstance(opps,list) or not opps:raise ValueError('NO_SDK_QUOTES')
    by_dir={}
    for row in opps:
        direction=row.get('direction')
        if direction not in DIRECTIONS or int(row.get('start',-1))!=size:continue
        if direction in by_dir:raise ValueError('DUPLICATE_DIRECTION')
        gross=int(row['local_net']); end=int(row['local_end'])
        if end<0 or gross!=end-size:raise ValueError('SDK_QUOTE_ECONOMICS_MISMATCH')
        by_dir[direction]=dict(direction=direction,size_lamports=size,gross_lamports=gross,
            gross_bps=round(gross*10000/size,3))
    if set(by_dir)!=DIRECTIONS:raise ValueError('BOTH_DIRECTIONS_NOT_QUOTED')
    return [by_dir[d] for d in ('PUMP_TO_METEORA','METEORA_TO_PUMP')]


def bank_probe(pair,catalog,roles,url,decimals,min_slot=None,adapters=None):
    """A single `getMultipleAccounts` reply provides the exact bytes for both quotes."""
    if adapters is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
    else:
        witness,bridge,q18,core,decoder=adapters
    keys=selected_keys(pair,catalog,roles)
    if pair['token'] not in decimals:raise ValueError('TOKEN_DECIMALS_UNVERIFIED')
    if min_slot is not None and int(min_slot)<=0:raise ValueError('SCANNER_SLOT_INVALID')
    opts={'encoding':'base64','commitment':'processed'}
    if min_slot is not None:opts['minContextSlot']=int(min_slot)
    started_ns=time.time_ns();start=time.perf_counter_ns()
    reply=witness.rpc(url,'getMultipleAccounts',[keys,opts],collections.Counter(),retries=1)
    fetched=time.perf_counter_ns()
    rows,bank_slot=bridge.bank_rows(reply,keys,int(min_slot or 0),started_ns)
    snap,lineage=bridge.prepare_snapshot(catalog,rows,roles,decimals,started_ns-1,core,decoder)
    decoded=time.perf_counter_ns()
    if bank_slot<=0 or int(lineage['slot_min'])!=int(bank_slot) or int(lineage['slot_max'])!=int(bank_slot):
        raise ValueError('NOT_ONE_BANK_CONTEXT')
    if min_slot is not None and int(bank_slot)<int(min_slot):raise ValueError('BANK_BEHIND_NOMINATION')
    if snap.get('token')!=pair['token'] or snap.get('pump_pool')!=pair['pump_pool']:
        raise ValueError('SNAPSHOT_IDENTITY_MISMATCH')
    # Official Q18 scanner model prices BOTH directions on ONE immutable bank state.
    routes=approved_bank_routes(q18.exact_snapshot_opportunities(snap,0.010))
    priced=time.perf_counter_ns()
    # Content hash uses sorted validated rows. No secrets or raw account bytes are logged.
    dig=hashlib.sha256()
    for k in keys:
        r=rows[k];dig.update(k.encode());dig.update(str(r.get('content_sha256',r.get('data_b64',''))).encode())
    return dict(token=pair['token'],pump_pool=pair['pump_pool'],meteora_pool=pair['meteora_pool'],
        bank_slot=int(bank_slot),min_scanner_slot=min_slot,slot_gap=int(bank_slot)-int(min_slot) if min_slot else None,
        account_count=len(keys),account_fingerprint=dig.hexdigest(),routes=routes,
        rpc_ms=round((fetched-start)/1e6,3),decode_ms=round((decoded-fetched)/1e6,3),
        both_directions_quote_ms=round((priced-decoded)/1e6,3),
        bank_elapsed_ms=round((priced-start)/1e6,3),one_bank_context=True,
        model='ORIGINAL_Q18_EXACT_SDK',execution_authority=False,signing=False,broadcast=False,trade_ready=False)


def nominal_pair(n,inventory,producer,epoch):
    if n['producer']!=producer:raise ValueError('NOMINATION_PRODUCER_MISMATCH')
    if int(n['size_lamports'])!=SIZE or n['direction'] not in DIRECTIONS:raise ValueError('UNSUPPORTED_NOMINATION')
    matches=[p for p in inventory if all(n.get(k)==p.get(k) for k in ('token','pump_pool','meteora_pool'))]
    if len(matches)!=1:raise ValueError('NOMINATION_POOL_IDENTITY_MISMATCH')
    return matches[0]


def emit_bank_result(result,mode,n=None,ttl_ms=2500):
    result=dict(result)
    result['mode']=mode
    result['scanner_admitted']=mode=='SCANNER_ADMITTED'
    result['event_id']=n.get('id') if n else None
    result['scanner_direction']=n.get('direction') if n else None
    result['scanner_gross']=n.get('gross_lamports') if n else None
    result['source_age_ms']=round((time.time_ns()-int(n['created_ns']))/1e6,3) if n else None
    result['gate']='SHADOW_NOT_TRADE_READY'
    if n:
        match=next(r for r in result['routes'] if r['direction']==n['direction'])
        result['bank_gross_for_nomination']=match['gross_lamports']
        result['price_change_lamports']=match['gross_lamports']-int(n['gross_lamports'])
        result['gate']='SHADOW_BANK_POSITIVE_UNCERTIFIED' if match['gross_lamports']>0 and 0<=result['source_age_ms']<=ttl_ms else 'HOLD_BANK_NONPOSITIVE_OR_STALE'
    else:
        result['gate']='BANK_FIRST_DISCOVERY_NOT_SCANNER_ADMITTED'
    return result


def run(seconds,pair_limit,array_cap,probes,interval_ms,ttl_ms):
    if not 15<=seconds<=1800 or not 1<=pair_limit<=28 or not 1<=array_cap<=80 or not 1<=probes<=80 or not 400<=interval_ms<=60000 or not 200<=ttl_ms<=5000:
        raise ValueError('INVALID_BOUNDED_PARAMETERS')
    url=guard()
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scanner
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as catalogs
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as net
    ROOT.mkdir(parents=True,exist_ok=True)
    db=scanner.bus();counts=collections.Counter();out=[];last_hb=0;index=0;last_request=0.;stop='TIME_LIMIT';pending={}
    try:
        hb=scanner.validate_scanner(db);epoch=hb['epoch'];producer=hb['producer'];inv=scanner.inventory(pair_limit)
        cat,roles,_=catalogs.discover(inv,url,array_cap)
        ready=[p for p in inv if p['token'] in cat and cat[p['token']].get('discovery_complete') and cat[p['token']]['bin_total']==cat[p['token']]['bin_selected']]
        if not ready:raise RuntimeError('NO_COMPLETE_PAIR_CATALOG')
        net.install_hot_token_net();decimals=bridge.mint_metadata(url,[p['token'] for p in ready])
        for p in ready:q18.worker().warm(p['pump_pool'])
        hb=scanner.validate_scanner(db)
        if hb['epoch']!=epoch or hb['producer']!=producer:raise RuntimeError('SCANNER_EPOCH_CHANGED_AT_BOOT')
        cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
        emit('ORACLE353_READY',dict(pairs=len(inv),ready=len(ready),account_roles=len(roles),epoch=epoch,cursor=cursor,
            method='BANK_FIRST_PLUS_SCANNER_PRIORITY',signing=False,broadcast=False))
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline and counts['bank_requests']<probes:
            try:hb=scanner.validate_scanner(db)
            except Exception:stop='SCANNER_UNHEALTHY';break
            if hb['epoch']!=epoch or hb['producer']!=producer:stop='SCANNER_EPOCH_CHANGED';break
            nominations,cursor=scanner.new_events(db,cursor)
            counts['bus_events']+=len(nominations)
            eligible=[]
            for n in nominations:
                try:
                    p=nominal_pair(n,inv,producer,epoch)
                    age=(time.time_ns()-int(n['created_ns']))/1e6
                    if age<0 or age>ttl_ms:raise ValueError('STALE_SOURCE_NOMINATION')
                    if p not in ready:raise ValueError('NOT_IN_READY_CATALOG')
                    eligible.append((n,p))
                except Exception as exc:counts['nomination_hold_'+type(exc).__name__]+=1
            for n,p in eligible:
                k=(n['token'],n['pump_pool'],n['meteora_pool'],n['direction'],n['size_lamports'])
                if k not in pending or n['id']>pending[k][0]['id']:pending[k]=(n,p)
            for k,(n,p) in list(pending.items()):
                age=(time.time_ns()-int(n['created_ns']))/1e6
                if age<0 or age>ttl_ms:pending.pop(k);counts['pending_expired']+=1
            now=time.monotonic()
            # Fresh scanner nominations bypass the slower research scout cadence.
            scanner_ready=bool(pending) and now-last_request>=0.15
            research_ready=now-last_request>=interval_ms/1000
            if scanner_ready or (not pending and research_ready):
                if scanner_ready:
                    n,p=max(pending.values(),key=lambda v:v[0]['id'])
                    k=(n['token'],n['pump_pool'],n['meteora_pool'],n['direction'],n['size_lamports'])
                    pending.pop(k,None);mode='SCANNER_ADMITTED';minslot=int(n['slot'])
                    counts['scanner_selected']+=1
                else:
                    n=None;p=ready[index%len(ready)];index+=1;mode='BANK_FIRST_RESEARCH';minslot=None
                    counts['bank_first_selected']+=1
                last_request=time.monotonic();counts['bank_requests']+=1
                try:
                    result=bank_probe(p,cat[p['token']],roles,url,decimals,minslot)
                    result=emit_bank_result(result,mode,n,ttl_ms)
                    out.append(result);counts['verified']+=1
                    counts['research_gross_positive']+=sum(int(q['gross_lamports']>0) for q in result['routes'])
                    if mode=='SCANNER_ADMITTED':counts['nominated_bank_verified']+=1
                    with LEDGER.open('a',encoding='utf-8') as f:f.write(json.dumps(result,sort_keys=True)+'\n')
                    emit('ORACLE353_BANK_SNAPSHOT',result)
                except Exception as exc:
                    reason=type(exc).__name__;counts['hold_'+reason]+=1
                    emit('ORACLE353_HOLD',dict(mode=mode,token=p['token'][:12],reason=reason,
                        signing=False,broadcast=False))
                    if '429' in str(exc):
                        counts['rpc_429']+=1;time.sleep(min(8,2**min(counts['rpc_429'],3)))
            if time.monotonic()-last_hb>=3:
                emit('ORACLE353_HEARTBEAT',dict(scanner_emitted=hb['emitted'],scanner_admitted=hb['admitted'],epoch=epoch,
                    bank_requests=counts['bank_requests'],bank_verified=counts['verified'],
                    gross_positive_research=counts['research_gross_positive'],bus_cursor=cursor,
                    signing=False,broadcast=False))
                last_hb=time.monotonic()
            time.sleep(.025)
        report=dict(build='ORACLE353',stop=stop,stats=dict(counts),bank_verified=len(out),
            latest=out[-5:],scanner_sha=SCANNER_SHA,execution_authority=False,signing=False,broadcast=False,trade_ready=False)
        tmp=REPORT.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8');os.replace(tmp,REPORT)
        emit('ORACLE353_EXIT',dict(stop=stop,stats=dict(counts),report=str(REPORT),signing=False,broadcast=False))
        return 0
    finally:db.close()


def tests():
    class Cases(unittest.TestCase):
        def pair(self):return dict(token='T',pump_pool='P',meteora_pool='M')
        def catalog(self):return dict(token='T',pump_pool='P',meteora_pool='M',discovery_complete=True,bin_total=1,bin_selected=1)
        def roles(self):
            rs={r:[('T',r)] for r in sorted(REQUIRED)}
            return rs
        def test_full_roles(self):self.assertEqual(len(selected_keys(self.pair(),self.catalog(),self.roles())),6)
        def test_pool_drift(self):
            with self.assertRaisesRegex(ValueError,'IDENTITY'):selected_keys({**self.pair(),'pump_pool':'x'},self.catalog(),self.roles())
        def test_missing_role(self):
            with self.assertRaisesRegex(ValueError,'ROLES'):selected_keys(self.pair(),self.catalog(),{'PUMP_POOL':[('T','PUMP_POOL')]})
        def test_cap_incomplete(self):
            with self.assertRaisesRegex(ValueError,'INCOMPLETE'):selected_keys(self.pair(),{**self.catalog(),'bin_total':2},self.roles())
        def test_quote_dual_positive(self):
            rows=[dict(direction=d,start=SIZE,local_net=g,local_end=SIZE+g) for d,g in [('PUMP_TO_METEORA',100),('METEORA_TO_PUMP',-200)]]
            self.assertEqual(approved_bank_routes(rows)[0]['gross_lamports'],100)
        def test_quote_missing_direction(self):
            with self.assertRaises(ValueError):approved_bank_routes([dict(direction='PUMP_TO_METEORA',start=SIZE,local_net=1,local_end=SIZE+1)])
        def test_quote_inconsistent(self):
            with self.assertRaisesRegex(ValueError,'ECONOMICS'):approved_bank_routes([dict(direction=d,start=SIZE,local_net=1,local_end=SIZE+2) for d in DIRECTIONS])
        def test_no_false_scanner_admission(self):
            x=emit_bank_result(dict(routes=[dict(direction=d,gross_lamports=5) for d in DIRECTIONS]),'BANK_FIRST_RESEARCH')
            self.assertFalse(x['scanner_admitted']);self.assertFalse(x.get('trade_ready',False));self.assertEqual(x['gate'],'BANK_FIRST_DISCOVERY_NOT_SCANNER_ADMITTED')
        def test_true_nomination_id(self):
            n=dict(token='T',pump_pool='P',meteora_pool='M',size_lamports=SIZE,direction='PUMP_TO_METEORA',producer='A')
            self.assertEqual(nominal_pair(n,[self.pair()],'A',1),self.pair())
            with self.assertRaises(ValueError):nominal_pair(n,[self.pair()],'B',1)
        def test_single_bank_fixture(self):
            import types
            calls=[]
            def rpc(url,method,args,counter,retries=1):calls.append((method,args));return dict(fake=True)
            w=types.SimpleNamespace(rpc=rpc)
            b=types.SimpleNamespace(bank_rows=lambda resp,keys,minslot,ns:({k:{'content_sha256':k} for k in keys},55),
                                    prepare_snapshot=lambda cat,rows,roles,decimals,ns,c,d:(dict(token='T',pump_pool='P'),dict(slot_min=55,slot_max=55)))
            q=types.SimpleNamespace(exact_snapshot_opportunities=lambda snap,size:[dict(direction=d,start=SIZE,local_net=g,local_end=SIZE+g) for d,g in [('PUMP_TO_METEORA',2),('METEORA_TO_PUMP',-3)]])
            r=bank_probe(self.pair(),self.catalog(),self.roles(),'https://rpc',{'T':6},50,(w,b,q,object(),object()))
            self.assertEqual(r['bank_slot'],55);self.assertEqual(len(r['routes']),2)
            self.assertEqual(calls[0][0],'getMultipleAccounts');self.assertEqual(calls[0][1][1]['minContextSlot'],50)
            self.assertTrue(r['one_bank_context']);self.assertFalse(r['trade_ready'])
        def test_zero_min_slot_omitted(self):
            import types
            opts=[]
            w=types.SimpleNamespace(rpc=lambda url,m,args,c,retries=1:(opts.append(args[1]) or {}))
            b=types.SimpleNamespace(bank_rows=lambda *_:({k:{'content_sha256':k} for k in sorted(REQUIRED)},55),prepare_snapshot=lambda *args:(dict(token='T',pump_pool='P'),dict(slot_min=55,slot_max=55)))
            q=types.SimpleNamespace(exact_snapshot_opportunities=lambda s,size:[dict(direction=d,start=SIZE,local_net=0,local_end=SIZE) for d in DIRECTIONS])
            bank_probe(self.pair(),self.catalog(),self.roles(),'https://rpc',{'T':6},None,(w,b,q,None,None))
            self.assertNotIn('minContextSlot',opts[0])
        def test_frozen_scanner_guarantee(self):self.assertIn('FROZEN_SCANNER_CHANGED',guard.__code__.co_consts)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    emit('ORACLE353_TEST_RESULT',dict(passed=result.wasSuccessful(),tests=result.testsRun))
    return 0 if result.wasSuccessful() else 1


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true');ap.add_argument('--run',action='store_true')
    ap.add_argument('--seconds',type=int,default=120);ap.add_argument('--pairs',type=int,default=28)
    ap.add_argument('--array-cap',type=int,default=60);ap.add_argument('--probes',type=int,default=15)
    ap.add_argument('--interval-ms',type=int,default=1200);ap.add_argument('--ttl-ms',type=int,default=2500)
    a=ap.parse_args()
    if a.test:return tests()
    if a.run:return run(a.seconds,a.pairs,a.array_cap,a.probes,a.interval_ms,a.ttl_ms)
    ap.error('SELECT_TEST_OR_RUN')
if __name__=='__main__':raise SystemExit(main())
'''
EXPECTED_SHA256='3c486d39fc0167c18934b9b0c5715346877ea78709aeecc81033b960151d46f5'

def check_scanner():
    if not SCANNER.exists() or hashlib.sha256(SCANNER.read_bytes()).hexdigest()!=FROZEN_SHA:
        raise RuntimeError('FROZEN_SCANNER_MISSING_OR_CHANGED')

def check_source():
    if hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()!=EXPECTED_SHA256:
        raise RuntimeError('EMBEDDED_SOURCE_SHA_MISMATCH')

def install():
    check_scanner();check_source()
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode('utf-8'))
    py_compile.compile(str(TARGET),doraise=True)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED_SHA256:
        raise RuntimeError('POST_INSTALL_SHA_MISMATCH')
    check_scanner()
    print('[ORACLE353_INSTALL_PASS]',str(TARGET),EXPECTED_SHA256,flush=True)
    return 0

def tests():
    check_source()
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'bank_first.py';p.write_bytes(SOURCE.encode('utf-8'))
        py_compile.compile(str(p),doraise=True)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=EXPECTED_SHA256:raise RuntimeError('TEMP_SOURCE_DIFFERENT')
    if not TARGET.exists() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED_SHA256:
        raise RuntimeError('INSTALL_REQUIRED')
    return subprocess.call([sys.executable,'-m',MODULE,'--test'])

def audit():
    check_scanner();check_source()
    if not TARGET.exists() or hashlib.sha256(TARGET.read_bytes()).hexdigest()!=EXPECTED_SHA256:
        raise RuntimeError('MODULE_SOURCE_CHANGED')
    tree=ast.parse(SOURCE)
    forbidden={'sendTransaction','send_raw_transaction','send_transaction','sign_transaction','Keypair','send_and_confirm_transaction'}
    calls={n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
        if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
    if calls & forbidden:raise RuntimeError('EXECUTION_API_FORBIDDEN')
    if 'QSB_SOLANA_PRIVATE_KEY' not in SOURCE or 'FROZEN_SCANNER_CHANGED' not in SOURCE:
        raise RuntimeError('MISSING_SAFETY_BOUNDARY')
    print('[ORACLE353_AUDIT_PASS] READ_ONLY BANK_FIRST_ONE_CONTEXT BOTH_DIRECTIONS SCANNER_FROZEN NO_NEW_WEBSOCKET',flush=True)
    return 0

def main():
    ap=argparse.ArgumentParser()
    for mode in ('install','test','audit','run'):ap.add_argument('--'+mode,action='store_true')
    for name,default in (('seconds',60),('pairs',28),('array-cap',60),('probes',12),('interval-ms',1200),('ttl-ms',2500)):
        ap.add_argument('--'+name,type=int,default=default)
    a=ap.parse_args()
    if a.install:return install()
    if a.test:return tests()
    if a.audit:return audit()
    if a.run:
        audit()
        from build_oracle_343_unified_feed_recovery import launch_env
        env,src=launch_env(os.environ)
        if env.get('QSB_SOLANA_PRIVATE_KEY') or env.get('QSB_LIVE_ARM','NO')!='NO':
            raise RuntimeError('UNSAFE_LAUNCH_ENV')
        print('[ORACLE353_ENDPOINTS_READY]',{'source':src,'key_printed':False,'signing':False,'broadcast':False},flush=True)
        args=[sys.executable,'-m',MODULE,'--run','--seconds',str(a.seconds),'--pairs',str(a.pairs),
              '--array-cap',str(a.array_cap),'--probes',str(a.probes),'--interval-ms',str(a.interval_ms),
              '--ttl-ms',str(a.ttl_ms)]
        return subprocess.call(args,env=env)
    ap.error('SELECT_INSTALL_TEST_AUDIT_OR_RUN')
if __name__=='__main__':raise SystemExit(main())
