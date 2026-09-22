from pathlib import Path
import ast,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem056_exact_kalshi_retrieval_candidate_selection.json'
TEST=ROOT/'test_ksem_056_exact_kalshi_retrieval_candidate_selection.py'

def main():
 print('='*120);print(' KSEM-056 EXACT KALSHI RETRIEVAL CANDIDATE SELECTION');print('='*120)
 rows=json.loads((S/'ksem055_exact_kalshi_single_market_source_audit.json').read_text())['candidates']; scored=[]
 for r in rows:
  p=ROOT/r['file'];src=p.read_text(encoding='utf-8');tree=ast.parse(src)
  fn=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==r['function'])
  body=ast.get_source_segment(src,fn) or '';low=body.lower();score=0
  if '/markets/' in low:score+=100
  if 'market_ticker' in low:score+=40
  if 'ticker' in r['args']:score+=30
  if 'market_ticker' in r['args']:score+=30
  if 'requests.get' in low or 'urlopen' in low:score+=20
  x={**r,'score':score};scored.append(x);print('[SCORED]',x)
 scored.sort(key=lambda x:(-x['score'],x['file'],x['function']))
 selected=scored[0] if scored and scored[0]['score']>=100 else None
 print('[SELECTED]',selected)
 OUT.write_text(json.dumps({'selected':selected,'ranked':scored,'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem056_exact_kalshi_retrieval_candidate_selection.json').read_text())\nassert d['selected'] is not None\nassert d['selected']['score']>=100\nprint('[PASS] exact single-market retrieval candidate selected from source')\nprint('[PASS] KSEM-056 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()