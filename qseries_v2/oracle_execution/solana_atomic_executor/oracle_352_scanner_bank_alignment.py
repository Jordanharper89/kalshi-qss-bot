"""ORACLE-352: scanner/executor one-bank price parity + positive admission observer.
This executable is shadow-only. It never imports a signer or an order broadcaster.
It does not alter the frozen scanner, its SQLite bus, inventory, or process.
"""
from __future__ import annotations
import argparse, collections, concurrent.futures, hashlib, json, os, pathlib, sqlite3, time, unittest

ROOT = pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT = ROOT/'oracle_352_alignment_report.json'
LEDGER = ROOT/'oracle_352_alignment_evidence.jsonl'
STATUS = ROOT/'scanner_live.json'
SCANNER = pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py')
EXPECTED_SCANNER_SHA = '9ceef817699e895aa25cce877e59c2065061e75046a0aee6b373128fc95ca805'
SIZE = 10_000_000
DIRS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def emit(tag, obj):
    print('['+tag+'] '+json.dumps(obj,sort_keys=True,default=str),flush=True)


def source_gate_audit():
    src=SCANNER.read_text(encoding='utf-8')
    if hashlib.sha256(SCANNER.read_bytes()).hexdigest()!=EXPECTED_SCANNER_SHA:
        raise RuntimeError('FROZEN_SCANNER_HASH_CHANGED')
    needles={
        'positive_counter_before_admission': "if net>0:stats['gross_positive_010']+=1",
        'pool_identity_guard': "str(snap.get('pump_pool'))!=p['pump_pool']",
        'newer_generation_guard': 'lane.newer_waiting(',
        'unpopulated_account_counter': "stats['subscribed_accounts']",
    }
    if not all(n in src for n in needles.values()):raise RuntimeError('SCANNER_GATE_SOURCE_CONTRACT_CHANGED')
    if src.count("stats['subscribed_accounts']") != 1:
        raise RuntimeError('ACCOUNT_COUNTER_SOURCE_ASSUMPTION_CHANGED')
    return dict(positive_increment_precedes_final_checks=True,
                possible_unemitted_positive_reasons=['PUMP_POOL_MISMATCH','NEWER_GENERATION_SUPERSEDES'],
                counter_accounts_is_uninstrumented=True,
                reason_per_withheld_positive_unavailable_without_scanner_internal_trace=True)


def status_snapshot(path=STATUS):
    try:
        st=path.stat()
        if time.time()-st.st_mtime > 12 or st.st_mtime-time.time()>2:return None
        obj=json.loads(path.read_text(encoding='utf-8'))
        if obj.get('build')!='ORACLE322' or obj.get('status')!='RUNNING':return None
        return obj
    except (OSError,ValueError,TypeError):return None


def status_candidates(st, inventory, max_age_ms=15000):
    """Telemetry is never a scanner-admitted nomination; unique prefix is diagnostic only."""
    if not st:return []
    out=[]
    for q in st.get('recent_quotes',[]):
        try:
            prefix=q['token'];direction=q['direction'];slot=int(q['slot'])
            gross=int(q['gross_lamports']);age=int(q['age_ms'])
            if direction not in DIRS or not 0<=age<=max_age_ms or slot<=0:continue
            unique=[p for p in inventory if p['token'].startswith(prefix)]
            if len(unique)!=1:continue
            pair=unique[0]
            # The age is reported at the time of the status write, not at our read time.
            created_ns=int(STATUS.stat().st_mtime_ns)-age*1_000_000 if STATUS.exists() else time.time_ns()-age*1_000_000
            out.append(dict(id=None,token=pair['token'],pump_pool=pair['pump_pool'],
                meteora_pool=pair['meteora_pool'],direction=direction,size_lamports=SIZE,
                gross_lamports=gross,slot=slot,created_ns=created_ns,producer=None,
                source='SCANNER_RECENT_QUOTES_TELEMETRY',admitted=False,
                telemetry_age_at_status_ms=age))
        except (KeyError,TypeError,ValueError):continue
    return out


