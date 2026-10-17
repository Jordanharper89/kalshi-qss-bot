"""ORACLE-076: use the ORIGINAL 054 scanner with ORACLE-074 compiler.
No new scanner, no transaction signing, no sendTransaction authority.
"""
import argparse
import base64
import os
import runpy
import sys
from pathlib import Path
import unittest
from build_oracle_074_native_v0_compiler import compile_existing_alt
from build_oracle_075_unsigned_profit_reconciliation import reconcile

EXECUTION_MODULE = ('qseries_v2.oracle_execution.solana_atomic_executor.'
                    'oracle_054_reverse_native_handoff')


def _hold(reason):
    return {'err': reason, 'units': 0, 'logs': [], 'net_profit_certified': False}


def unsigned_atomic_balance_sim(compiled, user, core):
    """One unsigned simulation; compare public wallet/ATA balances without signing."""
    if not isinstance(compiled, dict) or not compiled.get('ok'):
        return _hold('HOLD_NOT_COMPILED')
    if not isinstance(compiled.get('token'), str) or not compiled['token']:
        return _hold('HOLD_COMPILED_TOKEN_MISSING')
    try:
        mint = core.rpc('getAccountInfo', [compiled['token'],
                         {'encoding': 'base64', 'commitment': 'processed'}])['value']
        if not mint or not isinstance(mint.get('owner'), str):
            return _hold('HOLD_TOKEN_PROGRAM_UNKNOWN')
        token_ata = core.ata(user, compiled['token'], mint['owner'])
        wsol_ata = core.ata(user, core.WSOL, core.TOKEN)
        addresses = [user, wsol_ata, token_ata]
        pre = core.rpc('getMultipleAccounts', [addresses,
                       {'encoding': 'base64', 'commitment': 'processed'}])['value']
        response = core.rpc('simulateTransaction', [
            base64.b64encode(compiled['raw']).decode(),
            {'encoding': 'base64', 'sigVerify': False, 'commitment': 'processed',
             'accounts': {'encoding': 'base64', 'addresses': addresses}}])
        value = response['value']
        if not isinstance(value, dict):
            return _hold('HOLD_BAD_SIM_RESPONSE')
        sim = {'err': value.get('err'), 'units': value.get('unitsConsumed'),
               'logs': list(value.get('logs') or [])}
        assessment = reconcile(pre, value.get('accounts'), sim,
                               compiled['start_lamports'])
        print('[ORACLE076_UNSIGNED_TRUTH]', assessment['reason'],
              'estimated_net=', assessment.get('estimated_net_lamports'), flush=True)
        if sim['err'] is not None:
            return {'err': sim['err'], 'units': sim['units'], 'logs': sim['logs'],
                    'profit_check': assessment, 'net_profit_certified': False}
        if not assessment['ok']:
            return {'err': assessment['reason'], 'units': sim['units'],
                    'logs': sim['logs'], 'profit_check': assessment,
                    'net_profit_certified': False}
        return {'err': None, 'units': sim['units'], 'logs': sim['logs'],
                'profit_check': assessment, 'net_profit_certified': False}
    except Exception as exc:
        print('[ORACLE076_SIM_HOLD]', type(exc).__name__, flush=True)
        return _hold('HOLD_SIMULATION_EXCEPTION_' + type(exc).__name__)


def integrate(v51, rt, core, q87):
    """Installed before ORACLE-054 imports and starts existing hooks."""
    prior_install = v51.install_hooks
    counters = {'compiler_calls': 0, 'simulation_calls': 0, 'hook_installs': 0}

    def compiler(user, route, c, q, root, extra_alt=None):
        counters['compiler_calls'] += 1
        return compile_existing_alt(user, route, c, q, root, extra_alt, v51=v51)

    def install(*args, **kwargs):
        result = prior_install(*args, **kwargs)
        counters['hook_installs'] += 1
        def simulate(compiled, user):
            counters['simulation_calls'] += 1
            return unsigned_atomic_balance_sim(compiled, user, core)
        rt.simulate_current = simulate
        print('[ORACLE076_BOUND] canonical_native_compiler=TRUE '
              'unsigned_balance_sim=TRUE', flush=True)
        return result

    v51.compile_existing_alt = compiler
    v51.install_hooks = install
    rt.compile_current = lambda user, route: compiler(user, route, core, q87, Path.cwd())
    rt.simulate_current = lambda compiled, user: unsigned_atomic_balance_sim(compiled, user, core)
    return counters


class Tests(unittest.TestCase):
    def test_compilation_failure_holds_without_rpc(self):
        self.assertEqual(unsigned_atomic_balance_sim({'ok': False}, 'u', None)['err'],
                         'HOLD_NOT_COMPILED')

    def test_requires_token_identity(self):
        self.assertEqual(unsigned_atomic_balance_sim({'ok': True}, 'u', None)['err'],
                         'HOLD_COMPILED_TOKEN_MISSING')

    def test_installation_does_not_call_original_scanner(self):
        from types import SimpleNamespace
        v51 = SimpleNamespace(install_hooks=lambda: 7)
        rt = SimpleNamespace(simulate_current=None)
        counters = integrate(v51, rt, None, None)
        self.assertEqual(counters['compiler_calls'], 0)
        self.assertEqual(v51.install_hooks(), 7)
        self.assertEqual(counters['hook_installs'], 1)
        self.assertTrue(callable(rt.simulate_current))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--canary', action='store_true')
    p.add_argument('--seconds', type=int, default=90)
    p.add_argument('--cycles', type=int, default=2)
    a = p.parse_args()
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
        return 0
    if a.canary:
        print('[HOLD] LIVE_CANARY_NOT_AUTHORIZED: unsigned simulation and '
              'realized-profit gates not certified')
        return 2
    if not a.run:
        print('[PASS] ORACLE076_READY EXISTING_ORACLE054_RUNTIME')
        return 0
    if not (1 <= a.seconds <= 120 and 1 <= a.cycles <= 2):
        raise SystemExit('BOUNDED_RUNTIME_ONLY')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_051_original_scanner_alt_and_size_gate as v51, runtime as rt)
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
        qarb_087_two_second_compaction_liquidity_repair as q87)
    core = q87.c
    if rt.EXECUTION_AUTHORITY is not False or rt.PAPER_ONLY is not True:
        raise SystemExit('HOLD_EXECUTION_AUTHORITY_NOT_DISABLED')
    def forbid(*_args, **_kwargs):
        raise RuntimeError('ORACLE076_SIGNING_AND_BROADCAST_FORBIDDEN')
    original_rpc = core.rpc
    def guarded_rpc(method, params):
        if str(method).lower().startswith(('send', 'requestairdrop')):
            raise RuntimeError('ORACLE076_BROADCAST_RPC_FORBIDDEN')
        return original_rpc(method, params)
    core.rpc = guarded_rpc
    core.send = forbid
    core.signed_tx = forbid
    counters = integrate(v51, rt, core, q87)
    sys.argv = [EXECUTION_MODULE, '--run', '--seconds', str(a.seconds),
                '--cycles', str(a.cycles)]
    try:
        runpy.run_module(EXECUTION_MODULE, run_name='__main__')
    finally:
        print('[ORACLE076_GATES]', counters, flush=True)
        print('[BOUNDARY] PRIVATE_KEY_UNTOUCHED_SIGNING_FALSE_BROADCAST_FALSE', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())