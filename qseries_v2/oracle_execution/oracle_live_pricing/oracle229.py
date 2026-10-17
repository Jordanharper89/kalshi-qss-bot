from __future__ import annotations
import argparse
from pathlib import Path

DEST = Path(
    'qseries_v2/oracle_execution/oracle_live_pricing/oracle229.py'
)

RECOVERABLE = {
    'MISSING_ACCOUNT_BYTES',
    'STALE_ACCOUNT',
    'SLOT_SKEW',
    'INCOMPLETE_EXACT_QUOTE',
    'EXACT_PRICER_ERROR',
    'QUOTE_NOT_BOUND_TO_SNAPSHOT'
}


def guard(
    snapshot_result,
    quote_result,
    liquidity_raw=None,
    min_liquidity_raw=1
):
    if not snapshot_result.get('ok'):
        reason = snapshot_result.get(
            'reason', 'UNKNOWN_SNAPSHOT_ERROR'
        )

        return {
            'admit': False,
            'action': (
                'REHYDRATE_THEN_REPRICE'
                if reason in RECOVERABLE else 'HOLD'
            ),
            'reason': reason,
            'signing': False,
            'broadcast': False
        }

    if not quote_result.get('ok'):
        reason = quote_result.get(
            'reason', 'UNKNOWN_QUOTE_ERROR'
        )

        return {
            'admit': False,
            'action': (
                'REQUOTE_WITH_FRESH_SNAPSHOT'
                if reason in RECOVERABLE else 'HOLD'
            ),
            'reason': reason,
            'signing': False,
            'broadcast': False
        }

    if (
        type(liquidity_raw) is not int
        or type(min_liquidity_raw) is not int
        or liquidity_raw < min_liquidity_raw
        or min_liquidity_raw < 1
    ):
        return {
            'admit': False,
            'action': 'WAIT_LIQUIDITY',
            'reason': 'INSUFFICIENT_VERIFIED_LIQUIDITY',
            'signing': False,
            'broadcast': False
        }

    if not quote_result.get('profit_certified'):
        return {
            'admit': False,
            'action': 'WAIT_NET_ECONOMICS',
            'reason': 'NO_CERTIFIED_NET_PROFIT',
            'signing': False,
            'broadcast': False
        }

    return {
        'admit': False,
        'action': 'WAIT_ATOMIC_EXECUTION_GATES',
        'reason': 'BATCH1_NEVER_AUTHORIZES_EXECUTION',
        'signing': False,
        'broadcast': False
    }


def install():
    source = Path(__file__).read_bytes()

    if DEST.exists() and DEST.read_bytes() != source:
        raise RuntimeError(
            'REFUSE_OVERWRITE_EXISTING_ORACLE229'
        )

    DEST.parent.mkdir(parents=True, exist_ok=True)
    init = DEST.parent / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

    DEST.write_bytes(source)
    print('[ORACLE229_INSTALLED]', DEST)


def test():
    result = guard(
        {'ok': False, 'reason': 'STALE_ACCOUNT'}, {}
    )
    assert result['action'] == 'REHYDRATE_THEN_REPRICE'

    result = guard(
        {'ok': True},
        {'ok': False, 'reason': 'EXACT_PRICER_ERROR'}
    )
    assert result['action'] == 'REQUOTE_WITH_FRESH_SNAPSHOT'

    result = guard({'ok': True}, {'ok': True}, 0)
    assert result['action'] == 'WAIT_LIQUIDITY'

    result = guard({'ok': True}, {'ok': True}, 10)
    assert result['action'] == 'WAIT_NET_ECONOMICS'

    result = guard(
        {'ok': True},
        {'ok': True, 'profit_certified': True},
        10
    )

    assert result['admit'] is False
    assert result['signing'] is False
    assert result['broadcast'] is False

    print(
        '[ORACLE229_TEST_PASS] '
        'stale_recovery=TRUE '
        'liquidity_guard=TRUE '
        'quote_failure_guard=TRUE '
        'execution_locked=TRUE'
    )


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()

    if args.install:
        install()
    if args.test:
        test()
    if not args.install and not args.test:
        ap.print_help()