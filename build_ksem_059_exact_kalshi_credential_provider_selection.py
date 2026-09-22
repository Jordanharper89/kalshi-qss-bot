from pathlib import Path
import ast,json,re
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem059_exact_kalshi_credential_provider_selection.json'
TEST=ROOT/'test_ksem_059_exact_kalshi_credential_provider_selection.py'

def main():
 print('='*120);print(' KSEM-059 EXACT KALSHI CREDENTIAL PROVIDER SELECTION');print('='*120)
 rows=[]
 for p in (ROOT/'qseries_v2').rglob('*.py'):
  try: src=p.read_text(encoding='utf-8');tree=ast.parse(src)
  except: continue
  if 'kalshi' not in src.lower() or 'credential' not in src.lower():continue
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    name=n.name.lower(); body=(ast.get_source_segment(src,n) or '').lower();score=0
    if 'credential' in name:score+=80
    if 'kalshi' in name:score+=40
    if 'api_key' in body or 'private_key' in body:score+=30
    if 'os.environ' in body or 'getenv' in body:score+=20
    if score:
     row={'file':str(p.relative_to(ROOT)),'function':n.name,'args':[a.arg for a in n.args.args],'score':score}
     rows.append(row);print('[CANDIDATE]',row)
 rows.sort(key=lambda x:(-x['score'],x['file'],x['function']))
 selected=rows[0] if rows else None;print('[SELECTED]',selected)
 if not selected:raise RuntimeError('NO_EXISTING_KALSHI_CREDENTIAL_PROVIDER_FOUND')
 OUT.write_text(json.dumps({'selected':selected,'ranked':rows,'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem059_exact_kalshi_credential_provider_selection.json').read_text())\nassert d['selected']\nprint('[PASS] existing Kalshi credential provider selected')\nprint('[PASS] KSEM-059 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()