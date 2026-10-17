from __future__ import annotations
import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

DEST = Path(
    'qseries_v2/oracle_execution/oracle_live_pricing/oracle230.py'
)

ROOT = Path(
    'runtime_state/oracle/oracle_live_execution'
)

REPORT = ROOT / 'ORACLE230_LIVE_PRICING_ACCEPTANCE.json'
REGISTRY = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
CACHE = ROOT / 'ORACLE226_ACCOUNT_STATES.sqlite3'


def inspect(cache=CACHE, registry=REGISTRY):
    report = {
        'build': 'ORACLE230',
        'status': 'HOLD',
        'offline_tests_passed': False,
        'live_price_certified': False,
        'profit_certified': False,
        'execution_authority': False,
        'signing': False,
        'broadcast': False,
        'first_live_canary_sol': 0.010
    }

    try:
        from qseries_v2.oracle_execution.oracle_live_pricing import (
            oracle226,
            oracle227,
            oracle228,
            oracle229
        )

        oracle226.test()
        oracle227.test()
        oracle228.test()
        oracle229.test()

        report['offline_tests_passed'] = True

    except Exception as exc:
        report['reason'] = (
            'OFFLINE_TEST_FAILURE:' + type(exc).__name__
        )
        return report

    if not registry.is_file():
        report['reason'] = 'HOLD_ORACLE218_REGISTRY_MISSING'
        return report

    if not cache.is_file():
        report['reason'] = (
            'HOLD_RAW_WS_HANDOFF_NOT_CONNECTED'
        )
        return report

    try:
        uri = cache.resolve().as_uri() + '?mode=ro'

        with closing(
            sqlite3.connect(uri, uri=True)
        ) as db:
            count = db.execute(
                'SELECT COUNT(*),'
                'COUNT(DISTINCT address) '
                'FROM account_states'
            ).fetchone()

        report['raw_event_count'] = count[0]
        report['unique_accounts'] = count[1]

    except (sqlite3.Error, OSError):
        report['reason'] = (
            'HOLD_INVALID_RAW_ACCOUNT_CACHE'
        )
        return report

    report['reason'] = (
        'HOLD_LIVE_WS_AND_OFFICIAL_EXACT_'
        'PRICER_CERTIFICATION_REQUIRED'
    )

    return report


def install():
    source = Path(__file__).read_bytes()

    if DEST.exists() and DEST.read_bytes() != source:
        raise RuntimeError(
            'REFUSE_OVERWRITE_EXISTING_ORACLE230'
        )

    DEST.parent.mkdir(parents=True, exist_ok=True)
    init = DEST.parent / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

    DEST.write_bytes(source)
    print('[ORACLE230_INSTALLED]', DEST)


def test():
    from qseries_v2.oracle_execution.oracle_live_pricing import (
        oracle229
    )

    result = oracle229.guard(
        {'ok': True},
        {'ok': True, 'profit_certified': True},
        100
    )

    assert result['admit'] is False
    assert result['signing'] is False
    assert result['broadcast'] is False

    print(
        '[ORACLE230_TEST_PASS] '
        'integration_contract=TRUE '
        'execution_lock=TRUE'
    )


def run():
    result = inspect()

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    REPORT.write_text(
        json.dumps(result, indent=2),
        encoding='utf-8'
    )

    print(
        '[ORACLE230_RESULT]',
        json.dumps(result, sort_keys=True)
    )
    print('[REPORT]', REPORT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()

    if args.install:
        install()

    if args.test:
        test()

    if args.run:
        run()

    if not (args.install or args.test or args.run):
        ap.print_help()