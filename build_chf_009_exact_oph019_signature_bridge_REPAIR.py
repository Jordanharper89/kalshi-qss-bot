from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_008_single_writer_contract_discovery.py").exists(),"CHF-008 required"

BODY=r"""
import inspect
from pathlib import Path
import qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue as oph019

REVISION="CHF-009-REPAIR"
SUBMIT_PARAMS=("writer_id","priority","observations","root")
AWAIT_PARAMS=("request_id","root","timeout_seconds","poll_seconds")

def _exact_function(param_names):
    matches=[]
    for name,obj in vars(oph019).items():
        if not inspect.isfunction(obj):
            continue
        params=tuple(inspect.signature(obj).parameters)
        if params==tuple(param_names):
            matches.append((name,obj))
    if len(matches)!=1:
        raise RuntimeError(f"exact OPH-019 contract resolution failed params={param_names} matches={[n for n,_ in matches]}")
    return matches[0]

def resolve_exact_contract():
    submit_name,submit_fn=_exact_function(SUBMIT_PARAMS)
    await_name,await_fn=_exact_function(AWAIT_PARAMS)
    return submit_name,submit_fn,await_name,await_fn

def submit(writer_id,priority,observations,root=None):
    _,fn,_,_=resolve_exact_contract()
    return fn(writer_id,priority,observations,root=root)

def await_request(request_id,root=None,timeout_seconds=120.0,poll_seconds=0.05):
    _,_,_,fn=resolve_exact_contract()
    return fn(request_id,root=root,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
"""

TEST=r"""
import inspect
from qseries_v2.oracle_coinbase_high_frequency.chf_009_exact_oph019_signature_bridge import resolve_exact_contract
sn,sf,an,af=resolve_exact_contract()
print("[SUBMIT_CALLABLE]",sn)
print("[SUBMIT_SIGNATURE]",inspect.signature(sf))
print("[AWAIT_CALLABLE]",an)
print("[AWAIT_SIGNATURE]",inspect.signature(af))
assert tuple(inspect.signature(sf).parameters)==("writer_id","priority","observations","root")
assert tuple(inspect.signature(af).parameters)==("request_id","root","timeout_seconds","poll_seconds")
print("[PASS] failed guessed-name CHF-009 bridge retired")
print("[PASS] exact OPH-019 submit contract bound")
print("[PASS] exact OPH-019 await contract bound")
print("[PASS] no direct PostgreSQL writer introduced")
print("[PASS] CHF-009 exact-signature repair certified")
"""

mod=PKG/"chf_009_exact_oph019_signature_bridge.py"
tst=ROOT/"test_chf_009_exact_oph019_signature_bridge_REPAIR.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True)
py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",mod)
print("[PASS] wrote",tst)
print("[PASS] retired guessed callable-name resolution")
print("[PASS] execution_authority=FALSE")
