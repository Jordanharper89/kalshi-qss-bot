"""ORACLE-236..240: measured gross economics and fail-closed money gate.
No keys, no network requests, no trading modules imported.
"""
import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
REGISTRY = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
SAFETY = ROOT / 'ORACLE235O_COMBINED_SAFETY.json'
QUOTES = ROOT / 'ORACLE235D_DLMM_FILL_TRUTH.json'
OUTPUT = ROOT / 'ORACLE240_MONEY_PATH_GATE.json'
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}
START = 10_000_000


def read_json(path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else None
    except (ValueError, UnicodeError):
        return None


def unique_mint(prefix, known):
    if not isinstance(prefix, str) or len(prefix) < 12:
        return None
    matches = [m for m in known if m == prefix or m.startswith(prefix)]
    return matches[0] if len(matches) == 1 else None


def measured_quote(row):
    if not isinstance(row, dict) or row.get('status') != 'PASS_UNDERLYING_FULL_FILL':
        return None, 'NO_CERTIFIED_FULL_FILL'
    if row.get('size_sol') != 0.010:
        return None, 'UNMEASURED_SIZE'
    calls = row.get('dlmm_calls')
    quotes = row.get('gross_quotes')
    if not isinstance(calls, list) or len(calls) != 2:
        return None, 'MISSING_TWO_DLMM_CALLS'
    if not isinstance(quotes, list) or len(quotes) != 2:
        return None, 'MISSING_TWO_DIRECTIONS'
    if any(c.get('full_fill') is not True or c.get('complete') is not True
           or type(c.get('remaining_in')) is not int or c['remaining_in'] != 0
           for c in calls if isinstance(c, dict)) or any(not isinstance(c, dict) for c in calls):
        return None, 'DLMM_FILL_NOT_PROVEN'
    if {q.get('direction') for q in quotes if isinstance(q, dict)} != DIRECTIONS:
        return None, 'DIRECTION_MISMATCH'
    if any(not isinstance(q, dict) or type(q.get('local_end')) is not int
           or type(q.get('local_net')) is not int
           or q['local_end'] <= 0 or q['local_net'] != q['local_end'] - START
           for q in quotes):
        return None, 'INVALID_GROSS_ACCOUNTING'
    measured = sorted(({'direction': q['direction'], 'gross_lamports': q['local_net'],
                        'end_lamports': q['local_end'],
                        'gross_bps': q['local_net'] * 10000 / START}
                       for q in quotes), key=lambda x: x['gross_lamports'], reverse=True)
    return measured, None


def evaluate(known, safety, quotes):
    if not isinstance(safety, dict) or safety.get('build') != 'ORACLE235O_V2' \
       or safety.get('execution_admission') is not False \
       or safety.get('signing') is not False or safety.get('broadcast') is not False:
        raise ValueError('HOLD_UNTRUSTED_SAFETY_REPORT')
    if not isinstance(quotes, dict) or quotes.get('build') != 'ORACLE235D' \
       or quotes.get('signing') is not False or quotes.get('broadcast') is not False:
        raise ValueError('HOLD_UNTRUSTED_QUOTE_REPORT')
    safety_by_mint, quotes_by_mint = {}, {}
    issues = []
    for r in safety.get('tokens', []):
        if not isinstance(r, dict):
            issues.append('BAD_SAFETY_ROW')
            continue
        m = unique_mint(r.get('mint'), known)
        if not m or m in safety_by_mint:
            issues.append('AMBIGUOUS_SAFETY_IDENTITY')
            continue
        safety_by_mint[m] = r
    for r in quotes.get('routes', []):
        if not isinstance(r, dict):
            issues.append('BAD_QUOTE_ROW')
            continue
        m = unique_mint(r.get('token_prefix'), known)
        if not m or m in quotes_by_mint:
            issues.append('AMBIGUOUS_QUOTE_IDENTITY')
            continue
        quotes_by_mint[m] = r
    records = []
    for mint in sorted(known):
        s = safety_by_mint.get(mint)
        q = quotes_by_mint.get(mint)
        directions, failure = measured_quote(q)
        historical = isinstance(s, dict) and s.get('historical_checks_pass') is True \
                     and s.get('reasons') == []
        best = directions[0] if directions else None
        record = {'mint': mint, 'mint_prefix': mint[:12],
                  'size_sol': 0.010, 'start_lamports': START,
                  'historical_safety_pass': historical,
                  'directions': directions or [], 'best_gross': best,
                  'fee_estimate_lamports': None, 'signed_simulation': False,
                  'same_context_full_state': False, 'mriya_proven': False,
                  'execution_admission': False, 'signing': False, 'broadcast': False}
        reasons = []
        if not historical:
            reasons.append('HISTORICAL_SAFETY_NOT_COMPLETE')
        if failure:
            reasons.append(failure)
        elif best['gross_lamports'] <= 0:
            reasons.append('NONPOSITIVE_GROSS')
        else:
            reasons.append('NETWORK_AND_PRIORITY_FEES_UNMEASURED')
        reasons.append('SAME_CONTEXT_QUOTE_LINEAGE_NOT_CERTIFIED')
        reasons.append('SIGNED_ATOMIC_SIMULATION_NOT_CERTIFIED')
        reasons.append('MRIYA_ATTRIBUTION_NOT_VERIFIED')
        record['reasons'] = reasons
        record['status'] = 'REJECT_NEGATIVE_GROSS' if best and best['gross_lamports'] <= 0 else 'HOLD'
        records.append(record)
    return records, sorted(set(issues))


def run(root=ROOT, registry=REGISTRY, output=OUTPUT):
    if not registry.is_file():
        raise RuntimeError('HOLD_MISSING_REGISTRY')
    with closing(sqlite3.connect(registry.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        known = {r[0] for r in db.execute('SELECT mint FROM universal_routes')}
    if not known:
        raise RuntimeError('HOLD_EMPTY_REGISTRY')
    records, issues = evaluate(known, read_json(root/'ORACLE235O_COMBINED_SAFETY.json'),
                               read_json(root/'ORACLE235D_DLMM_FILL_TRUTH.json'))
    counts = dict(Counter(r['status'] for r in records))
    result = {'build': 'ORACLE236_240', 'first_canary_sol': 0.010,
              'registered_mints': len(known), 'measured_bidirectional_mints': sum(bool(r['directions']) for r in records),
              'historical_safety_mints': sum(r['historical_safety_pass'] for r in records),
              'gross_positive_mints': sum(bool(r['best_gross']) and r['best_gross']['gross_lamports'] > 0 for r in records),
              'outcomes': counts, 'source_issues': issues,
              'fees_proven': False, 'same_context_full_state': False, 'mriya_proven': False,
              'execution_admission': False, 'signing': False, 'broadcast': False,
              'status': 'HOLD_NO_NET_PROFIT_CERTIFICATION', 'tokens': records}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE236_GROSS_MEASUREMENTS]', result['measured_bidirectional_mints'])
    print('[ORACLE237_FEE_GATE] HOLD_NO_VERIFIED_TRANSACTION_FEES')
    print('[ORACLE238_SIZE_GATE] 0.010_MEASURED other_sizes=UNMEASURED')
    print('[ORACLE239_HISTORICAL_SAFETY]', result['historical_safety_mints'])
    print('[ORACLE240_RESULT]', json.dumps({k:v for k,v in result.items() if k != 'tokens'}, sort_keys=True))
    for row in records:
        if row['best_gross']:
            print('[ORACLE240_TOKEN]', json.dumps({'token':row['mint_prefix'], 'best_gross':row['best_gross'],
                                                   'historical_safety_pass':row['historical_safety_pass'],
                                                   'status':row['status']}))
    print('[REPORT]', output)
    return result


def test():
    from tempfile import TemporaryDirectory
    m = 'A'*32
    q = [{'direction':d,'local_end':START - 42000, 'local_net':-42000} for d in sorted(DIRECTIONS)]
    good = {'token_prefix': 'A'*12, 'status': 'PASS_UNDERLYING_FULL_FILL', 'size_sol':0.010,
            'dlmm_calls':[{'full_fill':True,'complete':True,'remaining_in':0} for _ in range(2)], 'gross_quotes':q}
    assert measured_quote(good)[0][0]['gross_lamports'] == -42000
    bad = json.loads(json.dumps(good))
    bad['dlmm_calls'][0]['remaining_in'] = 1
    assert measured_quote(bad)[0] is None
    safety = {'build':'ORACLE235O_V2','execution_admission':False,'signing':False,'broadcast':False,
              'tokens':[{'mint':m, 'historical_checks_pass':True,'reasons':[]}]}
    quotes = {'build':'ORACLE235D','signing':False,'broadcast':False,'routes':[good]}
    rows, errors = evaluate({m}, safety, quotes)
    assert len(rows) == 1 and not errors and rows[0]['status'] == 'REJECT_NEGATIVE_GROSS'
    assert rows[0]['execution_admission'] is False
    with TemporaryDirectory() as td:
        root = Path(td)
        with closing(sqlite3.connect(root/'db.sqlite3')) as db:
            db.execute('CREATE TABLE universal_routes(mint TEXT)')
            db.execute('INSERT INTO universal_routes VALUES(?)',(m,))
            db.commit()
        (root/'ORACLE235O_COMBINED_SAFETY.json').write_text(json.dumps(safety))
        (root/'ORACLE235D_DLMM_FILL_TRUTH.json').write_text(json.dumps(quotes))
        r = run(root, root/'db.sqlite3', root/'report.json')
        assert r['execution_admission'] is False and r['gross_positive_mints'] == 0
    print('[ORACLE236_240_TEST_PASS] gross=TRUE partial_rejected=TRUE negative_rejected=TRUE fees_fail_closed=TRUE')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    if not (args.test or args.run):
        ap.error('use --test or --run')
    if args.test:
        test()
    if args.run:
        run()