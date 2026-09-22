from pathlib import Path
import importlib,json,inspect
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem058_physical_exact_kalshi_market_call.json'
TEST=ROOT/'test_ksem_058_physical_exact_kalshi_market_call_gate.py'
T='KXNCAAFGAME-26SEP12OKLAMICH-OKLA'

def main():
 print('='*120);print(' KSEM-058 PHYSICAL EXACT KALSHI MARKET CALL GATE');print('='*120)
 d=json.loads((S/'ksem057_selected_exact_market_interface.json').read_text())
 mod=d['file'].replace('\\','.').replace('/','.').removesuffix('.py')
 fn=getattr(importlib.import_module(mod),d['function']);sig=inspect.signature(fn);kw={}
 for n,p in sig.parameters.items():
  if n in ('ticker','market_ticker'):kw[n]=T
  elif n=='root':kw[n]=ROOT
  elif n in ('timeout','timeout_seconds'):kw[n]=10
  elif p.default is inspect._empty:raise RuntimeError('UNSUPPORTED_REQUIRED_ARGUMENT:'+n)
 print('[CALL]',mod,d['function'],kw)
 r=fn(**kw);print('[RESULT_TYPE]',type(r).__name__);print('[RESULT]',repr(r))
 text=repr(r);matched=T in text
 print('[EXACT_TICKER_PRESENT]',matched)
 if not matched:raise RuntimeError('PHYSICAL_RESULT_DID_NOT_CONTAIN_CONTROL_TICKER')
 OUT.write_text(json.dumps({'ticker':T,'result_type':type(r).__name__,
  'result_repr':text,'exact_ticker_present':matched,'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem058_physical_exact_kalshi_market_call.json').read_text())\nassert d['exact_ticker_present'] is True\nprint('[PASS] selected existing Kalshi interface physically returned exact control market')\nprint('[PASS] KSEM-058 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()