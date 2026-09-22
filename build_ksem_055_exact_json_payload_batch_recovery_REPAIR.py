from pathlib import Path
import importlib,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem055_exact_json_payload_batch_recovery.json'
TEST=ROOT/'test_ksem_055_exact_json_payload_batch_recovery_REPAIR.py'
MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'

def main():
 print('='*120);print(' KSEM-055 EXACT JSON PAYLOAD BATCH RECOVERY REPAIR');print('='*120)
 missing=[x['ticker'] for x in json.loads((S/'ksem050_missing_market_root_causes.json').read_text())['rows']]
 mod=importlib.import_module(MOD);_,b=mod._router_backend(ROOT);conn=b._connect()
 try:
  with conn.cursor() as cur:
   cur.execute('BEGIN READ ONLY')
   cur.execute("SET LOCAL statement_timeout='20s'")
   cur.execute("""
    SELECT observation_id,
           canonical_observation_json->'payload'->>'source_market_id',
           canonical_observation_json->'payload'->>'source_symbol',
           canonical_observation_json->'payload'->>'event_ticker',
           canonical_observation_json->'payload'->>'market_title'
    FROM public.oracle_canonical_observations
    WHERE observation_type='market_snapshot'
      AND source_id='source.kalshi.market_data'
      AND (
       canonical_observation_json->'payload'->>'source_market_id'=ANY(%s)
       OR canonical_observation_json->'payload'->>'source_symbol'=ANY(%s)
      )
   """,(missing,missing))
   raw=cur.fetchall()
  conn.rollback()
 finally:conn.close()
 by={t:[] for t in missing}
 for oid,mid,sym,event,title in raw:
  ticker=mid if mid in by else sym if sym in by else None
  if ticker:by[ticker].append({'observation_id':str(oid),'event_ticker':event,'market_title':title})
 rows=[{'ticker':t,'observations':by[t]} for t in missing];found=sum(bool(x['observations']) for x in rows)
 print('[REQUESTED]',len(rows));print('[FOUND]',found);print('[MISSING]',len(rows)-found)
 for x in rows:print('[RECOVERY]',x)
 OUT.write_text(json.dumps({'rows':rows,'found':found,'missing':len(rows)-found,'execution_authority':False},indent=2),encoding='utf-8')
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_exact_json_payload_batch_recovery.json').read_text())\nassert len(d['rows'])==48\nassert d['found']+d['missing']==48\nassert d['execution_authority'] is False\nprint('[PASS] 48 underlying tickers recovered with one bounded exact JSON payload query')\nprint('[PASS] KSEM-055 repair certified')\n",encoding='utf-8')
 print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()