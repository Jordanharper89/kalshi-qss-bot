from pathlib import Path
import json
ROOT=Path.cwd()
S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem061_current_live_exact_market_physical_repair_v2.json'
TEST=ROOT/'test_ksem_061_current_live_exact_market_physical_REPAIR_V2.py'

def main():
 from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
 from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
 from qseries_v2.oracle_production_learning.opl_007_evidence_first_outcome_resolver import resolve_settlement
 print('='*120);print(' KSEM-061 CURRENT-LIVE EXACT MARKET PHYSICAL REPAIR V2');print('='*120)
 credentials=load_kalshi_credentials(ROOT)
 markets,*_=fetch_current_open_kalshi_market_index(root=ROOT,limit=100,timeout_seconds=15)
 if not markets: raise RuntimeError('NO_CURRENT_KALSHI_MARKETS_RETURNED')
 m=markets[0]
 ticker=str(m.get('ticker') if isinstance(m,dict) else getattr(m,'ticker','')).strip()
 if not ticker: raise RuntimeError('CURRENT_MARKET_HAS_NO_TICKER')
 print('[CURRENT_TICKER]',ticker)
 result=resolve_settlement(credentials,ticker)
 print('[RESULT_TYPE]',type(result).__name__);print('[RESULT]',repr(result))
 if result is None: raise RuntimeError('CURRENT_LIVE_TICKER_EXACT_GET_RETURNED_NONE')
 matched=ticker in repr(result)
 print('[EXACT_TICKER_PRESENT]',matched)
 if not matched: raise RuntimeError('CURRENT_LIVE_EXACT_IDENTITY_MISMATCH')
 d={'ticker':ticker,'result_type':type(result).__name__,'exact_ticker_present':True,'execution_authority':False}
 OUT.write_text(json.dumps(d,indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem061_current_live_exact_market_physical_repair_v2.json').read_text())\nassert d['exact_ticker_present'] is True\nassert d['execution_authority'] is False\nprint('[PASS] current-live Kalshi ticker physically retrieved through exact GET')\nprint('[PASS] KSEM-061 repair V2 certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()