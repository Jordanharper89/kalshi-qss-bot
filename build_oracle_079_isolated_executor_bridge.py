"""ORACLE-079 full installer: keep ORACLE-077 attached inside ORACLE-054 -I child.
Scanner unchanged. No private-key access, signing, broadcast or RPC in tests.
"""
import argparse
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
V54 = PKG / 'oracle_054_reverse_native_handoff.py'
V77 = PKG / 'oracle_077_native_executor.py'
FLAG = 'ORACLE079_CHILD_EXECUTOR_ENABLED'
PREFIX = 'qseries_v2.oracle_execution.solana_atomic_executor.'
SOURCES = {
    'build_oracle_072_route_contract.py': 'oracle_072_route_contract.py',
    'build_oracle_073_verified_alt_optimizer.py': 'oracle_073_verified_alt_optimizer.py',
    'build_oracle_074_native_v0_compiler.py': 'oracle_074_native_v0_compiler.py',
    'build_oracle_075_unsigned_profit_reconciliation.py': 'oracle_075_unsigned_profit_reconciliation.py',
    'build_oracle_076_canonical_money_path.py': 'oracle_076_canonical_money_path.py',
}
ENV_ANCHOR = '        env = v50.scrub(os.environ)\n'
ENV_ADD = (
    '        # ' + FLAG + '\n'
    '        if os.environ.get("ORACLE077_ENABLED") == "1":\n'
    '            env["ORACLE077_ENABLED"] = "1"\n'
)
IMPORTS = (
    ('from build_oracle_074_native_v0_compiler import compile_existing_alt',
     'from ' + PREFIX + 'oracle_074_native_v0_compiler import compile_existing_alt'),
    ('from build_oracle_076_canonical_money_path import unsigned_atomic_balance_sim',
     'from ' + PREFIX + 'oracle_076_canonical_money_path import unsigned_atomic_balance_sim'),
)


def generated_sources():
    result = {}
    for src, dest in SOURCES.items():
        source = (ROOT / src).read_text(encoding='utf-8')
        source = source.replace('from build_oracle_', 'from ' + PREFIX + 'oracle_')
        ast.parse(source, filename=dest)
        result[PKG / dest] = source
    return result


def patched_sources():
    old54 = V54.read_text(encoding='utf-8')
    old77 = V77.read_text(encoding='utf-8')
    if old54.count(ENV_ANCHOR) != 1:
        raise RuntimeError('ORACLE054_CHILD_ENV_ANCHOR_MISMATCH')
    if FLAG in old54:
        raise RuntimeError('ORACLE079_ALREADY_INSTALLED_USE_TEST')
    if 'def compile_native(' not in old77 or 'def simulate_native(' not in old77:
        raise RuntimeError('ORACLE077_EXECUTOR_CONTRACT_MISSING')
    new77 = old77
    for a, b in IMPORTS:
        if new77.count(a) != 1:
            raise RuntimeError('ORACLE077_IMPORT_ANCHOR_MISMATCH_' + a.split()[1])
        new77 = new77.replace(a, b, 1)
    new54 = old54.replace(ENV_ANCHOR, ENV_ANCHOR + ENV_ADD, 1)
    ast.parse(new54)
    ast.parse(new77)
    return {V54: new54, V77: new77}


