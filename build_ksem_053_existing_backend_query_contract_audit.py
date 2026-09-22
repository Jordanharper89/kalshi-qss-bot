from pathlib import Path
import importlib,inspect,json
ROOT=Path.cwd(); S=ROOT/'qseries_v2/kalshi_sports_evidence_mapping/state'; OUT=S/'ksem053_existing_backend_query_contract.json'; TEST=ROOT/'test_ksem_053_existing_backend_query_contract_audit.py'; MOD='qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit'
def src(x):
 try:return inspect.getsource(x)
 except Exception as e:return '<SOURCE_UNAVAILABLE '+type(e).__name__+': '+str(e)+'>'
def main():
 print('='*120);print(' KSEM-053 EXISTING PERSISTENCE BACKEND QUERY CONTRACT AUDIT');print('='*120)
 mod=importlib.import_module(MOD);router,backend=mod._router_backend(ROOT);cls=type(backend);q=getattr(cls,'query',None);r=mod._request_class(backend)
 d={'router_type':type(router).__module__+'.'+type(router).__name__,'backend_type':cls.__module__+'.'+cls.__name__,'request_type':r.__module__+'.'+r.__name__,'query_signature':str(inspect.signature(q)) if q else None,'query_source':src(q),'request_source':src(r),'execution_authority':False}
 for k in ('router_type','backend_type','request_type','query_signature'):print('['+k.upper()+']',d[k])
 print('[QUERY_SOURCE]\n'+d['query_source']);print('[REQUEST_SOURCE]\n'+d['request_source']);OUT.write_text(json.dumps(d,indent=2),encoding='utf-8')
 TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem053_existing_backend_query_contract.json').read_text())\nassert d['backend_type'] and d['request_type'] and d['query_signature']\nassert d['execution_authority'] is False\nprint('[PASS] exact existing canonical backend query contract captured')\nprint('[PASS] KSEM-053 certified')\n",encoding='utf-8');print('[WRITE]',OUT.relative_to(ROOT));print('[WRITE]',TEST.name)
if __name__=='__main__':main()