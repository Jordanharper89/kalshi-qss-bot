from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import time
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_524_verified_execution_shadow.py'
SCANNER = BASE / 'boss_scanner_live.py'
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
Q521 = Path('runtime_state/oracle/oracle_live_execution/oracle_521/quote_coverage.json')
Q523 = Path('runtime_state/oracle/oracle_live_execution/oracle_523/inventory_handoff.json')
REGISTRY = Path('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_524')
SHADOW = ROOT / 'verified_candidate_registry.json'
REPORT = ROOT / 'handoff_report.json'
REVISION = 'CHECKPOINT11_MULTI_POOL_REGISTRY_V1'
B58 = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')

class Hold(RuntimeError):
    pass

def pubkey(key):
    return isinstance(key, str) and 32 <= len(key) <= 44 and set(key) <= B58

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    if not path.is_file():
        raise Hold('MISSING_' + path.name)
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise Hold('INVALID_JSON_ROOT_' + path.name)
    return data

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

def registry_shape(registry):
    # Inspect native format without guessing or modifying it.
    containers = {}
    for key, value in registry.items():
        if isinstance(value, (list, dict)):
            sample = (
                next(iter(value.values()), None)
                if isinstance(value, dict)
                else (value[0] if value else None)
            )
            containers[key] = {
                'type': type(value).__name__,
                'length': len(value),
                'first_entry_type': type(sample).__name__,
                'first_entry_fields': (
                    sorted(sample.keys())
                    if isinstance(sample, dict) else []
                )
            }
    return {
        'top_level_keys': sorted(registry.keys()),
        'containers': containers
    }

def assemble(stage, observed, qualified, canonical):
    if observed.get('status') != 'PASS_LIVE_QUOTE_COVERAGE_MEASURED':
        raise Hold('ORACLE521_LIVE_PASS_REQUIRED')

    if canonical.get('revision') != REVISION:
        raise Hold('EXECUTOR_REGISTRY_REVISION_DRIFT')

    staged = stage.get('rows')
    evidence = observed.get('pair_results')

    if not isinstance(staged, list) or not 1 <= len(staged) <= 28:
        raise Hold('INVALID_STAGE_ROWS')

    if not isinstance(evidence, list) or len(evidence) != len(staged):
        raise Hold('521_PAIR_ROWS_COUNT_MISMATCH')

    if not isinstance(qualified, list):
        raise Hold('QUALIFIED_SELECTION_NOT_LIST')

    by_quote = {}

    for item in evidence:
        if not isinstance(item, dict) or not pubkey(item.get('token')):
            raise Hold('BAD_521_TOKEN')

        token = item['token']

        if token in by_quote:
            raise Hold('DUPLICATE_521_TOKEN')

        result = item.get('result')

        if result not in (
            'MATCHED_QUOTE_OBSERVED',
            'NO_MATCHED_QUOTE_IN_WINDOW'
        ):
            raise Hold('UNKNOWN_QUOTE_STATE')

        by_quote[token] = result == 'MATCHED_QUOTE_OBSERVED'

    if (
        len(evidence) != observed.get('visible_pairs')
        or sum(by_quote.values()) != observed.get('matched_quoted_pairs')
    ):
        raise Hold('ORACLE521_COUNTER_DRIFT')

    by_qualified = {}

    for row in qualified:
        if not isinstance(row, dict) or not pubkey(row.get('token')):
            raise Hold('INVALID_QUALIFIED_ROW')

        token = row['token']

        if token in by_qualified and row != by_qualified[token]:
            raise Hold('QUALIFIED_DUPLICATE_CONFLICT')

        by_qualified[token] = row

    joined = []
    used = set()

    for item in staged:
        if not isinstance(item, dict):
            raise Hold('BAD_STAGE_ROW')

        token = item.get('token')
        pump = item.get('pump_pool')

        if not pubkey(token) or not pubkey(pump) or token in used:
            raise Hold('BAD_OR_DUPLICATE_STAGE_IDENTITY')

        used.add(token)

        match = by_qualified.get(token)

        if match is None:
            raise Hold('NOT_IN_VERIFIED_QUALIFICATION_' + token[:12])

        if match.get('pump_pool') != pump:
            raise Hold('PUMP_POOL_MISMATCH_' + token[:12])

        meteora = match.get('meteora_pool')

        if not pubkey(meteora) or meteora == pump:
            raise Hold('BAD_METEORA_POOL_' + token[:12])

        joined.append({
            'pair_key': token + '|' + meteora,
            'token': token,
            'pump_pool': pump,
            'meteora_pool': meteora,
            'observed_quote_in_521_window': by_quote[token]
        })

    if used != set(by_quote):
        raise Hold('ORACLE521_STAGE_TOKEN_SET_MISMATCH')

    if len({r['pair_key'] for r in joined}) != len(joined):
        raise Hold('DUPLICATED_PAIR_KEY')

    # Independent candidate format.
    # Not yet a native Checkpoint-11 production registry.
    shadow = {
        'revision': 'ORACLE524_VERIFIED_CANDIDATE_SHADOW_V2',
        'canonical_reference_revision': REVISION,
        'row_key': 'pair_key',
        'rows': joined,
        'native_executor_compatible': False,
        'production_cutover': False
    }

    shape = registry_shape(canonical)

    report = {
        'status': 'PASS_VERIFIED_CANDIDATE_SHADOW_NOT_NATIVE_CUTOVER',
        'staged_pairs': len(joined),
        'quoted_pairs': sum(
            r['observed_quote_in_521_window'] for r in joined
        ),
        'quoted_pair_keys': [
            r['pair_key'] for r in joined
            if r['observed_quote_in_521_window']
        ],
        'canonical_registry_shape': shape,
        'native_hydration_certified': False,
        'native_executor_compatible': False,
        'net_profitability_certified': False,
        'signing': False,
        'broadcast': False,
        'execution_authority': False,
        'production_registry_modified': False
    }

    return shadow, report

