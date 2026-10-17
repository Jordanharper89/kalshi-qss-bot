"""ORACLE-348 full replacement installer; shadow-only."""
import argparse,hashlib,pathlib,py_compile,tempfile,sys,os,subprocess

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_348_milestone_run.py')
SOURCE='"""ORACLE348 scanner-driven bank milestone verifier, read-only bounded shadow."""\nimport argparse,collections,json,os,time,sys,pathlib,hashlib\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as scan\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_345_pool_identity as identity\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_346_https_catalog as cat\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_347_one_bank_quote as bank\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old\nfrom qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18\nfrom qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23\nROOT=pathlib.Path(\'runtime_state/oracle/final_boss_dual\'); REPORT=ROOT/\'oracle_348_milestone.json\'; EVENTS=ROOT/\'oracle_348_evidence.jsonl\'\n\ndef run(seconds=180,inventory_limit=28,array_cap=24,probes=8,cooldown=3,ttl_ms=2500):\n    if os.getenv(\'QSB_SOLANA_PRIVATE_KEY\') or os.getenv(\'QSB_LIVE_ARM\',\'NO\')!=\'NO\':raise RuntimeError(\'SHADOW_ONLY_NO_PRIVATE_KEY\')\n    url=os.getenv(\'SOLANA_RPC_URL\',\'\')\n    if not url.startswith(\'https://\'):raise RuntimeError(\'HTTPS_RPC_REQUIRED\')\n    ROOT.mkdir(parents=True,exist_ok=True)\n    db=scan.bus();stats=collections.Counter();last=0.;results=[];epoch=None\n    try:\n        hb=scan.validate_scanner(db);epoch=hb[\'epoch\'];producer=hb[\'producer\']\n        pairs=scan.inventory(inventory_limit)\n        print(\'[ORACLE348_DISCOVERY_START] \'+json.dumps({\'pairs\':len(pairs),\'epoch\':epoch}),flush=True)\n        cats,roles,diag=cat.discover(pairs,url,array_cap)\n        q23.install_hot_token_net()\n        try:q23.worker().refresh_epoch()\n        except Exception:pass\n        ready={t for t,c in cats.items() if c.get(\'discovery_complete\') and c[\'bin_selected\']==c[\'bin_total\']}\n        print(\'[ORACLE348_DISCOVERY_READY] \'+json.dumps({\'pairs\':len(pairs),\'complete\':len(ready),\'roles\':len(roles),\'stats\':diag}),flush=True)\n        # Start after discovery so every nomination is new and never stale replay.\n        cursor=int(db.execute(\'SELECT COALESCE(MAX(id),0) FROM events\').fetchone()[0]); deadline=time.monotonic()+seconds\n        while time.monotonic()<deadline:\n            hb=scan.validate_scanner(db)\n            if hb[\'epoch\']!=epoch or hb[\'producer\']!=producer:\n                stats[\'epoch_change_holds\']+=1;break\n            rows,cursor=scan.new_events(db,cursor)\n            stats[\'nominations_seen\']+=len(rows)\n            for nom in old.coalesce(rows):\n                try:\n                    identity.vetted(nom,pairs,hb)\n                    if old.nomination_age(nom,time.time_ns(),ttl_ms) is None:raise ValueError(\'NOMINATION_EXPIRED\')\n                    if nom[\'token\'] not in ready:raise ValueError(\'POOL_NOT_IN_READY_CATALOG\')\n                    if stats[\'bank_attempts\']>=probes or time.monotonic()-last<cooldown:raise ValueError(\'PROBE_BUDGET_OR_COOLDOWN\')\n                    stats[\'matched_nominations\']+=1;last=time.monotonic();stats[\'bank_attempts\']+=1\n                    q18.worker().warm(nom[\'pump_pool\'])\n                    result=bank.reprice(nom,cats[nom[\'token\']],roles,url)\n                    result.update(event_id=nom[\'id\'],epoch=epoch,execution_authority=False,trade_ready=False)\n                    stats[\'bank_verified\']+=int(result[\'single_context_verified\'])\n                    stats[\'bank_positive\']+=int(result[\'gate\']==\'BANK_GROSS_POSITIVE\')\n                    results.append(result)\n                    print(\'[ORACLE348_BANK_RESULT] \'+json.dumps(result,sort_keys=True),flush=True)\n                    with EVENTS.open(\'a\',encoding=\'utf8\') as f:f.write(json.dumps(result,sort_keys=True)+\'\\n\')\n                except Exception as e:\n                    reason=type(e).__name__+\':\'+str(e)\n                    # Prevent URL/secret propagation in failures.\n                    reason=old.redacted(e)\n                    stats[\'hold_\'+reason.split(\':\')[0]]+=1\n                    print(\'[ORACLE348_HOLD] \'+json.dumps({\'event_id\':nom[\'id\'],\'token\':nom[\'token\'][:12],\'reason\':reason}),flush=True)\n            if len(results)>0 and any(x[\'single_context_verified\'] for x in results):break\n            time.sleep(.1)\n        report=dict(stats=dict(stats),bank_results=results,scanner_sha256=hashlib.sha256(pathlib.Path(\'qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py\').read_bytes()).hexdigest(),signing=False,broadcast=False,production_cutover=False)\n        old.atomic_write(REPORT,report)\n        print(\'[ORACLE348_EXIT] \'+json.dumps(report,sort_keys=True),flush=True)\n        return 0\n    finally:db.close()\n\ndef main():\n    p=argparse.ArgumentParser();p.add_argument(\'--seconds\',type=int,default=180);p.add_argument(\'--pairs\',type=int,default=28);p.add_argument(\'--array-cap\',type=int,default=24);p.add_argument(\'--probes\',type=int,default=8)\n    a=p.parse_args();return run(a.seconds,a.pairs,a.array_cap,a.probes)\nif __name__==\'__main__\':raise SystemExit(main())\n'
EXPECTED='1553feba173977d203fff8233d24221784eacd1163464e06e4255026dab8397f'

def install():
    assert hashlib.sha256(SOURCE.encode()).hexdigest()==EXPECTED
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode())
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE348_INSTALL_PASS] '+str(TARGET));return 0

def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)/TARGET.name
        p.write_bytes(SOURCE.encode())
        py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    assert 'sendTransaction' not in SOURCE and 'sign_transaction' not in SOURCE
    print('[ORACLE348_TEST_PASS] source,hash,syntax,no_send');return 0

def audit():
    assert EXPECTED==hashlib.sha256(SOURCE.encode()).hexdigest()
    print('[ORACLE348_AUDIT] FROZEN_SCANNER_UNTOUCHED SIGNING_FALSE BROADCAST_FALSE')
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--install',action='store_true')
    p.add_argument('--test',action='store_true')
    p.add_argument('--audit',action='store_true')
    p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--pairs',type=int,default=28)
    p.add_argument('--array-cap',type=int,default=24)
    p.add_argument('--probes',type=int,default=8)
    a=p.parse_args()
    if a.install:return install()
    if a.test:return test()
    if a.audit:return audit()
    if a.run:
        from build_oracle_343_unified_feed_recovery import launch_env
        env,_=launch_env(os.environ)
        return subprocess.call([
            sys.executable,'-m',
            'qseries_v2.oracle_execution.solana_atomic_executor.oracle_348_milestone_run',
            '--seconds',str(a.seconds),
            '--pairs',str(a.pairs),
            '--array-cap',str(a.array_cap),
            '--probes',str(a.probes)
        ],env=env)
    p.error('SELECT_A_MODE')

if __name__=='__main__':raise SystemExit(main())