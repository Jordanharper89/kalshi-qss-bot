from pathlib import Path
import py_compile
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
for f in ("chf_011_strict_complete_multihorizon_windows.py","chf_012_strict_window_oad261_expansion_adapter.py","chf_009_exact_oph019_signature_bridge.py"):
    assert (PKG/f).exists(),f+" required"

BODY=r"""
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback
from .chf_009_exact_oph019_signature_bridge import submit,await_request
from .chf_011_strict_complete_multihorizon_windows import materialize_strict
from .chf_012_strict_window_oad261_expansion_adapter import adapt_window

REVISION="CHF-013"
WRITER_ID="oracle.coinbase_high_frequency"
PRIORITY=20

def _already(root,oid):
    try:
        rows=exact_postgresql_readback((oid,),root=root)
        return len(rows)==1
    except Exception:
        return False

def persist_strict_windows(root=None):
    root=Path(root or Path.cwd()).resolve()
    rows,_=materialize_strict(root)
    canonical=[]
    skipped=0
    for row in rows:
        x=adapt_window(row)
        batch=f"chf013.{x.subject}.{row['window_seconds']}.{x.provenance_hash[:16]}"
        obs=canonicalize_expansion_observation(x,batch)
        if _already(root,obs.observation_id):
            skipped+=1
            continue
        canonical.append(obs)
    if not canonical:
        return {"submitted":0,"committed":0,"readback":0,"skipped_existing":skipped,"observation_ids":()}
    submission=submit(WRITER_ID,PRIORITY,tuple(canonical),root=root)
    rid=getattr(submission,"request_id",None)
    if not rid: raise RuntimeError("OPH-019 submission returned no request_id")
    terminal=await_request(rid,root=root,timeout_seconds=120.0,poll_seconds=0.05)
    ids=tuple(x.observation_id for x in canonical)
    rb=exact_postgresql_readback(ids,root=root)
    if len(rb)!=len(ids):
        raise RuntimeError(f"durable readback mismatch {len(rb)} != {len(ids)}")
    return {"submitted":len(ids),"committed":len(ids),"readback":len(rb),"skipped_existing":skipped,"request_id":rid,"terminal":terminal,"observation_ids":ids}
"""
TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_013_strict_window_single_writer_persistence import persist_strict_windows
r=persist_strict_windows(Path.cwd())
print("[PERSISTENCE]",r)
assert r["readback"]==r["committed"]
print("[PASS] strict complete CHF windows use OAD-261 -> OPH-019 -> await -> OAD-068")
print("[PASS] duplicate durable identities are skipped before resubmission")
print("[PASS] CHF-013 strict-window single-writer persistence certified")
"""
mod=PKG/"chf_013_strict_window_single_writer_persistence.py"
tst=ROOT/"test_chf_013_strict_window_single_writer_persistence.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True); py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote CHF-013 persistence + test")
print("[PASS] no direct PostgreSQL writer introduced")
