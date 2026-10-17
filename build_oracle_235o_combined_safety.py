"""ORACLE-235O V2: strict historical evidence join; no execution."""
import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
DB = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
OUT = ROOT / 'ORACLE235O_COMBINED_SAFETY.json'
SOURCES = {
    'mint': ('ORACLE235K_RAW_TOKEN_EXTENSIONS.json', 'tokens',
             ('mint',), {'PASS_MINT_STRUCTURE_ONLY', 'PASS_METADATA_ONLY_MINT'}),
    'liquidity': ('ORACLE235I_BIN_ARRAY_RECONSTRUCTION.json', 'pairs',
                  ('token_prefix', 'token'), {'PASS_BIN_LIQUIDITY_MATCH'}),
    'pump_vault': ('ORACLE235M_VERIFIED_VAULTS.json', 'pairs',
                   ('token_prefix', 'token'), {'PASS_POOL_VAULT_ACCOUNT_FIELDS'}),
    'meteora_vault': ('ORACLE235N_METEORA_VAULT_SECURITY.json', 'pairs',
                      ('token_prefix', 'token'), {'PASS_PDA_AND_POOL_REFERENCE_FIELDS'}),
    'quote': ('ORACLE235D_DLMM_FILL_TRUTH.json', 'routes',
              ('token_prefix', 'token'), {'PASS_UNDERLYING_FULL_FILL'}),
}

def identity(row, fields, known):
    values = [row[k] for k in fields if isinstance(row.get(k), str) and row[k]]
    if not values:
        return None
    candidates = []
    for value in values:
        if len(value) < 12:
            return None
        matching = [mint for mint in known if mint == value or mint.startswith(value)]
        if len(matching) != 1:
            return None
        candidates.append(matching[0])
    return candidates[0] if len(set(candidates)) == 1 else None

def evaluate(known, reports):
    ledger = {mint: {'mint': mint, 'checks': {}, 'reasons': []} for mint in known}
    issues = []
    for category, (_, table, fields, pass_codes) in SOURCES.items():
        data = reports.get(category)
        if not isinstance(data, dict):
            issues.append(category + ':MISSING_REPORT')
            continue
        rows = data.get(table)
        if not isinstance(rows, list):
            issues.append(category + ':INVALID_ROWS')
            continue
        if data.get('signing') is not False or data.get('broadcast') is not False:
            issues.append(category + ':EXECUTION_FLAGS_NOT_FALSE')
            continue
        grouped = {}
        for row in rows:
            if not isinstance(row, dict):
                issues.append(category + ':INVALID_ROW')
                continue
            mint = identity(row, fields, known)
            if mint is None:
                issues.append(category + ':UNRESOLVED_IDENTITY')
                continue
            grouped.setdefault(mint, []).append(row)
        for mint, matches in grouped.items():
            if len(matches) != 1:
                issues.append(category + ':DUPLICATE_IDENTITY')
                ledger[mint]['reasons'].append(category + ':DUPLICATE_EVIDENCE')
                continue
            status = matches[0].get('status')
            ledger[mint]['checks'][category] = status
            if status not in pass_codes:
                ledger[mint]['reasons'].append(category + ':' + str(status))
        if not grouped:
            issues.append(category + ':ZERO_MATCHES')
    for item in ledger.values():
        for category in SOURCES:
            if category not in item['checks']:
                item['reasons'].append(category + ':NO_EVIDENCE')
        item['historical_checks_pass'] = not item['reasons']
        item['same_slot_state_proven'] = False
        item['mriya_proven'] = False
        item['fee_adjusted_profit_proven'] = False
        item['execution_admitted'] = False
    return ledger, sorted(set(issues))

