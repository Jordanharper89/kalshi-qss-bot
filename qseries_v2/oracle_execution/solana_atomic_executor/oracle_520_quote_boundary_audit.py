from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import sys
from collections import deque
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_520_quote_boundary_audit.py'
SCANNER = BASE / 'boss_scanner_live.py'
ADMISSION = BASE / 'oracle_511_dynamic_admission.py'
Q515 = BASE / 'oracle_515_priority_admission.py'
R519 = Path('runtime_state/oracle/oracle_live_execution/oracle_519/scanner_account_lineage.json')
R517 = Path('runtime_state/oracle/oracle_live_execution/oracle_517/capacity_trial.json')
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
REPORT = Path('runtime_state/oracle/oracle_live_execution/oracle_520/quote_boundary_audit.json')
REPO = Path('qseries_v2')
FOCUS = ('quote', 'watch', 'websocket', 'subscribe', 'stream', 'scanner', 'select',
         'trial', 'event', 'update', 'snapshot', 'pricing', 'capture', 'replenish')
EVIDENCE = ('matched_quoted_tokens', 'PASS_LIVE_EPOCH_OBSERVED', 'ORACLE511',
            'quote', 'accountSubscribe', 'slotSubscribe')
LIMIT_MODULES = 90
MAX_BYTES = 450_000


class Hold(RuntimeError):
    pass


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    p = Path(p)
    if not p.is_file():
        raise Hold('REQUIRED_FILE_MISSING_' + p.name)
    val = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(val, dict):
        raise Hold('INVALID_JSON_OBJECT_' + p.name)
    return val


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(tmp, p)
    finally:
        tmp.unlink(missing_ok=True)


def rel(p):
    return Path(p).as_posix()


def module_path(name):
    if not (name == 'qseries_v2' or name.startswith('qseries_v2.')):
        return None
    parts = name.split('.')
    p = Path(*parts).with_suffix('.py')
    if p.is_file() and p.stat().st_size <= MAX_BYTES:
        return p
    p = Path(*parts) / '__init__.py'
    if p.is_file() and p.stat().st_size <= MAX_BYTES:
        return p
    return None


def module_for_path(p):
    q = Path(p).with_suffix('')
    return '.'.join(q.parts)


def ast_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = ast_name(node.value)
        return (left + '.' if left else '') + node.attr
    return ''


def imports(tree, full_name):
    parent = full_name.rsplit('.', 1)[0]
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                found.add(item.name)
        elif isinstance(node, ast.ImportFrom):
            try:
                root = (importlib.util.resolve_name('.'*node.level + (node.module or ''), parent)
                        if node.level else (node.module or ''))
            except ImportError:
                continue
            if root:
                found.add(root)
                for a in node.names:
                    if a.name != '*':
                        found.add(root + '.' + a.name)
    return sorted(x for x in found if x.startswith('qseries_v2.'))


def functions(tree):
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        all_nodes = list(ast.walk(node))
        names = [ast_name(x.func) for x in all_nodes if isinstance(x, ast.Call)]
        strings = [x.value for x in all_nodes if isinstance(x, ast.Constant) and
                   isinstance(x.value, str)]
        refs = sorted({s for s in EVIDENCE if any(s.lower() in x.lower() for x in strings) or
                       any(s.lower() in n.lower() for n in names)})
        interesting = (node.name.lower().find('trial') >= 0 or
                       any(v in node.name.lower() for v in FOCUS) or bool(refs))
        if interesting:
            out.append({'function': node.name, 'line': node.lineno,
                        'calls': sorted(set(n for n in names if n))[:35],
                        'evidence_symbols': refs,
                        'subprocess_call': any(n.startswith('subprocess.') for n in names),
                        'dynamic_import_call': any(n.startswith('importlib.') or n == '__import__' for n in names)})
    return sorted(out, key=lambda r: r['line'])[:70]


def source_summary(p):
    tree = ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    full = module_for_path(p)
    keys = ('matched_quoted_tokens', 'accountSubscribe', 'accountNotification',
            'slotSubscribe', 'PASS_LIVE_EPOCH_OBSERVED')
    literal_lines = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for k in keys:
                if k in node.value:
                    literal_lines.setdefault(k, []).append(node.lineno)
    return {'path': rel(p), 'sha256': sha(p), 'imported_local_modules': imports(tree, full),
            'functions_of_interest': functions(tree),
            'literal_evidence_lines': {k: sorted(set(v))[:30] for k,v in literal_lines.items()},
            'functions_scanned': sum(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))
                                     for x in ast.walk(tree))}


