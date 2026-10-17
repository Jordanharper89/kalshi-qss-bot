
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import time
from pathlib import Path

TARGET = Path(
    'qseries_v2/oracle_execution/solana_atomic_executor/'
    'oracle_512_continuous_runtime.py'
)
ROOT = Path('runtime_state/oracle/oracle_live_execution')
STATE = ROOT / 'oracle_512_continuity_state.json'
REPORT = ROOT / 'oracle_512_runtime_certification.json'
CAP = 28


class Hold(RuntimeError):
    pass


def read(path, default):
    if not path.exists():
        return default
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        raise Hold('HOLD_INVALID_STATE_JSON')
    return obj


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        path.name + '.' + str(os.getpid()) + '.tmp'
    )
    try:
        temporary.write_text(
            json.dumps(obj, sort_keys=True, indent=2),
            encoding='utf-8'
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def select_rotation(rows, attempts, limit):
    return sorted(rows, key=lambda x: (
        int(attempts.get(x['token'], {}).get('count', 0)),
        int(attempts.get(x['token'], {}).get('last_epoch', 0)),
        -float(x.get('checked_at', 0)),
        x['token'],
    ))[:limit]


def record_attempts(attempts, rows, epoch):
    for row in rows:
        token = row['token']
        before = attempts.get(token, {})
        attempts[token] = {
            'count': int(before.get('count', 0)) + 1,
            'last_epoch': epoch,
        }


def certification(cycles):
    passed = [
        x for x in cycles
        if x.get('status') == 'PASS_LIVE_EPOCH_OBSERVED'
    ]

    if len(cycles) < 2 or len(passed) < 2:
        return 'HOLD_INSUFFICIENT_COMPLETED_EPOCHS'

    for old, new in zip(cycles, cycles[1:]):
        if old.get('status') != 'PASS_LIVE_EPOCH_OBSERVED':
            continue
        if new.get('status') != 'PASS_LIVE_EPOCH_OBSERVED':
            continue

        prior = set(old.get('matched_quoted_tokens') or ())
        latest = set(new.get('matched_quoted_tokens') or ())

        if (
            latest - prior
            and new.get('discovery_ran')
            and new.get('qualification_ran')
            and old.get('discovery', {}).get('catchup_complete')
            and new.get('discovery', {}).get('catchup_complete')
        ):
            return 'PASS_CONTINUOUS_REPLENISHMENT_TRIAL'

    if any(
        not x.get('discovery', {}).get('catchup_complete')
        for x in passed
    ):
        return 'HOLD_DISCOVERY_CATCHUP_PENDING'

    return 'HOLD_NEW_TOKEN_LIVE_PRICING_NOT_OBSERVED'


def walk_gap(
    rpc_call, rpc, address, anchor,
    page_size=1000, max_pages=20
):
    if (
        not anchor
        or not 1 <= page_size <= 1000
        or not 1 <= max_pages <= 20
    ):
        raise Hold('HOLD_GAP_CURSOR_OR_LIMIT_INVALID')

    rows = []
    seen = set()
    before = None

    for _ in range(max_pages):
        opts = {
            'limit': page_size,
            'commitment': 'confirmed',
        }
        if before:
            opts['before'] = before

        page = rpc_call(
            rpc,
            'getSignaturesForAddress',
            [address, opts]
        )

        if not isinstance(page, list):
            raise Hold('HOLD_GAP_SIGNATURE_RESPONSE_INVALID')

        for entry in page:
            sig = (
                entry.get('signature')
                if isinstance(entry, dict)
                else None
            )

            if not isinstance(sig, str) or not sig:
                raise Hold('HOLD_GAP_SIGNATURE_INVALID')

            if sig in seen:
                raise Hold('HOLD_GAP_SIGNATURE_DUPLICATED')

            if sig == anchor:
                return rows

            seen.add(sig)
            rows.append(entry)

        if len(page) < page_size:
            raise Hold('HOLD_SAVED_CURSOR_NOT_FOUND_NO_ADVANCE')

        tail = page[-1]['signature']
        if tail == before:
            raise Hold('HOLD_GAP_CURSOR_STALLED')

        before = tail

    raise Hold('HOLD_GAP_PAGE_CAP_NO_ADVANCE')


def oldest_contiguous(rows, count):
    if not 1 <= count <= 256:
        raise Hold('HOLD_GAP_BATCH_BOUND')

    return list(reversed(rows[-count:]))


def commit_mriya(m, previous, signatures, sleep_s=0.03):
    if not signatures:
        raise Hold('HOLD_EMPTY_GAP_COMMIT')

    found, failed = m.fetch_tokens(
        m.engine._rpc,
        signatures,
        sleep_s=sleep_s
    )

    old = m.read_json(m.TOKENS, {})
    old.update(found)

    next_state = dict(previous)
    next_state.update({
        'revision': 'ORACLE_508_V2',
        'head': signatures[-1]['signature'],
        'last_success_unix': time.time(),
    })

    # Commit tokens before advancing the cursor.
    # If interrupted between writes, replay is idempotent.
    m.atomic_json(m.TOKENS, old)
    m.atomic_json(m.CHECKPOINT, next_state)

    return (
        next_state,
        len(found),
        failed,
        len(old),
    )


def mriya_step(m, gap_batches=6, gap_size=64):
    previous = m.read_json(m.CHECKPOINT, {})
    head = previous.get('head') or previous.get('newest')

    # Confirm the saved cursor is physically present.
    # Never treat exhausted history as proof of continuity.
    if head:
        walk_gap(
            m.rpc_call,
            m.engine._rpc,
            m.engine.MRIYA,
            head
        )

    try:
        result, checkpoint, found = m.capture(
            m.engine._rpc,
            previous,
            size=16,
            pages=12,
            sleep_s=.03
        )

    except RuntimeError as exc:
        if str(exc) != 'INCREMENTAL_GAP_PAGE_LIMIT':
            raise

    else:
        existing = m.read_json(m.TOKENS, {})
        existing.update(found)

        m.atomic_json(m.TOKENS, existing)
        m.atomic_json(m.CHECKPOINT, checkpoint)

        return {
            'mode': 'NORMAL_CURSOR_SAFE',
            'new_signatures': result['signatures_new'],
            'history_backfilled': result['signatures_backfilled'],
            'known_mriya_tokens': len(existing),
            'history_complete': result['history_complete'],
            'catchup_complete': True,
            'gap_remaining': 0,
        }

    total_signatures = 0
    total_failed = 0
    total_tokens = 0
    existing_count = len(m.read_json(m.TOKENS, {}))
    gap_remaining = 0

    for i in range(gap_batches):
        anchor = previous.get('head') or previous.get('newest')

        rows = walk_gap(
            m.rpc_call,
            m.engine._rpc,
            m.engine.MRIYA,
            anchor
        )

        gap_remaining = len(rows)
        if not rows:
            break

        part = oldest_contiguous(rows, gap_size)

        previous, tokens, failed, existing_count = (
            commit_mriya(m, previous, part)
        )

        total_signatures += len(part)
        total_tokens += tokens
        total_failed += failed
        gap_remaining = max(0, len(rows) - len(part))

        print(
            '[ORACLE512_GAP_BRIDGE]',
            json.dumps({
                'batch': i + 1,
                'processed': len(part),
                'total_processed': total_signatures,
                'pending_at_scan': gap_remaining,
                'failed_tx_skipped': total_failed,
                'checkpoint_advanced': True,
            }, sort_keys=True),
            flush=True
        )

        if not gap_remaining:
            break

    return {
        'mode': 'CONTIGUOUS_GAP_BRIDGE',
        'new_signatures': total_signatures,
        'new_tokens_in_batches': total_tokens,
        'known_mriya_tokens': existing_count,
        'history_complete': bool(
            previous.get('history_complete')
        ),
        'catchup_complete': gap_remaining == 0,
        'gap_remaining': gap_remaining,
        'old_history_backfill_paused': True,
    }


def qualify_step(m, limit):
    try:
        m.audit(limit, 100, False)
    except SystemExit as e:
        if e.code not in (None, 0):
            raise Hold('HOLD_509_QUALIFICATION_ERRORS')

    report = read(m.REPORT, {})
    if report.get('status') != 'PASS_AUDIT':
        raise Hold('HOLD_509_QUALIFICATION_ERRORS')

    return {
        'checked': report.get('checked_this_run', 0),
        'pending': report.get('pending_unchecked', 0),
        'retry_pending': report.get('retry_pending', 0),
    }


def warm_step(candidates, q510, q18, q23):
    ready = []
    holds = []

    try:
        for row in candidates:
            try:
                warm = q510.warm_one(row)

                directions = {
                    x['direction']
                    for x in warm.get('directions', [])
                }

                if directions != set(q510.DIRECTIONS):
                    raise Hold('HOLD_INCOMPLETE_BIDIRECTIONAL_QUOTE')

                ready.append((row, warm))

                print(
                    '[ORACLE512_PREWARM]',
                    json.dumps({
                        'token': row['token'][:12],
                        'slot': warm['slot'],
                        'quote_directions': 2,
                    }),
                    flush=True
                )

            except Exception as e:
                reason = (
                    str(e)
                    if isinstance(e, (Hold, q510.Hold))
                    else type(e).__name__
                )
                holds.append({
                    'token': row['token'][:12],
                    'reason': reason,
                })
                print(
                    '[ORACLE512_WARM_HOLD]',
                    json.dumps(holds[-1]),
                    flush=True
                )

    finally:
        for mod in (q18, q23):
            worker = getattr(mod, '_worker', None)
            if worker is not None:
                worker.close()
                mod._worker = None

    if not ready:
        raise Hold('HOLD_NO_REWARMED_PAIR')

    return ready, holds


def stage_step(ready, q511):
    stage = q511.assert_contract()
    lock = Path(
        'runtime_state/oracle/final_boss_dual/scanner.lock'
    )

    if lock.exists():
        raise Hold('HOLD_SCANNER_LOCK_PRESENT')

    existing = []

    if stage.is_file():
        old = read(stage, {})
        if (
            isinstance(old.get('rows'), list)
            and 0 <= time.time()
            - float(old.get('generated_at', 0)) <= 600
        ):
            existing = old['rows'][:112]

    new = []

    for row, _ in ready:
        source = (
            'MRIYA_511_WARM'
            if 'MRIYA_COVERAGE' in row.get('sources', [])
            else 'LIVE_TAPE'
        )
        new.append({
            'token': row['token'],
            'pump_pool': row['pump_pool'],
            'source': source,
            'age': 0.0,
        })

    staged = q511.merger(existing, new)

    if len(staged) > 112:
        raise Hold('HOLD_STAGE_OVERFLOW')

    q511.scanner.save(stage, {
        'generated_at': time.time(),
        'rows': staged,
        'candidates': len(staged),
    })

    selected = q511.scanner.select_rows([])
    visible = q511.watchable(new, selected)

    if not visible:
        raise Hold('HOLD_NOT_VISIBLE_IN_28_PAIR_SELECTOR')

    return {
        'staged_path': str(stage),
        'stage_hash': hashlib.sha256(
            stage.read_bytes()
        ).hexdigest(),
        'visible_tokens': [
            x['token'] for x in visible
        ],
        'visible_in_first_28': len(visible),
        'staged_rows': len(staged),
    }


def live_cycle(epoch, args, state):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as q508,
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510,
        oracle_511_dynamic_admission as q511,
    )
    from qseries_v2.oracle_execution import (
        oracle_018_exact_sdk_hot_lane_cutover as q18,
        oracle_023_persistent_token_net_worker as q23,
    )

    lock = Path(
        'runtime_state/oracle/final_boss_dual/scanner.lock'
    )
    if lock.exists():
        raise Hold('HOLD_SCANNER_LOCK_PRESENT')

    print(
        '[ORACLE512_PHASE] epoch=%d discovery' % epoch,
        flush=True
    )
    discovery = mriya_step(
        q508,
        args.gap_batches,
        args.gap_size
    )
    print(
        '[ORACLE512_DISCOVERY]',
        json.dumps(discovery, sort_keys=True),
        flush=True
    )

    print(
        '[ORACLE512_PHASE] epoch=%d qualification' % epoch,
        flush=True
    )
    qualification = qualify_step(q509, args.qualify_limit)

    candidates, total = q510.selected(
        q509.load(q510.CHECKS), CAP
    )
    picked = select_rotation(
        candidates,
        state['attempts'],
        args.warm_limit
    )

    if not picked:
        raise Hold('HOLD_NO_509_VERIFIED_CANDIDATES')

    record_attempts(state['attempts'], picked, epoch)

    print(
        '[ORACLE512_PHASE] epoch=%d warm=%d verified=%d'
        % (epoch, len(picked), total),
        flush=True
    )
    warmed, holds = warm_step(
        picked, q510, q18, q23
    )

    stage = stage_step(warmed, q511)

    print(
        '[ORACLE512_PHASE] epoch=%d staged=%d visible=%d live_trial'
        % (
            epoch,
            stage['staged_rows'],
            stage['visible_in_first_28']
        ),
        flush=True
    )

    live = q511.trial(stage, args.seconds)

    result = {
        'epoch': epoch,
        'status': live.get(
            'status', 'HOLD_LIVE_TRIAL_NO_RESULT'
        ),
        'discovery_ran': True,
        'qualification_ran': True,
        'discovery': discovery,
        'qualification': qualification,
        'source_verified': total,
        'warm_attempted': len(picked),
        'warm_pass': len(warmed),
        'warm_holds': holds,
        'visible_in_first_28':
            stage['visible_in_first_28'],
        'staged_rows': stage['staged_rows'],
        'matched_quoted_tokens':
            live.get('matched_quoted_tokens', []),
        'market_heartbeats':
            live.get('market_heartbeats', 0),
        'quotes_010_max':
            live.get('quotes_010_max', 0),
        'epoch_completed':
            live.get('epoch_completed', False),
        'scanner_exit_code':
            live.get('returncode'),
        'scanner_admitted_observation':
            live.get('live_subscriptions_changed', False),
    }

    print(
        '[ORACLE512_EPOCH]',
        json.dumps(result, sort_keys=True),
        flush=True
    )
    return result


