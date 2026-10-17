from __future__ import annotations
import argparse, ast, hashlib, json, os
from pathlib import Path
BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_523_scanner_executor_handoff.py'
SCANNER = BASE / 'boss_scanner_live.py'
CP25 = BASE / 'checkpoint25_expanded_live_universe_cutover.py'
Q521 = Path('runtime_state/oracle/oracle_live_execution/oracle_521/quote_coverage.json')
OUT = Path('runtime_state/oracle/oracle_live_execution/oracle_523/inventory_handoff.json')
B58 = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')

class Hold(RuntimeError): pass

def pubkey(value):
    return isinstance(value, str) and 32 <= len(value) <= 44 and set(value) <= B58

def read(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict): raise Hold('JSON_ROOT_NOT_OBJECT')
    return data

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(tmp, path)
    finally: tmp.unlink(missing_ok=True)

def tokens(data):
    found = set()
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('token','token_mint','tokenMint','baseMint','base_mint','mint') and pubkey(child):
                    found.add(child)
                if key in ('pair_key','pairKey') and isinstance(child, str):
                    part = child.split('|', 1)[0]
                    if pubkey(part): found.add(part)
                if isinstance(key, str) and '|' in key:
                    part = key.split('|', 1)[0]
                    if pubkey(part): found.add(part)
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(data)
    return found

def roots():
    choices = []
    for root in (Path('runtime_state'), BASE):
        if root.exists():
            choices.extend(x for x in root.rglob('multi_dlmm_pair_registry.json') if x.is_file())
    return sorted(set(choices), key=lambda x: str(x))
def join(scanner_result, executor_result):
    if scanner_result.get('status') != 'PASS_LIVE_QUOTE_COVERAGE_MEASURED':
        raise Hold('ORACLE521_LIVE_PASS_REQUIRED')
    rows = scanner_result.get('pair_results')
    if not isinstance(rows, list) or not rows: raise Hold('ORACLE521_PAIR_RESULTS_MISSING')
    staged = set(); quoted = set()
    for row in rows:
        if not isinstance(row, dict) or not pubkey(row.get('token')): raise Hold('BAD_521_TOKEN')
        token = row['token']
        if token in staged: raise Hold('DUPLICATE_521_TOKEN')
        staged.add(token)
        if row.get('result') == 'MATCHED_QUOTE_OBSERVED': quoted.add(token)
        elif row.get('result') != 'NO_MATCHED_QUOTE_IN_WINDOW': raise Hold('UNKNOWN_521_RESULT')
    if len(quoted) != scanner_result.get('matched_quoted_pairs'):
        raise Hold('521_QUOTE_COUNTER_MISMATCH')
    available = tokens(executor_result)
    if not available: raise Hold('EXECUTOR_REGISTRY_SCHEMA_UNRESOLVED')
    overlap = staged & available
    matched = quoted & available
    return {'staged_pairs':len(staged),'observed_quote_pairs':len(quoted),
            'executor_distinct_token_mints':len(available),
            'staged_in_executor':len(overlap),'quoted_in_executor':len(matched),
            'quoted_not_in_executor':sorted(quoted - available),
            'staged_not_in_executor':sorted(staged - available),
            'quoted_in_executor_tokens':sorted(matched),
            'inventories_have_observed_quote_overlap':bool(matched),
            'not_a_live_profitability_test':True,'not_a_ws_subscription_certification':True,
            'signing':False,'broadcast':False,'execution_authority':False}

def run():
    if not Q521.is_file() or not CP25.is_file() or not SCANNER.is_file():
        raise Hold('521_OR_25_OR_FROZEN_SCANNER_MISSING')
    found = roots()
    if len(found) != 1:
        print('[ORACLE523_REGISTRY_PATHS]',json.dumps([str(x) for x in found]),flush=True)
        raise Hold('EXECUTOR_REGISTRY_PATH_NOT_UNIQUE')
    original = sha(SCANNER)
    stage = read(Q521)
    registry = read(found[0])
    report = join(stage, registry)
    report.update({'registry_path':str(found[0]),'scanner_sha256':original,
                   'registry_sha256':sha(found[0]),'oracle_521_sha256':sha(Q521)})
    report['status'] = ('PASS_QUOTED_INVENTORY_LINKED' if report['quoted_in_executor']
                        else 'HOLD_NO_QUOTED_PAIRS_IN_EXECUTOR_REGISTRY')
    if sha(SCANNER) != original: raise Hold('FROZEN_SCANNER_CHANGED')
    save(OUT, report)
    print('[ORACLE523_FINAL]',json.dumps({k:v for k,v in report.items()
         if k not in ('quoted_not_in_executor','staged_not_in_executor','quoted_in_executor_tokens')},sort_keys=True),flush=True)
    print('[ORACLE523_MISSING_QUOTED]',json.dumps(report['quoted_not_in_executor']),flush=True)
    print('[ORACLE523_REPORT]',OUT,flush=True)
    return 0 if report['status'].startswith('PASS_') else 2

def tests():
    a,b,c=('A'*32,'B'*32,'C'*32)
    sample={'status':'PASS_LIVE_QUOTE_COVERAGE_MEASURED','matched_quoted_pairs':2,
            'pair_results':[{'token':a,'result':'MATCHED_QUOTE_OBSERVED'},
                            {'token':b,'result':'MATCHED_QUOTE_OBSERVED'},
                            {'token':c,'result':'NO_MATCHED_QUOTE_IN_WINDOW'}]}
    result=join(sample,{'revision':'CHECKPOINT11_MULTI_POOL_REGISTRY_V1',
                        'pairs':{b+'|'+c:{'pair_key':b+'|'+c},c+'|'+a:{'token':c}}})
    assert result['staged_in_executor']==2 and result['quoted_in_executor']==1
    assert result['quoted_not_in_executor']==[a]
    try: join(sample,{'pairs':[]}); raise AssertionError('unresolved bypass')
    except Hold: pass
    try: join({**sample,'matched_quoted_pairs':3},{'pairs':[{'token':a}]}); raise AssertionError('bad counter bypass')
    except Hold: pass
    print('[PASS] ORACLE523 exact_token_join quote_counter_consistency fail_closed no_network no_mutation',flush=True)

def install():
    if not SCANNER.is_file() or not CP25.is_file(): raise Hold('LOCAL_REPO_REQUIRED')
    src=Path(__file__).read_text(encoding='utf-8'); ast.parse(src)
    frozen=sha(SCANNER)
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    tmp=TARGET.with_name(TARGET.name+'.'+str(os.getpid())+'.tmp')
    try:
        tmp.write_text(src,encoding='utf-8'); os.replace(tmp,TARGET)
    finally: tmp.unlink(missing_ok=True)
    if sha(SCANNER)!=frozen: raise Hold('SCANNER_CHANGED')
    print('[PASS] ORACLE523_FULL_INSTALL frozen_scanner no_signing no_broadcast',flush=True)

def main():
    p=argparse.ArgumentParser(); modes=p.add_mutually_exclusive_group(required=True)
    for name in ('install','test','run'): modes.add_argument('--'+name,action='store_true')
    a=p.parse_args()
    try:
        if a.install: install(); return 0
        if a.test: tests(); return 0
        return run()
    except Exception as exc:
        print('[ORACLE523_HOLD]',str(exc) if isinstance(exc,Hold) else type(exc).__name__,flush=True)
        return 2

if __name__=='__main__': raise SystemExit(main())