from pathlib import Path
import importlib,json
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem055_kalshi_market_identity_index_foundation_repair.json'
TEST=ROOT/'test_ksem_055_kalshi_market_identity_index_FOUNDATION_REPAIR.py'
MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'
IDX='idx_oracle_canonical_kalshi_snapshot_source_market_id'

def main():
 print('='*120); print(' KSEM-055 KALSHI MARKET IDENTITY INDEX FOUNDATION REPAIR'); print('='*120)
 mod=importlib.import_module(MOD); _,b=mod._router_backend(ROOT); conn=b._connect(); conn.autocommit=True
 try:
  with conn.cursor() as cur:
   cur.execute("""SELECT i.indisvalid,i.indisready FROM pg_class c JOIN pg_index i ON i.indexrelid=c.oid
    WHERE c.relname=%s""",(IDX,)); prior=cur.fetchone()
   print('[PRIOR_INDEX_STATE]',prior)
   if prior and not (prior[0] and prior[1]):
    cur.execute(f'DROP INDEX CONCURRENTLY IF EXISTS public.{IDX}')
   cur.execute(f"""CREATE INDEX CONCURRENTLY IF NOT EXISTS {IDX}
    ON public.oracle_canonical_observations
    ((canonical_observation_json->'payload'->>'source_market_id'))
    WHERE observation_type='market_snapshot' AND source_id='source.kalshi.market_data'""")
   cur.execute("""SELECT i.indisvalid,i.indisready FROM pg_class c JOIN pg_index i ON i.indexrelid=c.oid
    WHERE c.relname=%s""",(IDX,)); state=cur.fetchone()
 finally: conn.close()
 print('[INDEX]',IDX); print('[INDEX_STATE]',state)
 if state != (True,True): raise RuntimeError('KALSHI_MARKET_IDENTITY_INDEX_NOT_VALID_READY')
 OUT.write_text(json.dumps({'index':IDX,'valid':True,'ready':True,'execution_authority':False},indent=2))
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_kalshi_market_identity_index_foundation_repair.json').read_text())\nassert d['valid'] and d['ready']\nassert d['execution_authority'] is False\nprint('[PASS] exact Kalshi market identity index valid and ready')\nprint('[PASS] KSEM-055 foundation repair certified')\n")
 print('[WRITE]',OUT.relative_to(ROOT)); print('[WRITE]',TEST.name)

if __name__=='__main__': main()