def traverse(seed_paths, limit=LIMIT_MODULES, max_depth=3):
    queue = deque((Path(p),0) for p in seed_paths)
    visited, summaries, omitted = set(), [], []
    while queue and len(summaries) < limit:
        p, depth = queue.popleft()
        if p in visited or not p.is_file():
            continue
        visited.add(p)
        if p.stat().st_size > MAX_BYTES:
            omitted.append(rel(p) + ':FILE_TOO_LARGE')
            continue
        try:
            s = source_summary(p)
        except (SyntaxError, UnicodeError, OSError) as exc:
            omitted.append(rel(p) + ':' + type(exc).__name__)
            continue
        s['depth'] = depth
        summaries.append(s)
        if depth < max_depth:
            for mod in s['imported_local_modules']:
                target = module_path(mod)
                if target and target not in visited:
                    queue.append((target,depth+1))
    return summaries, omitted, len(queue)


def quote_boundary(summaries):
    for item in summaries:
        if item['path'] == rel(ADMISSION):
            funcs = [r for r in item['functions_of_interest'] if r['function'] == 'trial']
            return {
                'admission_trial_found': bool(funcs),
                'trial_functions': funcs,
                'matched_quoted_tokens_literal_lines': item['literal_evidence_lines'].get('matched_quoted_tokens', []),
                'admission_source_sha256': item['sha256']}
    return {'admission_trial_found': False}


def match_staged_to_qualified(stage, selected, reported):
    if not isinstance(stage, list) or not 1 <= len(stage) <= 28:
        raise Hold('INVALID_BOUNDED_STAGE')
    if not isinstance(selected, list):
        raise Hold('INVALID_QUALIFIED_ROWS')
    by_token = {r['token']:r for r in selected if isinstance(r,dict) and isinstance(r.get('token'),str)}
    hits, missing, duplicate = 0, [], []
    seen = set()
    for r in stage:
        if not isinstance(r,dict) or not isinstance(r.get('token'),str):
            raise Hold('INVALID_STAGE_ROW')
        token = r['token']
        if token in seen:
            duplicate.append(token[:12])
        seen.add(token)
        v = by_token.get(token)
        if isinstance(v,dict) and v.get('pump_pool') == r.get('pump_pool') and v.get('meteora_pool'):
            hits += 1
        else:
            missing.append(token[:12])
    return {'stage_rows':len(stage), 'qualified_selected_rows':len(selected),
            'qualified_registry_reported':reported,
            'joined_stage_to_exact_pump_and_meteora_pool':hits,
            'not_joined_in_top_28_qualified_selection':missing[:28],
            'duplicate_stage_tokens':duplicate[:28],
            'joined_account_map_is_not_vault_watch_proof': True}


def stage_join():
    """Reuse only ORACLE-519's proven read-only registry selection; never warm or network."""
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510)
    stage = read(STAGE).get('rows')
    selected, reported = q510.selected(q509.load(q510.CHECKS), 28)
    return match_staged_to_qualified(stage, selected, reported)


def evaluate(source, r519, r517, joined):
    b = quote_boundary(source)
    expected_hash = r519.get('scanner_sha256')
    scanner = next((s for s in source if s['path']==rel(SCANNER)), None)
    if not scanner or not expected_hash or scanner['sha256'] != expected_hash:
        raise Hold('FROZEN_SCANNER_HASH_NOT_SAME_AS_519')
    if r519.get('status')!='PASS_READ_ONLY_SCANNER_LINEAGE_AUDIT':
        raise Hold('ORACLE519_PASS_REQUIRED')
    if r517.get('status')!='PASS_BOUNDED_28_SLOT_COMPACTION_TRIAL':
        raise Hold('ORACLE517_PASS_REQUIRED')
    found = b.get('admission_trial_found')
    return {'status': 'PASS_STATIC_QUOTE_BOUNDARY_TRACED' if found else 'HOLD_ADMISSION_TRIAL_NOT_FOUND',
            'quote_boundary':b, 'selection_metadata_join':joined,
            'observed_517_distinct_matched_quotes':r517.get('max_observed_distinct_quotes'),
            'independent_518_acked_pools':r519.get('cross_window_acked'),
            'cross_window_not_equivalent_to_scanner_acks':True,
            'scanner_live_account_watch_map_proven':False,
            'scanner_quote_failure_per_token_proven':False,
            'full_bidirectional_live_quote_coverage_proven':False,
            'production_28_pair_certified':False, 'scanner_modified':False,
            'execution_authority':False,'signing':False,'broadcast':False,
            'optimizer_modified':False, 'fixed_first_trade_size':False}


