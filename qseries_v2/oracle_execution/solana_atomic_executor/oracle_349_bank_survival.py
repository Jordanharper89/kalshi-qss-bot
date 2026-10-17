"""ORACLE-349: bounded real nomination bank-survival certification; SHADOW ONLY."""
import argparse,collections,hashlib,json,os,pathlib,sys,time,unittest
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT=ROOT/'oracle_349_bank_survival_report.json'
EVIDENCE=ROOT/'oracle_349_bank_survival_evidence.jsonl'
SCANNER=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py')
SCANNER_SHA='9ceef817699e895aa25cce877e59c2065061e75046a0aee6b373128fc95ca805'

def emit(event,obj):
    print('['+event+'] '+json.dumps(obj,sort_keys=True,default=str),flush=True)

def scanner_guard():
    if not SCANNER.is_file() or hashlib.sha256(SCANNER.read_bytes()).hexdigest()!=SCANNER_SHA:
        raise RuntimeError('FROZEN_SCANNER_SHA256_CHANGED')

def gate_result(nom,result,at_ns,ttl_ms):
    assert result.get('single_context_verified') is True
    assert result['token']==nom['token'] and result['direction']==nom['direction']
    assert int(result['size_lamports'])==int(nom['size_lamports'])
    slot_gap=int(result['bank_slot'])-int(nom['slot'])
    if slot_gap<0:raise ValueError('BANK_BEHIND_SCANNER')
    age_ms=(int(at_ns)-int(nom['created_ns']))/1000000
    if age_ms<0:raise ValueError('NOMINATION_FROM_FUTURE')
    bank_gross=int(result['bank_gross']); scanner_gross=int(nom['gross_lamports'])
    outcome=dict(result,source_event_id=int(nom['id']),source_generation=nom['generation'],
        source=nom['source'],source_age_at_bank_end_ms=round(age_ms,2),
        bank_slot_gap=slot_gap,delta_gross_lamports=bank_gross-scanner_gross,
        scanner_bps=round(10000*scanner_gross/int(nom['size_lamports']),3),
        bank_bps=round(10000*bank_gross/int(nom['size_lamports']),3),
        signing=False,broadcast=False,trade_ready=False,execution_authority=False)
    outcome['gate']=('HOLD_BANK_EXPIRED' if age_ms>ttl_ms else
          'BANK_GROSS_POSITIVE_SHADOW' if bank_gross>0 else 'HOLD_BANK_NONPOSITIVE')
    return outcome

