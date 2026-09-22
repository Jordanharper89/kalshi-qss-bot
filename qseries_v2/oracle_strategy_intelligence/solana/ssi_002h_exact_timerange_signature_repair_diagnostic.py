
import inspect
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
def diagnose():
 fn=CanonicalPersistenceQueryRequest.by_observed_time_range
 sig=str(inspect.signature(fn))
 print("[SSI-002H] by_observed_time_range signature =",sig)
 return {"signature":sig,"read_only":True,"execution_authority":False}
