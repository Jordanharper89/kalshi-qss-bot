"""ORACLE-303 complete installer: local repository native PumpSwap quote discovery.
Read-only static AST: no module imports, RPC, signing, trading or code modification.
"""
import argparse
import ast
import json
import os
from pathlib import Path
from collections import Counter

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE303_PUMP_NATIVE_BINDING.json')
TERMS = ('pumpswap', 'pump_swap', 'pump_amm', 'pumpamm', 'pumpfun', 'pump_fun', 'pump_exact')
QUOTE = ('quote', 'sell', 'buy', 'pricing', 'price', 'swap', 'exact', 'sdk')
SKIP = {'venv', '.venv', '.git', '__pycache__', 'node_modules', 'site-packages', 'runtime_state'}
GRID = [round(0.010 + 0.005*i, 3) for i in range(19)]


def locate(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP and not d.startswith('.')]
        rel = Path(base).relative_to(root)
        if len(rel.parts) > 9:
            dirs.clear()
            continue
        for name in files:
            if name.endswith('.py') and not name.startswith('build_') and name != Path(__file__).name:
                path = Path(base) / name
                if path.stat().st_size <= 650_000:
                    yield path


def summarize(path, root):
    try:
        source = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError):
        return None
    declarations = []
    symbols = Counter()
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, 'module', '') or ''
            names = [a.name for a in node.names]
            terms = ' '.join([module] + names).lower()
            if any(t in terms for t in TERMS):
                imports.append({'line':node.lineno,'module':module,'names':names[:12]})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lower()
            calls = []
            for call in ast.walk(node):
                if isinstance(call, ast.Call):
                    target = ast.unparse(call.func)
                    if any(x in target.lower() for x in QUOTE + TERMS):
                        calls.append(target[:100]);symbols[target] += 1
            snippet = ast.get_source_segment(source, node) or ''
            has_pump = any(t in (name + snippet[:12000]).lower() for t in TERMS)
            is_quote = any(t in (name + ' '.join(calls)).lower() for t in QUOTE)
            if has_pump and is_quote:
                args = [x.arg for x in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
                declarations.append({'line':node.lineno,'function':node.name,
                  'args':args[:20], 'calls':sorted(set(calls))[:20],
                  'has_network_dependency':any(k in snippet.lower() for k in ('requests.', 'urllib.', 'httpx.', 'getaccountinfo','getmultipleaccounts')),
                  'code_size':len(snippet)})
    if not (imports or declarations or symbols):return None
    return {'file':str(path.relative_to(root)).replace('\\','/'),
        'imports':imports[:20],'functions':declarations[:60],
        'quote_calls':symbols.most_common(20)}


def rank(row):
    name=row['file'].lower()
    score=0
    if 'oracle_execution' in name:score+=12
    if 'sdk' in name or 'official' in name:score+=15
    if 'pumpswap' in name or 'pump_swap' in name:score+=15
    score+=min(30,len(row['functions'])*7)+min(15,len(row['imports'])*3)
    return score


def report(root):
    files=0;results=[]
    for path in locate(root):
        files+=1
        row=summarize(path,root)
        if row:row['score']=rank(row);results.append(row)
    results.sort(key=lambda r:(-r['score'],r['file']))
    return {'build':'ORACLE303','status':'NATIVE_PUMP_BINDING_CANDIDATES_DISCOVERED' if results else 'HOLD_NO_NATIVE_PUMP_EVIDENCE',
      'files_inspected':files,'matching_files':len(results),'functions_found':sum(len(r['functions']) for r in results),
      'candidates':results[:100],'size_grid':GRID,
      'pump_sdk_bound':False,'cross_venue_quoted':False,
      'quote_rpc_calls':0,'rpc_calls':0,'signing':False,'broadcast':False,'execution_admission':False,
      'scanner_modified':False}


def test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);target=root/'qseries_v2/oracle_execution/solana_atomic_executor/pump_helper.py'
        target.parent.mkdir(parents=True)
        target.write_text('from official_pumpswap_sdk import sell_quote\n'
          'def pump_exact_sell(pool, token_in, amount_raw):\n'
          '    return sell_quote(pool, token_in, amount_raw)\n',encoding='utf-8')
        (root/'bad.py').write_text('def broken(:\n',encoding='utf-8')
        r=report(root)
        assert r['matching_files']==1 and r['functions_found']==1
        assert 'sell_quote' in str(r['candidates'][0])
        assert r['quote_rpc_calls']==0 and not r['execution_admission']
        assert len(r['size_grid'])==19 and r['size_grid'][0]==0.01
    print('[ORACLE303_TEST_PASS] recursive_native_discovery=TRUE quote_calls=TRUE corrupt_hold=TRUE no_rpc=TRUE no_orders=TRUE')


def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    root=Path.cwd()
    if not (root/'qseries_v2').is_dir():raise RuntimeError('REPOSITORY_ROOT_REQUIRED')
    r=report(root)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE303_RESULT]',json.dumps({k:v for k,v in r.items() if k not in ('candidates','size_grid')},sort_keys=True))
    for row in r['candidates'][:18]:
        print('[ORACLE303_CANDIDATE]',json.dumps(row,sort_keys=True))
    print('[REPORT]',OUT)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.test:test()
    if a.run:run()
    if not (a.test or a.run):p.error('Specify --test or --run')
