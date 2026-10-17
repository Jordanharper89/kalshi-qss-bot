from __future__ import annotations
"""ORACLE-500: one V16 scanner writer, canonical event bus; no signing."""
import argparse, getpass, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runtime_state/oracle/final_boss_dual'
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.final_boss_v16_supervisor'
SCANNER=ROOT/'build_final_boss_v16_scanner_runtime.py'
SUPERVISOR=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v16_supervisor.py'
SCANNER_SHA='7262e9b226495d2fd835feb7061894a37ff181b3f5dbf48b214d68e8a1d6a222'
SUPERVISOR_SHA='fdbc1e4b5cca602d623485e2ca1ba60ee95861ad270ed8b39590e6d29e5eb874'
CANONICAL_SCHEMA='events(id,producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source)'
SIZE_GRID=tuple(range(10_000_000,100_000_001,5_000_000))
FORBIDDEN=('PRIVATE_KEY','MNEMONIC','KEYPAIR','SEED_PHRASE','SECRET')
class Hold(RuntimeError):pass

def attest(path,expected):
    if not path.is_file() or path.is_symlink():raise Hold('FROZEN_RUNTIME_NOT_FOUND')
    digest=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    if digest!=expected:raise Hold('INSTALLED_V16_SHA_MISMATCH')
    return digest

def child_env(key,env=None):
    src=os.environ if env is None else env
    safe={k:v for k,v in src.items() if not any(x in k.upper() for x in FORBIDDEN)}
    safe['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+key
    safe['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+key
    safe['QSB_LIVE_ARM']='NO'
    return safe

def scanner_command(epoch_seconds=240,pairs=28,epochs=0):
    if not 150<=epoch_seconds<=3600 or not 1<=pairs<=28 or not 0<=epochs<=1000:raise Hold('SCANNER_ARGUMENTS_INVALID')
    return [sys.executable,'-m',MODULE,'--run','--epochs',str(epochs),
            '--epoch-seconds',str(epoch_seconds),'--pairs',str(pairs)]

def snapshot():
    def doc(name):
        p=BASE/name
        try:return json.loads(p.read_text(encoding='utf-8')) if p.is_file() and not p.is_symlink() else {}
        except (OSError,ValueError):return {}
    p=BASE/'scanner_status.json';s=doc('scanner_status.json');v=doc('final_boss_v16_supervisor.json')
    age=round(time.time()-p.stat().st_mtime,2) if p.exists() else None
    return {'scanner_status':s.get('status'),'scanner_epoch':s.get('epoch'),
            'native_admitted':s.get('admitted'),'gross_candidates_sent':s.get('candidates_to_executor'),
            'scanner_heartbeat_age_seconds':age,'supervisor_status':v.get('status'),
            'observer_started_by_scanner':False,'broadcast':False,'funded_execution':False}

def tests():
    assert len(SIZE_GRID)==19 and (SIZE_GRID[0],SIZE_GRID[-1])==(10_000_000,100_000_000)
    e=child_env('EXAMPLE',{'QSB_SOLANA_PRIVATE_KEY':'never','HI':'ok','X_MNEMONIC':'never'})
    assert 'QSB_SOLANA_PRIVATE_KEY' not in e and 'X_MNEMONIC' not in e and e['HI']=='ok'
    assert e['QSB_LIVE_ARM']=='NO'
    c=scanner_command(240,28,2)
    assert c[-6:]==['--epochs','2','--epoch-seconds','240','--pairs','28']
    assert '--observe-executor' not in c and '--signed-sim' not in c
    for args in ((149,28,1),(240,29,1),(240,28,-1)):
        try:scanner_command(*args)
        except Hold:pass
        else:raise AssertionError('ARGUMENT_GATE_BYPASS')
    assert 'size_lamports' in CANONICAL_SCHEMA and 'meteora_pool' in CANONICAL_SCHEMA
    print('[PASS] ORACLE500 single-writer command, V16 attestation, 19 sizes, secret scrub, no broadcast')

def run(args):
    attest(SCANNER,SCANNER_SHA);attest(SUPERVISOR,SUPERVISOR_SHA)
    # V16 owns the actual cross-venue websocket, frozen exact Q18/Q20/Q25
    # quotes, next-epoch V10 admission and canonical SQLite writes.
    # This machine must NOT start a second observer or an alternate scanner.
    k=getpass.getpass('Helius API key (hidden): ').strip()
    if not k:raise Hold('HELIUS_KEY_REQUIRED')
    env=child_env(k);k=None
    print('[ORACLE500_SCANNER] '+json.dumps({'mode':'V16_CANONICAL_SINGLE_WRITER',
        'epochs':args.epochs,'epoch_seconds':args.epoch_seconds,'pairs_capacity':args.pairs,
        'gross_best_size_grid':len(SIZE_GRID),'size_risk_net_certified':False,
        'shared_bus':'ORACLE344_EVENTS_SQLITE','executor_started':False,
        'broadcast':False,'signing':False},sort_keys=True),flush=True)
    try:return subprocess.call(scanner_command(args.epoch_seconds,args.pairs,args.epochs),cwd=str(ROOT),env=env)
    except KeyboardInterrupt:
        print('[ORACLE500_INTERRUPT] Child supervisor owns orderly stop and lock lifecycle',flush=True)
        return 130

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--inspect',action='store_true');g.add_argument('--run',action='store_true')
    p.add_argument('--epochs',type=int,default=0,help='0 = continuous controlled epochs')
    p.add_argument('--epoch-seconds',type=int,default=240);p.add_argument('--pairs',type=int,default=28)
    a=p.parse_args()
    try:
        if a.test:tests();return 0
        if a.inspect:print('[ORACLE500_INSPECT] '+json.dumps(snapshot(),sort_keys=True));return 0
        return run(a)
    except Exception as e:
        print('[ORACLE500_HOLD] '+(str(e) if isinstance(e,Hold) else type(e).__name__).split(':')[0][:100],flush=True)
        return 2
if __name__=='__main__':raise SystemExit(main())
