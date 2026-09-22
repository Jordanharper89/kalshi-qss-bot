from dataclasses import dataclass
from .slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from .slop_020_prospective_resolution_ledger import read_resolution_dicts
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class PhysicalReport:
 frozen:int;resolved:int;independent_tokens:int;target_first:int;stop_first:int;timeout:int
 net_expectancy:float|None;state:str;execution_authority:bool=False
def physical_report(root=None,min_resolved=15,min_tokens=3):
 ps=tuple(read_predictions(root));rs=tuple(read_resolution_dicts(root))
 pmap={p.prediction_id:p for p in ps};tokens={pmap[x["prediction_id"]].token_address for x in rs if x["prediction_id"] in pmap}
 outs=[str(x["outcome"]) for x in rs];nets=[float(x["net_return"]) for x in rs];e=sum(nets)/len(nets) if nets else None
 token_nets={t:[] for t in tokens}
 for x in rs:
  p=pmap.get(x["prediction_id"])
  if p is not None:token_nets[p.token_address].append(float(x["net_return"]))
 token_means=[sum(v)/len(v) for v in token_nets.values() if v]
 positive_tokens=sum(x>0 for x in token_means)
 majority=positive_tokens>len(token_means)/2
 if len(rs)<int(min_resolved) or len(tokens)<int(min_tokens):state="INSUFFICIENT_PHYSICAL_SUPPORT"
 elif e is not None and e>0 and majority:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 else:state="GENERALIZATION_NOT_CERTIFIED"
 return PhysicalReport(len(ps),len(rs),len(tokens),outs.count("TARGET_FIRST"),outs.count("STOP_FIRST"),
  outs.count("TIMEOUT"),e,state,False)