def run(max_age):
    sources = [SCANNER, STAGE, Q521, Q523, REGISTRY]

    for p in sources:
        if not p.is_file():
            raise Hold('MISSING_' + p.name)

    frozen = {str(p): sha(p) for p in sources}

    linkage = read(Q523)
    observed = read(Q521)
    staged = read(STAGE)
    canonical = read(REGISTRY)

    if linkage.get('status') not in (
        'HOLD_NO_QUOTED_PAIRS_IN_EXECUTOR_REGISTRY',
        'PASS_QUOTED_INVENTORY_LINKED'
    ):
        raise Hold('ORACLE523_LINEAGE_NOT_VERIFIED')

    if (
        linkage.get('scanner_sha256') != sha(SCANNER)
        or linkage.get('oracle_521_sha256') != sha(Q521)
        or linkage.get('registry_sha256') != sha(REGISTRY)
    ):
        raise Hold('ORACLE523_PROTECTED_HASH_DRIFT')

    if int(linkage.get('staged_pairs', -1)) != len(
        staged.get('rows') or []
    ):
        raise Hold('ORACLE523_STAGE_COUNT_CHANGED')

    age = time.time() - float(staged.get('generated_at', 0))

    if age < 0 or age > max_age:
        raise Hold('STAGED_INVENTORY_EXPIRED_REFRESH_REQUIRED')

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510
    )

    selected, total = q510.selected(q509.load(q510.CHECKS), 28)

    shadow, report = assemble(
        staged, observed, selected, canonical
    )

    if any(
        sha(Path(path)) != h for path, h in frozen.items()
    ):
        raise Hold('SOURCE_CHANGED_DURING_HANDOFF')

    report.update({
        'qualified_selected': len(selected),
        'qualified_registry_reported': total,
        'stage_age_seconds': round(age, 1),
        'canonical_registry_sha256': frozen[str(REGISTRY)],
        'scanner_sha256': frozen[str(SCANNER)],
        'candidate_registry_path': str(SHADOW)
    })

    write(SHADOW, shadow)
    report['candidate_registry_sha256'] = sha(SHADOW)
    write(REPORT, report)

    print(
        '[ORACLE524_FINAL]',
        json.dumps({
            k: v for k, v in report.items()
            if k not in ('quoted_pair_keys', 'canonical_registry_shape')
        }, sort_keys=True),
        flush=True
    )

    print(
        '[ORACLE524_REGISTRY_SCHEMA]',
        json.dumps(report['canonical_registry_shape'], sort_keys=True),
        flush=True
    )

    print(
        '[ORACLE524_QUOTED_PAIR_KEYS]',
        json.dumps(report['quoted_pair_keys']),
        flush=True
    )

    return 0

