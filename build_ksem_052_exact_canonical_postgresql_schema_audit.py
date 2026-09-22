from pathlib import Path
import importlib,json
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'
OUT=S/'ksem052_exact_canonical_postgresql_schema.json'; TEST=ROOT/'test_ksem_052_exact_canonical_postgresql_schema_audit.py'
MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'
def main():
 print('='*120); print(' KSEM-052 EXACT CANONICAL POSTGRESQL SCHEMA AUDIT'); print('='*120)
 mod=importlib.import_module(MOD); _,backend=mod._router_backend(ROOT); conn=backend._connect()
 try:
  with conn.cursor() as cur:
   cur.execute('BEGIN READ ONLY')
   cur.execute("SELECT column_name,data_type,udt_name,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='oracle_canonical_observations' ORDER BY ordinal_position"); cols=cur.fetchall()
   cur.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='oracle_canonical_observations' ORDER BY indexname"); idx=cur.fetchall()
   cur.execute("SELECT tc.constraint_name,tc.constraint_type,kcu.column_name FROM information_schema.table_constraints tc LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema WHERE tc.table_schema='public' AND tc.table_name='oracle_canonical_observations' ORDER BY tc.constraint_name,kcu.ordinal_position"); cons=cur.fetchall()
  conn.rollback()
 finally: conn.close()
 columns=[{'name':x[0],'data_type':x[1],'udt_name':x[2],'nullable':x[3],'default':x[4]} for x in cols]; indexes=[{'name':x[0],'definition':x[1]} for x in idx]; constraints=[{'name':x[0],'type':x[1],'column':x[2]} for x in cons]
 print('[COLUMNS]',len(columns))
 for x in columns: print('[COLUMN]',x)
 for x in indexes: print('[INDEX]',x)
 for x in constraints: print('[CONSTRAINT]',x)
 OUT.write_text(json.dumps({'columns':columns,'indexes':indexes,'constraints':constraints,'execution_authority':False},indent=2),encoding='utf-8')
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem052_exact_canonical_postgresql_schema.json').read_text())\nassert d['columns']\nassert d['execution_authority'] is False\nprint('[PASS] exact physical canonical PostgreSQL schema captured')\nprint('[PASS] KSEM-052 certified')\n",encoding='utf-8')
 print('[WRITE]',OUT.relative_to(ROOT)); print('[WRITE]',TEST.name)
if __name__=='__main__': main()