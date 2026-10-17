"""V1 scanner using frozen ORACLE-500/V16."""
from __future__ import annotations
import argparse
import ast
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CANONICAL = BASE / 'oracle_500_scanner_machine.py'
MODULE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_500_scanner_machine'
PAIRS = 28
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')
TEMPLATES = PAIRS * len(DIRECTIONS)

def flags(path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError('CANONICAL_SCANNER_SOURCE_MISSING_OR_LINKED')
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
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

def command(epoch_seconds=180, epochs=0, options=None):
    opts = flags(CANONICAL) if options is None else set(options)
    missing = {'--pairs', '--epochs', '--run'} - opts
    if missing:
        raise RuntimeError(
            'CANONICAL_SCANNER_CLI_DRIFT:' + ','.join(sorted(missing))
        )
    if not 150 <= epoch_seconds <= 3600 or not 0 <= epochs <= 1000:
        raise ValueError('CANONICAL_EPOCH_LIMIT_VIOLATION')
    args = [
        sys.executable, '-m', MODULE,
        '--run', '--pairs', str(PAIRS),
        '--epochs', str(epochs)
    ]
    if '--epoch-seconds' in opts:
        args += ['--epoch-seconds', str(epoch_seconds)]
    elif '--seconds' in opts:
        args += ['--seconds', str(epoch_seconds)]
    else:
        raise RuntimeError('CANONICAL_SCANNER_EPOCH_OPTION_NOT_FOUND')
    return args

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Oracle V1 frozen 28-pair scanner entrypoint'
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--run', action='store_true')
    ap.add_argument('--epoch-seconds', type=int, default=180)
    ap.add_argument('--epochs', type=int, default=0)
    a = ap.parse_args(argv)
    cmd = command(a.epoch_seconds, a.epochs)
    print('[V1_SCANNER] ORACLE500/ORACLE322/V16 pairs=28 directions=56')
    print('[CONTRACT] Original WS and ORACLE344 SQLite')
    print('[COMMAND]', ' '.join(cmd[1:]), flush=True)
    if a.preflight:
        print('[PASS] V1_28_SCANNER_ENTRYPOINT_PREFLIGHT')
        return 0
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError(
            'SCANNER_REQUIRES_SEPARATE_KEY_FREE_CMD_NO_PARENT_ENV_MUTATION'
        )
    return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
