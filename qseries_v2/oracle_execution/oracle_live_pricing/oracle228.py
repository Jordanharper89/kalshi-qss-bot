from __future__ import annotations
import argparse
import inspect
import math
from pathlib import Path

DEST = Path(
    'qseries_v2/oracle_execution/oracle_live_pricing/oracle228.py'
)

DIRECTIONS = (
    'PUMP_TO_METEORA',
    'METEORA_TO_PUMP'
)


def quote_both(snap, size_sol, exact_pricer=None):
    if not snap.get('ok'):
        return {
            'ok': False,
            'reason': 'SNAPSHOT_UNCERTIFIED'
        }

    if exact_pricer is None:
        return {
            'ok': False,
            'reason': 'HOLD_OFFICIAL_EXACT_PRICER_NOT_BOUND'
        }

    if inspect.iscoroutinefunction(exact_pricer):
        return {
            'ok': False,
            'reason': 'ASYNC_PRICER_REQUIRES_EXPLICIT_ADAPTER'
        }

    if (
        type(size_sol) not in (int, float)
        or not math.isfinite(size_sol)
        or size_sol < 0.010
    ):
        return {
            'ok': False,
            'reason': 'INVALID_TRADE_SIZE'
        }

    quotes = {}

    for direction in DIRECTIONS:
        try:
            result = exact_pricer(
                snapshot=snap,
                direction=direction,
                size_sol=size_sol
            )
        except Exception as exc:
            return {
                'ok': False,
                'reason': 'EXACT_PRICER_ERROR',
                'direction': direction,
                'error_type': type(exc).__name__
            }

        if not isinstance(result, dict):
            return {
                'ok': False,
                'reason': 'INVALID_QUOTE_RESPONSE'
            }

        if result.get('ok') is not True:
            return {
                'ok': False,
                'reason': 'INCOMPLETE_EXACT_QUOTE',
                'direction': direction
            }

        if (
            result.get('direction') != direction
            or result.get('input_size_sol') != size_sol
        ):
            return {
                'ok': False,
                'reason': 'QUOTE_IDENTITY_MISMATCH'
            }

        required = (
            'input_raw',
            'output_raw',
            'pool_addresses',
            'quote_slot',
            'official_sdk'
        )

        if any(key not in result for key in required):
            return {
                'ok': False,
                'reason': 'QUOTE_LINEAGE_NOT_PROVEN'
            }

        if result['official_sdk'] is not True:
            return {
                'ok': False,
                'reason': 'OFFICIAL_PRICING_NOT_VERIFIED'
            }

        expected = {
            snap['pump']['address'],
            snap['meteora']['address']
        }

        if (
            type(result['input_raw']) is not int
            or result['input_raw'] <= 0
            or type(result['output_raw']) is not int
            or result['output_raw'] <= 0
            or not isinstance(result['pool_addresses'], (list, tuple))
            or len(result['pool_addresses']) != 2
            or set(result['pool_addresses']) != expected
            or type(result['quote_slot']) is not int
            or result['quote_slot'] < snap['min_slot']
        ):
            return {
                'ok': False,
                'reason': 'QUOTE_NOT_BOUND_TO_SNAPSHOT',
                'direction': direction
            }

        quotes[direction] = result

    return {
        'ok': True,
        'quotes': quotes,
        'profit_certified': False,
        'execution_authority': False
    }


def install():
    source = Path(__file__).read_bytes()

    if DEST.exists() and DEST.read_bytes() != source:
        raise RuntimeError(
            'REFUSE_OVERWRITE_EXISTING_ORACLE228'
        )

    DEST.parent.mkdir(parents=True, exist_ok=True)
    init = DEST.parent / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

    DEST.write_bytes(source)
    print('[ORACLE228_INSTALLED]', DEST)


def test():
    snap = {
        'ok': True,
        'min_slot': 8,
        'pump': {'address': 'P'},
        'meteora': {'address': 'M'}
    }

    assert quote_both(snap, 0.010)['reason'] == (
        'HOLD_OFFICIAL_EXACT_PRICER_NOT_BOUND'
    )

    def fixture_pricer(*, snapshot, direction, size_sol):
        return {
            'ok': True,
            'direction': direction,
            'input_size_sol': size_sol,
            'input_raw': 100,
            'output_raw': 101,
            'pool_addresses': ['P', 'M'],
            'quote_slot': 8,
            'official_sdk': True
        }

    result = quote_both(snap, 0.010, fixture_pricer)

    assert result['ok']
    assert len(result['quotes']) == 2
    assert result['profit_certified'] is False

    assert not quote_both(
        snap, 0.009, fixture_pricer
    )['ok']

    assert not quote_both(
        snap, 0.010, lambda **kwargs: {'ok': True}
    )['ok']

    print(
        '[ORACLE228_TEST_PASS] '
        'bidirectional_contract=TRUE '
        'fixture_validation=TRUE '
        'missing_official_adapter_hold=TRUE '
        'execution_disabled=TRUE'
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