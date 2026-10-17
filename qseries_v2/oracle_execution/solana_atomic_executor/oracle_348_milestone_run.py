"""ORACLE348 scanner-driven bank milestone verifier, read-only bounded shadow."""
import argparse,collections,json,os,time,sys,pathlib,hashlib
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_347_one_bank_quote as bank
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual'); REPORT=ROOT/'oracle_348_milestone.json'; EVENTS=ROOT/'oracle_348_evidence.jsonl'

def run(seconds=180,inventory_limit=28,array_cap=24,probes=8,cooldown=3,ttl_ms=2500):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO')!='NO':raise RuntimeError('SHADOW_ONLY_NO_PRIVATE_KEY')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    ROOT.mkdir(parents=True,exist_ok=True)
    db=scan.bus();stats=collections.Counter();last=0.;results=[];epoch=None
    try:
        hb=scan.validate_scanner(db);epoch=hb['epoch'];producer=hb['producer']
        pairs=scan.inventory(inventory_limit)
        print('[ORACLE348_DISCOVERY_START] '+json.dumps({'pairs':len(pairs),'epoch':epoch}),flush=True)
        cats,roles,diag=cat.discover(pairs,url,array_cap)
        q23.install_hot_token_net()
        try:q23.worker().refresh_epoch()
        except Exception:pass
        ready={t for t,c in cats.items() if c.get('discovery_complete') and c['bin_selected']==c['bin_total']}
        print('[ORACLE348_DISCOVERY_READY] '+json.dumps({'pairs':len(pairs),'complete':len(ready),'roles':len(roles),'stats':diag}),flush=True)
        # Start after discovery so every nomination is new and never stale replay.
        cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0]); deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            hb=scan.validate_scanner(db)
            if hb['epoch']!=epoch or hb['producer']!=producer:
                stats['epoch_change_holds']+=1;break
            rows,cursor=scan.new_events(db,cursor)
            stats['nominations_seen']+=len(rows)
            for nom in old.coalesce(rows):
                try:
                    identity.vetted(nom,pairs,hb)
                    if old.nomination_age(nom,time.time_ns(),ttl_ms) is None:raise ValueError('NOMINATION_EXPIRED')
                    if nom['token'] not in ready:raise ValueError('POOL_NOT_IN_READY_CATALOG')
                    if stats['bank_attempts']>=probes or time.monotonic()-last<cooldown:raise ValueError('PROBE_BUDGET_OR_COOLDOWN')
                    stats['matched_nominations']+=1;last=time.monotonic();stats['bank_attempts']+=1
                    q18.worker().warm(nom['pump_pool'])
                    result=bank.reprice(nom,cats[nom['token']],roles,url)
                    result.update(event_id=nom['id'],epoch=epoch,execution_authority=False,trade_ready=False)
                    stats['bank_verified']+=int(result['single_context_verified'])
                    stats['bank_positive']+=int(result['gate']=='BANK_GROSS_POSITIVE')
                    results.append(result)
                    print('[ORACLE348_BANK_RESULT] '+json.dumps(result,sort_keys=True),flush=True)
                    with EVENTS.open('a',encoding='utf8') as f:f.write(json.dumps(result,sort_keys=True)+'\n')
                except Exception as e:
                    reason=type(e).__name__+':'+str(e)
                    # Prevent URL/secret propagation in failures.
                    reason=old.redacted(e)
                    stats['hold_'+reason.split(':')[0]]+=1
                    print('[ORACLE348_HOLD] '+json.dumps({'event_id':nom['id'],'token':nom['token'][:12],'reason':reason}),flush=True)
            if len(results)>0 and any(x['single_context_verified'] for x in results):break
            time.sleep(.1)
        report=dict(stats=dict(stats),bank_results=results,scanner_sha256=hashlib.sha256(pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py').read_bytes()).hexdigest(),signing=False,broadcast=False,production_cutover=False)
        old.atomic_write(REPORT,report)
        print('[ORACLE348_EXIT] '+json.dumps(report,sort_keys=True),flush=True)
        return 0
    finally:db.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=180);p.add_argument('--pairs',type=int,default=28);p.add_argument('--array-cap',type=int,default=24);p.add_argument('--probes',type=int,default=8)
    a=p.parse_args();return run(a.seconds,a.pairs,a.array_cap,a.probes)
if __name__=='__main__':raise SystemExit(main())
