
"""ORACLE197 complete installer: reverse bin arrays, simulation only."""
import argparse, ast
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST = ROOT / 'oracle197_reverse_bin_array_execution.py'

CODE = r'''"""Existing funded executor with expanded warm reverse bin-array metas."""
import argparse, copy, os, subprocess, sys
from . import runtime as r
from . import oracle194_reverse_wsol_execution as q194
from . import oracle195_consolidated_reverse_execution as q195

DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def expand(route, direction, limit=3):
    if direction != 'METEORA_TO_PUMP':
        return route

    token = str(route.get('token', ''))
    t = r.METEORA_TEMPLATES.get(token)
    if not isinstance(t, dict):
        raise RuntimeError('ORACLE197_NO_WARM_TEMPLATE')

    available = list(t.get('arrays') or [])
    if len(available) < 2:
        raise RuntimeError('ORACLE197_TOO_FEW_WARM_ARRAYS')

    reverse_direction = not bool(t['swap_for_y'])
    ordered = available if reverse_direction else list(reversed(available))
    selected = [str(x[1]) for x in ordered[:min(limit, len(ordered))]]

    if len(selected) != len(set(selected)):
        raise RuntimeError('ORACLE197_DUPLICATE_BIN_ARRAY')

    swap = route.get('meteora_ix') or {}
    accounts = swap.get('accounts') or []
    if swap.get('programId') != DLMM or len(accounts) != 17:
        raise RuntimeError('ORACLE197_EXPECT_ONE_ORIGINAL_BIN_ARRAY')

    if accounts[16].get('pubkey') != selected[0]:
        raise RuntimeError('ORACLE197_BIN_ARRAY_DIRECTION_DRIFT')
    if not accounts[16].get('isWritable'):
        raise RuntimeError('ORACLE197_BIN_ARRAY_NOT_WRITABLE')

    extra = [
        {'pubkey': p, 'isSigner': False, 'isWritable': True}
        for p in selected[1:]
    ]
    revised = copy.deepcopy(swap)
    revised['accounts'] = copy.deepcopy(accounts) + extra

    candidates = []
    for candidate in route.get('original_candidates') or []:
        if not isinstance(candidate, (tuple, list)) or len(candidate) != 2:
            raise RuntimeError('ORACLE197_CANDIDATE_CONTRACT')
        name, ixs = candidate
        places = [
            i for i, ix in enumerate(ixs)
            if ix.get('programId') == DLMM
        ]
        if len(places) != 1:
            raise RuntimeError('ORACLE197_SWAP2_COUNT')
        j = places[0]
        if ixs[j].get('accounts') != accounts:
            raise RuntimeError('ORACLE197_CANDIDATE_LAYOUT_DRIFT')

        cp = copy.deepcopy(ixs)
        cp[j] = copy.deepcopy(revised)
        candidates.append((name, cp))

    if not candidates:
        raise RuntimeError('ORACLE197_NO_CANDIDATES')

    out = dict(route)
    out['meteora_ix'] = revised
    out['original_candidates'] = candidates

    print('[ORACLE197_REVERSE_ARRAYS] warmed=%d included=%d ordered=TRUE broadcast=FALSE' %
          (len(available), len(selected)), flush=True)
    return out

def worker():
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE197_ARMED_REFUSED')
    armed = getattr(r, '_live_010_armed', None)
    if not callable(armed) or armed():
        raise RuntimeError('ORACLE197_DISARM_UNCERTIFIED')

    previous = q194.inject

    def combined(route, direction):
        return expand(previous(route, direction), direction)

    q194.inject = combined
    try:
        q195.worker()
    finally:
        q194.inject = previous

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    d = vault.api()
    h = vault.load(d, vault.HELIUS)
    s = vault.load(d, vault.SOLANA)
    if not h or not s:
        raise RuntimeError('ORACLE197_VAULT_MISSING')

    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = s
    env['SOLANA_RPC_URL'] = (
        'https://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['SOLANA_WS_URL'] = (
        'wss://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['QSB_LIVE_ARM'] = 'NO'
    return subprocess.call([
        sys.executable, '-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.'
        'oracle197_reverse_bin_array_execution',
        '--worker'
    ], env=env)

def test():
    original = dict(r.METEORA_TEMPLATES)
    try:
        r.METEORA_TEMPLATES['T'] = {
            'swap_for_y': True,
            'arrays': [(1, 'a'), (2, 'b'), (3, 'c')]
        }
        ix = {
            'programId': DLMM,
            'accounts': [
                {'pubkey': 'named', 'isWritable': False}
                for _ in range(16)
            ] + [{'pubkey': 'c', 'isWritable': True}]
        }
        route = {
            'token': 'T',
            'meteora_ix': ix,
            'original_candidates': [
                ('x', [ix, {'programId': 'OTHER'}])
            ]
        }
        out = expand(route, 'METEORA_TO_PUMP')
        assert [x['pubkey'] for x in out['meteora_ix']['accounts'][16:]] == [
            'c', 'b', 'a'
        ]
        assert len(out['original_candidates'][0][1][0]['accounts']) == 19
        assert len(route['meteora_ix']['accounts']) == 17
        assert expand(route, 'PUMP_TO_METEORA') is route
    finally:
        r.METEORA_TEMPLATES.clear()
        r.METEORA_TEMPLATES.update(original)

    print('[TEST PASS] ORACLE197 ordered arrays, original unchanged, no broadcast')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--run', action='store_true')
    g.add_argument('--worker', action='store_true')
    a = p.parse_args()
    test() if a.test else sys.exit(launch()) if a.run else worker()
'''

def test():
    ast.parse(CODE)
    assert 'q195.worker()' in CODE
    assert 'q194.inject = combined' in CODE
    assert 'sendTransaction' not in CODE
    print('[INSTALLER TEST PASS] ORACLE197 isolated module parses')

def install():
    for name in (
        'runtime.py',
        'oracle194_reverse_wsol_execution.py',
        'oracle195_consolidated_reverse_execution.py'
    ):
        if not (ROOT / name).is_file():
            raise RuntimeError('ORACLE197_MISSING_' + name)
    if DEST.exists() and DEST.read_text(encoding='utf-8') != CODE:
        raise RuntimeError('ORACLE197_DESTINATION_DIFFERS')
    DEST.write_text(CODE, encoding='utf-8')
    print('[INSTALL PASS] ORACLE197 reverse arrays; scanner unchanged')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    a = p.parse_args()
    test() if a.test else install()
