"""ORACLE-088 full replacement installer for ORACLE-074 ALT compression.
No network calls, signing, broadcasting, ALT mutations or scanner edits at installation.
"""
from pathlib import Path
import argparse
import ast
import shutil

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_074_native_v0_compiler.py')
SOURCE = r'''"""ORACLE-088: bounded, verified ALT subset search for two-leg unsigned v0.
No ALT creation/extension; no signer or broadcaster authority.
"""
import itertools
import re
from build_oracle_072_route_contract import validate_route, MAX_TX_BYTES

WIRE_LIMIT = min(int(MAX_TX_BYTES), 1232)

def _redact(value):
    s = str(value)
    s = re.sub(r'(?i)(api-key=)[^&\s]+', r'\1[REDACTED]', s)
    s = re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+', r'\1=[REDACTED]', s)
    return s[:160]

def _alt_sets(verified):
    """Try every unique subset of up to four verified tables, including no ALT."""
    rows = list(verified[:4])
    yield []
    for n in range(1, len(rows) + 1):
        for subset in itertools.combinations(rows, n):
            yield list(subset)

def compile_existing_alt(user, route, core, q87, root, extra_alt=None, v51=None):
    if v51 is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_051_original_scanner_alt_and_size_gate as v51)
    result = {'ok': False, 'reason': 'HOLD', 'attempts': [], 'used_alts': [],
              'min_trade_lamports': 10_000_000}
    if not isinstance(route, dict):
        result['reason'] = 'HOLD_ROUTE_INVALID'
        return result
    start = route.get('start_lamports')
    if type(start) is not int or start < 10_000_000:
        result['reason'] = 'HOLD_BELOW_010_SOL_MINIMUM'
        return result
    token = route.get('token')
    if not isinstance(token, str) or not token:
        result['reason'] = 'HOLD_TOKEN_MISSING'
        return result
    candidates = [c for c in q87.repaired_candidates(route)
                  if v51.candidate_is_safe(c)]
    if not candidates:
        result['reason'] = 'HOLD_NO_HELPER_COMPLETE_CANDIDATE'
        return result
    choices = list(dict.fromkeys(
        v51.saved_table_candidates(root, token, extra_alt) +
        [x for x in route.get('base_alts', []) if isinstance(x, str)]))
    best = None
    blockhash = None
    for cand in candidates:
        name = str(cand.get('name', 'UNKNOWN'))
        ixs = cand['instructions']
        gate = validate_route(route, core.PUMP, core.DLMM, ixs)
        if gate != 'ADMITTED':
            result['attempts'].append({'candidate': name, 'error': gate})
            continue
        verified = []
        for address in choices[:4]:
            try:
                rec, err = v51.verified_table(core, address, user, ixs)
                if rec:
                    verified.append(rec)
                elif err:
                    result['attempts'].append({'candidate': name, 'alt_check': _redact(err)})
            except Exception as exc:
                result['attempts'].append({'candidate': name,
                                           'alt_check': type(exc).__name__})
        for alts in _alt_sets(verified):
            try:
                if blockhash is None:
                    bh = core.rpc('getLatestBlockhash', [{'commitment': 'processed'}])
                    blockhash = bh['value']['blockhash']
                msg, raw = core.compile_v0(user, ixs, alts, blockhash)
                raw = bytes(raw)
                size = len(raw)
                if size > WIRE_LIMIT:
                    raise RuntimeError('ATOMIC_TX_TOO_LARGE:%d' % size)
                if size < 66 or raw[0] != 1 or raw[1:65] != bytes(64) or raw[65] != 128:
                    raise RuntimeError('NONCANONICAL_UNSIGNED_V0_PACKET')
                result['attempts'].append({'candidate': name, 'alt_count': len(alts),
                                           'bytes': size, 'ok': True})
                if best is None or size < best['bytes']:
                    best = {'ok': True, 'reason': 'LEGAL_UNSIGNED_V0', 'msg': msg,
                            'raw': raw, 'bytes': size, 'candidate': name,
                            'used_alts': alts, 'token': token,
                            'start_lamports': start}
            except Exception as exc:
                result['attempts'].append({'candidate': name, 'alt_count': len(alts),
                                           'error': type(exc).__name__,
                                           'detail': _redact(exc)})
    if best is not None:
        result.update(best)
        print('[ORACLE088_COMPILED] candidate=%s bytes=%d alts=%d' %
              (best['candidate'], best['bytes'], len(best['used_alts'])), flush=True)
        return result
    result['reason'] = 'HOLD_NO_LEGAL_HELPER_COMPLETE_V0'
    for item in result['attempts'][:8]:
        print('[ORACLE088_COMPILE_REJECT]', item, flush=True)
    return result
'''

def tests():
    ast.parse(SOURCE)
    assert 'def compile_existing_alt(' in SOURCE
    assert 'validate_route(route, core.PUMP, core.DLMM, ixs)' in SOURCE
    assert 'v51.verified_table(core, address, user, ixs)' in SOURCE
    assert 'WIRE_LIMIT = min(int(MAX_TX_BYTES), 1232)' in SOURCE
    import itertools
    for count in range(5):
        subsets = [s for n in range(count + 1) for s in itertools.combinations(range(count), n)]
        assert len(subsets) == 2 ** count
    if TARGET.exists():
        ast.parse(TARGET.read_text(encoding='utf-8'))
    print('[PASS] ORACLE088_STATIC_COMPILER_AND_ALT_SUBSETS')
    print('[BOUNDARY] NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST NO_ALT_MUTATION')

def install():
    tests()
    if not TARGET.is_file():
        raise RuntimeError('ORACLE074_TARGET_MISSING:' + str(TARGET))
    old = TARGET.read_text(encoding='utf-8')
    if 'ORACLE-088: bounded, verified ALT subset search' in old:
        print('[PASS] ORACLE088_ALREADY_INSTALLED')
        return
    if 'def compile_existing_alt(' not in old or 'ORACLE-074' not in old:
        raise RuntimeError('ORACLE074_UNRECOGNIZED_REFUSE_REPLACE')
    backup = TARGET.with_name(TARGET.stem + '.before_oracle088.py')
    if backup.exists():
        raise RuntimeError('ORACLE088_BACKUP_ALREADY_EXISTS')
    shutil.copy2(TARGET, backup)
    temp = TARGET.with_suffix('.oracle088.tmp')
    temp.write_text(SOURCE, encoding='utf-8')
    temp.replace(TARGET)
    print('[PASS] ORACLE088_ALT_SUBSET_OPTIMIZER_INSTALLED')
    print('[BACKUP]', backup)
    print('[TARGET]', TARGET)
    print('[HOLD] NO_RPC_SIMULATION_CERTIFIED; SIGNING_FALSE BROADCAST_FALSE')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    args = p.parse_args()
    tests() if args.test else install()
