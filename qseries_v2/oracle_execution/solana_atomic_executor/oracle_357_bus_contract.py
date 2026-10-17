"""ORACLE-357: strict, local, no-RPC nomination validation/coalescing."""
from collections.abc import Mapping

FIELDS = ('id', 'token', 'pump_pool', 'meteora_pool', 'direction', 'size_lamports', 'created_ns')
DIRECTIONS = frozenset(('PUMP_TO_METEORA', 'METEORA_TO_PUMP'))
MIN_SIZE = 10_000_000
MAX_SIZE = 100_000_000

def _valid(n):
    if not isinstance(n, Mapping):
        return None, 'NON_MAPPING'
    if any(f not in n for f in FIELDS):
        return None, 'MISSING_FIELDS'
    if not all(isinstance(n[f], str) and n[f].strip() for f in ('token', 'pump_pool', 'meteora_pool')):
        return None, 'INVALID_IDENTITY'
    if n['direction'] not in DIRECTIONS:
        return None, 'INVALID_DIRECTION'
    try:
        ident = int(n['id'])
        size = int(n['size_lamports'])
        created = int(n['created_ns'])
    except (ValueError, TypeError, OverflowError):
        return None, 'INVALID_NUMERIC'
    if ident <= 0 or created <= 0 or size < MIN_SIZE or size > MAX_SIZE:
        return None, 'INVALID_BOUNDS'
    # Accept only genuinely integral numeric fields; no floats/booleans as IDs/sizes.
    for k, value in (('id', ident), ('size_lamports', size), ('created_ns', created)):
        raw = n[k]
        if isinstance(raw, bool) or isinstance(raw, float) or str(raw) != str(value):
            return None, 'NON_CANONICAL_NUMERIC'
    return dict(n), None

def keep_latest_valid(rows, counts):
    # No speculative decoding: scanner.new_events must return a list/tuple of nominations.
    if not isinstance(rows, (list, tuple)):
        counts['bus_contract_bad_batch'] += 1
        return []
    latest = {}
    for row in rows:
        n, reason = _valid(row)
        if reason:
            counts['bus_contract_' + reason] += 1
            continue
        key = (n['token'], n['pump_pool'], n['meteora_pool'], n['direction'], int(n['size_lamports']))
        ident = int(n['id'])
        if key not in latest or ident > int(latest[key]['id']):
            if key in latest:
                counts['bus_contract_superseded'] += 1
            latest[key] = n
        else:
            counts['bus_contract_superseded'] += 1
    return sorted(latest.values(), key=lambda n: int(n['id']))
