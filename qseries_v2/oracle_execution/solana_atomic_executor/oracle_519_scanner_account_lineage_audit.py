from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_519_scanner_account_lineage_audit.py'
SCANNER = BASE / 'boss_scanner_live.py'
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
R517 = Path('runtime_state/oracle/oracle_live_execution/oracle_517/capacity_trial.json')
R518 = Path('runtime_state/oracle/oracle_live_execution/oracle_518/ws_lineage_report.json')
REPORT = Path('runtime_state/oracle/oracle_live_execution/oracle_519/scanner_account_lineage.json')
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
KEY_HINT = ('pool','vault','reserve','account','bin_array','bitmap','oracle','mint','dlmm','meteora','pump','token')
BLOCKED = ('secret','private','signer','payer','password','api_key','authorization')
WATCH_HINT = ('watch','subscribe','listen','websocket','stream','slot','vault','meteora','dlmm','account','quote','select_rows')

class Hold(RuntimeError):
    pass


def read(path):
    path = Path(path)
    if not path.is_file():
        raise Hold('MISSING_' + path.name)
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        raise Hold('INVALID_OBJECT_' + path.name)
    return obj


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def safe_key(name):
    s = str(name).lower()
    return bool(any(k in s for k in KEY_HINT) and not any(k in s for k in BLOCKED))


def account_shape(rows):
    fields = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key, val in row.items():
            if not safe_key(key):
                continue
            stat = fields.setdefault(str(key), {'present':0,'address_like':0,'value_types':set()})
            stat['present'] += 1
            stat['value_types'].add(type(val).__name__)
            stat['address_like'] += int(isinstance(val, str) and bool(B58.fullmatch(val)))
    return {k: {'present':v['present'], 'address_like':v['address_like'],
                'value_types':sorted(v['value_types'])} for k,v in sorted(fields.items())}


def static_scanner_lineage(source):
    tree = ast.parse(source)
    funcs, method_counts = [], {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if any(h in name.lower() for h in WATCH_HINT):
                funcs.append(name)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in ('accountSubscribe','programSubscribe','logsSubscribe',
                              'slotSubscribe','accountNotification','programNotification'):
                method_counts[node.value] = method_counts.get(node.value, 0) + 1
    return {'scanner_functions_of_interest':sorted(set(funcs))[:80],
            'literal_ws_rpc_methods':method_counts,
            'function_count':sum(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))
                                 for x in ast.walk(tree))}


def qualified_shape():
    # This calls only the existing registry load/selection functions; never warms,
    # opens a socket, places an order, or changes source data.
    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_509_exact_pair_qualification as q509,
            oracle_510_warm_pair_preflight as q510)
        if not Path(q510.CHECKS).is_file():
            return {'status':'HOLD_QUALIFIED_CHECKS_MISSING'}
        chosen, count = q510.selected(q509.load(q510.CHECKS), 28)
        if not isinstance(chosen, list):
            return {'status':'HOLD_SELECTED_ROWS_NOT_LIST'}
        return {'status':'PASS_REGISTRY_INSPECTED', 'selected_rows':len(chosen),
                'verified_registry_reported':count,
                'account_fields':account_shape(chosen),
                'row_key_sets':[sorted(str(k) for k in r if safe_key(k))
                                for r in chosen[:3] if isinstance(r,dict)]}
    except Exception as exc:
        return {'status':'HOLD_REGISTRY_INTERFACE_' + type(exc).__name__}


def analyze(stage, r517, r518, shape, qualified, current_stage_hash):
    rows = stage.get('rows')
    if not isinstance(rows,list) or not 1 <= len(rows) <= 28:
        raise Hold('STAGE_NOT_BOUNDED')
    if r517.get('status') != 'PASS_BOUNDED_28_SLOT_COMPACTION_TRIAL':
        raise Hold('ORACLE517_PASS_REQUIRED')
    if r518.get('status') != 'PASS_INDEPENDENT_WS_ACK_AND_SLOT_FEED':
        raise Hold('ORACLE518_PASS_REQUIRED')
    tokens = [r.get('token') for r in rows if isinstance(r,dict)]
    if len(tokens) != len(rows) or len(tokens) != len(set(tokens)):
        raise Hold('INVALID_STAGE_TOKENS')
    p518 = r518.get('pairs')
    if not isinstance(p518,list):
        raise Hold('ORACLE518_PAIR_EVIDENCE_MISSING')
    evidence = {p.get('token'):p for p in p518 if isinstance(p,dict)}
    same_snapshot = current_stage_hash == r518.get('stage_sha256')
    matched = sum(token in evidence for token in tokens)
    acked = sum(evidence.get(t,{}).get('ack') is True for t in tokens)
    notified = sum(int(evidence.get(t,{}).get('notifications') or 0)>0 for t in tokens)
    # Acknowledgments and notifications were measured in a different window
    # than the scanner quote trial; do not fabricate per-token causation.
    return {
        'status':('PASS_READ_ONLY_SCANNER_LINEAGE_AUDIT'
                  if qualified.get('status') == 'PASS_REGISTRY_INSPECTED'
                  else 'HOLD_QUALIFIED_METADATA_INTERFACE_UNRESOLVED'),
        'stage_pairs':len(rows), 'stage_equals_518_snapshot':same_snapshot,
        'cross_window_evidence_pairs':matched, 'cross_window_acked':acked,
        'cross_window_account_notified':notified,
        'stage_account_fields':account_shape(rows),
        'qualified_metadata':qualified, 'scanner_static':shape,
        'last_517_distinct_quotes':r517.get('max_observed_distinct_quotes'),
        'last_517_stage_occupancy':r517.get('max_staged'),
        'independent_probe_only':True,
        'same_time_scanner_subscription_proven':False,
        'full_vault_and_meteora_watch_map_proven':False,
        'production_28_pair_certified':False,
        'scanner_modified':False, 'signing':False,'broadcast':False,
        'execution_authority':False,'fixed_first_trade_size':False,
    }


