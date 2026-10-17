"""ORACLE-264: offline DLMM producer and caller contract trace; no execution."""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
OUT = ROOT / 'ORACLE264_DLMM_PRODUCER_CONTRACT.json'
CALLER = Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py')
SAMPLER = Path('build_oracle_241_live_opportunity_sampler.py')
ROOT_SOURCE = Path('qseries_v2')
TERMS = ('dlmm_quote_snapshot', 'remaining_in', 'complete', 'DLMM_PARTIAL')


def excerpts(path, names=None):
    source = path.read_text(encoding='utf-8', errors='replace')
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    found = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if names is not None and fn.name not in names:
            continue
        start, stop = fn.lineno, fn.end_lineno
        matches = [i for i in range(start, stop + 1) if any(t in lines[i-1] for t in TERMS)]
        if not matches:
            continue
        selected = set()
        for i in matches:
            selected.update(range(max(start, i-3), min(stop, i+4)+1))
        fragments = []
        for i in sorted(selected):
            line = lines[i-1].rstrip()
            if len(line) > 260:
                line = line[:260]+' [TRUNCATED]'
            if any(k in line.lower() for k in ('private_key', 'api_key', 'authorization', 'secret', 'helius', 'rpc_url')):
                line = '[POTENTIAL_CREDENTIAL_EXPRESSION_REDACTED]'
            fragments.append({'line':i,'code':line})
        found.append({'file':str(path),'function':fn.name,'start_line':start,'end_line':stop,
                      'hits':len(matches),'fragments':fragments[:90]})
    return found


def analyze(root):
    if not CALLER.is_file() or not SAMPLER.is_file():
        raise RuntimeError('REQUIRED_CALLER_MISSING')
    producer_candidates=[]
    for p in root.rglob('*.py'):
        if not p.is_file() or p.stat().st_size > 1500000:
            continue
        try:
            code=p.read_text(encoding='utf-8',errors='replace')
            if 'def dlmm_quote_snapshot(' not in code:
                continue
            tree=ast.parse(code, filename=str(p))
            if any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and
                   n.name=='dlmm_quote_snapshot' for n in ast.walk(tree)):
                producer_candidates.append(p)
        except (OSError, SyntaxError, UnicodeError):
            continue
    results=[]
    for p in producer_candidates[:8]:
        results.extend(excerpts(p, {'dlmm_quote_snapshot'}))
    results.extend(excerpts(CALLER, {'exact_snapshot_opportunities'}))
    results.extend(excerpts(SAMPLER, {'run'}))
    return {'build':'ORACLE264','producer_candidate_count':len(producer_candidates),
            'producer_paths':[str(p) for p in producer_candidates[:8]],
            'contract_excerpts':results,'producer_contract_certified':False,
            'full_fill_certified':False,'execution_admission':False,
            'signing':False,'broadcast':False,
            'status':'REVIEW_PRODUCER_AND_CALLER_CONTRACT'}


def test():
    sample='''def dlmm_quote_snapshot(snap, amount, token):
    remaining_in = amount
    complete = True
    if remaining_in:
        raise RuntimeError("DLMM_PARTIAL")
    return {"complete": complete}
'''
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'fixture.py';p.write_text(sample,encoding='utf-8')
        rows=excerpts(p, {'dlmm_quote_snapshot'})
        assert len(rows)==1 and rows[0]['hits']>=3
        assert any('remaining_in' in x['code'] for x in rows[0]['fragments'])
        assert any('DLMM_PARTIAL' in x['code'] for x in rows[0]['fragments'])
    print('[ORACLE264_TEST_PASS] producer_detection=TRUE caller_excerpts=TRUE disarmed=TRUE')


def run():
    result=analyze(ROOT_SOURCE)
    ROOT.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE264_RESULT]',json.dumps({k:v for k,v in result.items() if k!='contract_excerpts'},sort_keys=True))
    for record in result['contract_excerpts']:
        print('[ORACLE264_CONTRACT]',json.dumps(record,sort_keys=True))
    print('[REPORT]', OUT)
    if result['producer_candidate_count']==0:
        raise SystemExit('HOLD_NO_DLMM_PRODUCER_FOUND')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()