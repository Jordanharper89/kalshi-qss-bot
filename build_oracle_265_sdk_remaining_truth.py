"""ORACLE-265: inspect exact installed Meteora SDK quote semantics, offline."""
import argparse
import ast
import inspect
import json
import textwrap
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE265_SDK_REMAINING_TRUTH.json')
TERMS = ('remaining_in', 'complete', 'strict', 'amount_in', 'bins_crossed', 'liquidity', 'swap_for_y')


def excerpt(fn):
    try:
        src = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(src)
        lines = src.splitlines()
        hits = [i for i, line in enumerate(lines) if any(term in line.lower() for term in TERMS)]
        selected = sorted({j for i in hits for j in range(max(0, i-2), min(len(lines), i+3))})
        body = []
        for i in selected[:85]:
            line = lines[i].strip()[:190]
            if any(w in line.lower() for w in ('api_key', 'private_key', 'authorization', 'secret')):
                line = '[REDACTED]'
            body.append({'offset': i+1, 'text': line})
        calls = sorted({n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)})
        return {'available': True, 'hits':len(hits), 'lines':body, 'calls':calls[:45]}
    except (OSError, TypeError, SyntaxError, IndentationError) as exc:
        return {'available':False, 'reason':type(exc).__name__}


def inspect_sdk(module):
    quote = getattr(module, 'quote', None)
    if not callable(quote):
        raise RuntimeError('SDK_QUOTE_NOT_CALLABLE')
    primary = excerpt(quote)
    helpers = []
    for name in primary.get('calls', []):
        fn = getattr(quote, '__globals__', {}).get(name)
        if not inspect.isfunction(fn) or getattr(fn, '__module__', '') != getattr(quote, '__module__', ''):
            continue
        evidence = excerpt(fn)
        if evidence.get('hits', 0):
            helpers.append({'name':name, 'evidence':evidence})
        if len(helpers) >= 5:
            break
    try:
        signature = str(inspect.signature(quote))[:400]
    except (TypeError, ValueError):
        signature = 'UNAVAILABLE'
    return {'sdk_module':str(getattr(quote,'__module__','UNKNOWN')),
            'sdk_file_name':Path(inspect.getfile(quote)).name,
            'signature':signature, 'quote':primary, 'helpers':helpers,
            'remaining_semantics_certified':False, 'liquidity_cause_certified':False,
            'execution_admission':False, 'signing':False, 'broadcast':False,
            'status':'REVIEW_SDK_REMAINING_SEMANTICS'}


def test():
    def example(state, amount_in, strict=True):
        remaining_in = amount_in
        complete = strict
        return {'remaining_in': remaining_in, 'complete': complete}
    detail = excerpt(example)
    assert detail['available'] and detail['hits'] >= 2
    assert any('remaining_in' in r['text'] for r in detail['lines'])
    print('[ORACLE265_TEST_PASS] source_extract=TRUE no_rpc=TRUE no_execution=TRUE')


def run():
    import meteora_dlmm
    result = inspect_sdk(meteora_dlmm)
    result['build'] = 'ORACLE265'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE265_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('quote','helpers')},sort_keys=True))
    print('[ORACLE265_QUOTE]',json.dumps(result['quote'],sort_keys=True))
    for helper in result['helpers']:
        print('[ORACLE265_HELPER]',json.dumps(helper,sort_keys=True))
    print('[REPORT]',OUT)
    if not result['quote'].get('available'):
        raise SystemExit('HOLD_SDK_SOURCE_UNAVAILABLE')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    args=p.parse_args()
    if not (args.test or args.run):p.error('Specify --test or --run')
    if args.test:test()
    if args.run:run()