def isolated_probe():
    code = (
        'import sys;from pathlib import Path;'
        'sys.path.insert(0,str(Path.cwd()));'
        'from qseries_v2.oracle_execution.solana_atomic_executor import '
        'oracle_051_original_scanner_alt_and_size_gate as v51;'
        'class_dummy="";'
        'from types import SimpleNamespace;'
        'c=SimpleNamespace(rpc=lambda *a: (_ for _ in ()).throw(Exception("RPC_FORBIDDEN")));'
        'r=v51.compile_existing_alt("U",{"token":"T","start_lamports":1},c,None,Path.cwd());'
        'assert r.get("reason")=="HOLD_BELOW_010_SOL_MINIMUM",r;'
        'print("[ORACLE079_ISOLATED_COMPILER_PASS]")'
    )
    env = os.environ.copy()
    env['ORACLE077_ENABLED'] = '1'
    child = subprocess.run([sys.executable, '-I', '-c', code], cwd=ROOT,
                           env=env, capture_output=True, text=True, timeout=30)
    if (child.returncode or '[ORACLE077_COMPILER_CALLED]' not in child.stdout
            or '[ORACLE079_ISOLATED_COMPILER_PASS]' not in child.stdout):
        raise RuntimeError('ORACLE079_ISOLATED_IMPORT_OR_DISPATCH_FAILED: ' +
                           (child.stdout + child.stderr)[-600:])
    print('[PASS] ORACLE079_ISOLATED_COMPILER_DISPATCH')


def env_probe():
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_054_reverse_native_handoff as v54
    captured = []

    class FakeProcess:
        stdout = ()
        def wait(self, *a, **k):
            return 0

    def fake_popen(*args, **kwargs):
        captured.append(kwargs['env'])
        return FakeProcess()

    with patch.dict(os.environ, {'ORACLE077_ENABLED': '1'}):
        with patch.object(v54.subprocess, 'Popen', fake_popen):
            result = v54.batch(ROOT, 1, 1)
    if result != 0 or len(captured) != 1 or captured[0].get('ORACLE077_ENABLED') != '1':
        raise RuntimeError('ORACLE079_CHILD_ENV_NOT_PROPAGATED')
    if 'QSB_SOLANA_PRIVATE_KEY' in captured[0]:
        raise RuntimeError('ORACLE079_CHILD_PRIVATE_KEY_LEAK')
    print('[PASS] ORACLE079_ORIGINAL_BATCH_CHILD_ENV')


def verify():
    if FLAG not in V54.read_text(encoding='utf-8'):
        raise RuntimeError('ORACLE079_CUTOVER_NOT_INSTALLED')
    for target in [V54, V77, *(PKG / name for name in SOURCES.values())]:
        ast.parse(target.read_text(encoding='utf-8'), filename=str(target))
    isolated_probe()
    env_probe()
    print('[PASS] ORACLE079_PACKAGE_AND_CHILD_PROCESS_TEST')
    print('[BOUNDARY] NO_RPC_NO_SIGNING_NO_BROADCAST_IN_TEST')


def install():
    if FLAG in V54.read_text(encoding='utf-8'):
        verify()
        return
    all_new = {**generated_sources(), **patched_sources()}
    originals = {}
    created = []
    for target, source in all_new.items():
        if target.exists():
            prior = target.read_text(encoding='utf-8')
            if target not in (V54, V77) and prior != source:
                raise RuntimeError('ORACLE079_MODULE_CONFLICT_' + target.name)
            originals[target] = prior
        else:
            created.append(target)
    for target in (V54, V77):
        backup = target.with_name(target.stem + '.before_oracle079.py')
        if backup.exists() and backup.read_text(encoding='utf-8') != originals[target]:
            raise RuntimeError('ORACLE079_BACKUP_CONFLICT_' + target.name)
        if not backup.exists():
            shutil.copy2(target, backup)
    try:
        for target, source in all_new.items():
            if target.exists() and target.read_text(encoding='utf-8') == source:
                continue
            stage = target.with_suffix('.oracle079.tmp')
            stage.write_text(source, encoding='utf-8')
            os.replace(stage, target)
        verify()
    except Exception:
        for target, prior in originals.items():
            target.write_text(prior, encoding='utf-8')
        for target in created:
            target.unlink(missing_ok=True)
        print('[ROLLBACK] ORACLE079_RESTORED_PREVIOUS_RUNTIME')
        raise
    print('[PASS] ORACLE079_ISOLATED_EXECUTOR_CONNECTED')
    print('[PATH] ORIGINAL_Q25_Q20_Q18 -> ORACLE054_CHILD -> ORACLE077 -> ORACLE074 -> UNSIGNED_SIM')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    verify() if args.test else install()