def quote_parity(bank_quote, scanner_quote):
    if scanner_quote is None:return 'SCANNER_Q18_UNAVAILABLE'
    return 'SAME_BANK_MODEL_PARITY' if int(scanner_quote)==int(bank_quote) else 'SAME_BANK_MODEL_MISMATCH'


def admission_classification(st, bus_count, prior, last_bus_id):
    count=int(st.get('exact_gross_positive_010',0))
    sent=int(st.get('candidates_to_executor',0))
    if prior is not None and count < prior[0]:return 'SCANNER_COUNTER_RESET'
    if prior is not None and count>prior[0] and bus_count==0 and sent==prior[1]:
        return 'POSITIVE_COUNT_ROSE_BUT_NO_ADMITTED_EVENT'
    if count>sent:return 'CUMULATIVE_POSITIVE_EXCEEDS_EMITTED_REASON_NOT_EXPOSED'
    if last_bus_id is None:return 'NO_BUS_PRODUCER_EVIDENCE'
    return 'NO_UNEXPLAINED_COUNT_GAP'


def snapshot_quote(n,catalog,roles,url,decimals,adapters=None):
    """One RPC context; both pricing models on same decoded account bytes.

    Fixture adapters are explicit rather than sys.modules monkeypatches: Python's
    from-package imports can retain an already-loaded parent attribute.
    Production requires and imports the real dependencies without substitutes.
    """
    if adapters is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
        from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_350_quote_parity as parity
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as sdk
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
    else:
        if len(adapters)!=6:raise ValueError('FIXTURE_ADAPTER_COUNT_INVALID')
        witness,bridge,parity,sdk,core,decoder=adapters
    if not catalog.get('discovery_complete') or int(catalog['bin_selected'])!=int(catalog['bin_total']):
        raise ValueError('CATALOG_NOT_COMPLETE')
    if n['token'] not in decimals:raise ValueError('MINT_METADATA_MISSING')
    keys=sorted(k for k,rr in roles.items() if any(t==n['token'] for t,_ in rr))
    required={'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}
    available={role for k in keys for t,role in roles[k] if t==n['token']}
    if not required.issubset(available) or not 6<=len(keys)<=100:
        raise ValueError('ONE_BANK_ROLES_OR_ACCOUNT_LIMIT')
    minslot=int(n['slot']); start_ns=time.time_ns(); t0=time.perf_counter_ns()
    reply=witness.rpc(url,'getMultipleAccounts',
        [keys,{'encoding':'base64','commitment':'processed','minContextSlot':minslot}],collections.Counter(),retries=1)
    t1=time.perf_counter_ns()
    rows,slot=bridge.bank_rows(reply,keys,minslot,start_ns)
    snap,lin=bridge.prepare_snapshot(catalog,rows,roles,decimals,start_ns-1,core,decoder)
    t2=time.perf_counter_ns()
    if int(lin['slot_min'])!=slot or int(lin['slot_max'])!=slot:raise ValueError('BANK_CONTEXT_MIXED')
    if snap.get('token')!=n['token'] or snap.get('pump_pool')!=n['pump_pool']:
        raise ValueError('BANK_SNAPSHOT_POOL_IDENTITY_DRIFT')
    leg=parity.leg_quote(n,snap,decimals)
    t3=time.perf_counter_ns()
    expected=None; reason=None; orig=None
    try:
        orig=sdk.exact_snapshot_opportunities(snap,float(n['size_lamports'])/1e9)
        match=[op for op in orig if op.get('direction')==n['direction'] and int(op.get('start') or 0)==int(n['size_lamports'])]
        if len(match)!=1:reason='Q18_EXACT_DIRECTION_NOT_FOUND'
        else:expected=int(match[0]['local_net'])
    except Exception as exc:reason='Q18_QUOTE_'+type(exc).__name__
    t4=time.perf_counter_ns()
    same_bank=quote_parity(leg['bank_gross'],expected)
    gap=slot-minslot
    if gap<0:raise ValueError('BANK_BEHIND_SCANNER_SLOT')
    age_ms=round((time.time_ns()-int(n['created_ns']))/1e6,2)
    # A delayed positive cannot be certified as executable, even if bank gross > 0.
    return dict(event_id=n.get('id'),token=n['token'],pump_pool=n['pump_pool'],meteora_pool=n['meteora_pool'],
        direction=n['direction'],size_lamports=int(n['size_lamports']),source=n['source'],admitted=bool(n.get('admitted')),
        scanner_gross=int(n['gross_lamports']),q18_same_bank_gross=expected,executor_same_bank_gross=int(leg['bank_gross']),
        scanner_slot=minslot,bank_slot=slot,bank_slot_gap=gap,source_age_at_bank_end_ms=age_ms,
        quote_model_result=same_bank,q18_reason=reason,leg_breakdown=leg,account_count=len(keys),
        account_fingerprint=parity.fingerprint(rows,keys),rpc_ms=round((t1-t0)/1e6,3),
        snapshot_decode_ms=round((t2-t1)/1e6,3),executor_quote_ms=round((t3-t2)/1e6,3),
        scanner_model_same_bank_ms=round((t4-t3)/1e6,3),single_context_verified=True,
        fee_adjusted_profit_certified=False,signing=False,broadcast=False,trade_ready=False)


def classify_result(result,ttl_ms):
    if result['quote_model_result']=='SAME_BANK_MODEL_MISMATCH':return 'HOLD_SAME_BANK_PRICING_DEFECT'
    if not result['admitted']:return 'TELEMETRY_ONLY_NOT_ADMITTED'
    if result['source_age_at_bank_end_ms']>ttl_ms:return 'HOLD_STALE_BANK_EVIDENCE'
    if result['quote_model_result']!='SAME_BANK_MODEL_PARITY':return 'HOLD_Q18_PARITY_UNCERTIFIED'
    if result['executor_same_bank_gross']<=0:return 'HOLD_BANK_NONPOSITIVE'
    return 'BANK_GROSS_POSITIVE_SHADOW_NOT_TRADE_READY'


def probe_finished(pending):
    return pending is not None and pending[1].done()


def run(seconds,pair_limit,cap,probes,ttl_ms,controls):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO')!='NO':
        raise RuntimeError('SHADOW_ONLY_SECRET_ENV_DISALLOWED')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    if not 20<=seconds<=1800 or not 1<=pair_limit<=28 or not 1<=cap<=80 or not 1<=probes<=40 or not 200<=ttl_ms<=5000 or not 0<=controls<=10:
        raise ValueError('INVALID_BOUNDED_PARAMETERS')
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_351_fast_bank_parity as old351
    from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as sdk
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as net
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
    audit=source_gate_audit();ROOT.mkdir(parents=True,exist_ok=True)
    c=scan.bus();counts=collections.Counter();out=[];seen_telemetry=set();queue={};pending=None
    reason='TIME_LIMIT';st_prev=None;last_status=0;last_emit=0;last_check=0;last_bus_id=None;source_counter_prev=None
    executor=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='oracle352_bank')
    try:
        hb=scan.validate_scanner(c);epoch=int(hb['epoch']);producer=hb['producer']
        inv=scan.inventory(pair_limit)
        catalogs,roles,diag=cat.discover(inv,url,cap)
        ready={t for t,x in catalogs.items() if x.get('discovery_complete') and int(x['bin_total'])==int(x['bin_selected'])}
        if not ready:raise RuntimeError('NO_READY_PAIRS')
        net.install_hot_token_net();decimals=bridge.mint_metadata(url,sorted(ready))
        for pair in inv:
            if pair['token'] in ready:sdk.worker().warm(pair['pump_pool'])
        hb=scan.validate_scanner(c)
        if int(hb['epoch'])!=epoch or hb['producer']!=producer:raise RuntimeError('SCANNER_EPOCH_CHANGED_DURING_SETUP')
        cursor=int(c.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
        emit('ORACLE352_READY',dict(epoch=epoch,producer=producer,admitted_pairs=len(inv),ready_pairs=len(ready),
            accounts_discovered=len(roles),metadata=len(decimals),cursor=cursor,feed='SCANNER_BUS_PLUS_TELEMETRY_NO_NEW_WS',
            source_audit=audit,signing=False,broadcast=False))
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline and counts['bank_submitted']<probes:
            try:hb=scan.validate_scanner(c)
            except Exception:reason='SCANNER_UNHEALTHY';break
            if int(hb['epoch'])!=epoch or hb['producer']!=producer:reason='EPOCH_OR_PRODUCER_CHANGED';break
            entries,cursor=scan.new_events(c,cursor)
            counts['bus_events']+=len(entries)
            for nom in old351.keep_latest(entries):
                try:
                    identity.vetted(nom,inv,hb)
                    if nom['token'] not in ready:raise ValueError('NOT_READY')
                    if int(nom['size_lamports'])!=SIZE:raise ValueError('NOT_CANARY_010')
                    if (time.time_ns()-int(nom['created_ns']))/1e6>ttl_ms:raise ValueError('NOMINATION_EXPIRED')
                    nom['admitted']=True
                    queue[(nom['token'],nom['direction'],nom['size_lamports'])]=nom
                    counts['bus_matched']+=1;last_bus_id=nom['id']
                except Exception as exc:
                    counts['bus_hold_'+type(exc).__name__]+=1
                    emit('ORACLE352_BUS_HOLD',dict(event_id=nom.get('id'),error_type=type(exc).__name__))
            now=time.monotonic()
            if now-last_status>=0.1:
                st=status_snapshot();last_status=now
                if st and st.get('epoch')==epoch:
                    adm=admission_classification(st,len(entries),source_counter_prev,last_bus_id)
                    current=(int(st.get('exact_gross_positive_010',0)),int(st.get('candidates_to_executor',0)))
                    if source_counter_prev is not None and current[0]>source_counter_prev[0] and current[1]==source_counter_prev[1]:
                        counts['unemitted_positive_increments']+=current[0]-source_counter_prev[0]
                        emit('ORACLE352_POSITIVE_NOT_ADMITTED',dict(epoch=epoch,
                            positive_delta=current[0]-source_counter_prev[0],candidate_delta=0,
                            classification=adm,possible_gates=audit['possible_unemitted_positive_reasons'],
                            exact_in_process_reason_not_exposed=True))
                    if source_counter_prev is None and current[0]>current[1]:
                        emit('ORACLE352_POSITIVE_GAP_AT_START',dict(
                            counted_gross_positives=current[0],admitted_candidates=current[1],
                            possible_gates=audit['possible_unemitted_positive_reasons'],
                            reason_not_exported_by_frozen_scanner=True))
                    source_counter_prev=current
                    st_prev=st
                    for n in status_candidates(st,inv):
                        key=(n['token'],n['direction'],n['slot'],n['gross_lamports'])
                        if key in seen_telemetry:continue
                        seen_telemetry.add(key)
                        # Quote negative controls to establish Q18 vs executor same-bank parity while bus is quiet.
                        if n['token'] not in ready:continue
                        if n['gross_lamports']>0:
                            counts['telemetry_positive_seen']+=1
                            if (time.time_ns()-n['created_ns'])/1e6 <= ttl_ms:
                                queue.setdefault((n['token'],n['direction'],SIZE),n)
                                counts['telemetry_positive_queued']+=1
                            else:counts['telemetry_positive_stale']+=1
                        elif counts['control_queued']<controls and now>last_check+2:
                            if (time.time_ns()-n['created_ns'])/1e6 < 8000:
                                queue.setdefault((n['token'],n['direction'],SIZE),n)
                                counts['control_queued']+=1;last_check=now
            if probe_finished(pending):
                n,f=pending;pending=None
                try:
                    r=f.result();r['gate']=classify_result(r,ttl_ms);out.append(r)
                    counts['bank_verified']+=1
                    if r['quote_model_result']=='SAME_BANK_MODEL_MISMATCH':counts['model_mismatch']+=1
                    if r['quote_model_result']=='SAME_BANK_MODEL_PARITY':counts['model_parity']+=1
                    if r['gate']=='BANK_GROSS_POSITIVE_SHADOW_NOT_TRADE_READY':counts['fresh_bank_positive']+=1
                    with LEDGER.open('a',encoding='utf-8') as log:log.write(json.dumps(r,sort_keys=True)+'\n')
                    emit('ORACLE352_BANK_PARITY',r)
                except Exception as exc:
                    counts['bank_error_'+type(exc).__name__]+=1
                    emit('ORACLE352_BANK_HOLD',dict(event_id=n.get('id'),error_type=type(exc).__name__,
                        token=n.get('token','')[:12]))
            if pending is None and queue and counts['bank_submitted']<probes:
                # Prioritize admitted candidates; after that use newest telemetry, never replay stale bank trades.
                n=max(queue.values(),key=lambda z:(bool(z.get('admitted')),z['created_ns']))
                queue.pop((n['token'],n['direction'],n['size_lamports']),None)
                age=(time.time_ns()-int(n['created_ns']))/1e6
                limit=ttl_ms if n.get('admitted') or n['gross_lamports']>0 else 8000
                if age>limit or age<0:counts['queue_expired']+=1
                else:
                    counts['bank_submitted']+=1
                    pending=(n,executor.submit(snapshot_quote,n,catalogs[n['token']],roles,url,decimals))
                    emit('ORACLE352_BANK_SUBMIT',dict(event_id=n.get('id'),admitted=bool(n.get('admitted')),
                        token=n['token'][:12],direction=n['direction'],scanner_gross=n['gross_lamports'],age_ms=round(age,2)))
            if now-last_emit>=3:
                emit('ORACLE352_HEARTBEAT',dict(epoch=epoch,bus_cursor=cursor,scanner_emitted=hb['emitted'],
                    scanner_admitted=hb['admitted'],bank_submitted=counts['bank_submitted'],bank_verified=counts['bank_verified'],
                    queue_len=len(queue),bank_inflight=pending is not None,scanner_positive_count=source_counter_prev[0] if source_counter_prev else None,
                    account_counter_uninstrumented=True,websocket_429_observed=st_prev.get('websocket_429') if st_prev else None))
                checkpoint=dict(build='ORACLE352',mode='RUNNING',epoch=epoch,cursor=cursor,
                    bank_verified=counts['bank_verified'],counters=dict(counts),
                    positive_counter=source_counter_prev[0] if source_counter_prev else None,
                    candidates_to_executor=source_counter_prev[1] if source_counter_prev else None,
                    scanner_gate_audit=audit,signing=False,broadcast=False,trade_ready=False)
                temp=REPORT.with_suffix('.tmp');temp.write_text(json.dumps(checkpoint,indent=2,sort_keys=True),encoding='utf-8');os.replace(temp,REPORT)
                last_emit=now
            time.sleep(.025)
        # Complete any already-submitted probe but never launch additional RPCs after the time limit.
        if pending:
            n,f=pending
            try:
                r=f.result(timeout=8);r['gate']=classify_result(r,ttl_ms);out.append(r)
                counts['bank_verified']+=1
                with LEDGER.open('a',encoding='utf-8') as log:log.write(json.dumps(r,sort_keys=True)+'\n')
                emit('ORACLE352_BANK_PARITY',r)
            except Exception:counts['bank_inflight_exit_error']+=1
        report=dict(build='ORACLE352',scanner_epoch=epoch,scanner_producer=producer,reason=reason,
            scanner_gate_audit=audit,counters=dict(counts),samples=out[-20:],
            websocket_connection_claim=False,feed='EXISTING_SCANNER_AND_HTTPS_ONLY',
            execution_authority=False,signing=False,broadcast=False,trade_ready=False)
        temp=REPORT.with_suffix('.tmp');temp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8');os.replace(temp,REPORT)
        emit('ORACLE352_EXIT',dict(reason=reason,counts=dict(counts),bank_verified=len(out),report=str(REPORT),
            signing=False,broadcast=False))
        return 0
    finally:
        c.close();executor.shutdown(wait=False,cancel_futures=True)


def tests():
    class Cases(unittest.TestCase):
        def test_parity_positive(self):
            self.assertEqual(quote_parity(3,3),'SAME_BANK_MODEL_PARITY')
        def test_parity_disagree(self):
            self.assertEqual(quote_parity(4,3),'SAME_BANK_MODEL_MISMATCH')
        def test_parity_missing(self):
            self.assertEqual(quote_parity(4,None),'SCANNER_Q18_UNAVAILABLE')
        def test_admission_explanation(self):
            self.assertEqual(admission_classification(dict(exact_gross_positive_010=2,candidates_to_executor=0),0,(1,0),None),'POSITIVE_COUNT_ROSE_BUT_NO_ADMITTED_EVENT')
        def test_counter_reset(self):
            self.assertEqual(admission_classification(dict(exact_gross_positive_010=0,candidates_to_executor=0),0,(5,1),None),'SCANNER_COUNTER_RESET')
        def test_telemetry_prefix_ambiguous(self):
            st=dict(recent_quotes=[dict(token='ABC',direction='PUMP_TO_METEORA',slot=1,gross_lamports=9,age_ms=200)])
            inv=[dict(token='ABC'+str(i),pump_pool='p',meteora_pool='m') for i in range(2)]
            self.assertEqual(status_candidates(st,inv),[])
        def test_telemetry_no_nomination(self):
            st=dict(recent_quotes=[dict(token='T123',direction='METEORA_TO_PUMP',slot=4,gross_lamports=23,age_ms=10)])
            inv=[dict(token='T123'+'abcd'*8,pump_pool='P',meteora_pool='M')]
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                global STATUS
                old=STATUS;STATUS=pathlib.Path(d)/'status.json';STATUS.write_text('{}')
                try:
                    n=status_candidates(st,inv)[0];self.assertFalse(n['admitted']);self.assertIsNone(n['id'])
                finally:STATUS=old
        def test_classify_unadmitted(self):
            self.assertEqual(classify_result(dict(quote_model_result='SAME_BANK_MODEL_PARITY',admitted=False,source_age_at_bank_end_ms=1,executor_same_bank_gross=42),2500),'TELEMETRY_ONLY_NOT_ADMITTED')
        def test_classify_stale(self):
            self.assertEqual(classify_result(dict(quote_model_result='SAME_BANK_MODEL_PARITY',admitted=True,source_age_at_bank_end_ms=2700,executor_same_bank_gross=42),2500),'HOLD_STALE_BANK_EVIDENCE')
        def test_frozen_scanner_gate_contract(self):
            self.assertTrue(source_gate_audit()['positive_increment_precedes_final_checks'])
        def test_single_bank_dual_model_same_bytes(self):
            from types import SimpleNamespace as S
            calls=[]
            def rpc(url,method,params,counts,retries):
                calls.append((method,params))
                return dict(context=dict(slot=105),value=[])
            data=dict(token='mint',pump_pool='pool',meteora_pool='dlmm',direction='PUMP_TO_METEORA',
                      slot=100,size_lamports=SIZE,gross_lamports=17,created_ns=time.time_ns(),source='fixture')
            adapters=(
                S(rpc=rpc),
                S(bank_rows=lambda reply,keys,minslot,start:({k:{'owner':'p','content_sha256':'abc'} for k in keys},105),
                  prepare_snapshot=lambda catalog,rows,roles,decimals,ns,core,decoder:(
                      dict(token='mint',pump_pool='pool'),dict(slot_min=105,slot_max=105))),
                S(leg_quote=lambda n,s,d:dict(bank_gross=123,leg_1_raw_token_out=7,leg_2_out_lamports=SIZE+123),
                  fingerprint=lambda r,k:'fingerprint'),
                S(exact_snapshot_opportunities=lambda s,z:[dict(direction='PUMP_TO_METEORA',start=SIZE,local_net=123)]),
                S(),S())
            roles={f'k{i}':[('mint',r)] for i,r in enumerate((
                'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'))}
            result=snapshot_quote(data,dict(discovery_complete=True,bin_selected=2,bin_total=2),
                                  roles,'https://localhost',{'mint':6},adapters=adapters)
            self.assertEqual(result['quote_model_result'],'SAME_BANK_MODEL_PARITY')
            self.assertEqual(result['q18_same_bank_gross'],123)
            self.assertEqual(result['executor_same_bank_gross'],123)
            self.assertEqual(result['bank_slot'],105)
            self.assertEqual(calls[0][0],'getMultipleAccounts')
            self.assertEqual(calls[0][1][1]['minContextSlot'],100)
            self.assertEqual(len(calls[0][1][0]),6)
            self.assertFalse(result['trade_ready'])
        def test_single_bank_true_model_mismatch(self):
            from types import SimpleNamespace as S
            bank= S(rpc=lambda *a,**k:dict(context=dict(slot=105),value=[]))
            bridge=S(bank_rows=lambda response,keys,slot,ns:({k:dict(owner='p',content_sha256='x') for k in keys},105),
                     prepare_snapshot=lambda *a:(dict(token='mint',pump_pool='pool'),dict(slot_min=105,slot_max=105)))
            parity=S(leg_quote=lambda *a:dict(bank_gross=80),fingerprint=lambda *a:'digest')
            q18=S(exact_snapshot_opportunities=lambda *a:[dict(start=SIZE,direction='PUMP_TO_METEORA',local_net=42)])
            keys=('PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE')
            roles={'k'+str(i):[('mint',r)] for i,r in enumerate(keys)}
            n=dict(token='mint',pump_pool='pool',meteora_pool='dlmm',direction='PUMP_TO_METEORA',
                   slot=100,size_lamports=SIZE,gross_lamports=17,created_ns=time.time_ns(),source='fixture')
            result=snapshot_quote(n,dict(discovery_complete=True,bin_selected=2,bin_total=2),
                        roles,'https://localhost',{'mint':6},adapters=(bank,bridge,parity,q18,S(),S()))
            self.assertEqual(result['quote_model_result'],'SAME_BANK_MODEL_MISMATCH')
            self.assertEqual(classify_result(dict(result,admitted=True),2500),'HOLD_SAME_BANK_PRICING_DEFECT')
        def test_q18_unavailable_is_not_parity(self):
            from types import SimpleNamespace as S
            bank=S(rpc=lambda *a,**k:dict(context=dict(slot=105),value=[]))
            bridge=S(bank_rows=lambda response,keys,slot,ns:({k:dict(owner='p',content_sha256='x') for k in keys},105),
                     prepare_snapshot=lambda *a:(dict(token='mint',pump_pool='pool'),dict(slot_min=105,slot_max=105)))
            parity=S(leg_quote=lambda *a:dict(bank_gross=80),fingerprint=lambda *a:'digest')
            q18=S(exact_snapshot_opportunities=lambda *a:[])
            keys=('PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE')
            roles={'k'+str(i):[('mint',r)] for i,r in enumerate(keys)}
            n=dict(token='mint',pump_pool='pool',meteora_pool='dlmm',direction='PUMP_TO_METEORA',
                   slot=100,size_lamports=SIZE,gross_lamports=17,created_ns=time.time_ns(),source='fixture')
            result=snapshot_quote(n,dict(discovery_complete=True,bin_selected=2,bin_total=2),
                        roles,'https://localhost',{'mint':6},adapters=(bank,bridge,parity,q18,S(),S()))
            self.assertEqual(result['quote_model_result'],'SCANNER_Q18_UNAVAILABLE')
            self.assertEqual(result['q18_reason'],'Q18_EXACT_DIRECTION_NOT_FOUND')
            self.assertEqual(classify_result(dict(result,admitted=True),2500),'HOLD_Q18_PARITY_UNCERTIFIED')
        def test_inflight_future_completion(self):
            from concurrent.futures import Future
            f=Future()
            self.assertFalse(probe_finished(None))
            self.assertFalse(probe_finished(({},f)))
            f.set_result(dict(gross=0))
            self.assertTrue(probe_finished(({},f)))
        def test_no_execution_claim(self):
            self.assertNotIn('sendTransaction',run.__code__.co_names)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    emit('ORACLE352_TEST',dict(tests=result.testsRun,passed=result.wasSuccessful()))
    return 0 if result.wasSuccessful() else 1


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run',action='store_true');p.add_argument('--test',action='store_true')
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--array-cap',type=int,default=60)
    p.add_argument('--probes',type=int,default=12)
    p.add_argument('--ttl-ms',type=int,default=2500)
    p.add_argument('--controls',type=int,default=3)
    a=p.parse_args()
    if a.test:return tests()
    if a.run:return run(a.seconds,a.pairs,a.array_cap,a.probes,a.ttl_ms,a.controls)
    p.error('SELECT_MODE')

if __name__=='__main__':raise SystemExit(main())
