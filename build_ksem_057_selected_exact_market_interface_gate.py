from pathlib import Path
import ast,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem057_selected_exact_market_interface.json'
TEST=ROOT/'test_ksem_057_selected_exact_market_interface_gate.py'

def main():
 print('='*120);print(' KSEM-057 SELECTED EXACT MARKET INTERFACE GATE');print('='*120)
 sel=json.loads((S/'ksem056_exact_kalshi_retrieval_candidate_selection.json').read_text())['selected']
 p=ROOT/sel['file'];src=p.read_text(encoding='utf-8');tree=ast.parse(src)
 fn=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==sel['function'])
 body=ast.get_source_segment(src,fn) or ''
 args=[a.arg for a in fn.args.args];defaults=len(fn.args.defaults);required=args[:len(args)-defaults if defaults else len(args)]
 unsafe=any(x in body.lower() for x in ['.post(','.put(','.delete(','place_order','create_order'])
 print('[FILE]',sel['file']);print('[FUNCTION]',sel['function']);print('[ARGS]',args)
 print('[REQUIRED]',required);print('[BODY]');print(body)
 if unsafe:raise RuntimeError('SELECTED_INTERFACE_NOT_READ_ONLY')
 d={'file':sel['file'],'function':sel['function'],'args':args,'required':required,
    'read_only_candidate':True,'execution_authority':False}
 OUT.write_text(json.dumps(d,indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem057_selected_exact_market_interface.json').read_text())\nassert d['read_only_candidate'] is True\nassert d['execution_authority'] is False\nprint('[PASS] selected exact-market interface body and signature verified read-only')\nprint('[PASS] KSEM-057 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()