def runtime(args):
    if (
        os.getenv('QSB_SOLANA_PRIVATE_KEY')
        or os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO'
    ):
        raise Hold('HOLD_PRIVATE_KEY_ISOLATION_REQUIRED')

    if (
        not os.getenv('SOLANA_RPC_URL', '').startswith('https://')
        or not os.getenv('SOLANA_WS_URL', '').startswith('wss://')
    ):
        raise Hold('HOLD_RPC_AND_WS_REQUIRED')

    state = read(STATE, {
        'revision': 'ORACLE_512',
        'attempts': {},
        'cycles': [],
    })

    if (
        not isinstance(state.get('attempts'), dict)
        or not isinstance(state.get('cycles'), list)
    ):
        raise Hold('HOLD_STATE_SCHEMA_INVALID')

    completed = []
    epoch = int(state.get('next_epoch', 1))

    try:
        while args.epochs == 0 or len(completed) < args.epochs:
            print(
                '[ORACLE512_CYCLE_START] %d' % epoch,
                flush=True
            )

            try:
                entry = live_cycle(epoch, args, state)
            except Exception as exc:
                entry = {
                    'epoch': epoch,
                    'status': 'HOLD_EPOCH',
                    'reason': (
                        str(exc)
                        if isinstance(exc, Hold)
                        else type(exc).__name__
                    ),
                }
                print(
                    '[ORACLE512_EPOCH_HOLD]',
                    json.dumps(entry),
                    flush=True
                )

            completed.append(entry)
            state['cycles'] = (
                state['cycles'] + [entry]
            )[-16:]
            state['next_epoch'] = epoch + 1
            write(STATE, state)

            decision = certification(completed)

            quoted = set()
            for item in completed:
                quoted.update(
                    item.get('matched_quoted_tokens', [])
                )

            report = {
                'status': decision,
                'run_mode': (
                    'CONTINUOUS'
                    if args.epochs == 0
                    else 'BOUNDED_CERTIFICATION'
                ),
                'epochs_in_run': len(completed),
                'epochs_pass': sum(
                    e['status'] == 'PASS_LIVE_EPOCH_OBSERVED'
                    for e in completed
                ),
                'unique_tokens_quoted': len(quoted),
                'active_pair_cap': CAP,
                'full_cap_eviction_certified': False,
                'ws_acknowledgments_independently_verified': False,
                'scanner_code_modified': False,
                'read_only': True,
                'signing': False,
                'broadcast': False,
                'execution_authority': False,
                'latest_epoch': entry,
            }
            write(REPORT, report)

            print(
                '[ORACLE512]',
                json.dumps({
                    k: v for k, v in report.items()
                    if k != 'latest_epoch'
                }, sort_keys=True),
                flush=True
            )

            epoch += 1

            if entry['status'] != 'PASS_LIVE_EPOCH_OBSERVED':
                return 2

            if args.epochs == 0:
                time.sleep(args.pause)

    except KeyboardInterrupt:
        print(
            '[ORACLE512_STOP] USER_INTERRUPT',
            flush=True
        )
        return 130

    return (
        0
        if certification(completed).startswith('PASS_')
        else 2
    )


