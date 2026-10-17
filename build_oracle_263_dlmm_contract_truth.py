"""ORACLE-263: offline DLMM accounting and exact source-contract evidence."""
import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path('runtime_state/oracle/oracle_live_execution')
RAW = BASE / 'ORACLE258_ROTATION_RAW.json'
SRC = Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py')
SAMPLER = Path('build_oracle_241_live_opportunity_sampler.py')
OUT = BASE / 'ORACLE263_DLMM_CONTRACT_TRUTH.json'
TERMS = ('remaining_in', 'complete', 'DLMM_PARTIAL', 'dlmm_quote_snapshot', 'exact_snapshot_opportunities')


def source_evidence(path, limit=38):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    lines = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if n.name not in ('exact_snapshot_opportunities', 'run', 'dlmm_quote_snapshot'):
            continue
        selected = []
        for node in ast.walk(n):
            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.If, ast.Raise, ast.Return, ast.Call)):
                continue
            expression = ast.unparse(node)
            if any(t in expression for t in TERMS):
                if isinstance(node, ast.Call):
                    expression = 'CALL ' + ast.unparse(node.func)
                elif isinstance(node, ast.Raise):
                    expression = 'RAISE ' + (ast.unparse(node.exc.func) if isinstance(node.exc, ast.Call) else type(node.exc).__name__)
                elif isinstance(node, ast.If):
                    expression = 'IF ' + ast.unparse(node.test)
                else:
                    expression = expression.splitlines()[0]
                selected.append({'line': node.lineno, 'kind': type(node).__name__, 'expression': expression[:180]})
        lines.append({'file': str(path), 'function': n.name, 'matches': sorted(selected, key=lambda x:x['line'])[:limit]})
    return lines


def audit(data):
    if data.get('build') != 'ORACLE241' or any(data.get(x) is not False for x in ('signing','broadcast','execution_admission')):
        raise ValueError('UNTRUSTED_INPUT')
    if not isinstance(data.get('observations'), list):
        raise ValueError('MISSING_OBSERVATIONS')
    stats = defaultdict(Counter)
    examples = []
    for r in data['observations']:
        if not isinstance(r, dict) or r.get('exception_code') != 'DLMM_PARTIAL':
            continue
        mint = r.get('mint')
        size = r.get('size_sol')
        if not isinstance(mint, str) or type(size) not in (float,int) or size <= 0:
            continue
        requested = round(size * 1_000_000_000)
        for call in r.get('dlmm_calls', []):
            if not isinstance(call, dict):
                continue
            rem = call.get('remaining_in')
            if type(rem) is not int or rem < 0:
                continue
            complete = call.get('complete')
            label = ('ZERO' if rem == 0 else 'MATCHES_SOL_LAMPORTS' if rem == requested else 'OTHER_POSITIVE')
            stats[mint[:12]][label] += 1
            stats[mint[:12]]['calls'] += 1
            if complete is True:
                stats[mint[:12]]['complete_true_' + label] += 1
            if len(examples) < 12 and (label == 'OTHER_POSITIVE' or complete is True):
                examples.append({'token':mint[:12], 'size_sol':size, 'remaining_in':rem,
                                 'sol_lamports_reference':requested, 'complete':complete,'bucket':label})
    return {'build':'ORACLE263','source_observations':len(data['observations']),
            'token_call_buckets':{k:dict(v) for k,v in sorted(stats.items())},
            'examples':examples,'source_contract':[],
            'units_certified':False,'complete_means_full_fill_certified':False,
            'net_profit_certified':False,'execution_admission':False,'signing':False,'broadcast':False,
            'status':'HOLD_DLMM_ACCOUNTING_SEMANTICS'}


def test():
    d={'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,
       'observations':[{'mint':'A'*32,'size_sol':.01,'exception_code':'DLMM_PARTIAL',
       'dlmm_calls':[{'remaining_in':10000000,'complete':True}, {'remaining_in':42,'complete':False}]}]}
    r=audit(d)['token_call_buckets']['A'*12]
    assert r['MATCHES_SOL_LAMPORTS']==1 and r['OTHER_POSITIVE']==1
    assert r['complete_true_MATCHES_SOL_LAMPORTS']==1
    d['signing']=True
    try:audit(d)
    except ValueError:pass
    else:raise AssertionError('UNSAFE_SOURCE')
    print('[ORACLE263_TEST_PASS] remaining_buckets=TRUE contradictory_complete=TRUE disarmed=TRUE')


def run():
    if not RAW.is_file() or not SRC.is_file() or not SAMPLER.is_file():
        raise RuntimeError('REQUIRED_SOURCE_MISSING')
    output=audit(json.loads(RAW.read_text(encoding='utf-8')))
    output['source_contract']=source_evidence(SRC)+source_evidence(SAMPLER)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print('[ORACLE263_RESULT]',json.dumps({k:v for k,v in output.items() if k not in ('source_contract','examples')},sort_keys=True))
    for record in output['source_contract']:
        print('[ORACLE263_SOURCE]',json.dumps(record,sort_keys=True))
    for example in output['examples'][:6]:
        print('[ORACLE263_EXAMPLE]',json.dumps(example,sort_keys=True))
    print('[REPORT]',OUT)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('specify --test or --run')
    if a.test:test()
    if a.run:run()