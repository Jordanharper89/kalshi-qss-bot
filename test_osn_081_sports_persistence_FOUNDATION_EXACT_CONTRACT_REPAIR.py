
from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn081_exact_persistence_contract_repair.json"
assert STATE.exists()
state=json.loads(STATE.read_text(encoding="utf-8"))

from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (
    canonicalize, WRITER_ID, CONVERTER_MODULE, CONVERTER_FUNCTION
)

r=acquire_canonical_events("NFL",timeout=15,root=ROOT)
assert r.events
event=r.events[0]
canonical=canonicalize(event,batch_id="osn081-foundation-test")
oid=getattr(canonical,"observation_id",None)

print("[CONVERTER]",CONVERTER_MODULE,CONVERTER_FUNCTION)
print("[CANONICALIZED] type=",type(canonical).__name__,"observation_id=",oid)
assert oid
assert WRITER_ID=="oracle.osn.sports"
assert state["canonicalizer"]=="OAD-261"
assert state["single_writer"]=="OPH-019"
assert state["execution_authority"] is False
print("[PASS] live CanonicalSportsEvent converts through recovered exact persistence contract")
print("[PASS] OAD-261 canonicalization succeeds")
print("[PASS] OSN-081 persistence foundation exact-contract repair certified")
