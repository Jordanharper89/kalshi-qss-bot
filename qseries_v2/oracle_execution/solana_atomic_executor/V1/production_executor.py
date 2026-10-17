"""V1 executor using canonical ORACLE-504 native simulation."""
from __future__ import annotations
import argparse
import ast
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CANONICAL = BASE / 'oracle_504_execution_engine.py'
MODULE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_504_execution_engine'
PAIRS = 28
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')
TEMPLATES = PAIRS * len(DIRECTIONS)
FIRST_CANARY_MAX_LAMPORTS = 10_000_000
PUBKEY = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}\Z')

def flags(path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError('CANONICAL_EXECUTOR_SOURCE_MISSING_OR_LINKED')
    text = path.read_text(encoding='utf-8-sig')
    tree = ast.parse(text)
    needed = (
        'provider.prepare_unsigned(row)',
        'bridge.signed_preflight(',
        'proof_contract(',
        "row['direction']",
        'm365 = mod('
    )
    missing = [x for x in needed if x not in text]
    if missing:
        raise RuntimeError(
            'NATIVE_OR_BUS_CONTRACT_DRIFT:' + ','.join(missing)
        )
    opts = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'add_argument'):
            opts.update(
                a.value for a in node.args
                if isinstance(a, ast.Constant)
                and isinstance(a.value, str)
                and a.value.startswith('--')
            )
    return opts

def command(wallet, seconds=90, signed_sim=True, options=None):
    opts = flags(CANONICAL) if options is None else set(options)
    missing = {
        '--observe', '--seconds', '--wallet', '--signed-sim'
    } - opts
    if missing:
        raise RuntimeError(
            'CANONICAL_EXECUTOR_CLI_DRIFT:' + ','.join(sorted(missing))
        )
    if not PUBKEY.fullmatch(wallet or ''):
        raise ValueError('PUBLIC_WALLET_REQUIRED_AND_MUST_BE_BASE58')
    if not 1 <= seconds <= 3600:
        raise ValueError('BOUNDED_SECONDS_REQUIRED')
    out = [
        sys.executable, '-m', MODULE,
        '--observe', '--seconds', str(seconds),
        '--wallet', wallet
    ]
    if signed_sim:
        out.append('--signed-sim')
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Oracle V1 canonical native executor'
    )
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument('--preflight', action='store_true')
    modes.add_argument('--run', action='store_true')
    ap.add_argument('--seconds', type=int, default=90)
    ap.add_argument(
        '--wallet',
        default=os.getenv('QSB_SOLANA_WALLET', '')
    )
    ap.add_argument('--unsigned-only', action='store_true')
    a = ap.parse_args(argv)
    opts = flags(CANONICAL)
    assert FIRST_CANARY_MAX_LAMPORTS == 10_000_000
    print('[V1_EXECUTOR] ORACLE504/ORACLE365/ORACLE401')
    print('[INVENTORY_CONTRACT] 28 pairs / 56 directions')
    print('[BROADCAST] FALSE')
    print('[FIRST_CANARY_MAX_SOL] 0.010')
    print('[MIN_OUT_CERTIFIED] FALSE')
    if a.preflight:
        needed = {
            '--observe', '--seconds', '--wallet', '--signed-sim'
        }
        if not needed.issubset(opts):
            raise RuntimeError('CANONICAL_EXECUTOR_FLAGS_INCOMPLETE')
        print('[PASS] V1_ATOMIC_EXECUTOR_ENTRYPOINT_PREFLIGHT')
        return 0
    cmd = command(
        a.wallet, a.seconds,
        signed_sim=not a.unsigned_only,
        options=opts
    )
    print(
        '[MODE]',
        'UNSIGNED_OBSERVE' if a.unsigned_only
        else 'SIGNED_SIMULATION_NO_SEND',
        flush=True
    )
    return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