def tests():
    a = {'token': 'A' * 32, 'checked_at': 5}
    b = {'token': 'B' * 32, 'checked_at': 8}
    c = {'token': 'C' * 32, 'checked_at': 1}

    assert [
        x['token']
        for x in select_rotation([a, b, c], {}, 2)
    ] == [b['token'], a['token']]

    attempts = {}
    record_attempts(attempts, [b, a], 1)

    assert select_rotation(
        [a, b, c], attempts, 1
    )[0]['token'] == c['token']

    successful = [
        {
            'status': 'PASS_LIVE_EPOCH_OBSERVED',
            'matched_quoted_tokens': ['A'],
            'discovery': {'catchup_complete': True},
        },
        {
            'status': 'PASS_LIVE_EPOCH_OBSERVED',
            'matched_quoted_tokens': ['A', 'B'],
            'discovery': {'catchup_complete': True},
            'discovery_ran': True,
            'qualification_ran': True,
        },
    ]

    assert certification(successful).startswith('PASS_')

    unchanged = [
        successful[0],
        dict(
            successful[1],
            matched_quoted_tokens=['A']
        ),
    ]
    assert certification(unchanged).startswith('HOLD_')

    pending = [
        dict(
            successful[0],
            discovery={'catchup_complete': False}
        ),
        successful[1],
    ]
    assert certification(pending).startswith('HOLD_')

    class GapRpc:
        def __init__(self):
            self.sigs = [
                {'signature': f's{i}', 'err': None}
                for i in range(12, 0, -1)
            ]

        def call(self, _rpc, _method, params):
            opts = params[1]
            rows = self.sigs

            if opts.get('before'):
                start = next(
                    i for i, x in enumerate(rows)
                    if x['signature'] == opts['before']
                ) + 1
                rows = rows[start:]

            return rows[:opts['limit']]

    fake = GapRpc()
    rows = walk_gap(
        fake.call, None, 'TEST', 's2',
        page_size=4, max_pages=4
    )

    assert [
        x['signature'] for x in rows
    ] == [f's{i}' for i in range(12, 2, -1)]

    assert [
        x['signature']
        for x in oldest_contiguous(rows, 3)
    ] == ['s3', 's4', 's5']

    try:
        walk_gap(
            fake.call, None, 'TEST', 's99',
            page_size=4, max_pages=4
        )
    except Hold as exc:
        assert str(exc) == (
            'HOLD_SAVED_CURSOR_NOT_FOUND_NO_ADVANCE'
        )
    else:
        raise AssertionError('MISSING_ANCHOR_CANNOT_ADVANCE')

    try:
        walk_gap(
            fake.call, None, 'TEST', 's2',
            page_size=4, max_pages=1
        )
    except Hold as exc:
        assert str(exc) == 'HOLD_GAP_PAGE_CAP_NO_ADVANCE'
    else:
        raise AssertionError('CAPPED_GAP_CANNOT_ADVANCE')

    print(
        '[PASS] ORACLE512_V2 gap_pagination contiguous_cursor '
        'restart_safe no_skipped_signatures'
    )
    print(
        '[PASS] ORACLE512 rotation_fairness '
        '2_epoch_gate new_token_gate failclosed'
    )


