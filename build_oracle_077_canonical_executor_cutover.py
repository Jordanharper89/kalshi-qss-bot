"""ORACLE-077 full installer: durable native executor connection for ORACLE-051/054.
Original scanner is frozen. Builds 072-076 are prerequisites.
"""
import argparse
import ast
import getpass
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
TARGET = PKG / 'oracle_051_original_scanner_alt_and_size_gate.py'
MODULE = PKG / 'oracle_077_native_executor.py'
BACKUP = PKG / 'oracle_051_original_scanner_alt_and_size_gate.before_oracle077.py'
MARK = 'ORACLE077_PERSISTENT_NATIVE_DISPATCH'

EXECUTOR = '''"""ORACLE-077 canonical executor: one scanner, both venue directions.
Uses official-SDK-derived instructions from existing q87; v0 ALT compiler from 074.
No signing or broadcast. No private-key access.
"""

def guard(core):
    if not getattr(core.rpc, '_oracle077_guard', False):
        previous = core.rpc

        def guarded(method, params):
            name = str(method).lower()
            if name.startswith(('send', 'requestairdrop')):
                raise RuntimeError('ORACLE077_BROADCAST_FORBIDDEN')
            return previous(method, params)

        guarded._oracle077_guard = True
        core.rpc = guarded

    def forbidden(*args, **kwargs):
        raise RuntimeError('ORACLE077_SIGNING_OR_BROADCAST_FORBIDDEN')

    core.send = forbidden
    core.signed_tx = forbidden


def compile_native(user, route, core, q87, root, extra_alt=None):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_051_original_scanner_alt_and_size_gate as v51)
    from build_oracle_074_native_v0_compiler import compile_existing_alt

    guard(core)
    print('[ORACLE051_NATIVE] [ORACLE077_COMPILER_CALLED]', flush=True)

    result = compile_existing_alt(
        user, route, core, q87, root, extra_alt, v51=v51
    )

    if not isinstance(result, dict):
        raise RuntimeError('ORACLE077_COMPILER_BAD_RESULT')

    print(
        '[ORACLE051_NATIVE] [ORACLE077_NATIVE_RESULT] '
        'ok=%s reason=%s attempts=%d' % (
            bool(result.get('ok')),
            result.get('reason'),
            len(result.get('attempts') or [])
        ),
        flush=True
    )

    if not result.get('ok'):
        for item in (result.get('attempts') or [])[:6]:
            fields = (
                'candidate', 'alt_count', 'alt_check',
                'error', 'detail', 'bytes'
            )
            print(
                '[ORACLE051_NATIVE] [ORACLE077_COMPILE_ATTEMPT]',
                {k: item[k] for k in fields if k in item},
                flush=True
            )

    if result.get('ok'):
        assert len(bytes(result.get('raw') or b'')) <= 1232
        assert result.get('start_lamports', 0) >= 10_000_000

    return result


def simulate_native(compiled, user):
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from build_oracle_076_canonical_money_path import unsigned_atomic_balance_sim

    guard(core)
    result = unsigned_atomic_balance_sim(compiled, user, core)

    if not isinstance(result, dict):
        return {
            'err': 'ORACLE077_SIM_RESULT_INVALID',
            'units': 0,
            'logs': []
        }

    check = result.get('profit_check') or {}

    print(
        '[ORACLE051_SIM] [ORACLE077_SIMULATION] '
        'err=%s units=%s estimate=%s realized=FALSE' % (
            type(result.get('err')).__name__
            if result.get('err') is not None else 'None',
            result.get('units'),
            check.get('estimated_net_lamports')
        ),
        flush=True
    )

    return result
'''


def expected_sources():
    for name in (
        'build_oracle_072_route_contract.py',
        'build_oracle_073_verified_alt_optimizer.py',
        'build_oracle_074_native_v0_compiler.py',
        'build_oracle_075_unsigned_profit_reconciliation.py',
        'build_oracle_076_canonical_money_path.py'
    ):
        if not (ROOT / name).is_file():
            raise RuntimeError('MISSING_REQUIRED_BUILD_' + name)

    if not TARGET.is_file():
        raise RuntimeError('ORACLE051_LOCAL_SOURCE_MISSING')


def transformed_source(source):
    ast.parse(source)

    signature = (
        'def compile_existing_alt(user, route, core, q87, root, extra_alt=None):\n'
    )
    hook_at = '    rt.simulate_current = simulation_hook\n'

    if source.count(signature) != 1 or source.count(hook_at) != 1:
        raise RuntimeError('ORACLE051_ANCHOR_MISMATCH_NO_MODIFICATION')

    dispatch = (
        '    # ' + MARK + '\n'
        "    if __import__('os').environ.get('ORACLE077_ENABLED') == '1':\n"
        '        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_077_native_executor as ex77\n'
        '        return ex77.compile_native(user, route, core, q87, root, extra_alt)\n'
    )

    simulation = (
        "    if __import__('os').environ.get('ORACLE077_ENABLED') == '1':\n"
        '        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_077_native_executor as ex77\n'
        '        ex77.guard(core)\n'
        '        rt.simulate_current = ex77.simulate_native\n'
        "        print('[ORACLE051_NATIVE] [ORACLE077_SIMULATOR_ATTACHED]', flush=True)\n"
    )

    altered = source.replace(signature, signature + dispatch, 1)
    altered = altered.replace(hook_at, hook_at + simulation, 1)

    ast.parse(altered)
    return altered


