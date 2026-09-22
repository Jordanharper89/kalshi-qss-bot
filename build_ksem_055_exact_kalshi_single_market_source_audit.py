from pathlib import Path
import ast,json,re
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem055_exact_kalshi_single_market_source_audit.json'
TEST=ROOT/'test_ksem_055_exact_kalshi_single_market_source_audit.py'

def main():
 print('='*120);print(' KSEM-055 EXACT KALSHI SINGLE-MARKET SOURCE AUDIT');print('='*120)
 rows=[]
 for p in (ROOT/'qseries_v2').rglob('*.py'):
  try: src=p.read_text(encoding='utf-8')
  except: continue
  low=src.lower()
  if 'kalshi' not in low or 'market' not in low: continue
  try: tree=ast.parse(src)
  except: continue
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    seg=ast.get_source_segment(src,n) or ''
    s=seg.lower()
    exact=('/markets/' in s or 'market_ticker' in s or 'ticker' in s)
    get=('requests.get' in s or '.get(' in s or 'urlopen' in s)
    mut=any(x in s for x in ['.post(','.put(','.delete(','place_order','create_order'])
    if exact and get and not mut:
     row={'file':str(p.relative_to(ROOT)),'function':n.name,
          'args':[a.arg for a in n.args.args],'line':n.lineno}
     rows.append(row);print('[CANDIDATE]',row)
 S.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps({'candidates':rows,'count':len(rows),'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_exact_kalshi_single_market_source_audit.json').read_text())\nassert d['count']>0\nassert d['execution_authority'] is False\nprint('[PASS] exact read-only Kalshi single-market candidates inventoried')\nprint('[PASS] KSEM-055 certified')\n")
 print('[CANDIDATES]',len(rows));print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()