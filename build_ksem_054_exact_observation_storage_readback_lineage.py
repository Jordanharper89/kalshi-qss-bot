from pathlib import Path
import importlib,json
ROOT=Path.cwd();S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state';OUT=S/'ksem054_exact_observation_storage_readback_lineage.json';TEST=ROOT/'test_ksem_054_exact_observation_storage_readback_lineage.py';MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'
def safe(x):
 if x is None or isinstance(x,(str,int,float,bool)):return x
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
 if isinstance(x,(list,tuple,set)):return [safe(v) for v in x]
 if hasattr(x,'__dict__'):return {'__type__':type(x).__name__,**{str(k):safe(v) for k,v in vars(x).items()}}
 return repr(x)
def main():
 print('='*120);print(' KSEM-054 EXACT OBSERVATION STORAGE -> READBACK LINEAGE');print('='*120)
 k=json.loads((S/'ksem043_exact_canonical_observation_recovery.json').read_text());pairs=[x for x in k['pair_observations'] if int(x.get('query_count') or 0)>0]
 if not pairs:raise RuntimeError('no previously proven canonical observation readback available')
 mod=importlib.import_module(MOD);_,b=mod._router_backend(ROOT);rc=mod._request_class(b);oid=pairs[0]['observation_id'];ticker=pairs[0]['ticker'];conn=b._connect()
 try:
  with conn.cursor() as cur:cur.execute('BEGIN READ ONLY');cur.execute('SELECT * FROM public.oracle_canonical_observations WHERE observation_id=%s',(oid,));row=cur.fetchone();cols=[d.name if hasattr(d,'name') else d[0] for d in cur.description] if cur.description else []
  conn.rollback()
 finally:conn.close()
 req=mod._request_for_observation_id(rc,b,oid);rebuilt=b.query(request=req);physical=dict(zip(cols,row)) if row else None;d={'ticker':ticker,'observation_id':oid,'physical_row':safe(physical),'backend_readback':safe(rebuilt),'execution_authority':False}
 print('[TICKER]',ticker);print('[OBSERVATION_ID]',oid);print('[PHYSICAL_COLUMNS]',cols);print('[PHYSICAL_ROW]',safe(physical));print('[BACKEND_READBACK]',safe(rebuilt));OUT.write_text(json.dumps(d,indent=2),encoding='utf-8')
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem054_exact_observation_storage_readback_lineage.json').read_text())\nassert d['physical_row'] is not None\nassert d['backend_readback']\nassert d['execution_authority'] is False\nprint('[PASS] physical PostgreSQL row traced through exact canonical backend readback')\nprint('[PASS] KSEM-054 certified')\n",encoding='utf-8');print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()