def tests():
    a, b, p, m = 'A'*32, 'B'*32, 'P'*32, 'M'*32

    stage = {
        'rows': [
            {'token': a, 'pump_pool': p},
            {'token': b, 'pump_pool': p}
        ]
    }

    observed = {
        'status': 'PASS_LIVE_QUOTE_COVERAGE_MEASURED',
        'visible_pairs': 2,
        'matched_quoted_pairs': 1,
        'pair_results': [
            {'token': a, 'result': 'MATCHED_QUOTE_OBSERVED'},
            {'token': b, 'result': 'NO_MATCHED_QUOTE_IN_WINDOW'}
        ]
    }

    selection = [
        {'token': a, 'pump_pool': p, 'meteora_pool': m},
        {'token': b, 'pump_pool': p, 'meteora_pool': 'N'*32}
    ]

    for key in ('rows', 'pairs', 'entries', 'pair_rows'):
        canonical = {
            'revision': REVISION,
            key: [{'token': 'X'*32}]
        }

        shadow, report = assemble(
            stage, observed, selection, canonical
        )

        assert len(shadow['rows']) == 2
        assert report['quoted_pairs'] == 1
        assert key in report['canonical_registry_shape']['containers']
        assert not shadow['native_executor_compatible']

    try:
        bad = [
            {'token': a, 'pump_pool': 'Q'*32, 'meteora_pool': m},
            selection[1]
        ]
        assemble(stage, observed, bad, canonical)
        raise AssertionError('BAD_POOL_ACCEPTED')
    except Hold:
        pass

    print(
        '[PASS] ORACLE524_V2 actual_registry_schema_independent '
        'exact_pool_join safe_shadow',
        flush=True
    )

def install():
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_MISSING')

    source = Path(__file__).read_text(encoding='utf-8')
    ast.parse(source)
    before = sha(SCANNER)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_name(
        TARGET.name + '.' + str(os.getpid()) + '.tmp'
    )

    try:
        tmp.write_text(source, encoding='utf-8')
        os.replace(tmp, TARGET)
    finally:
        tmp.unlink(missing_ok=True)

    if sha(SCANNER) != before:
        raise Hold('FROZEN_SCANNER_CHANGED')

    print(
        '[PASS] ORACLE524_V2_FULL_REPLACEMENT '
        'non_native_shadow frozen_scanner',
        flush=True
    )

def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)

    for opt in ('install', 'test', 'run'):
        group.add_argument('--' + opt, action='store_true')

    p.add_argument('--max-stage-age', type=int, default=14400)
    args = p.parse_args()

    try:
        if args.install:
            install()
            return 0

        if args.test:
            tests()
            return 0

        if not 300 <= args.max_stage_age <= 14400:
            raise Hold('INVALID_STAGE_AGE_LIMIT')

        return run(args.max_stage_age)

    except Exception as exc:
        print(
            '[ORACLE524_HOLD]',
            str(exc) if isinstance(exc, Hold)
            else type(exc).__name__,
            flush=True
        )
        return 2

if __name__ == '__main__':
    raise SystemExit(main())