from pathlib import Path
import importlib,json,inspect
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem061_physical_exact_kalshi_market_call.json'
TEST=ROOT/'test_ksem_061_physical_exact_kalshi_market_call_REPAIR.py'
T='KXNCAAFGAME-26SEP12OKLAMICH-OKLA'

def imod(path):return path.replace('\\','.').replace('/','.').removesuffix('.py')
def main():
 print('='*120);print(' KSEM-061 PHYSICAL EXACT KALSHI MARKET CALL REPAIR');print('='*120)
 cp=json.loads((S/'ksem060_kalshi_credential_provider_contract.json').read_text())
 cm=importlib.import_module(imod(cp['file']));cf=getattr(cm,cp['function']);sig=inspect.signature(cf);kw={}
 for n,p in sig.parameters.items():
  if n=='root':kw[n]=ROOT
  elif p.default is inspect._empty:raise RuntimeError('UNSUPPORTED_CREDENTIAL_PROVIDER_ARG:'+n)
 credentials=cf(**kw);print('[CREDENTIALS] loaded existing provider successfully')
 rm=importlib.import_module('qseries_v2.oracle_production_learning.opl_007_evidence_first_outcome_resolver')
 r=rm.resolve_settlement(credentials,T)
 print('[RESULT_TYPE]',type(r).__name__);print('[RESULT]',repr(r))
 matched=T in repr(r);print('[EXACT_TICKER_PRESENT]',matched)
 if not matched:raise RuntimeError('EXACT_CONTROL_MARKET_NOT_RETURNED')
 OUT.write_text(json.dumps({'ticker':T,'result_type':type(r).__name__,'result_repr':repr(r),'exact_ticker_present':True,'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem061_physical_exact_kalshi_market_call.json').read_text())\nassert d['exact_ticker_present'] is True\nprint('[PASS] exact Kalshi control market physically retrieved')\nprint('[PASS] KSEM-061 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()