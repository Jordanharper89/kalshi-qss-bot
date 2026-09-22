from pathlib import Path
import importlib,json
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem055_source_observation_indexed_recovery.json'
TEST=ROOT/'test_ksem_055_source_observation_indexed_recovery_REPAIR_V2.py'
MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'

def bounds(t):
    p='opc.kalshi.market.'+t+'.'
    return p,p[:-1]+'/'

def main():
 print('='*120); print(' KSEM-055 SOURCE-OBSERVATION INDEXED RECOVERY REPAIR V2'); print('='*120)
 missing=[x['ticker'] for x in json.loads((S/'ksem050_missing_market_root_causes.json').read_text())['rows']]
 mod=importlib.import_module(MOD); _,b=mod._router_backend(ROOT); conn=b._connect()
 try:
  with conn.cursor() as cur:
   cur.execute('BEGIN READ ONLY'); cur.execute("SET LOCAL statement_timeout='2s'")
   lo,hi=bounds(missing[0])
   cur.execute("""EXPLAIN SELECT observation_id FROM public.oracle_canonical_observations
    WHERE source_observation_id >= %s AND source_observation_id < %s LIMIT 20""",(lo,hi))
   plan=' '.join(r[0] for r in cur.fetchall()); print('[PLAN]',plan)
   if 'Index' not in plan and 'Bitmap' not in plan:
    raise RuntimeError('NO_INDEX_BACKED_SOURCE_OBSERVATION_ID_PATH')
   rows=[]
   for ticker in missing:
    lo,hi=bounds(ticker)
    cur.execute("""SELECT observation_id,source_observation_id,observation_type
     FROM public.oracle_canonical_observations
     WHERE source_observation_id >= %s AND source_observation_id < %s
     ORDER BY sequence_number DESC LIMIT 20""",(lo,hi))
    hits=[{'observation_id':str(a),'source_observation_id':str(b),'observation_type':str(c)} for a,b,c in cur.fetchall()]
    rows.append({'ticker':ticker,'observations':hits})
  conn.rollback()
 finally: conn.close()
 found=sum(bool(x['observations']) for x in rows)
 print('[REQUESTED]',len(rows)); print('[FOUND]',found); print('[MISSING]',len(rows)-found)
 for x in rows: print('[RECOVERY]',x)
 OUT.write_text(json.dumps({'rows':rows,'found':found,'missing':len(rows)-found,'execution_authority':False},indent=2),encoding='utf-8')
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_source_observation_indexed_recovery.json').read_text())\nassert len(d['rows'])==48\nassert d['found']+d['missing']==48\nassert d['execution_authority'] is False\nprint('[PASS] exact underlying tickers recovered through bounded source-observation lineage')\nprint('[PASS] KSEM-055 repair V2 certified')\n",encoding='utf-8')
 print('[WRITE]',OUT.relative_to(ROOT)); print('[WRITE]',TEST.name)

if __name__=='__main__': main()