"""ORACLE350 two-leg single-bank parity and stage-latency diagnostic, shadow only."""
import argparse,collections,hashlib,json,os,pathlib,time,unittest
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_bank_requote as bridge
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_349_bank_survival as baseline
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as sdk
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as net
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as decoder
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT=ROOT/'oracle_350_parity_report.json'; LEDGER=ROOT/'oracle_350_parity_evidence.jsonl'
def line(tag,thing):print('['+tag+'] '+json.dumps(thing,sort_keys=True,default=str),flush=True)
def fingerprint(rows,keys):
    h=hashlib.sha256()
    for k in keys:
        row=rows[k];h.update(k.encode());h.update(str(row.get('owner','')).encode());h.update(str(row.get('content_sha256',row.get('data_b64',''))).encode())
    return h.hexdigest()
def leg_quote(n,snap,decimals):
    size=int(n['size_lamports']);token=n['token'];d=n['direction'];start=time.perf_counter_ns()
    if d=='PUMP_TO_METEORA':
        first=sdk.worker().buy(snap,size);raw=int(first['baseOut']);net_tokens=int(sdk.token_net(token,raw))
        if raw<=0 or net_tokens<=0 or net_tokens>raw:raise ValueError('PUMP_BUY_OR_FEE_INVALID')
        end,partial=bridge.dlmm_quote_or_partial(snap,net_tokens,token,core)
        if partial:raise ValueError('DLMM_PARTIAL')
        steps={'leg_1':'PUMP_BUY','leg_1_input_lamports':size,'leg_1_raw_token_out':raw,'leg_1_net_token_out':net_tokens,'leg_2':'DLMM_SELL','leg_2_input_tokens':net_tokens,'leg_2_out_lamports':int(end)}
    elif d=='METEORA_TO_PUMP':
        raw,partial=bridge.dlmm_quote_or_partial(snap,size,bridge.SOL,core)
        if partial:raise ValueError('DLMM_PARTIAL')
        net_tokens=int(sdk.token_net(token,int(raw)))
        if raw<=0 or net_tokens<=0 or net_tokens>raw:raise ValueError('DLMM_OUT_OR_FEE_INVALID')
        second=sdk.worker().sell(snap,net_tokens);end=int(second['uiQuote'])
        steps={'leg_1':'DLMM_BUY','leg_1_input_lamports':size,'leg_1_raw_token_out':int(raw),'leg_1_net_token_out':net_tokens,'leg_2':'PUMP_SELL','leg_2_input_tokens':net_tokens,'leg_2_out_lamports':int(end)}
    else:raise ValueError('UNKNOWN_DIRECTION')
    if int(end)<0:raise ValueError('NEGATIVE_OUTPUT')
    steps.update(bank_gross=int(end)-size,quote_ms=round((time.perf_counter_ns()-start)/1e6,3))
    return steps