def child_probe():
    code = (
        'from pathlib import Path; from types import SimpleNamespace; '
        'from qseries_v2.oracle_execution.solana_atomic_executor import '
        'oracle_051_original_scanner_alt_and_size_gate as v51; '
        'c=SimpleNamespace(rpc=lambda m,p:None,'
        'send=lambda:None,signed_tx=lambda:None); '
        "r=v51.compile_existing_alt("
        "'TEST',{'token':'fixture','start_lamports':1},"
        'c,None,Path.cwd()); '
        "assert r.get('reason')=='HOLD_BELOW_010_SOL_MINIMUM',r; "
        "print('[ORACLE077_CHILD_PROCESS_DISPATCH_PASS]')"
    )

    env = os.environ.copy()
    env['ORACLE077_ENABLED'] = '1'

    run = subprocess.run(
        [sys.executable, '-c', code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=25
    )

    if (
        run.returncode
        or '[ORACLE077_COMPILER_CALLED]' not in run.stdout
        or '[ORACLE077_CHILD_PROCESS_DISPATCH_PASS]' not in run.stdout
    ):
        raise RuntimeError(
            'ORACLE077_CHILD_DISPATCH_FAILED:'
            + (run.stdout + run.stderr)[-800:]
        )

    print('[PASS] ORACLE077_CHILD_PROCESS_DISPATCH', flush=True)


def install():
    expected_sources()
    current = TARGET.read_text(encoding='utf-8')

    if MARK in current:
        if not MODULE.is_file():
            raise RuntimeError('INCOMPLETE_PRIOR_INSTALL_NO_OVERWRITE')
        print('[PASS] ORACLE077_ALREADY_INSTALLED')
        child_probe()
        return

    altered = transformed_source(current)
    ast.parse(EXECUTOR)

    if BACKUP.exists() and BACKUP.read_text(encoding='utf-8') != current:
        raise RuntimeError('BACKUP_MISMATCH_MANUAL_REVIEW_REQUIRED')

    if not BACKUP.exists():
        BACKUP.write_text(current, encoding='utf-8')

    MODULE.write_text(EXECUTOR, encoding='utf-8')

    try:
        temporary = TARGET.with_suffix('.oracle077.tmp')
        temporary.write_text(altered, encoding='utf-8')
        os.replace(temporary, TARGET)
        child_probe()
    except Exception:
        TARGET.write_text(current, encoding='utf-8')
        print('[ROLLBACK] ORACLE051_SOURCE_RESTORED', flush=True)
        raise

    print('[PASS] ORACLE077_PERSISTENT_EXECUTOR_CONNECTED')
    print(
        '[PATH] Q25/Q20/Q18 -> ORACLE051 + ORACLE054 '
        '-> ORACLE077 -> ORACLE074 -> UNSIGNED_SIM'
    )
    print(
        '[BOUNDARY] SCANNER_UNCHANGED_SIGNING_DISABLED_BROADCAST_DISABLED'
    )


def test():
    expected_sources()
    s = TARGET.read_text(encoding='utf-8')

    if MARK not in s or not MODULE.is_file():
        raise RuntimeError('INSTALL_REQUIRED_FIRST')

    ast.parse(s)
    ast.parse(MODULE.read_text(encoding='utf-8'))
    child_probe()

    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_077_native_executor as ex

    class Dummy:
        def rpc(self, name, params):
            return name

        def send(self):
            return 1

        def signed_tx(self):
            return 2

    c = Dummy()
    ex.guard(c)

    assert c.rpc('getLatestBlockhash', []) == 'getLatestBlockhash'

    for call in (
        lambda: c.rpc('sendTransaction', []),
        c.send,
        c.signed_tx
    ):
        try:
            call()
        except RuntimeError:
            continue
        raise AssertionError('SIGN_OR_SEND_GUARD_BROKEN')

    print('[PASS] ORACLE077_PERSISTENCE_AND_SAFETY_TESTS')


def live(seconds, cycles):
    test()

    if not 30 <= seconds <= 120 or not 1 <= cycles <= 2:
        raise RuntimeError('BOUNDED_WINDOW_REQUIRED')

    env = os.environ.copy()
    env['ORACLE077_ENABLED'] = '1'

    if not env.get('SOLANA_RPC_URL') or not env.get('SOLANA_WS_URL'):
        key = getpass.getpass('Helius API key (hidden): ').strip()
        if not key:
            raise RuntimeError('HELIUS_KEY_REQUIRED')
        env['SOLANA_RPC_URL'] = (
            'https://mainnet.helius-rpc.com/?api-key=' + key
        )
        env['SOLANA_WS_URL'] = (
            'wss://mainnet.helius-rpc.com/?api-key=' + key
        )

    print(
        '[ORACLE077_LIVE] existing_ORACLE054_original_scanner=TRUE',
        flush=True
    )

    command = [
        sys.executable,
        '-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.oracle_054_reverse_native_handoff',
        '--run',
        '--seconds', str(seconds),
        '--cycles', str(cycles)
    ]

    return subprocess.call(command, cwd=ROOT, env=env)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--seconds', type=int, default=90)
    p.add_argument('--cycles', type=int, default=1)
    args = p.parse_args()

    if args.run:
        sys.exit(live(args.seconds, args.cycles))
    if args.test:
        test()
    else:
        install()