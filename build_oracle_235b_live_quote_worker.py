"""ORACLE-235B: disarmed, real canonical quote probe. No trades."""
import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE235B_LIVE_QUOTES.json')
DIRECTIONS = {'METEORA_TO_PUMP', 'PUMP_TO_METEORA'}
SIZE = 0.010


def outcome_status(quotes, start):
    if not isinstance(quotes, (list, tuple)):
        return 'HOLD_NON_LIST_QUOTES', []
    directions = [q.get('direction') for q in quotes if isinstance(q, dict)]
    if len(quotes) != 2 or set(directions) != DIRECTIONS:
        return 'HOLD_MISSING_DIRECTION', []
    output = []
    for q in quotes:
        mq = q.get('mq')
        if not isinstance(mq, dict):
            return 'HOLD_DLMM_QUOTE_MISSING', []
        # Different SDKs expose differing completeness markers. None is not PASS.
        filled = mq.get('complete') is True
        remaining = mq.get('remaining_raw', mq.get('remaining_in'))
        if not filled or type(remaining) is not int or remaining != 0:
            return 'HOLD_DLMM_COMPLETENESS_UNPROVEN', []
        end = q.get('local_end')
        if type(end) is not int or end <= 0 or q.get('start') != start:
            return 'HOLD_AMOUNT_CONTRACT', []
        net = q.get('local_net')
        if type(net) is not int or net != end - start:
            return 'HOLD_NET_MISMATCH', []
        output.append({'direction': q['direction'], 'start_lamports': start,
                       'end_lamports': end, 'gross_delta_lamports': net,
                       'remaining_raw': 0, 'complete': True})
    return 'PASS_CANONICAL_HYDRATED_QUOTE', output


def test():
    start = 10_000_000
    good = [{'direction': d, 'start': start, 'local_end': start+7,
             'local_net': 7, 'mq': {'complete': True, 'remaining_raw': 0}}
            for d in sorted(DIRECTIONS)]
    assert outcome_status(good, start)[0] == 'PASS_CANONICAL_HYDRATED_QUOTE'
    assert outcome_status(good[:1], start)[0] == 'HOLD_MISSING_DIRECTION'
    bad = json.loads(json.dumps(good))
    bad[0]['mq']['remaining_raw'] = 3
    assert outcome_status(bad, start)[0] == 'HOLD_DLMM_COMPLETENESS_UNPROVEN'
    bad = json.loads(json.dumps(good))
    bad[0]['local_net'] = 8
    assert outcome_status(bad, start)[0] == 'HOLD_NET_MISMATCH'
    print('[ORACLE235B_TEST_PASS] both_directions=TRUE partials_rejected=TRUE gross_math=TRUE')


def launch(seconds, limit):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_LIVE_ARM_MUST_BE_NO')
    # This research process does not need a signer.
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT_REFUSE_RESEARCH_PROCESS')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('HOLD_RPC_URL_NOT_PROVIDED')
    result = {'build': 'ORACLE235B', 'mode': 'READ_ONLY', 'size_sol': SIZE,
              'signing': False, 'broadcast': False, 'profit_certified': False,
              'live_price_certified': False, 'ws_hydration_reconciled': False,
              'mriya_certified': False, 'pairs': [], 'failures': [],
              'started_at': datetime.now(timezone.utc).isoformat()}
    started = time.monotonic()
    original_rpc = None
    r = None
    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as d
        original_rpc = r.q87.c.rpc
        r.q87.c.rpc = d.restricted_rpc_factory(original_rpc)
        # Do not call d.bootstrap(): it requests a wallet identity
        # and prepares transaction templates.
        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)
        pairs = list(state.get('pairs') or [])
        result['prepared_pairs'] = len(pairs)
        for pair in pairs[:limit]:
            if time.monotonic() - started > seconds:
                result['failures'].append('TIME_LIMIT')
                break
            label = str(getattr(pair, 'token', ''))[:12]
            row = {'token_prefix': label, 'size_sol': SIZE}
            try:
                r.q18.worker().warm(str(pair.pump_pool))
                snapshot = r.immutable_snapshot(pair)
                if not snapshot.get('dlmm_state'):
                    raise RuntimeError('DLMM_NOT_HYDRATED')
                quotes = r.q18.exact_snapshot_opportunities(snapshot, SIZE)
                code, inspected = outcome_status(quotes, 10_000_000)
                row.update({'status': code, 'quotes': inspected})
            except Exception as exc:
                row.update({'status': 'HOLD_QUOTE_FAILURE',
                            'failure_type': type(exc).__name__,
                            'failure_code': str(exc)[:100] if str(exc) in (
                                'DLMM_PARTIAL', 'DLMM_DIRECTION',
                                'REVERSE_TOKEN_NET_ZERO', 'FORWARD_TOKEN_NET_ZERO')
                            else 'UNCLASSIFIED'})
            result['pairs'].append(row)
    except Exception as exc:
        result['failures'].append('PREPARE_' + type(exc).__name__)
    finally:
        if original_rpc is not None and r is not None:
            r.q87.c.rpc = original_rpc
        result['finished_at'] = datetime.now(timezone.utc).isoformat()
        result['pair_outcomes'] = dict(Counter(p['status'] for p in result['pairs']))
        result['status'] = 'HOLD_WS_HYDRATION_NOT_RECONCILED'
        if not result['pairs']:
            result['status'] = 'HOLD_NO_QUOTE_RESULTS'
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print('[ORACLE235B_RESULT]', json.dumps({
            'status': result['status'],
            'prepared_pairs': result.get('prepared_pairs', 0),
            'pair_outcomes': result['pair_outcomes'],
            'failures': result['failures'],
            'live_price_certified': False,
            'signing': False,
            'broadcast': False
        }, sort_keys=True))
        print('[REPORT]', REPORT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--seconds', type=int, default=40)
    parser.add_argument('--pairs', type=int, default=12)
    args = parser.parse_args()
    if args.test:
        test()
    if args.run:
        launch(max(1, min(args.seconds, 120)), max(1, min(args.pairs, 30)))