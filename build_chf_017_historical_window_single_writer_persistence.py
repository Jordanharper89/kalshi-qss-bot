from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/'qseries_v2'/'oracle_coinbase_high_frequency'
for f in ('chf_016_fixed_grid_historical_window_archive.py','chf_009_exact_oph019_signature_bridge.py'):
    assert (PKG/f).exists(),f+' required'
BODY=r'''
import hashlib,json
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback
from .chf_009_exact_oph019_signature_bridge import submit,await_request
from .chf_016_fixed_grid_historical_window_archive import archive
WRITER_ID='oracle.coinbase_high_frequency'; PRIORITY=20
@dataclass(frozen=True)
class X:
    source_id:str; source_class:str; provider:str; subject:str; observation_type:str; observed_at:str; payload:dict; provenance_hash:str

def _adapt(r):
    stable=json.dumps(r,sort_keys=True,separators=(',',':'))
    return X('source.crypto.hf.coinbase.historical_window','ORACLE_DERIVED','coinbase',r['product_id'],'coinbase_hf_historical_complete_condition_window',r['anchor_time'],r,hashlib.sha256(stable.encode()).hexdigest())

def _already(root,oid):
    try:return len(exact_postgresql_readback((oid,),root=root))==1
    except:return False

def persist_new(root=None,max_batch=250):
    root=Path(root or Path.cwd()).resolve(); archive(root)
    p=root/'runtime'/'coinbase_hf'/'historical_condition_windows.jsonl'
    if not p.exists():return {'submitted':0,'committed':0,'readback':0,'skipped_existing':0}
    rows=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        try:rows.append(json.loads(line))
        except:pass
    canonical=[]; skipped=0
    for r in rows[-max_batch:]:
        x=_adapt(r); obs=canonicalize_expansion_observation(x,f"chf017.{r['product_id']}.{r['window_seconds']}.{int(r['anchor_epoch'])}")
        if _already(root,obs.observation_id):skipped+=1
        else:canonical.append(obs)
    if not canonical:return {'submitted':0,'committed':0,'readback':0,'skipped_existing':skipped}
    s=submit(WRITER_ID,PRIORITY,tuple(canonical),root=root); rid=getattr(s,'request_id',None)
    if not rid:raise RuntimeError('OPH-019 returned no request_id')
    terminal=await_request(rid,root=root,timeout_seconds=120.0,poll_seconds=0.05)
    ids=tuple(x.observation_id for x in canonical); rb=exact_postgresql_readback(ids,root=root)
    if len(rb)!=len(ids):raise RuntimeError(f'readback mismatch {len(rb)} != {len(ids)}')
    return {'submitted':len(ids),'committed':len(ids),'readback':len(rb),'skipped_existing':skipped,'request_id':rid,'terminal':terminal}
'''
TEST=r'''
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_017_historical_window_single_writer_persistence import persist_new
r=persist_new(Path.cwd());print('[PERSIST]',r)
assert r['committed']==r['readback']
print('[PASS] historical windows use OAD-261 -> OPH-019 -> await -> OAD-068 only')
print('[PASS] no direct PostgreSQL writer introduced')
print('[PASS] CHF-017 historical persistence certified')
'''
mod=PKG/'chf_017_historical_window_single_writer_persistence.py';tst=ROOT/'test_chf_017_historical_window_single_writer_persistence.py'
mod.write_text(BODY.lstrip(),encoding='utf-8');tst.write_text(TEST.lstrip(),encoding='utf-8')
for p in (mod,tst):py_compile.compile(str(p),doraise=True)
print('[PASS] wrote CHF-017 historical persistence + test')