def run(root=ROOT, db=DB, output=OUT):
    if not db.is_file():
        raise RuntimeError('HOLD_REGISTRY_MISSING')
    with closing(sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True)) as con:
        known = {r[0] for r in con.execute('SELECT mint FROM universal_routes')}
    if not known:
        raise RuntimeError('HOLD_NO_REGISTERED_ROUTES')
    reports, source_slots, errors = {}, {}, []
    for category, (filename, _, _, _) in SOURCES.items():
        file = root / filename
        if not file.is_file():
            reports[category] = None
            errors.append(category + ':MISSING_FILE')
            continue
        try:
            data = json.loads(file.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            data = None
            errors.append(category + ':INVALID_JSON')
        reports[category] = data
        if isinstance(data, dict):
            source_slots[category] = data.get('context_slot')
    ledger, issues = evaluate(known, reports)
    counts = dict(Counter('HISTORICAL_CHECKS_PASS' if x['historical_checks_pass']
                          else 'HOLD' for x in ledger.values()))
    result = {'build': 'ORACLE235O_V2', 'registered_mints': len(known),
              'historical_outcomes': counts, 'source_issues': sorted(set(errors + issues)),
              'source_slots': source_slots, 'historical_pass_not_trade_safety': True,
              'same_slot_state_proven': False, 'mriya_proven': False,
              'fee_adjusted_profit_proven': False, 'execution_admission': False,
              'signing': False, 'broadcast': False,
              'status': 'HOLD_SYNCHRONIZED_QUOTE_AND_MRIYA',
              'tokens': [ledger[m] for m in sorted(ledger)]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE235O_V2_RESULT]', json.dumps({k: v for k, v in result.items()
                                               if k != 'tokens'}, sort_keys=True))
    for item in result['tokens']:
        print('[ORACLE235O_V2_TOKEN]', json.dumps({'mint_prefix': item['mint'][:12],
             'historical_checks_pass': item['historical_checks_pass'],
             'reasons': item['reasons']}, sort_keys=True))
    print('[REPORT]', output)
    return result

def test():
    from tempfile import TemporaryDirectory
    known = {'A'*32, 'B'*32}
    reports = {}
    for category, (_, table, fields, accepted) in SOURCES.items():
        reports[category] = {'signing': False, 'broadcast': False,
                              table: [{fields[0]: 'A'*32 if category == 'mint' else 'A'*12,
                                       'status': sorted(accepted)[0]}]}
    ledger, errors = evaluate(known, reports)
    assert ledger['A'*32]['historical_checks_pass']
    assert not ledger['B'*32]['historical_checks_pass']
    assert not ledger['A'*32]['execution_admitted']
    reports['liquidity']['pairs'][0]['status'] = 'HOLD_BIN_LIQUIDITY_DRIFT'
    assert not evaluate(known, reports)[0]['A'*32]['historical_checks_pass']
    reports['liquidity']['pairs'][0]['status'] = 'PASS_BIN_LIQUIDITY_MATCH'
    reports['pump_vault']['pairs'].append(dict(reports['pump_vault']['pairs'][0]))
    assert not evaluate(known, reports)[0]['A'*32]['historical_checks_pass']
    reports['pump_vault']['pairs'].pop()
    reports['mint']['broadcast'] = True
    assert not evaluate(known, reports)[0]['A'*32]['historical_checks_pass']
    with TemporaryDirectory() as td:
        base = Path(td)
        with closing(sqlite3.connect(base/'test.sqlite3')) as con:
            con.execute('CREATE TABLE universal_routes(mint TEXT)')
            con.executemany('INSERT INTO universal_routes VALUES(?)', [(v,) for v in sorted(known)])
            con.commit()
        for category, (filename, _, _, _) in SOURCES.items():
            reports[category]['broadcast'] = False
            (base/filename).write_text(json.dumps(reports[category]), encoding='utf-8')
        result = run(base, base/'test.sqlite3', base/'out.json')
        assert result['execution_admission'] is False
        assert result['historical_outcomes']['HISTORICAL_CHECKS_PASS'] == 1
    print('[ORACLE235O_V2_TEST_PASS] real_report_fields=TRUE unique_prefix=TRUE '
          'duplicate_rejected=TRUE drift_rejected=TRUE execution=FALSE')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.test: test()
    if args.run: run()
