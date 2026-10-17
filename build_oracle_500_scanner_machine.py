from __future__ import annotations
"""Full ORACLE-500 machine installer. Independent of V17/V17B; no source patching."""
import argparse,ast,hashlib,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_500_scanner_machine.py'
SOURCE='from __future__ import annotations\n"""ORACLE-500: one V16 scanner writer, canonical event bus; no signing."""\nimport argparse, getpass, hashlib, json, os, subprocess, sys, time\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[3]\nBASE=ROOT/\'runtime_state/oracle/final_boss_dual\'\nMODULE=\'qseries_v2.oracle_execution.solana_atomic_executor.final_boss_v16_supervisor\'\nSCANNER=ROOT/\'build_final_boss_v16_scanner_runtime.py\'\nSUPERVISOR=ROOT/\'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v16_supervisor.py\'\nSCANNER_SHA=\'7262e9b226495d2fd835feb7061894a37ff181b3f5dbf48b214d68e8a1d6a222\'\nSUPERVISOR_SHA=\'fdbc1e4b5cca602d623485e2ca1ba60ee95861ad270ed8b39590e6d29e5eb874\'\nCANONICAL_SCHEMA=\'events(id,producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source)\'\nSIZE_GRID=tuple(range(10_000_000,100_000_001,5_000_000))\nFORBIDDEN=(\'PRIVATE_KEY\',\'MNEMONIC\',\'KEYPAIR\',\'SEED_PHRASE\',\'SECRET\')\nclass Hold(RuntimeError):pass\n\ndef attest(path,expected):\n    if not path.is_file() or path.is_symlink():raise Hold(\'FROZEN_RUNTIME_NOT_FOUND\')\n    digest=hashlib.sha256(path.read_bytes().replace(b\'\\r\\n\',b\'\\n\')).hexdigest()\n    if digest!=expected:raise Hold(\'INSTALLED_V16_SHA_MISMATCH\')\n    return digest\n\ndef child_env(key,env=None):\n    src=os.environ if env is None else env\n    safe={k:v for k,v in src.items() if not any(x in k.upper() for x in FORBIDDEN)}\n    safe[\'SOLANA_RPC_URL\']=\'https://mainnet.helius-rpc.com/?api-key=\'+key\n    safe[\'SOLANA_WS_URL\']=\'wss://mainnet.helius-rpc.com/?api-key=\'+key\n    safe[\'QSB_LIVE_ARM\']=\'NO\'\n    return safe\n\ndef scanner_command(epoch_seconds=240,pairs=28,epochs=0):\n    if not 150<=epoch_seconds<=3600 or not 1<=pairs<=28 or not 0<=epochs<=1000:raise Hold(\'SCANNER_ARGUMENTS_INVALID\')\n    return [sys.executable,\'-m\',MODULE,\'--run\',\'--epochs\',str(epochs),\n            \'--epoch-seconds\',str(epoch_seconds),\'--pairs\',str(pairs)]\n\ndef snapshot():\n    def doc(name):\n        p=BASE/name\n        try:return json.loads(p.read_text(encoding=\'utf-8\')) if p.is_file() and not p.is_symlink() else {}\n        except (OSError,ValueError):return {}\n    p=BASE/\'scanner_status.json\';s=doc(\'scanner_status.json\');v=doc(\'final_boss_v16_supervisor.json\')\n    age=round(time.time()-p.stat().st_mtime,2) if p.exists() else None\n    return {\'scanner_status\':s.get(\'status\'),\'scanner_epoch\':s.get(\'epoch\'),\n            \'native_admitted\':s.get(\'admitted\'),\'gross_candidates_sent\':s.get(\'candidates_to_executor\'),\n            \'scanner_heartbeat_age_seconds\':age,\'supervisor_status\':v.get(\'status\'),\n            \'observer_started_by_scanner\':False,\'broadcast\':False,\'funded_execution\':False}\n\ndef tests():\n    assert len(SIZE_GRID)==19 and (SIZE_GRID[0],SIZE_GRID[-1])==(10_000_000,100_000_000)\n    e=child_env(\'EXAMPLE\',{\'QSB_SOLANA_PRIVATE_KEY\':\'never\',\'HI\':\'ok\',\'X_MNEMONIC\':\'never\'})\n    assert \'QSB_SOLANA_PRIVATE_KEY\' not in e and \'X_MNEMONIC\' not in e and e[\'HI\']==\'ok\'\n    assert e[\'QSB_LIVE_ARM\']==\'NO\'\n    c=scanner_command(240,28,2)\n    assert c[-6:]==[\'--epochs\',\'2\',\'--epoch-seconds\',\'240\',\'--pairs\',\'28\']\n    assert \'--observe-executor\' not in c and \'--signed-sim\' not in c\n    for args in ((149,28,1),(240,29,1),(240,28,-1)):\n        try:scanner_command(*args)\n        except Hold:pass\n        else:raise AssertionError(\'ARGUMENT_GATE_BYPASS\')\n    assert \'size_lamports\' in CANONICAL_SCHEMA and \'meteora_pool\' in CANONICAL_SCHEMA\n    print(\'[PASS] ORACLE500 single-writer command, V16 attestation, 19 sizes, secret scrub, no broadcast\')\n\ndef run(args):\n    attest(SCANNER,SCANNER_SHA);attest(SUPERVISOR,SUPERVISOR_SHA)\n    # V16 owns the actual cross-venue websocket, frozen exact Q18/Q20/Q25\n    # quotes, next-epoch V10 admission and canonical SQLite writes.\n    # This machine must NOT start a second observer or an alternate scanner.\n    k=getpass.getpass(\'Helius API key (hidden): \').strip()\n    if not k:raise Hold(\'HELIUS_KEY_REQUIRED\')\n    env=child_env(k);k=None\n    print(\'[ORACLE500_SCANNER] \'+json.dumps({\'mode\':\'V16_CANONICAL_SINGLE_WRITER\',\n        \'epochs\':args.epochs,\'epoch_seconds\':args.epoch_seconds,\'pairs_capacity\':args.pairs,\n        \'gross_best_size_grid\':len(SIZE_GRID),\'size_risk_net_certified\':False,\n        \'shared_bus\':\'ORACLE344_EVENTS_SQLITE\',\'executor_started\':False,\n        \'broadcast\':False,\'signing\':False},sort_keys=True),flush=True)\n    try:return subprocess.call(scanner_command(args.epoch_seconds,args.pairs,args.epochs),cwd=str(ROOT),env=env)\n    except KeyboardInterrupt:\n        print(\'[ORACLE500_INTERRUPT] Child supervisor owns orderly stop and lock lifecycle\',flush=True)\n        return 130\n\ndef main():\n    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)\n    g.add_argument(\'--test\',action=\'store_true\');g.add_argument(\'--inspect\',action=\'store_true\');g.add_argument(\'--run\',action=\'store_true\')\n    p.add_argument(\'--epochs\',type=int,default=0,help=\'0 = continuous controlled epochs\')\n    p.add_argument(\'--epoch-seconds\',type=int,default=240);p.add_argument(\'--pairs\',type=int,default=28)\n    a=p.parse_args()\n    try:\n        if a.test:tests();return 0\n        if a.inspect:print(\'[ORACLE500_INSPECT] \'+json.dumps(snapshot(),sort_keys=True));return 0\n        return run(a)\n    except Exception as e:\n        print(\'[ORACLE500_HOLD] \'+(str(e) if isinstance(e,Hold) else type(e).__name__).split(\':\')[0][:100],flush=True)\n        return 2\nif __name__==\'__main__\':raise SystemExit(main())\n'
ENGINE=''
ENGINE_TARGET=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_501_execution_engine.py'

