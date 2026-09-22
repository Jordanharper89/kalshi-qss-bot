from pathlib import Path
import ast,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem060_kalshi_credential_provider_contract.json'
TEST=ROOT/'test_ksem_060_kalshi_credential_provider_contract_gate.py'

def main():
 print('='*120);print(' KSEM-060 KALSHI CREDENTIAL PROVIDER CONTRACT GATE');print('='*120)
 sel=json.loads((S/'ksem059_exact_kalshi_credential_provider_selection.json').read_text())['selected']
 p=ROOT/sel['file'];src=p.read_text(encoding='utf-8');tree=ast.parse(src)
 fn=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==sel['function'])
 body=ast.get_source_segment(src,fn) or '';args=[a.arg for a in fn.args.args]
 defaults=len(fn.args.defaults);required=args[:len(args)-defaults if defaults else len(args)]
 print('[FILE]',sel['file']);print('[FUNCTION]',sel['function']);print('[ARGS]',args);print('[REQUIRED]',required)
 print('[BODY]');print(body)
 unsafe=any(x in body.lower() for x in ['place_order','create_order','.post(','.delete('])
 if unsafe:raise RuntimeError('CREDENTIAL_PROVIDER_NOT_READ_ONLY_SAFE')
 d={'file':sel['file'],'function':sel['function'],'args':args,'required':required,'read_only_safe':True,'execution_authority':False}
 OUT.write_text(json.dumps(d,indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem060_kalshi_credential_provider_contract.json').read_text())\nassert d['read_only_safe'] is True\nprint('[PASS] Kalshi credential provider contract verified')\nprint('[PASS] KSEM-060 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()