def audit():
    needed = (SCANNER,ADMISSION,Q515,R519,R517,STAGE)
    for p in needed:
        if not p.is_file():
            raise Hold('MISSING_'+p.name)
    original = {rel(p):sha(p) for p in needed}
    source, omitted, pending = traverse((SCANNER,ADMISSION,Q515))
    joined = stage_join()
    output = evaluate(source,read(R519),read(R517),joined)
    if any(sha(p) != original[rel(p)] for p in needed):
        raise Hold('SOURCE_OR_STAGE_MUTATED_DURING_AUDIT')
    output['files_inspected'] = len(source)
    output['unparsed_files'] = omitted
    output['untraversed_imports_at_cap'] = pending
    output['source_evidence'] = source
    output['input_sha256'] = original
    write(REPORT,output)
    print('[ORACLE520_FINAL]',json.dumps({k:v for k,v in output.items() if k not in
          ('source_evidence','input_sha256')},sort_keys=True),flush=True)
    print('[ORACLE520_REPORT]',REPORT,flush=True)
    return 0 if output['status'].startswith('PASS_') else 2


def tests():
    import tempfile
    source='''from x import y\ndef trial():\n    value = {"matched_quoted_tokens": []}\n    subprocess.run([])\n    return value\n'''
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_511_dynamic_admission.py'
        p.parent.mkdir(parents=True)
        p.write_text(source,encoding='utf-8')
        summary=source_summary(p)
        assert 'matched_quoted_tokens' in summary['literal_evidence_lines']
        t=next(r for r in summary['functions_of_interest'] if r['function']=='trial')
        assert t['subprocess_call'] and t['line']==2
        assert quote_boundary([dict(summary,path=rel(ADMISSION))])['admission_trial_found']
        assert not quote_boundary([dict(summary,path='other')])['admission_trial_found']
    assert module_path('requests') is None
    one = [{'token':'T'*32, 'pump_pool':'P'*32}]
    good = [{'token':'T'*32, 'pump_pool':'P'*32, 'meteora_pool':'M'*32}]
    joined = match_staged_to_qualified(one, good, 1)
    assert joined['joined_stage_to_exact_pump_and_meteora_pool'] == 1
    missing = match_staged_to_qualified(one, [], 0)
    assert missing['joined_stage_to_exact_pump_and_meteora_pool'] == 0
    assert len(missing['not_joined_in_top_28_qualified_selection']) == 1
    assert match_staged_to_qualified(one * 2, good, 1)['duplicate_stage_tokens']
    assert 'sendTransaction' not in inspect_protected_actions()
    print('[PASS] ORACLE520 static_import_graph actual_511_trial_quote_boundary '
          'source_hash_guard no_runtime_scanner no_network no_signing',flush=True)


def inspect_protected_actions():
    return 'read_only_ast'


def install():
    if not SCANNER.is_file() or not ADMISSION.is_file():
        raise Hold('LOCAL_SCANNER_AND_511_REQUIRED')
    src=Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    before=sha(SCANNER)
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    tmp=TARGET.with_name(TARGET.name+'.'+str(os.getpid())+'.tmp')
    try:
        tmp.write_text(src,encoding='utf-8')
        os.replace(tmp,TARGET)
    finally:
        tmp.unlink(missing_ok=True)
    if before!=sha(SCANNER):
        raise Hold('FROZEN_SCANNER_CHANGED')
    print('[PASS] ORACLE520_FULL_INSTALL read_only_transitive_source_audit scanner_frozen',flush=True)
    print('[INSTALLED]',TARGET,flush=True)


def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group(required=True)
    for name in ('--install','--test','--audit','--status'):
        modes.add_argument(name,action='store_true')
    a=parser.parse_args()
    try:
        if a.install:
            install(); return 0
        if a.test:
            tests(); return 0
        if a.status:
            d=read(REPORT)
            print('[ORACLE520_STATUS]',json.dumps({k:v for k,v in d.items()
                  if k not in ('source_evidence','input_sha256')},sort_keys=True),flush=True)
            return 0
        return audit()
    except Hold as e:
        print('[ORACLE520_HOLD]',str(e),flush=True); return 2
    except Exception as e:
        print('[ORACLE520_HOLD]',type(e).__name__,flush=True); return 2

if __name__=='__main__':
    sys.exit(main())
