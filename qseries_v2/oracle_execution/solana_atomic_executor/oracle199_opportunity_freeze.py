"""ORACLE199: SHA256 freeze and conservative multi-size opportunity ranking."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
STATE = Path('runtime_state/oracle/oracle_live_execution')
MANIFEST = STATE / 'ORACLE199_EXECUTION_FREEZE.json'
RANKING = STATE / 'ORACLE199_OPPORTUNITY_RANKING.json'
SIZES = (0.010, 0.015, 0.025, 0.050)
RESERVE = 150000  # Provisional cost cushion; NOT certified network/DEX fees.

def source_hashes():
    if not (ROOT / 'runtime.py').is_file():
        raise RuntimeError('ORACLE199_REPO_ROOT_NOT_FOUND')
    return {str(p.as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*.py')) if p.is_file()}

def freeze():
    current = source_hashes()
    if MANIFEST.exists():
        old = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if old.get('sha256') != current:
            raise RuntimeError('ORACLE199_EXECUTION_SOURCE_CHANGED_FREEZE_REFUSED')
        print('[ORACLE199_FREEZE_VERIFIED] files=%d unchanged=TRUE' % len(current))
        return
    STATE.mkdir(parents=True, exist_ok=True)
    payload = {'build': 'ORACLE199', 'status': 'REFERENCE_NOT_LIVE_CERTIFIED',
               'execution_authority': False, 'broadcast': False,
               'scope': 'All current executor Python sources; not an immutable git commit',
               'sha256': current}
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print('[ORACLE199_FREEZE_CREATED] files=%d broadcast=FALSE' % len(current))
    print('[MANIFEST]', MANIFEST)

def evaluate(quotes, token, size):
    rows = []
    for q in quotes:
        direction = str(q.get('direction', 'UNKNOWN'))
        start = int(q.get('start') or 0)
        end = int(q.get('local_end') or 0)
        minimum = q.get('local_min_end')
        minimum = int(minimum) if minimum is not None else None
        net = end - start
        min_net = minimum - start if minimum is not None else None
        reasons = []
        if start != round(size * 1e9): reasons.append('SIZE_MISMATCH')
        if direction not in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP'):
            reasons.append('UNKNOWN_DIRECTION')
        if net <= 0: reasons.append('NONPOSITIVE_GROSS_NET')
        if min_net is None: reasons.append('NO_CONSERVATIVE_MIN_END')
        elif min_net <= RESERVE: reasons.append('MIN_NET_BELOW_COST_RESERVE')
        rows.append({'token': token[:12], 'direction': direction, 'size_sol': size,
                     'start_lamports': start, 'estimated_end_lamports': end,
                     'estimated_net_lamports': net, 'min_end_lamports': minimum,
                     'min_net_lamports': min_net, 'assumed_cost_reserve_lamports': RESERVE,
                     'research_eligible': not reasons, 'hold_reasons': reasons,
                     'simulation_certified': False, 'execution_authorized': False})
    return rows

def rank():
    freeze()
    if os.environ.get('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE199_ARMED_REFUSED')
    from . import oracle186_direct_route_truth as d
    from . import runtime as r
    d.safety()
    old_rpc = r.q87.c.rpc
    r.q87.c.rpc = d.restricted_rpc_factory(old_rpc)
    rows = []
    errors = []
    try:
        pairs, user = d.bootstrap()
        for pair in pairs:
            token = str(pair.token)
            try:
                snap = r.immutable_snapshot(pair)
            except Exception as exc:
                errors.append({'token': token[:12], 'stage': 'SNAPSHOT',
                               'type': type(exc).__name__})
                continue
            for size in SIZES:
                try:
                    quotes = r.q18.exact_snapshot_opportunities(snap, size)
                    rows.extend(evaluate(quotes, token, size))
                except Exception as exc:
                    errors.append({'token': token[:12], 'size_sol': size,
                                   'stage': 'QUOTE', 'type': type(exc).__name__})
    finally:
        r.q87.c.rpc = old_rpc
        w = getattr(r.q18, '_worker', None)
        if w is not None:
            try: w.close(); r.q18._worker = None
            except Exception: pass
    rows.sort(key=lambda x: (x['research_eligible'], x['min_net_lamports'] or -10**18,
                              x['estimated_net_lamports']), reverse=True)
    report = {'build': 'ORACLE199', 'status': 'READ_ONLY_RESEARCH',
              'cost_reserve_provisional': True, 'quote_freshness_certified': False,
              'transfer_fees_certified': False, 'full_simulation_certified': False,
              'execution_authorized': False, 'broadcast': False,
              'scanned_pair_count': len(pairs), 'quoted_routes': len(rows),
              'eligible_research_only': sum(x['research_eligible'] for x in rows),
              'rows': rows, 'errors': errors}
    STATE.mkdir(parents=True, exist_ok=True)
    RANKING.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE199_RANK] pairs=%d quotes=%d provisional_positive=%d broadcast=FALSE' %
          (len(pairs), len(rows), report['eligible_research_only']))
    for row in rows[:10]:
        print('[CANDIDATE] token=%s direction=%s size=%.3f net=%d min_net=%s status=%s' %
              (row['token'], row['direction'], row['size_sol'],
               row['estimated_net_lamports'], row['min_net_lamports'],
               'RESEARCH_ONLY' if row['research_eligible'] else 'HOLD'))
    print('[REPORT]', RANKING)

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api(); h = vault.load(db, vault.HELIUS)
    s = vault.load(db, vault.SOLANA)
    if not h or not s: raise RuntimeError('ORACLE199_CREDENTIALS_MISSING')
    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = s
    env['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['SOLANA_WS_URL'] = 'wss://mainnet.helius-rpc.com/?api-key=' + vault.quote(h, safe='')
    env['QSB_LIVE_ARM'] = 'NO'
    return subprocess.call([sys.executable, '-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.oracle199_opportunity_freeze',
        '--rank-worker'], env=env)

def test():
    rows = evaluate([{'direction': 'METEORA_TO_PUMP', 'start': 10000000,
                      'local_end': 10100000, 'local_min_end': 10020000}], 'T', 0.010)
    assert rows[0]['research_eligible'] is False
    rows = evaluate([{'direction': 'METEORA_TO_PUMP', 'start': 10000000,
                      'local_end': 11000000, 'local_min_end': 10500000}], 'T', 0.010)
    assert rows[0]['research_eligible'] is True
    assert not evaluate([{'direction':'PUMP_TO_METEORA', 'start':10000000,
                          'local_end':12000000}], 'T', 0.010)[0]['research_eligible']
    print('[TEST PASS] ORACLE199 negative, missing floor and positive admission')

if __name__ == '__main__':
    p = argparse.ArgumentParser(); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--freeze', action='store_true')
    g.add_argument('--test', action='store_true')
    g.add_argument('--rank', action='store_true')
    g.add_argument('--rank-worker', action='store_true')
    a = p.parse_args()
    if a.test: test()
    elif a.freeze: freeze()
    elif a.rank: sys.exit(launch())
    else: rank()
