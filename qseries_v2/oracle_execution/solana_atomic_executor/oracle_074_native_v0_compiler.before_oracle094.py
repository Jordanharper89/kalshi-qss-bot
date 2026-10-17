"""ORACLE-092: verified registered ALT discovery and bounded, verified ALT subset search for two-leg unsigned v0.
No ALT creation/extension; no signer or broadcaster authority.
"""
import itertools
import re
import json
from pathlib import Path
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


ALT_KEYS = frozenset(('address', 'alt_address', 'alt', 'lookup_table',
                      'lookup_table_address', 'address_lookup_table'))

def _local_alt_candidates(root, token):
    """Read only bounded ALT manifests. Every address still needs RPC attestation."""
    base = Path(root)
    directories = (
        base / 'runtime_state/qseries/qarb_execution_engineering',
        base / 'runtime_state/oracle/oracle_live_execution',
    )
    found = []
    files_seen = 0
    def walk(obj, depth=0):
        if depth > 7:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                low = str(k).lower()
                if low in ALT_KEYS and isinstance(v, str):
                    if 32 <= len(v) <= 44 and re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]+', v):
                        found.append(v)
                elif low in ('tables', 'alts', 'lookup_tables', 'alt_registry',
                             'shared_alts', 'shared', 'tokens', 'registry'):
                    walk(v, depth+1)
                elif k == token:
                    walk(v, depth+1)
        elif isinstance(obj, list):
            for item in obj[:64]:
                walk(item, depth+1)
    for folder in directories:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob('*.json')):
            if files_seen >= 40:
                break
            if not any(s in path.name.lower() for s in ('alt', 'lookup', 'registry')):
                continue
            try:
                if path.stat().st_size > 256000:
                    continue
                doc = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError, UnicodeError):
                continue
            files_seen += 1
            walk(doc)
    return list(dict.fromkeys(found))[:24]

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
        [x for x in route.get('base_alts', []) if isinstance(x, str)] +
        _local_alt_candidates(root, token)))
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
        for address in choices[:24]:
            try:
                rec, err = v51.verified_table(core, address, user, ixs)
                if rec:
                    verified.append(rec)
                elif err:
                    result['attempts'].append({'candidate': name, 'alt_check': _redact(err)})
            except Exception as exc:
                result['attempts'].append({'candidate': name,
                                           'alt_check': type(exc).__name__})
        verified.sort(key=lambda r: -int(r.get('covered_accounts', 0)))
        print('[ORACLE092_ALT_COVERAGE] candidate=%s addresses=%d verified=%d best_coverage=%d' %
              (name, len(choices), len(verified),
               max((int(r.get('covered_accounts', 0)) for r in verified), default=0)), flush=True)
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
