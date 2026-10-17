"""ORACLE-074: drop-in replacement for ORACLE-051 compile_existing_alt.
Does not touch the scanner, signer, broadcaster, or on-chain ALT state.
"""
import re
import sys
import unittest
from build_oracle_072_route_contract import validate_route, MAX_TX_BYTES
from build_oracle_073_verified_alt_optimizer import plan_alt_sets


def _redact(value):
    s = str(value)
    s = re.sub(r'(?i)(api-key=)[^&\s]+', r'\1[REDACTED]', s)
    s = re.sub(r'(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+',
               r'\1=[REDACTED]', s)
    return s[:160]


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
    choices = list(dict.fromkeys(v51.saved_table_candidates(root, token, extra_alt) +
                                 [x for x in route.get('base_alts', []) if isinstance(x, str)]))
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
        for alts in plan_alt_sets(verified):
            try:
                if blockhash is None:
                    bh = core.rpc('getLatestBlockhash', [{'commitment': 'processed'}])
                    blockhash = bh['value']['blockhash']
                msg, raw = core.compile_v0(user, ixs, alts, blockhash)
                raw = bytes(raw)
                if len(raw) > MAX_TX_BYTES:
                    raise RuntimeError('ATOMIC_TX_TOO_LARGE:%d' % len(raw))
                if len(raw) < 66 or raw[0] != 1 or raw[1:65] != bytes(64) or raw[65] != 128:
                    raise RuntimeError('NONCANONICAL_UNSIGNED_V0_PACKET')
                result['attempts'].append({'candidate': name, 'alt_count': len(alts),
                                           'bytes': len(raw), 'ok': True})
                result.update({'ok': True, 'reason': 'LEGAL_UNSIGNED_V0', 'msg': msg,
                               'raw': raw, 'bytes': len(raw), 'candidate': name,
                               'used_alts': alts, 'token': token,
                               'start_lamports': start})
                print('[ORACLE074_COMPILED] candidate=%s bytes=%d alts=%d' %
                      (name, len(raw), len(alts)), flush=True)
                return result
            except Exception as exc:
                detail = _redact(exc)
                result['attempts'].append({'candidate': name, 'alt_count': len(alts),
                                           'error': type(exc).__name__, 'detail': detail})
    result['reason'] = 'HOLD_NO_LEGAL_HELPER_COMPLETE_V0'
    for item in result['attempts'][:8]:
        print('[ORACLE074_COMPILE_REJECT]', item, flush=True)
    return result


class Tests(unittest.TestCase):
    def test_first_legal_alt_produces_packet(self):
        from types import SimpleNamespace
        ixs = [{'programId': p, 'data': '', 'accounts': []} for p in ('P', 'D')]
        v51 = SimpleNamespace(candidate_is_safe=lambda x: True,
                              saved_table_candidates=lambda *a: ['ALT'],
                              verified_table=lambda *a: ({'address': 'ALT', 'covered_accounts': 2}, None))
        class Core:
            PUMP, DLMM = 'P', 'D'
            def rpc(self, *_):
                return {'value': {'blockhash': 'blockhash'}}
            def compile_v0(self, _user, _ixs, alts, _bh):
                if not alts:
                    raise RuntimeError('ATOMIC_TX_TOO_LARGE:1550')
                return b'\x80', bytes([1]) + bytes(64) + bytes([128]) + bytes(150)
        q87 = SimpleNamespace(repaired_candidates=lambda _: [{'name': 'native', 'instructions': ixs}])
        result = compile_existing_alt('wallet', {'start_lamports': 10_000_000, 'token': 't'},
                                      Core(), q87, '.', v51=v51)
        self.assertTrue(result['ok'])
        self.assertEqual(result['used_alts'], ['ALT'])

    def test_no_venue_leg_fails_closed(self):
        from types import SimpleNamespace
        v51 = SimpleNamespace(candidate_is_safe=lambda _: True,
                              saved_table_candidates=lambda *a: [], verified_table=None)
        q87 = SimpleNamespace(repaired_candidates=lambda _: [{'name': 'bad', 'instructions':
                              [{'programId': 'P', 'accounts': [], 'data': ''}]}])
        core = SimpleNamespace(PUMP='P', DLMM='D')
        result = compile_existing_alt('wallet', {'start_lamports': 10_000_000, 'token': 't'},
                                      core, q87, '.', v51=v51)
        self.assertFalse(result['ok'])
        self.assertEqual(result['attempts'][0]['error'], 'NOT_EXACTLY_TWO_VENUE_LEGS')


if __name__ == '__main__':
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        print('[PASS] ORACLE074_READY EXACT_TWO_LEG_UNSIGNED_V0')
        print('[BOUNDARY] NO_SIGNING_NO_BROADCAST_NO_ALT_MUTATION')