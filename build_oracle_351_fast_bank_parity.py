"""ORACLE-351 full installer, executor-side rapid bank verifier, no live trading."""
import argparse,hashlib,pathlib,py_compile,subprocess,sys,os,tempfile
TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_351_fast_bank_parity.py')
SOURCE = r'''"""ORACLE351 bounded fast single-bank validation; scanner stays immutable."""
import argparse,collections,json,os,time,pathlib,concurrent.futures,unittest
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_350_quote_parity as old350
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_349_bank_survival as old349
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old343
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as sdk
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as net
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT=ROOT/'oracle_351_fast_bank_report.json'
LEDGER=ROOT/'oracle_351_fast_bank_evidence.jsonl'

def log(tag,data):
    print('['+tag+'] '+json.dumps(data,sort_keys=True,default=str),flush=True)

def verified_once(n,catalog,roles,url,decimals):
    # Same exact bank account validation as ORACLE350, but only one quote pass.
    if not catalog.get('discovery_complete') or catalog['bin_total']!=catalog['bin_selected']:
        raise ValueError('INCOMPLETE_ACCOUNT_CATALOG')
    keys=sorted(k for k,rr in roles.items() if any(t==n['token'] for t,_ in rr))
    required={'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}
    present={role for k in keys for t,role in roles[k] if t==n['token']}
    if not required.issubset(present) or not 6<=len(keys)<=100:
        raise ValueError('BANK_ACCOUNTS_INCOMPLETE_OR_OVERSIZE')
    import collections as _c
    nomination_received_ns=time.time_ns()
    t0=time.perf_counter_ns()
    rpc=witness.rpc(url,'getMultipleAccounts',[keys,{'encoding':'base64','commitment':'processed','minContextSlot':int(n['slot'])}],_c.Counter(),retries=1)
    t1=time.perf_counter_ns()
    rows,bank_slot=bridge.bank_rows(rpc,keys,int(n['slot']),nomination_received_ns)
    t2=time.perf_counter_ns()
    snapshot,lineage=bridge.prepare_snapshot(catalog,rows,roles,decimals,nomination_received_ns-1,core,decoder)
    t3=time.perf_counter_ns()
    if lineage['slot_min']!=bank_slot or lineage['slot_max']!=bank_slot:
        raise ValueError('MIXED_BANK_CONTEXT')
    quote=old350.leg_quote(n,snapshot,decimals)
    t4=time.perf_counter_ns()
    # No repeat quote in critical path. Gross-positive remains research-only.
    source_age_ms=(time.time_ns()-int(n['created_ns']))/1e6
    source_gross=int(n['gross_lamports']); bank_gross=quote['bank_gross']; size=int(n['size_lamports'])
    return {'event_id':n['id'],'token':n['token'],'pump_pool':n['pump_pool'],
        'meteora_pool':n['meteora_pool'],'direction':n['direction'],'size_lamports':size,
        'scanner_slot':int(n['slot']),'bank_slot':bank_slot,'slot_gap':bank_slot-int(n['slot']),
        'scanner_gross':source_gross,'bank_gross':bank_gross,
        'scanner_bps':round(source_gross*10000/size,3),'bank_bps':round(bank_gross*10000/size,3),
        'delta_lamports':bank_gross-source_gross,'bank_fingerprint':old350.fingerprint(rows,keys),
        'account_count':len(keys),'source_age_at_bank_end_ms':round(source_age_ms,3),
        'rpc_ms':round((t1-t0)/1e6,3),'bank_decode_ms':round((t3-t1)/1e6,3),
        'exact_quote_ms':round((t4-t3)/1e6,3),'original_legs':quote,
        'single_context_verified':True,'gross_only':True,'signing':False,'broadcast':False,
        'trade_ready':False}

def keep_latest(rows):
    """Coalesce only duplicate identity/direction/size, newest id wins."""
    keyed={}
    for n in rows:
        k=(n['token'],n['pump_pool'],n['meteora_pool'],n['direction'],n['size_lamports'])
        if k not in keyed or n['id']>keyed[k]['id']:keyed[k]=n
    return sorted(keyed.values(),key=lambda n:n['id'])

def run(seconds=300,pairs=28,array_cap=60,probes=20,ttl_ms=2500):
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO')!='NO':
        raise RuntimeError('READ_ONLY_NO_PRIVATE_KEY')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_REQUIRED')
    if not (30<=seconds<=1800 and 1<=pairs<=28 and 1<=array_cap<=80 and 1<=probes<=40 and 500<=ttl_ms<=5000):
        raise ValueError('INVALID_BOUNDS')
    old349.scanner_guard()
    ROOT.mkdir(parents=True,exist_ok=True)
    db=scan.bus();counts=collections.Counter();out=[];holds=collections.Counter()
    try:
        hb=scan.validate_scanner(db);epoch=hb['epoch'];producer=hb['producer']
        inventory=scan.inventory(pairs)
        catalog,roles,_=cat.discover(inventory,url,array_cap)
        complete={token for token,c in catalog.items() if c.get('discovery_complete') and c['bin_total']==c['bin_selected']}
        net.install_hot_token_net();decimals=bridge.mint_metadata(url,sorted(complete))
        for pair in inventory:
            if pair['token'] in complete:sdk.worker().warm(pair['pump_pool'])
        hb=scan.validate_scanner(db)
        if hb['epoch']!=epoch or hb['producer']!=producer:raise RuntimeError('SCANNER_EPOCH_CHANGE_DURING_WARMUP')
        cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
        log('ORACLE351_READY',{'scanner_epoch':epoch,'pairs':len(inventory),'complete':len(complete),'cursor':cursor,'account_roles':len(roles)})
        deadline=time.monotonic()+seconds
        # One in-flight call at a time protects shared SDK state and RPC rate budget.
        # No fixed 2-second cooldown: next nomination starts immediately after prior result.
        while time.monotonic()<deadline and counts['bank_attempts']<probes:
            try:hb=scan.validate_scanner(db)
            except Exception as e:
                holds['SCANNER_UNHEALTHY']+=1;log('ORACLE351_HOLD',{'reason':'SCANNER_UNHEALTHY'});break
            if hb['epoch']!=epoch or hb['producer']!=producer:
                holds['SCANNER_EPOCH_CHANGED']+=1;break
            nominations,cursor=scan.new_events(db,cursor)
            counts['nominations']+=len(nominations)
            for n in keep_latest(nominations):
                if counts['bank_attempts']>=probes:break
                try:
                    identity.vetted(n,inventory,hb)
                    if n['token'] not in complete:raise ValueError('INCOMPLETE_PAIR')
                    if old343.nomination_age(n,time.time_ns(),ttl_ms) is None:raise ValueError('STALE_NOMINATION')
                    counts['bank_attempts']+=1
                    result=verified_once(n,catalog[n['token']],roles,url,decimals)
                    result['gate']='BANK_GROSS_POSITIVE_SHADOW' if result['bank_gross']>0 and result['source_age_at_bank_end_ms']<=ttl_ms else 'HOLD_BANK_NEGATIVE_OR_EXPIRED'
                    counts['verified']+=1;counts['positive']+=int(result['gate']=='BANK_GROSS_POSITIVE_SHADOW')
                    out.append(result);log('ORACLE351_BANK_RESULT',result)
                    with LEDGER.open('a',encoding='utf-8') as f:f.write(json.dumps(result,sort_keys=True)+'\n')
                except Exception as e:
                    reason=type(e).__name__
                    holds[reason]+=1
                    log('ORACLE351_HOLD',{'event_id':n.get('id'),'error_class':reason,'detail':old343.redacted(e)})
            time.sleep(.025)
        report={'build':'ORACLE351','results':out,'counts':dict(counts),'holds':dict(holds),
                'scanner_epoch':epoch,'scanner_sha':old349.SCANNER_SHA,'signing':False,
                'broadcast':False,'trade_ready':False}
        old343.atomic_write(REPORT,report)
        log('ORACLE351_EXIT',{'verified':len(out),'positive':counts['positive'],'counts':dict(counts),'holds':dict(holds),'report':str(REPORT)})
        return 0 if out else 2
    finally:db.close()

def tests():
    class Cases(unittest.TestCase):
        def test_coalesce_latest(self):
            n={'token':'t','pump_pool':'p','meteora_pool':'d','direction':'PUMP_TO_METEORA','size_lamports':10,'id':1}
            self.assertEqual(keep_latest([n,{**n,'id':3},{**n,'id':2}])[0]['id'],3)
        def test_preserve_reverse(self):
            a={'token':'t','pump_pool':'p','meteora_pool':'d','direction':'PUMP_TO_METEORA','size_lamports':10,'id':1}
            self.assertEqual(len(keep_latest([a,{**a,'direction':'METEORA_TO_PUMP'}])),2)
        def test_shadow_only(self):
            self.assertIn('READ_ONLY_NO_PRIVATE_KEY',run.__code__.co_consts)
        def test_limit(self):
            self.assertTrue(6<=18<=100)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    return 0 if r.wasSuccessful() else 1

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=300);p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--array-cap',type=int,default=60);p.add_argument('--probes',type=int,default=20)
    p.add_argument('--ttl-ms',type=int,default=2500)
    a=p.parse_args()
    return tests() if a.test else run(a.seconds,a.pairs,a.array_cap,a.probes,a.ttl_ms) if a.run else p.error('SELECT_MODE')
if __name__=='__main__':raise SystemExit(main())
'''
EXPECTED=hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()
def install():
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_bytes(SOURCE.encode('utf-8'))
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE351_INSTALL_PASS]',TARGET,EXPECTED);return 0
def test():
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/TARGET.name;p.write_bytes(SOURCE.encode());py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    return subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle_351_fast_bank_parity','--test'])
def audit():
    assert TARGET.exists() and hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    assert not any(s in SOURCE for s in ('sendTransaction','send_raw_transaction','Keypair.from','sign_transaction'))
    print('[ORACLE351_AUDIT_PASS] FROZEN_SCANNER SINGLE_BANK ONE_QUOTE NO_SEND');return 0
def main():
    p=argparse.ArgumentParser()
    for opt in ('install','test','audit','run'):p.add_argument('--'+opt,action='store_true')
    for opt,default in (('seconds',300),('pairs',28),('array-cap',60),('probes',20),('ttl-ms',2500)):
        p.add_argument('--'+opt,type=int,default=default)
    a=p.parse_args()
    if a.install:return install()
    if a.test:return test()
    if a.audit:return audit()
    if a.run:
        from build_oracle_343_unified_feed_recovery import launch_env
        env,_=launch_env(os.environ)
        assert not env.get('QSB_SOLANA_PRIVATE_KEY') and env.get('QSB_LIVE_ARM','NO')=='NO'
        args=['--run','--seconds',str(a.seconds),'--pairs',str(a.pairs),'--array-cap',str(a.array_cap),'--probes',str(a.probes),'--ttl-ms',str(a.ttl_ms)]
        return subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle_351_fast_bank_parity',*args],env=env)
    p.error('SELECT_MODE')
if __name__=='__main__':raise SystemExit(main())
