
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
PREVIOUS = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_382_staged_native_capacity'
NAMES = {
  390:'executor_native_28_startup',391:'executor_scoped_28',
  392:'executor_runtime_witness',393:'executor_startup_hold_trace',
  394:'native_capacity_witness',395:'executor_backoff',396:'atomic_readiness'
}

def targets(root):
    result=[]
    for n, suffix in NAMES.items():
        result += [root / f'build_oracle_{n}_{suffix}.py',
                   root / PKG / f'oracle_{n}_{suffix}.py']
    return result

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def preserve_scanner(root):
    rows = list(root.glob('build_oracle_322_scanner_isolated_discovery.py'))
    folder = root / PKG
    if folder.exists():
        rows += list(folder.glob('oracle_322*.py'))
    return {str(p.relative_to(root)):digest(p) for p in rows if p.is_file()}

def check(root):
    baseline=root / PKG / 'oracle_382_staged_native_capacity.py'
    if not baseline.is_file():
        raise RuntimeError('HOLD_ORACLE382_BASELINE_MISSING_NO_DELETION')
    forbidden=tuple('oracle_'+str(n)+'_' for n in NAMES)
    dependents=[]
    for p in (root / PKG).glob('*.py'):
        if p in targets(root):
            continue
        content=p.read_text(encoding='utf-8-sig', errors='replace')
        if any(x in content for x in forbidden):
            dependents.append(p.name)
    if dependents:
        raise RuntimeError('HOLD_LIVE_DEPENDENCIES_ON_390_396:'+','.join(dependents[:12]))
    return baseline

def reset(root):
    base=check(root)
    present=[p for p in targets(root) if p.is_file()]
    scanner_before=preserve_scanner(root)
    if not present:
        print('[ORACLE397] ALREADY_CLEAN; original 382 preserved')
        return
    timestamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup=root/'runtime_state/oracle/rollback_397'/timestamp
    manifest=[]
    for p in present:
        relative=p.relative_to(root)
        dest=backup/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        expected=digest(p)
        shutil.copy2(p,dest)
        if digest(dest)!=expected:
            raise RuntimeError('HOLD_BACKUP_HASH_MISMATCH:'+str(relative))
        manifest.append({'path':str(relative),'sha256':expected})
    (backup/'manifest.json').write_text(json.dumps({
        'retired':manifest,'baseline_sha256':digest(base),
        'scanner_sha256_before':scanner_before},indent=2),encoding='utf-8')
    for p in present:
        p.unlink()
        print('[RETIRED]',p.relative_to(root))
    if preserve_scanner(root)!=scanner_before:
        raise RuntimeError('HOLD_SCANNER_CHANGED_UNEXPECTEDLY')
    print('[PASS] CLEAN_ROLLBACK baseline=ORACLE382 legacy_native_stack_preserved')
    print('[BACKUP]',backup.relative_to(root))
    print('[SCANNER] UNTOUCHED [390-396] OUT_OF_ACTIVE_TREE')

def safe_env():
    env=os.environ.copy()
    for key in tuple(env):
        if any(part in key.upper() for part in (
            'PRIVATE_KEY','PRIVATEKEY','SECRET','MNEMONIC','KEYPAIR','SEED_PHRASE')):
            env.pop(key,None)
    env.update(QSB_LIVE_ARM='NO', PYTHONUNBUFFERED='1')
    return env

def launch(minutes,poll_ms):
    check(ROOT)
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:
        raise RuntimeError('HOLD_INVALID_ORACLE382_CLI_BOUNDS')
    env=safe_env()
    print('[ORACLE397] ORIGINAL_ORACLE382_NO_WRAPPERS, SCANNER_UNTOUCHED',flush=True)
    print('[WALLET_KEY] NOT_PASSED [SIGNING] DISABLED [BROADCAST] DISABLED',flush=True)
    status=subprocess.call([sys.executable,'-m',PREVIOUS,'--health-gate'],env=env)
    if status:
        print('[HOLD] SCANNER_HEALTH_GATE_FAILED; baseline not started')
        return status
    return subprocess.call([sys.executable,'-m',PREVIOUS,'--run',
                            '--minutes',str(minutes),'--poll-ms',str(poll_ms)],env=env)

def tests():
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); folder=r/PKG;folder.mkdir(parents=True)
        base=folder/'oracle_382_staged_native_capacity.py'
        base.write_text('OLD_CANONICAL_WORKING_SOURCE',encoding='utf-8')
        scan=r/'build_oracle_322_scanner_isolated_discovery.py'
        scan.write_text('SCANNER_FROZEN_SOURCE',encoding='utf-8')
        original=targets(r)
        for p in original:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('temporary wrapper',encoding='utf-8')
        reset(r)
        assert all(not p.exists() for p in original)
        assert base.read_text()=='OLD_CANONICAL_WORKING_SOURCE'
        assert scan.read_text()=='SCANNER_FROZEN_SOURCE'
        archives=list((r/'runtime_state/oracle/rollback_397').glob('*/manifest.json'))
        assert len(archives)==1 and len(json.loads(archives[0].read_text())['retired'])==14
        reset(r)
    print('[PASS] ORACLE397 scoped removal, 14-file archive, integrity, baseline and scanner preserved')

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    for name in ('test','audit','reset','start'):
        a.add_argument('--'+name,action='store_true')
    p.add_argument('--minutes',type=int,default=1)
    p.add_argument('--poll-ms',type=int,default=50)
    args=p.parse_args()
    if args.test:tests();return 0
    if args.audit:
        check(ROOT)
        print('[AUDIT] baseline=ORACLE382 present; 390-396 files=',sum(p.is_file() for p in targets(ROOT)))
        print('[SCANNER] UNTOUCHED [SIZING] existing native stack')
        return 0
    if args.reset:reset(ROOT);return 0
    return launch(args.minutes,args.poll_ms)

if __name__=='__main__':sys.exit(main())