def check():
    ast.parse(SOURCE)
    if ENGINE:ast.parse(ENGINE)
    if any(s in SOURCE for s in ('sendTransaction','sendRawTransaction','send_raw_transaction')):
        raise RuntimeError('BROADCAST_SYMBOL_FORBIDDEN')
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_500_scanner_machine.py';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(SOURCE,encoding='utf-8')
        rc=subprocess.call([sys.executable,str(p),'--test'])
        if rc:raise RuntimeError('DETERMINISTIC_TEST_FAILED')
        if ENGINE:
            ep=p.with_name('oracle_501_execution_engine.py');ep.write_text(ENGINE,encoding='utf-8')
            if subprocess.call([sys.executable,str(ep),'--test']):raise RuntimeError('NATIVE_ENGINE_TEST_FAILED')
    print('[PASS] COMPLETE_MODULE_SOURCE_AND_DETERMINISTIC_TESTS')

def install():
    check()
    if TARGET.is_symlink() or (ENGINE and ENGINE_TARGET.is_symlink()):raise RuntimeError('SYMLINK_TARGET_REFUSED')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    raw=SOURCE.encode('utf-8');sha=hashlib.sha256(raw).hexdigest()
    outputs=[(TARGET,raw)]+([(ENGINE_TARGET,ENGINE.encode('utf-8'))] if ENGINE else [])
    for path,data in outputs:
        if path.is_file() and path.read_bytes()!=data:raise RuntimeError('EXISTING_MACHINE_SOURCE_DRIFT_REFUSE_OVERWRITE')
    for path,data in outputs:
        if path.is_file():continue
        with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False,suffix='.tmp') as f:
            f.write(data);tmp=Path(f.name)
        try:os.replace(tmp,path)
        finally:tmp.unlink(missing_ok=True)
        assert path.read_bytes()==data
    print('[PASS] ORACLE_500_FULL_MACHINE_INSTALLED')
    print('[SHA256]',sha)
    print('[PRESERVED] Original ORACLE322 Q18/Q20/Q25 V14 V16 ORACLE402; no signing except explicit simulation; no broadcast')

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--install',action='store_true')
    a=p.parse_args()
    try:
        if a.test:check()
        else:install()
        return 0
    except Exception as e:
        print('[ORACLE_500_HOLD]',type(e).__name__,str(e)[:130]);return 2
if __name__=='__main__':raise SystemExit(main())
