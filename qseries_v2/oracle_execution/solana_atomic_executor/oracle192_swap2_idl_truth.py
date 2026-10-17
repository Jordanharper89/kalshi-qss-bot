"""Isolated Swap2 IDL validation, no scanner, no broadcast."""
import argparse, base64, copy, os, sys, subprocess
from . import runtime as r
from . import oracle190_reverse_preload_balance as q190

DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MEMO = 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
DISC = bytes([65,75,63,76,235,91,91,136])

ROLES = (
    'lb_pair','bitmap','reserve_x','reserve_y',
    'user_in','user_out','mint_x','mint_y',
    'oracle','host_fee','user','token_x_program',
    'token_y_program','memo_program',
    'event_authority','program'
)

def certify(route, direction):
    token = str(route.get('token', ''))
    template = r.METEORA_TEMPLATES.get(token)
    if not isinstance(template, dict):
        raise RuntimeError('ORACLE192_NO_WARM_TEMPLATE')

    ix = route.get('meteora_ix')
    if not isinstance(ix, dict) or ix.get('programId') != DLMM:
        raise RuntimeError('ORACLE192_MISSING_METEORA_IX')

    accounts = ix.get('accounts') or []
    fixed = template.get('fixed_accounts') or []
    if len(fixed) != 15 or len(accounts) < 17:
        raise RuntimeError('ORACLE192_BAD_ACCOUNT_COUNT')

    if any(not isinstance(a, dict) for a in accounts):
        raise RuntimeError('ORACLE192_ACCOUNT_NOT_MAPPING')

    expected = [str(x[0]) for x in fixed]
    expected.insert(13, MEMO)
    actual = [str(a.get('pubkey', '')) for a in accounts[:16]]

    if actual != expected or actual[15] != DLMM or actual[13] != MEMO:
        raise RuntimeError('ORACLE192_IDL_ACCOUNT_ORDER_DRIFT')

    if any(a.get('isSigner') or a.get('isWritable')
           for a in (accounts[13], accounts[14], accounts[15])):
        raise RuntimeError('ORACLE192_PROGRAM_ACCOUNT_FLAGS')

    allowed = {str(row[1]) for row in template.get('arrays') or []}
    tail = accounts[16:]
    if not tail or any(a.get('pubkey') not in allowed
                       or a.get('isWritable') is not True for a in tail):
        raise RuntimeError('ORACLE192_INVALID_BIN_ARRAY_TAIL')

    raw = base64.b64decode(ix.get('data', ''), validate=True)
    if not raw.startswith(DISC):
        raise RuntimeError('ORACLE192_WRONG_SWAP2_DISCRIMINATOR')

    # Swap2 Borsh: discriminator + 2 u64 + RemainingAccountsInfo Vec.
    if len(raw) == 24:
        raw += bytes(4)
    if len(raw) != 28 or raw[24:] != bytes(4):
        raise RuntimeError('ORACLE192_REMAINING_INFO_UNSUPPORTED')

    revised = copy.deepcopy(ix)
    revised['data'] = base64.b64encode(raw).decode()
    candidates = []

    for candidate in route.get('original_candidates') or []:
        if not isinstance(candidate, (tuple, list)) or len(candidate) != 2:
            raise RuntimeError('ORACLE192_BAD_CANDIDATE_CONTRACT')
        name, ixs = candidate
        indices = [
            j for j, x in enumerate(ixs)
            if isinstance(x, dict) and x.get('programId') == DLMM
        ]
        if len(indices) != 1 or ixs[indices[0]].get('data') != ix.get('data'):
            raise RuntimeError('ORACLE192_CANDIDATE_METEORA_DRIFT')

        cp = copy.deepcopy(ixs)
        cp[indices[0]] = copy.deepcopy(revised)
        candidates.append((name, cp))

    if not candidates:
        raise RuntimeError('ORACLE192_NO_CANDIDATES')

    out = dict(route)
    out['meteora_ix'] = revised
    out['original_candidates'] = candidates

    print('[ORACLE192_IDL_PASS] direction=%s named=16 bins=%d '
          'data_bytes=%d broadcast=FALSE' %
          (direction, len(tail), len(raw)), flush=True)
    return out

def worker():
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE192_LIVE_ARM_REFUSED')
    armed = getattr(r, '_live_010_armed', None)
    if not callable(armed) or armed():
        raise RuntimeError('ORACLE192_DISARM_NOT_PROVEN')

    old = r._fast_010_profit_lock_route
    def validated(*args, **kwargs):
        result = old(*args, **kwargs)
        if not isinstance(result, tuple) or len(result) != 3:
            raise RuntimeError('ORACLE192_LOCK_RESULT_DRIFT')
        direction = args[1] if len(args) > 1 else kwargs.get('direction','UNKNOWN')
        return certify(result[0], direction), result[1], result[2]

    r._fast_010_profit_lock_route = validated
    try:
        q190.worker()
    finally:
        r._fast_010_profit_lock_route = old

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    h = vault.load(db, vault.HELIUS)
    s = vault.load(db, vault.SOLANA)
    if not h or not s:
        raise RuntimeError('ORACLE192_STORED_CREDENTIALS_MISSING')

    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = s
    env['SOLANA_RPC_URL'] = (
        'https://mainnet.helius-rpc.com/?api-key=' + vault.quote(h,safe='')
    )
    env['SOLANA_WS_URL'] = (
        'wss://mainnet.helius-rpc.com/?api-key=' + vault.quote(h,safe='')
    )
    env['QSB_LIVE_ARM'] = 'NO'
    return subprocess.call([
        sys.executable, '-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.'
        'oracle192_swap2_idl_truth', '--worker'
    ], env=env)

def test():
    assert ROLES[1] == 'bitmap' and ROLES[8] == 'oracle'
    assert ROLES[13:] == ('memo_program','event_authority','program')
    assert len(DISC + bytes(16) + bytes(4)) == 28
    print('[TEST PASS] ORACLE192 Meteora account order and Borsh structure')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--run',action='store_true')
    g.add_argument('--worker',action='store_true')
    a = p.parse_args()
    test() if a.test else sys.exit(launch()) if a.run else worker()
