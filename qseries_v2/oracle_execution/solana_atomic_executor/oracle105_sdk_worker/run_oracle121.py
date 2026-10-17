"""ORACLE-121 integrated Mriya discovery, replenishment and guarded atomic evaluator.
Full launch program. Does not edit existing scanner. Does not use private key.
"""
from __future__ import annotations
import argparse
import getpass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path.cwd()
DIR = Path(__file__).resolve().parent
JS = DIR / 'oracle121_atomic_machine.cjs'
DISCOVERY = 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'
REPLENISH = 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_071_continuous_mriya_replenishment'
REGISTRY = ROOT / 'runtime_state/qseries/qarb_clean_bot/qarb_071_replenishment.json'
CANONICAL = ROOT / 'runtime_state/oracle/oracle_live_execution/ORACLE_121_LIVE_REPLENISHED_PAIRS.json'
STATIC = ROOT / 'runtime_state/oracle/solana_atomic_executor'
KEYS = ('token','pump_pool','meteora_pool')

def read(path):
    try:
        if path.stat().st_size > 15_000_000:
            return {}
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return {}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding='utf-8')
    os.replace(temp, path)

def rows(data):
    return data if isinstance(data, list) else data.get('rows', []) if isinstance(data, dict) else []

def materialize():
    discovery = read(REGISTRY)
    fresh = discovery.get('tokens', {}) if isinstance(discovery, dict) else {}
    candidates = {}
    # Discovery output is authoritative for fresh pool identities, but it may only contain token IDs.
    for item in fresh.values() if isinstance(fresh, dict) else []:
        if isinstance(item, dict) and all(item.get(k) for k in KEYS):
            k=tuple(item[x] for x in KEYS)
            candidates[k]=dict(item, source='MRIYA_REPLENISHED')
    # Historical identities are NOT evidence of current on-chain freshness. SDK must validate them.
    for name in ('live_hot_book.json','capacity_aware_warm_universe.json',
                 'full_surface_replenishment_inventory.json','multi_dlmm_pair_registry.json'):
        for item in rows(read(STATIC/name)):
            if isinstance(item,dict) and all(item.get(k) for k in KEYS):
                k=tuple(item[x] for x in KEYS)
                candidates.setdefault(k,dict(item,source='POOL_IDENTITY_ONLY'))
    out={'revision':'ORACLE-121','observed_unix':time.time(),
         'discovery_registry_updated_unix': discovery.get('updated_epoch') if isinstance(discovery,dict) else None,
         'discovered_registry_tokens':len(fresh) if isinstance(fresh,dict) else 0,
         'replenished_valid_identities':sum(x.get('source')=='MRIYA_REPLENISHED' for x in candidates.values()),
         'rows':list(candidates.values()),'minimum_fresh_pairs':28,'fresh_pairs_verified':0,
         'inventory_is_identity_only':True,'execution_authority':False,'broadcast':False}
    write(CANONICAL,out)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--watch',action='store_true')
    ap.add_argument('--trade',action='store_true')
    ap.add_argument('--once',action='store_true')
    a=ap.parse_args()
    if a.trade:
        print('[HOLD] LIVE_EXECUTION_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST')
        return 2
    if not shutil.which('node') or not JS.is_file():
        print('[HOLD] JS_WORKER_OR_NODE_MISSING')
        return 2
    if not (ROOT/'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_043b_paced_mriya_token_discovery.py').is_file():
        print('[HOLD] MRIYA_DISCOVERY_MODULE_MISSING: repository copy must include original scanner')
        return 2
    env=os.environ.copy()
    if not env.get('SOLANA_RPC_URL','').startswith('https://'):
        key=getpass.getpass('Helius API key (hidden): ').strip()
        if not key:return 2
        env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+key
    env.setdefault('SOLANA_WS_URL',env['SOLANA_RPC_URL'].replace('https://','wss://',1))
    # Read-only worker requires a public wallet address; derive from secret in isolated Node worker if given.
    if not env.get('QSB_SOLANA_PRIVATE_KEY') and not env.get('ORACLE_PUBLIC_KEY'):
        print('[HOLD] Set ORACLE_PUBLIC_KEY in CMD for read-only mode; no private key required')
        return 2
    # Do not forward wallet secret to scanner or discovery. Evaluator may derive wallet pubkey if already supplied.
    scanenv={k:v for k,v in env.items() if not any(s in k.upper() for s in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC'))}
    print('[ORACLE-121] ORIGINAL_MRIYA_DISCOVERY + MRIYA_REPLENISHMENT + LIVE_SDK_ATOMIC_WATCH',flush=True)
    print('[SAFETY] discovery/read-only; trade disabled until SDK-native signed simulation certified',flush=True)
    scanner=subprocess.Popen([sys.executable,'-m',DISCOVERY],cwd=ROOT,env=scanenv)
    restart_count=0
    worker=None
    try:
        if a.once:
            subprocess.run([sys.executable,'-m',REPLENISH],cwd=ROOT,env=scanenv,check=False,timeout=90)
            r=materialize()
            print('[INVENTORY] tokens=%d pairs=%d'% (r['discovered_registry_tokens'],len(r['rows'])),flush=True)
            return subprocess.call(['node',str(JS),'--watch','--once'],cwd=ROOT,env=env)
        worker=subprocess.Popen(['node',str(JS),'--watch'],cwd=ROOT,env=env)
        while True:
            if scanner.poll() is not None:
                restart_count+=1
                cooldown=min(120,10*restart_count)
                print('[SCANNER_RECOVERY] code=%s cooldown_seconds=%s'%(scanner.returncode,cooldown),flush=True)
                time.sleep(cooldown)
                scanner=subprocess.Popen([sys.executable,'-m',DISCOVERY],cwd=ROOT,env=scanenv)
            if worker.poll() is not None:
                restart_count+=1
                cooldown=min(120,10*restart_count)
                print('[EVALUATOR_RECOVERY] code=%s cooldown_seconds=%s'%(worker.returncode,cooldown),flush=True)
                time.sleep(cooldown)
                worker=subprocess.Popen(['node',str(JS),'--watch'],cwd=ROOT,env=env)
            try:
                result=subprocess.run([sys.executable,'-m',REPLENISH],cwd=ROOT,env=scanenv,timeout=90)
                if result.returncode:
                    print('[REPLENISH_WARNING] original replenishment module exited nonzero',flush=True)
            except subprocess.TimeoutExpired:
                print('[REPLENISH_WARNING] cycle timeout',flush=True)
            r=materialize()
            print('[INVENTORY] mriya_tokens=%d mriya_pool_identities=%d total_pool_identities=%d'%(
                r['discovered_registry_tokens'],r['replenished_valid_identities'],len(r['rows'])),flush=True)
            time.sleep(60)
    except KeyboardInterrupt:
        print('[STOP] SIGINT - scanner and evaluator shutdown',flush=True)
        return 0
    finally:
        for p in (worker,scanner):
            if p and p.poll() is None:
                p.terminate()
                try:p.wait(timeout=8)
                except subprocess.TimeoutExpired:p.kill()

if __name__=='__main__':
    raise SystemExit(main())
