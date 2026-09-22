from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class EconomicFunnel:
 frozen:int;resolved:int;target_first:int;stop_first:int;timeout:int;unresolved:int
 net_expectancy:float|None;execution_authority:bool=False
def economic_funnel(root=None):
 ps=read_predictions(root);rs=read_resolution_dicts(root)
 outcomes=[str(x["outcome"]) for x in rs];nets=[float(x["net_return"]) for x in rs]
 return EconomicFunnel(len(ps),len(rs),outcomes.count("TARGET_FIRST"),outcomes.count("STOP_FIRST"),
  outcomes.count("TIMEOUT"),max(0,len(ps)-len(rs)),(sum(nets)/len(nets) if nets else None),False)
