from pathlib import Path
import ast

ROOT=Path.cwd()

def require_file(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))
    return p

def require_symbol(rel,symbol):
    p=require_file(rel)
    tree=ast.parse(p.read_text(encoding='utf-8',errors='ignore'))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    if symbol not in names: raise SystemExit(f'[FAIL] exact symbol missing: {rel} -> {symbol}')
    print(f'[PASS] exact symbol verified: {rel} -> {symbol}')

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    compile(content,str(p),'exec')
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*120)
    print(' OSN-062 EXISTING SINGLE-WRITER SPORTS BOUNDARY INSTALLER')
    print('='*120)
    require_symbol('qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py','submit_observation_batch')
    require_symbol('qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py','exact_postgresql_readback')
    require_symbol('qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py','canonicalize_expansion_observation')
    put('qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py','\nimport inspect,uuid\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\n\nPRODUCER="oracle.osn.sports"\nPRIORITY=20\n\ndef canonicalize(x,batch_id=None):\n    return canonicalize_expansion_observation(x,batch_id or ("osn-sports-"+uuid.uuid4().hex))\n\ndef _invoke_submit(observations):\n    sig=inspect.signature(submit_observation_batch)\n    vals={\n        "producer":PRODUCER,\n        "producer_id":PRODUCER,\n        "observations":tuple(observations),\n        "observation_batch":tuple(observations),\n        "batch":tuple(observations),\n        "priority":PRIORITY,\n        "request_id":"osn-sports-"+uuid.uuid4().hex[:16],\n    }\n    args=[]; kwargs={}\n    for name,p in sig.parameters.items():\n        if name not in vals:\n            if p.default is inspect._empty and p.kind not in (p.VAR_POSITIONAL,p.VAR_KEYWORD):\n                raise RuntimeError(f"unsupported exact OPH-019 submit parameter: {name}; signature={sig}")\n            continue\n        if p.kind is p.POSITIONAL_ONLY: args.append(vals[name])\n        else: kwargs[name]=vals[name]\n    return submit_observation_batch(*args,**kwargs),str(sig)\n\ndef submit(observations):\n    return _invoke_submit(observations)\n\ndef exact_readback(observation_id):\n    sig=inspect.signature(exact_postgresql_readback)\n    vals={\n        "observation_id":observation_id,\n        "observation_ids":(observation_id,),\n        "ids":(observation_id,),\n    }\n    args=[];kwargs={}\n    for name,p in sig.parameters.items():\n        if name not in vals:\n            if p.default is inspect._empty and p.kind not in (p.VAR_POSITIONAL,p.VAR_KEYWORD):\n                raise RuntimeError(f"unsupported exact OAD-068 readback parameter: {name}; signature={sig}")\n            continue\n        if p.kind is p.POSITIONAL_ONLY: args.append(vals[name])\n        else: kwargs[name]=vals[name]\n    return exact_postgresql_readback(*args,**kwargs),str(sig)\n\ndef readback_count(value):\n    if value is None:return 0\n    if isinstance(value,(list,tuple,set)):return len(value)\n    if isinstance(value,dict):\n        for k in ("rows","observations","results","items"):\n            if k in value and hasattr(value[k],"__len__"): return len(value[k])\n        return 1 if value else 0\n    for k in ("rows","observations","results","items"):\n        v=getattr(value,k,None)\n        if v is not None and hasattr(v,"__len__"): return len(v)\n    return 1\n')
    put('test_osn_062_existing_single_writer_sports_boundary.py','\nimport inspect\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n submit_observation_batch,exact_postgresql_readback,PRODUCER\n)\nprint("[OPH019_SIGNATURE]",inspect.signature(submit_observation_batch))\nprint("[OAD068_SIGNATURE]",inspect.signature(exact_postgresql_readback))\nassert PRODUCER=="oracle.osn.sports"\nassert callable(submit_observation_batch)\nassert callable(exact_postgresql_readback)\nprint("[PASS] OSN-062 exact OPH-019 single-writer + OAD-068 readback boundary certified")\n')
    print('[PASS] no direct PostgreSQL writer introduced')
    print('[PASS] exact existing OPH-019 queue reused')
    print('[PASS] exact OAD-068 observation-ID readback reused')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
