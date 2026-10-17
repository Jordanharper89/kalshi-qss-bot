"""ORACLE-084 offline atomic readiness and failure contract audit."""
import argparse
import ast
import json
import re
from pathlib import Path

PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_084_READINESS.json')
SIZES = (10_000_000, 15_000_000, 20_000_000, 25_000_000, 30_000_000)
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')


def classify(err, logs):
    text = (' '.join(map(str, logs)) + ' ' + str(err)).lower()
    if 'accountnotinitialized' in text or 'account not initialized' in text or '0xbc4' in text:
        return 'DLMM_OUTPUT_ACCOUNT_NOT_INITIALIZED'
    if 'insufficientfunds' in text or 'insufficient funds' in text:
        return 'PUMP_SOURCE_ACCOUNT_INSUFFICIENT_FUNDS'
    if err is not None:
        return 'OTHER_SIMULATION_REJECTION'
    return 'NO_REJECTION_IN_RECORD'


def choose(rows):
    """Only independently certified net-positive rows can be selected."""
    eligible = [r for r in rows if r.get('direction') in DIRECTIONS
                and r.get('size_lamports') in SIZES
                and r.get('atomic_sim_pass') is True
                and r.get('fresh') is True
                and r.get('fees_and_residue_verified') is True
                and isinstance(r.get('net_profit_lamports'), int)
                and r['net_profit_lamports'] > 0]
    return max(eligible, key=lambda r: r['net_profit_lamports']) if eligible else None


def locate():
    needles = ('user_token_out', 'BuyExactQuoteIn', 'BUY_EXACT_QUOTE_IN_DISC',
               'simulate_native', 'SyncNative', 'sync_native', 'create_associated_token_account')
    result = []
    for path in sorted(PKG.glob('*.py')):
        if '.before_oracle' in path.name:
            continue
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
            ast.parse('\n'.join(lines), filename=str(path))
        except (OSError, UnicodeError, SyntaxError):
            continue
        for n, line in enumerate(lines, 1):
            if any(needle.lower() in line.lower() for needle in needles):
                result.append({'file': str(path), 'line': n,
                               'terms': [x for x in needles if x.lower() in line.lower()]})
    return result


def latest_failure():
    candidates = [Path('runtime_state/oracle/oracle_live_execution/oracle_083_sim_failure.json'),
                  Path('runtime_state/oracle/oracle_live_execution/ORACLE_083_SIM_FAILURE.json')]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                continue
            return {'file': str(path), 'category': classify(data.get('error'), data.get('program_trace', [])),
                    'instruction_index': data.get('instruction_index'),
                    'error_present': data.get('error') is not None}
        except (OSError, ValueError):
            continue
    return {'status': 'NO_ORACLE083_FAILURE_REPORT_FOUND'}


def test():
    assert len(SIZES) == 5 and SIZES[0] == 10_000_000 and SIZES[-1] == 30_000_000
    assert classify({'InstructionError': [2, {'Custom': 3012}]}, ['AccountNotInitialized']) == 'DLMM_OUTPUT_ACCOUNT_NOT_INITIALIZED'
    assert classify('InsufficientFunds', []) == 'PUMP_SOURCE_ACCOUNT_INSUFFICIENT_FUNDS'
    good = {'direction': 'METEORA_TO_PUMP', 'size_lamports': 15_000_000,
            'atomic_sim_pass': True, 'fresh': True, 'fees_and_residue_verified': True,
            'net_profit_lamports': 1234}
    assert choose([good]) == good
    for field in ('atomic_sim_pass', 'fresh', 'fees_and_residue_verified'):
        bad = dict(good, **{field: False})
        assert choose([bad]) is None
    assert choose([dict(good, size_lamports=40_000_000)]) is None
    assert choose([dict(good, net_profit_lamports=-1)]) is None
    assert choose([dict(good, net_profit_lamports=0)]) is None
    assert choose([dict(good, net_profit_lamports=500), good]) == good
    print('[PASS] ORACLE084_SIZE_SELECTION_AND_ATOMIC_PROFIT_GATES')
    print('[PASS] ORACLE084_KNOWN_FAILURE_CLASSIFICATION')
    print('[BOUNDARY] OFFLINE NO_RPC NO_SIGNING NO_BROADCAST')


def run():
    test()
    if not PKG.is_dir():
        raise SystemExit('[HOLD] CANONICAL_EXECUTOR_DIRECTORY_MISSING')
    hits = locate()
    failure = latest_failure()
    required = {'oracle_054_reverse_native_handoff.py', 'oracle_077_native_executor.py', 'runtime.py'}
    missing = sorted(x for x in required if not (PKG / x).is_file())
    report = {'revision': 'ORACLE_084_ATOMIC_READINESS',
              'status': 'HOLD_NATIVE_ACCOUNT_FUNDING_REPAIR',
              'allowed_sizes_lamports': list(SIZES), 'first_live_canary_lamports': SIZES[0],
              'directions': list(DIRECTIONS), 'native_source_locations': hits,
              'latest_failure': failure, 'missing_required_sources': missing,
              'execution_authority': False, 'signing': False, 'broadcast': False,
              'simulation_certified': False, 'realized_profit_certified': False}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE084] source_matches=%d missing_sources=%d' % (len(hits), len(missing)))
    for hit in hits:
        if any(x in hit['terms'] for x in ('user_token_out', 'BuyExactQuoteIn', 'simulate_native')):
            print('[SOURCE]', hit['file'], 'line='+str(hit['line']), ','.join(hit['terms']))
    print('[FAILURE]', json.dumps(failure, sort_keys=True))
    print('[HOLD] Native account initialization and WSOL funding not yet repaired')
    print('[REPORT]', OUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else run()
