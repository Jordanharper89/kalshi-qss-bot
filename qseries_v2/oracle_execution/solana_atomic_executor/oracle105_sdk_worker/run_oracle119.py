"""Run the single ORACLE-119 worker without echoing credentials."""
from __future__ import annotations
import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKER = HERE / 'oracle119_atomic_machine.cjs'


def main() -> int:
    ap = argparse.ArgumentParser(description='ORACLE-119 single atomic money-path worker')
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument('--watch', action='store_true', help='Read-only unsigned atomic simulations')
    modes.add_argument('--trade', action='store_true', help='Enable guarded live 0.010-SOL canary')
    ap.add_argument('--once', action='store_true', help='Check one bounded candidate batch')
    a = ap.parse_args()
    if not WORKER.is_file():
        print('[HOLD] ORACLE-119 worker not installed')
        return 2
    if not shutil.which('node'):
        print('[HOLD] Node.js not on PATH')
        return 2
    e = os.environ.copy()
    if a.trade and not e.get('QSB_SOLANA_PRIVATE_KEY'):
        print('[HOLD] QSB_SOLANA_PRIVATE_KEY missing in this CMD environment; no key requested or printed')
        return 2
    if not e.get('SOLANA_RPC_URL', '').startswith('https://'):
        key = getpass.getpass('Helius API key (hidden): ').strip()
        if not key:
            print('[HOLD] Helius API key required')
            return 2
        e['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + key
    cmd = ['node', str(WORKER), '--trade' if a.trade else '--watch']
    if a.once:
        cmd.append('--once')
    return subprocess.call(cmd, cwd=str(ROOT), env=e)


if __name__ == '__main__':
    sys.exit(main())