def install():
    scanner = Path(
        'qseries_v2/oracle_execution/solana_atomic_executor/'
        'boss_scanner_live.py'
    )

    if not scanner.is_file() or not TARGET.parent.is_dir():
        raise Hold('HOLD_SCANNER_REPOSITORY_REQUIRED')

    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)

    temporary = TARGET.with_name(
        TARGET.name + '.' + str(os.getpid()) + '.tmp'
    )

    try:
        temporary.write_text(src, encoding='utf-8')
        os.replace(temporary, TARGET)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(
        '[PASS] ORACLE512_V2_FULL_INSTALL '
        'scanner_frozen no_signing no_broadcast'
    )
    print('[INSTALLED]', TARGET)


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument('--install', action='store_true')
    mode.add_argument('--test', action='store_true')
    mode.add_argument('--certify', action='store_true')
    mode.add_argument('--run', action='store_true')

    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--seconds', type=int, default=90)
    parser.add_argument('--warm-limit', type=int, default=4)
    parser.add_argument('--qualify-limit', type=int, default=12)
    parser.add_argument('--pause', type=int, default=5)
    parser.add_argument('--gap-batches', type=int, default=6)
    parser.add_argument('--gap-size', type=int, default=64)

    args = parser.parse_args()

    if args.install:
        install()
        return 0
    if args.test:
        tests()
        return 0

    if not (
        60 <= args.seconds <= 110
        and 1 <= args.warm_limit <= 28
        and 1 <= args.qualify_limit <= 28
        and 0 <= args.pause <= 300
        and 1 <= args.gap_batches <= 16
        and 1 <= args.gap_size <= 256
    ):
        parser.error('INVALID_BOUNDS')

    if args.certify and not 2 <= args.epochs <= 8:
        parser.error('CERTIFICATION_NEEDS_2_TO_8_EPOCHS')

    if args.run:
        args.epochs = 0

    return runtime(args)


if __name__ == '__main__':
    raise SystemExit(main())