def one(n,catalog,roles,url,decimals):
    if not catalog.get('discovery_complete') or catalog['bin_total']!=catalog['bin_selected']:raise ValueError('INCOMPLETE_CATALOG')
    keys=sorted(k for k,rr in roles.items() if any(t==n['token'] for t,_ in rr))
    required={'PUMP_POOL','DLMM_POOL','PUMP_BASE_VAULT','PUMP_QUOTE_VAULT','DLMM_SOL_RESERVE','DLMM_TOKEN_RESERVE'}
    present={role for k in keys for t,role in roles[k] if t==n['token']}
    if not required.issubset(present) or not 6<=len(keys)<=100:raise ValueError('ACCOUNT_ROLE_OR_COUNT')
    t0=time.perf_counter_ns();ns=time.time_ns();rpc=witness.rpc(url,'getMultipleAccounts',[keys,{'encoding':'base64','commitment':'processed','minContextSlot':int(n['slot'])}],collections.Counter(),retries=1)
    t1=time.perf_counter_ns();rows,slot=bridge.bank_rows(rpc,keys,int(n['slot']),ns);t2=time.perf_counter_ns()
    snapshot,lineage=bridge.prepare_snapshot(catalog,rows,roles,decimals,ns-1,core,decoder);t3=time.perf_counter_ns()
    if lineage['slot_min']!=slot or lineage['slot_max']!=slot:raise ValueError('MIXED_BANK_SLOT')
    out1=leg_quote(n,snapshot,decimals);out2=leg_quote(n,snapshot,decimals)
    if out1['bank_gross']!=out2['bank_gross'] or any(out1.get(k)!=out2.get(k) for k in ('leg_1_raw_token_out','leg_1_net_token_out','leg_2_out_lamports')):raise ValueError('NONDETERMINISTIC_SAME_BANK_QUOTE')
    total_ms=(time.perf_counter_ns()-t0)/1e6
    return dict(event_id=n['id'],token=n['token'],pump_pool=n['pump_pool'],meteora_pool=n['meteora_pool'],direction=n['direction'],size_lamports=n['size_lamports'],source=n.get('source'),source_generation=n.get('generation'),scanner_slot=n['slot'],bank_slot=slot,slot_gap=slot-n['slot'],scanner_gross=n['gross_lamports'],bank_gross=out1['bank_gross'],delta_lamports=out1['bank_gross']-n['gross_lamports'],scanner_bps=round(1e4*n['gross_lamports']/n['size_lamports'],3),bank_bps=round(1e4*out1['bank_gross']/n['size_lamports'],3),account_count=len(keys),fingerprint=fingerprint(rows,keys),rpc_ms=round((t1-t0)/1e6,3),decode_ms=round((t3-t2)/1e6,3),total_ms=round(total_ms,3),first=out1,repeat=out2,same_bank_deterministic=True,fee_adjusted=False,signing=False,broadcast=False,trade_ready=False)
def run(seconds,pairs,cap,probes,ttl):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO')!='NO':raise RuntimeError('PRIVATE_KEY_DISALLOWED')
    url=os.getenv('SOLANA_RPC_URL','');assert url.startswith('https://')
    if not 30<=seconds<=1800 or not 1<=pairs<=28 or not 1<=cap<=80 or not 1<=probes<=30 or not 500<=ttl<=5000:raise ValueError('PARAMETERS_OUT_OF_RANGE')
    baseline.scanner_guard();ROOT.mkdir(parents=True,exist_ok=True);counts=collections.Counter();observed=[];db=scan.bus()
    try:
        hb=scan.validate_scanner(db);epoch=hb['epoch'];producer=hb['producer'];inventory=scan.inventory(pairs)
        cats,roles,disc=cat.discover(inventory,url,cap);ready={t for t,c in cats.items() if c['discovery_complete'] and c['bin_selected']==c['bin_total']}
        net.install_hot_token_net();decimals=bridge.mint_metadata(url,sorted(ready))
        for p in inventory:
            if p['token'] in ready:sdk.worker().warm(p['pump_pool'])
        hb=scan.validate_scanner(db)
        if hb['epoch']!=epoch or hb['producer']!=producer:raise RuntimeError('EPOCH_CHANGED_DURING_WARMUP')
        cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]);line('ORACLE350_READY',dict(pairs=len(inventory),complete=len(ready),watched_accounts=len(roles),decimals=len(decimals),cursor=cursor,epoch=epoch))
        deadline=time.monotonic()+seconds;last=-1e8;held={}
        while time.monotonic()<deadline and counts['probes']<probes:
            try:hb=scan.validate_scanner(db)
            except Exception:counts['scanner_unhealthy']+=1;break
            if hb['epoch']!=epoch or hb['producer']!=producer:counts['epoch_change']+=1;break
            incoming,cursor=scan.new_events(db,cursor);counts['events']+=len(incoming)
            for n in old.coalesce(incoming):
                try:
                    identity.vetted(n,inventory,hb)
                    if n['token'] not in ready:raise ValueError('NO_FULL_CATALOG')
                    if old.nomination_age(n,time.time_ns(),ttl) is None:raise ValueError('EXPIRED_BEFORE_PROBE')
                    if time.monotonic()-last<2:counts['cooldown']+=1;continue
                    last=time.monotonic();counts['probes']+=1;entry=one(n,cats[n['token']],roles,url,decimals)
                    entry['age_at_completion_ms']=round((time.time_ns()-n['created_ns'])/1e6,2)
                    entry['outcome']='BANK_POSITIVE_SHADOW' if entry['bank_gross']>0 and entry['age_at_completion_ms']<=ttl else 'HOLD_NO_FRESH_BANK_PROFIT'
                    observed.append(entry);counts['verified']+=1;counts['positive']+=int(entry['outcome']=='BANK_POSITIVE_SHADOW')
                    with LEDGER.open('a',encoding='utf-8') as f:f.write(json.dumps(entry,sort_keys=True)+'\n')
                    line('ORACLE350_PARITY_RESULT',entry)
                except Exception as exc:
                    counts['held']+=1;key=type(exc).__name__;held[key]=held.get(key,0)+1
                    line('ORACLE350_HOLD',dict(event_id=n.get('id'),error_class=key,reason=old.redacted(exc)))
                if counts['probes']>=probes:break
            time.sleep(.05)
        report=dict(build='ORACLE350',bank_verified=len(observed),bank_positive=counts['positive'],counts=dict(counts),holds=held,results=observed,scanner_sha=baseline.SCANNER_SHA,signing=False,broadcast=False,trade_ready=False)
        old.atomic_write(REPORT,report);line('ORACLE350_EXIT',dict(bank_verified=len(observed),bank_positive=counts['positive'],counts=dict(counts),holds=held,report=str(REPORT)))
        return 0 if observed else 2
    finally:db.close()
