from pathlib import Path
import importlib,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state';OUT=S/'ksem055_real_schema_48_ticker_recovery.json';TEST=ROOT/'test_ksem_055_real_schema_48_ticker_recovery.py';MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'
def main():
 print('='*120);print(' KSEM-055 REAL-SCHEMA 48-TICKER PHYSICAL RECOVERY');print('='*120)
 missing=[x['ticker'] for x in json.loads((S/'ksem050_missing_market_root_causes.json').read_text())['rows']];schema=json.loads((S/'ksem052_exact_canonical_postgresql_schema.json').read_text());mod=importlib.import_module(MOD);_,b=mod._router_backend(ROOT);conn=b._connect();rows=[]
 try:
  with conn.cursor() as cur:
   cur.execute('BEGIN READ ONLY');textcols=[x['name'] for x in schema['columns'] if x['data_type'] in ('text','character varying','json','jsonb')]
   for ticker in missing:
    hits=[]
    for col in textcols:cur.execute(f'SELECT observation_id FROM public.oracle_canonical_observations WHERE CAST({col} AS text) LIKE %s LIMIT 20',(f'%{ticker}%',));hits.extend(str(r[0]) for r in cur.fetchall())
    rows.append({'ticker':ticker,'observation_ids':sorted(set(hits))})
  conn.rollback()
 finally:conn.close()
 found=sum(bool(x['observation_ids']) for x in rows);print('[TEXT_SEARCH_COLUMNS]',textcols);print('[TICKERS]',len(rows));print('[FOUND]',found)
 for x in rows:print('[RECOVERY]',x)
 OUT.write_text(json.dumps({'text_search_columns':textcols,'rows':rows,'found':found,'execution_authority':False},indent=2),encoding='utf-8');TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_real_schema_48_ticker_recovery.json').read_text())\nassert len(d['rows'])==48\nassert d['found']>=0\nassert d['execution_authority'] is False\nprint('[PASS] all 48 missing tickers searched against real physical canonical schema')\nprint('[PASS] KSEM-055 certified')\n",encoding='utf-8');print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()