def audit():
    for p in (SCANNER,STAGE,R517,R518):
        if not p.is_file():
            raise Hold('REQUIRED_EVIDENCE_MISSING_' + p.name)
    before = sha(SCANNER)
    current_stage_hash = sha(STAGE)
    shape = static_scanner_lineage(SCANNER.read_text(encoding='utf-8'))
    result = analyze(read(STAGE),read(R517),read(R518),shape,
                     qualified_shape(),current_stage_hash)
    if sha(SCANNER) != before or sha(STAGE) != current_stage_hash:
        raise Hold('PROTECTED_INPUT_CHANGED_DURING_AUDIT')
    result['scanner_sha256'] = before
    result['stage_sha256'] = current_stage_hash
    write(REPORT,result)
    print('[ORACLE519_FINAL]',json.dumps(result,sort_keys=True),flush=True)
    return 0 if result['status'].startswith('PASS_') else 2


def tests():
    source = 'def watch_accounts():\n    op = "accountSubscribe"\n    return op\n'
    s = static_scanner_lineage(source)
    assert s['literal_ws_rpc_methods']['accountSubscribe'] == 1
    assert 'watch_accounts' in s['scanner_functions_of_interest']
    assert account_shape([{'pump_pool':'P'*32,'secret_key':'s'*32}])['pump_pool']['address_like']==1
    assert 'secret_key' not in account_shape([{'secret_key':'s'*32}])
    rows = [{'token':'T'*32,'pump_pool':'P'*32}]
    h = 'z'*64
    r517 = {'status':'PASS_BOUNDED_28_SLOT_COMPACTION_TRIAL', 'max_observed_distinct_quotes':7}
    r518 = {'status':'PASS_INDEPENDENT_WS_ACK_AND_SLOT_FEED', 'stage_sha256':h,
            'pairs':[{'token':'T'*32,'ack':True,'notifications':3}]}
    out = analyze({'rows':rows},r517,r518,s,{'status':'PASS_REGISTRY_INSPECTED'},h)
    assert out['stage_equals_518_snapshot'] and out['cross_window_account_notified']==1
    assert not out['same_time_scanner_subscription_proven']
    r518['stage_sha256'] = 'other'
    assert not analyze({'rows':rows},r517,r518,s,{'status':'PASS_REGISTRY_INSPECTED'},h)['stage_equals_518_snapshot']
    print('[PASS] ORACLE519 source_AST registry_field_lineage stage_to_518_matching '
          'cross_window_guard no_scanner_mutation no_signing',flush=True)


def install():
    if not BASE.is_dir() or not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_REPO_REQUIRED')
    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    temp = TARGET.with_name(TARGET.name+'.'+str(os.getpid())+'.tmp')
    try:
        temp.write_text(src,encoding='utf-8')
        os.replace(temp,TARGET)
    finally:
        temp.unlink(missing_ok=True)
    print('[PASS] ORACLE519_FULL_INSTALL scanner_unmodified read_only_no_network',flush=True)
    print('[INSTALLED]',TARGET,flush=True)


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    for name in ('--install','--test','--audit','--status'):
        g.add_argument(name,action='store_true')
    a=ap.parse_args()
    try:
        if a.install:
            install(); return 0
        if a.test:
            tests(); return 0
        if a.status:
            print('[ORACLE519_STATUS]',json.dumps(read(REPORT),sort_keys=True),flush=True)
            return 0
        return audit()
    except Hold as exc:
        print('[ORACLE519_HOLD]',str(exc),flush=True)
        return 2
    except Exception as exc:
        print('[ORACLE519_HOLD]',type(exc).__name__,flush=True)
        return 2


if __name__=='__main__':
    sys.exit(main())
