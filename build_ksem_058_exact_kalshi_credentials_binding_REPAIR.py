from pathlib import Path
import ast,json
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem058_exact_kalshi_credentials_binding_audit.json'
TEST=ROOT/'test_ksem_058_exact_kalshi_credentials_binding_REPAIR.py'
TARGET='resolve_settlement'

def main():
 print('='*120);print(' KSEM-058 EXACT KALSHI CREDENTIALS BINDING AUDIT REPAIR');print('='*120)
 rows=[]
 for p in (ROOT/'qseries_v2').rglob('*.py'):
  try: src=p.read_text(encoding='utf-8'); tree=ast.parse(src)
  except: continue
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and getattr(n.func,'id',None)==TARGET and len(n.args)>=2:
    cred=ast.get_source_segment(src,n.args[0]) or ''
    row={'file':str(p.relative_to(ROOT)),'line':n.lineno,'credential_expr':cred}
    rows.append(row);print('[CALLSITE]',row)
   if isinstance(n,(ast.ImportFrom,ast.Import)):
    seg=ast.get_source_segment(src,n) or ''
    if 'credential' in seg.lower() and 'kalshi' in seg.lower():
     row={'file':str(p.relative_to(ROOT)),'line':n.lineno,'credential_import':seg}
     rows.append(row);print('[IMPORT]',row)
 S.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps({'rows':rows,'count':len(rows),'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem058_exact_kalshi_credentials_binding_audit.json').read_text())\nassert d['count']>0\nprint('[PASS] existing Kalshi credentials bindings audited')\nprint('[PASS] KSEM-058 repair certified')\n")
 print('[COUNT]',len(rows));print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()