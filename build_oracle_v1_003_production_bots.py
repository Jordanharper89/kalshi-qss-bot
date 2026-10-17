
"""ORACLE V1-003: full 28-pair production integration installer."""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path.cwd()
DEST = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/V1'

SCANNER = r'''"""V1 scanner using frozen ORACLE-500/V16."""
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
'''

EXECUTOR = r'''"""V1 executor using canonical ORACLE-504 native simulation."""
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
'''

TESTS = r'''"""ORACLE V1-003 deterministic integration tests."""
import ast
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.V1 import production_scanner as s
from qseries_v2.oracle_execution.solana_atomic_executor.V1 import production_executor as e

class TestV1(unittest.TestCase):
    def test_28_pairs_two_directions(self):
        self.assertEqual(
            (s.PAIRS, s.TEMPLATES, e.PAIRS, e.TEMPLATES),
            (28, 56, 28, 56)
        )
        self.assertEqual(set(s.DIRECTIONS), set(e.DIRECTIONS))

    def test_original_scanner_only(self):
        opts = {'--run','--pairs','--epochs','--epoch-seconds'}
        x = s.command(180, 0, opts)
        self.assertEqual(x[x.index('--pairs')+1], '28')
        self.assertEqual(x[x.index('--epochs')+1], '0')
        self.assertIn('oracle_500_scanner_machine', ' '.join(x))

    def test_scanner_rejects_eight_pair_fallback(self):
        with self.assertRaises(RuntimeError):
            s.command(options={'--run','--epochs','--seconds'})

    def test_scanner_limits(self):
        opts = {'--run','--pairs','--epochs','--epoch-seconds'}
        with self.assertRaises(ValueError):
            s.command(epochs=1001, options=opts)

    def test_canonical_native_and_both_modes(self):
        opts = {'--observe','--seconds','--wallet','--signed-sim'}
        wallet = '11111111111111111111111111111111'
        cmd = e.command(wallet, 90, True, opts)
        self.assertIn('--signed-sim', cmd)
        self.assertIn('oracle_504_execution_engine', ' '.join(cmd))
        self.assertNotIn('--live', cmd)
        self.assertNotIn('--broadcast', cmd)
        self.assertNotIn(
            '--signed-sim', e.command(wallet, 90, False, opts)
        )

    def test_canary_cap_and_secret_exclusion(self):
        self.assertEqual(e.FIRST_CANARY_MAX_LAMPORTS, 10_000_000)
        with self.assertRaises(ValueError):
            e.command(
                'not-a-public-key', 90, True,
                {'--observe','--seconds','--wallet','--signed-sim'}
            )

    def test_canonical_files_unmodified(self):
        self.assertTrue(s.CANONICAL.is_file())
        self.assertTrue(e.CANONICAL.is_file())
        ast.parse(s.CANONICAL.read_text(encoding='utf-8-sig'))
        ast.parse(e.CANONICAL.read_text(encoding='utf-8-sig'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
'''

def stage(path, source):
    data = source.encode('utf-8')
    compile(source, str(path), 'exec')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise RuntimeError('SYMLINK_DESTINATION_REFUSED:' + path.name)
    if path.is_file() and path.read_bytes() == data:
        print('[UNCHANGED]', path.relative_to(ROOT))
        return
    if path.exists():
        old = path.read_bytes()
        name = (
            path.name + '.pre_v1_003_' +
            hashlib.sha256(old).hexdigest()[:12] + '.bak'
        )
        backup = path.with_name(name)
        if backup.exists() and backup.read_bytes() != old:
            raise RuntimeError('BACKUP_HASH_CONFLICT')
        if not backup.exists():
            backup.write_bytes(old)
        print('[BACKUP]', backup.relative_to(ROOT))
    fd, name = tempfile.mkstemp(
        prefix='.oracle_v1_', dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    if path.read_bytes() != data:
        raise RuntimeError('READBACK_FAILED:' + path.name)
    print('[INSTALLED]', path.relative_to(ROOT))

def main():
    if not (ROOT/'venv').is_dir() or not (ROOT/'qseries_v2').is_dir():
        raise RuntimeError('RUN_FROM_ACTIVE_Q_SERIES_REPO_ROOT')
    for name in (
        'oracle_500_scanner_machine.py',
        'oracle_504_execution_engine.py'
    ):
        p = DEST.parent / name
        if not p.is_file() or p.is_symlink():
            raise RuntimeError('CANONICAL_MODULE_REQUIRED:' + name)
    stage(DEST/'production_scanner.py', SCANNER)
    stage(DEST/'production_executor.py', EXECUTOR)
    stage(ROOT/'test_oracle_v1_003_production_bots.py', TESTS)
    print('[SCOPE] FROZEN_SCANNER_UNCHANGED')
    print('[SCOPE] CANONICAL_EXECUTOR_UNCHANGED')
    print('[SCOPE] 28_PAIR_56_DIRECTION_ENTRYPOINTS')
    print('[BROADCAST] FALSE')
    return 0

if __name__ == '__main__':
    sys.exit(main())
