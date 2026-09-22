from pathlib import Path
import ast,hashlib,json
R=Path.cwd(); P=R/'qseries_v2'/'oracle_predictive_discovery'; D=R/'runtime'/'predictive_data'
if not (P/'opd_041_exact_live_token_materializer.py').is_file(): raise RuntimeError('OPD-041 missing')
def src(prefix):
    hits=[]
    for d in (P,R/'qseries_v2'/'oracle_predictive_data'):
        if d.is_dir(): hits += [x for x in d.glob(prefix+'*.py') if not x.name.startswith(('build_','test_'))]
    if len(hits)!=1: raise RuntimeError(f'{prefix}: expected 1 bounded source, found {len(hits)}: {hits}')
    return hits[0]
def pick(path,terms):
    text=path.read_text(encoding='utf-8'); tree=ast.parse(text); c=[]
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and not n.name.startswith('_'):
            seg=(ast.get_source_segment(text,n) or '').lower(); name=n.name.lower()
            s=sum(8 if t in name else 2 if t in seg else 0 for t in terms)
            if s:c.append((s,n.name))
    c.sort(reverse=True)
    if not c or (len(c)>1 and c[0][0]==c[1][0]): raise RuntimeError(f'callable not uniquely proved in {path}: {c[:8]}')
    return c[0][1]
reader=src('opd_036_'); intake=src('opd_032_'); rf=pick(reader,('bounded','read','live','state')); inf=pick(intake,('intake','state','ledger','append'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
m="""from pathlib import Path
import hashlib,importlib.util
READER_PATH=r'{rp}'; READER_SHA256='{rsha}'; READER_CALLABLE='{rf}'
INTAKE_PATH=r'{ip}'; INTAKE_SHA256='{isha}'; INTAKE_CALLABLE='{inf}'
execution_authority=False; probability_enabled=False; direction_enabled=False; publication_allowed=False
def _load(root,relative,expected_sha,callable_name):
 p=Path(root)/relative
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected_sha: raise RuntimeError('certified upstream source changed: '+relative)
 s=importlib.util.spec_from_file_location('_opd042_'+callable_name,p); x=importlib.util.module_from_spec(s); s.loader.exec_module(x); f=getattr(x,callable_name,None)
 if not callable(f): raise RuntimeError('proved callable disappeared: '+callable_name)
 return f
""".format(rp=reader.relative_to(R),rsha=sha(reader),rf=rf,ip=intake.relative_to(R),isha=sha(intake),inf=inf)
(P/'opd_042_live_state_to_prospective_intake_bridge.py').write_text(m,encoding='utf-8')
(D/'opd_042_live_state_intake_bridge_contract.json').write_text(json.dumps({'schema_version':'OPD-042','reader_path':str(reader.relative_to(R)),'reader_callable':rf,'intake_path':str(intake.relative_to(R)),'intake_callable':inf,'opd041_exact_token_lineage':True,'execution_authority':False,'probability_enabled':False,'direction_enabled':False,'publication_allowed':False},indent=2),encoding='utf-8')
t="""from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_042_live_state_to_prospective_intake_bridge as m
r=Path.cwd(); assert m.execution_authority is False and m.probability_enabled is False and m.direction_enabled is False and m.publication_allowed is False
assert callable(m._load(r,m.READER_PATH,m.READER_SHA256,m.READER_CALLABLE)); assert callable(m._load(r,m.INTAKE_PATH,m.INTAKE_SHA256,m.INTAKE_CALLABLE))
print('[READER]',m.READER_PATH,m.READER_CALLABLE); print('[INTAKE]',m.INTAKE_PATH,m.INTAKE_CALLABLE); print('[PASS] OPD-042 bounded exact-contract bridge certified')
"""
(R/'test_opd_042_live_state_to_prospective_intake_bridge.py').write_text(t,encoding='utf-8')
print('[PASS] OPD-042 bounded AST-only installer complete')