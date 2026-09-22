import inspect
from qseries_v2.oracle_adapters.independent import oad_314_solana_verified_forward_outcome_attribution as o314
from qseries_v2.oracle_strategy_intelligence.solana import ssi_002_physical_exact_future_price_path_materialization as s2

def certify():
    p=getattr(o314,"_price_for_pair",None)
    m=getattr(s2,"materialize_exact_future_price_paths",None)
    if not callable(p): raise AssertionError("OAD-314 _price_for_pair missing")
    if not callable(m): raise AssertionError("SSI-002 exact path materializer missing")
    r={"price_for_pair_signature":str(inspect.signature(p)),
       "path_materializer_signature":str(inspect.signature(m)),
       "exact_horizon":60,"target":0.10,"stop":0.05,"friction_bps":200,
       "condition":("order_flow","BUY_PRESSURE"),
       "read_only":True,"execution_authority":False}
    print("[SSI-013A]",r);return r