def one_bank_exact(nom,catalog,roles,url,decimals,sdk,bridge,witness,core,decoder):
    token=nom['token']
    if not catalog.get('discovery_complete') or catalog['bin_total']!=catalog['bin_selected']:
        raise ValueError('BIN_ARRAY_CATALOG_INCOMPLETE')
    if token not in decimals:raise ValueError('MINT_METADATA_UNVERIFIED')
    keys=sorted(k for k,rr in roles.items() if any(t==token for t,role in rr))
    if not 6<=len(keys)<=100:raise ValueError('BANK_ACCOUNT_COUNT_UNSUPPORTED')
    required={'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}
    present={role for key in keys for t,role in roles[key] if t==token}
    if not required.issubset(present):raise ValueError('BANK_REQUIRED_ROLES_MISSING')
    start_ns=time.time_ns();min_slot=int(nom['slot'])
    response=witness.rpc(url,'getMultipleAccounts',
        [keys,{'encoding':'base64','commitment':'processed','minContextSlot':min_slot}],collections.Counter(),retries=1)
    rows,slot=bridge.bank_rows(response,keys,min_slot,start_ns)
    snap,lineage=bridge.prepare_snapshot(catalog,rows,roles,decimals,start_ns-1,core,decoder)
    if lineage['slot_min']!=slot or lineage['slot_max']!=slot:raise ValueError('BANK_MIXED_CONTEXT')
    qstart=time.perf_counter_ns();size=int(nom['size_lamports'])
    if nom['direction']=='PUMP_TO_METEORA':
        buy=sdk.worker().buy(snap,size)
        tokens=int(sdk.token_net(token,int(buy['baseOut'])))
        if tokens<=0:raise ValueError('PUMP_TOKEN_NET_ZERO')
        ending,partial=bridge.dlmm_quote_or_partial(snap,tokens,token,core)
    elif nom['direction']=='METEORA_TO_PUMP':
        tokens,partial=bridge.dlmm_quote_or_partial(snap,size,bridge.SOL,core)
        if partial:raise ValueError('DLMM_PARTIAL_EXACT')
        tokens=int(sdk.token_net(token,tokens))
        if tokens<=0:raise ValueError('DLMM_TOKEN_NET_ZERO')
        sell=sdk.worker().sell(snap,tokens)
        ending=int(sell['uiQuote'])
    else:raise ValueError('UNSUPPORTED_DIRECTION')
    if partial:raise ValueError('DLMM_PARTIAL_EXACT')
    quote_ms=round((time.perf_counter_ns()-qstart)/1e6,2)
    elapsed=(time.time_ns()-start_ns)/1e6
    return dict(token=token,direction=nom['direction'],size_lamports=size,scanner_slot=min_slot,
        bank_slot=slot,scanner_gross=int(nom['gross_lamports']),bank_gross=int(ending)-size,
        account_count=len(keys),single_context_verified=True,quote_ms=quote_ms,
        bank_elapsed_ms=round(elapsed,2),gross_only=True,signing=False,broadcast=False)

def summarize(rows,counts,epoch,producer,stopped):
    positive=[r for r in rows if r['gate']=='BANK_GROSS_POSITIVE_SHADOW']
    deltas=sorted(r['delta_gross_lamports'] for r in rows)
    return dict(build='ORACLE349',mode='SHADOW_ONLY',scanner_epoch=epoch,
       scanner_producer=producer,scanner_sha256=SCANNER_SHA,
       verified_bank_quotes=len(rows),fresh_gross_positive=len(positive),
       gross_positive_rate=round(len(positive)/len(rows),4) if rows else 0,
       median_delta_lamports=deltas[len(deltas)//2] if deltas else None,
       best_bank_bps=max((r['bank_bps'] for r in rows),default=None),
       last_evidence=rows[-1] if rows else None,stats=dict(counts),stop_reason=stopped,
       signing=False,broadcast=False,trade_ready=False,production_cutover=False)

def run(seconds=300,pairs_limit=28,array_cap=60,probes=20,cooldown=3,ttl_ms=2500):
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO')!='NO':
        raise RuntimeError('NO_PRIVATE_KEY_IN_SHADOW_CHILD')
    url=os.environ.get('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    if not (1<=pairs_limit<=100 and 1<=array_cap<=80 and 1<=probes<=30 and cooldown>=2 and 500<=ttl_ms<=5000 and 30<=seconds<=1800):
        raise ValueError('BOUNDED_PARAMETERS_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as sdk
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as net
    scanner_guard();ROOT.mkdir(parents=True,exist_ok=True)
    counts=collections.Counter();rows=[];epoch=None;producer=None;stop_reason='TIME_LIMIT'
    conn=scan.bus()
    try:
        try:
            hb=scan.validate_scanner(conn);epoch=hb['epoch'];producer=hb['producer']
            pairs=scan.inventory(pairs_limit)
            emit('ORACLE349_DISCOVERY_START',dict(epoch=epoch,pairs=len(pairs),array_cap=array_cap))
            catalogs,roles,diagnostics=cat.discover(pairs,url,array_cap)
            net.install_hot_token_net()
            ready={t for t,c in catalogs.items() if c.get('discovery_complete') and c['bin_selected']==c['bin_total']}
            emit('ORACLE349_DISCOVERY_READY',dict(inventory_pairs=len(pairs),complete=len(ready),watch_accounts=len(roles),discovery_stats=diagnostics))
            if not ready:raise RuntimeError('NO_COMPLETE_BANK_CATALOG')
            decimals=bridge.mint_metadata(url,sorted(ready))
            emit('ORACLE349_MINT_METADATA',dict(verified=len(decimals),requested=len(ready)))
            hb=scan.validate_scanner(conn)
            if hb['epoch']!=epoch or hb['producer']!=producer:raise RuntimeError('SCANNER_EPOCH_CHANGED_DURING_DISCOVERY')
            cursor=int(conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            deadline=time.monotonic()+seconds;last_probe=-100000.;last_heartbeat=0.;warmed=set()
            emit('ORACLE349_START',dict(cursor=cursor,epoch=epoch,ready=len(ready),probes=probes,cooldown_s=cooldown))
            while time.monotonic()<deadline:
                try:hb=scan.validate_scanner(conn)
                except Exception:stop_reason='SCANNER_HEALTH_HOLD';break
                if hb['epoch']!=epoch or hb['producer']!=producer:
                    stop_reason='SCANNER_EPOCH_OR_PRODUCER_CHANGED';break
                incoming,cursor=scan.new_events(conn,cursor)
                counts['nominations_seen']+=len(incoming)
                nominations=old.coalesce(incoming);counts['coalesced_nominations']+=len(nominations)
                for nom in nominations:
                    try:
                        identity.vetted(nom,pairs,hb)
                        if nom['token'] not in ready:raise ValueError('NO_COMPLETE_CATALOG_FOR_NOMINATION')
                        if old.nomination_age(nom,time.time_ns(),ttl_ms) is None:raise ValueError('NOMINATION_TOO_OLD')
                        if counts['bank_attempts']>=probes:stop_reason='PROBE_BUDGET';break
                        if time.monotonic()-last_probe<cooldown:counts['cooldown_skip']+=1;continue
                        counts['matched_nominations']+=1
                        if nom['token'] not in warmed:
                            sdk.worker().warm(nom['pump_pool']);warmed.add(nom['token'])
                        if old.nomination_age(nom,time.time_ns(),ttl_ms) is None:raise ValueError('NOMINATION_EXPIRED_DURING_WARM')
                        last_probe=time.monotonic();counts['bank_attempts']+=1
                        raw=one_bank_exact(nom,catalogs[nom['token']],roles,url,decimals,sdk,bridge,witness,core,decoder)
                        item=gate_result(nom,raw,time.time_ns(),ttl_ms)
                        rows.append(item);counts['verified_single_bank']+=1
                        if item['bank_gross']>0:counts['bank_gross_positive_regardless_of_age']+=1
                        if item['gate']=='BANK_GROSS_POSITIVE_SHADOW':counts['fresh_bank_positive']+=1
                        if item['gate']=='HOLD_BANK_EXPIRED':counts['expired_after_bank']+=1
                        with EVIDENCE.open('a',encoding='utf-8') as f:f.write(json.dumps(item,sort_keys=True)+'\n')
                        emit('ORACLE349_BANK_RESULT',item)
                    except Exception as exc:
                        why=old.redacted(exc);counts['hold_'+type(exc).__name__]+=1
                        emit('ORACLE349_HOLD',dict(event_id=nom['id'],token=nom['token'][:12],reason=why))
                if counts['bank_attempts']>=probes:stop_reason='PROBE_BUDGET';break
                if time.monotonic()-last_heartbeat>10:
                    emit('ORACLE349_HEARTBEAT',dict(scanner=hb,bank_attempts=counts['bank_attempts'],verified=len(rows),bank_positive=counts['fresh_bank_positive'],holds=sum(v for k,v in counts.items() if k.startswith('hold_'))))
                    last_heartbeat=time.monotonic()
                time.sleep(.1)
        except Exception as exc:
            stop_reason=type(exc).__name__
            emit('ORACLE349_BLOCKER',dict(reason=old.redacted(exc)))
        report=summarize(rows,counts,epoch,producer,stop_reason)
        old.atomic_write(REPORT,report);emit('ORACLE349_EXIT',report)
        return 0 if rows else 2
    finally:conn.close()

def tests():
    class T(unittest.TestCase):
        def setUp(self):self.nom=dict(id=10,token='T',direction='PUMP_TO_METEORA',size_lamports=10000000,slot=100,created_ns=1_000_000_000,gross_lamports=40000,generation=1,source='scanner')
        def quote(self,gross=-130000,slot=103):return dict(token='T',direction='PUMP_TO_METEORA',size_lamports=10000000,scanner_slot=100,bank_slot=slot,scanner_gross=40000,bank_gross=gross,single_context_verified=True)
        def test_negative(self):self.assertEqual(gate_result(self.nom,self.quote(),1_800_000_000,2500)['gate'],'HOLD_BANK_NONPOSITIVE')
        def test_positive(self):self.assertEqual(gate_result(self.nom,self.quote(10000),1_800_000_000,2500)['gate'],'BANK_GROSS_POSITIVE_SHADOW')
        def test_expired(self):self.assertEqual(gate_result(self.nom,self.quote(10000),4_000_000_000,2500)['gate'],'HOLD_BANK_EXPIRED')
        def test_slot(self):self.assertRaises(ValueError,gate_result,self.nom,self.quote(slot=99),1_800_000_000,2500)
        def test_future(self):self.assertRaises(ValueError,gate_result,self.nom,self.quote(),0,2500)
        def test_no_claim(self):self.assertFalse(summarize([],{},None,None,'TEST')['production_cutover'])
        def test_rate(self):self.assertEqual(summarize([gate_result(self.nom,self.quote(10000),1_800_000_000,2500)],{},4,'p','END')['gross_positive_rate'],1.)
        def test_fee_not_certified(self):self.assertFalse(gate_result(self.nom,self.quote(10000),1_800_000_000,2500)['trade_ready'])
        def test_one_bank_exact_route(self):
            import types
            nom=self.nom;roles={str(i):[(nom['token'],v)] for i,v in enumerate(('PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'))}
            cat={'token':'T','discovery_complete':True,'bin_total':1,'bin_selected':1}
            sdk=types.SimpleNamespace(worker=lambda:types.SimpleNamespace(buy=lambda snap,n:{'baseOut':10}),token_net=lambda token,n:n)
            bridge=types.SimpleNamespace(bank_rows=lambda r,k,s,t:({key:{'slot':101} for key in k},101),prepare_snapshot=lambda c,r,roles,dec,ts,core,decoder:({},dict(slot_min=101,slot_max=101)),dlmm_quote_or_partial=lambda snap,tok,mint,core:(10001000,None))
            witness=types.SimpleNamespace(rpc=lambda *args,**kw:{'context':{'slot':101}})
            out=one_bank_exact(nom,cat,roles,'https://example.test',{'T':6},sdk,bridge,witness,None,None)
            self.assertEqual(out['bank_gross'],1000)
            self.assertTrue(out['single_context_verified'])
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res=unittest.TextTestRunner(verbosity=2).run(suite)
    print('[ORACLE349_TESTS]',res.testsRun,flush=True)
    return 0 if res.wasSuccessful() else 1

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=300);p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--array-cap',type=int,default=60);p.add_argument('--probes',type=int,default=20)
    p.add_argument('--cooldown',type=int,default=3);p.add_argument('--ttl-ms',type=int,default=2500)
    a=p.parse_args()
    if a.test:return tests()
    if a.run:return run(a.seconds,a.pairs,a.array_cap,a.probes,a.cooldown,a.ttl_ms)
    p.error('SELECT_TEST_OR_RUN')
if __name__=='__main__':raise SystemExit(main())