def tests():
    class T(unittest.TestCase):
        def test_fingerprint(self):
            rows={'a':{'owner':'p','content_sha256':'abcd'}};self.assertEqual(fingerprint(rows,['a']),fingerprint(rows,['a']))
            self.assertNotEqual(fingerprint(rows,['a']),fingerprint({'a':{'owner':'p','content_sha256':'def'}},['a']))
        def test_leg_forward(self):
            import types
            global sdk,bridge,core
            a,b,c=sdk,bridge,core
            try:
                sdk=types.SimpleNamespace(worker=lambda:types.SimpleNamespace(buy=lambda s,n:{'baseOut':100}),token_net=lambda t,n:95)
                bridge=types.SimpleNamespace(dlmm_quote_or_partial=lambda s,n,t,c:(11000000,False),SOL='SOL')
                out=leg_quote(dict(token='T',direction='PUMP_TO_METEORA',size_lamports=10000000),{},None)
                self.assertEqual(out['bank_gross'],1000000);self.assertEqual(out['leg_1_net_token_out'],95)
            finally:sdk,bridge,core=a,b,c
        def test_leg_reverse(self):
            import types
            global sdk,bridge,core
            a,b,c=sdk,bridge,core
            try:
                sdk=types.SimpleNamespace(worker=lambda:types.SimpleNamespace(sell=lambda s,n:{'uiQuote':9900000}),token_net=lambda t,n:95)
                bridge=types.SimpleNamespace(dlmm_quote_or_partial=lambda s,n,t,c:(100,False),SOL='SOL')
                out=leg_quote(dict(token='T',direction='METEORA_TO_PUMP',size_lamports=10000000),{},None)
                self.assertEqual(out['bank_gross'],-100000);self.assertEqual(out['leg_1_net_token_out'],95)
            finally:sdk,bridge,core=a,b,c
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));return 0 if result.wasSuccessful() else 1
def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--seconds',type=int,default=300);p.add_argument('--pairs',type=int,default=28);p.add_argument('--array-cap',type=int,default=60);p.add_argument('--probes',type=int,default=12);p.add_argument('--ttl-ms',type=int,default=2500)
    a=p.parse_args();return tests() if a.test else run(a.seconds,a.pairs,a.array_cap,a.probes,a.ttl_ms) if a.run else p.error('MODE_REQUIRED')
if __name__=='__main__':raise SystemExit(main())
