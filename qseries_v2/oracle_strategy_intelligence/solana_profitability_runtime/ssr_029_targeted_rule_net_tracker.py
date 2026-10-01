from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_028_targeted_rule_outcome_ledger import build as outcomes
FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"
def _med(v):
 v=sorted(v);return None if not v else v[len(v)//2]
def build(root):
 root=Path(root);o=outcomes(root);f=json.loads((root/FRI).read_text(encoding="utf-8"))
 rr=[x for x in f.get("ready_rows",[]) if x.get("family")=="PUMP_SWAP" and x.get("executable_ready")]
 fees=[float(x["fee_fraction"]) for x in rr if isinstance(x.get("fee_fraction"),(int,float))]
 devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in rr if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
 fee=_med(fees);dev=_med(devs);fr=None if fee is None or dev is None else 2*fee+2*dev
 vals=[float(x["gross_forward_return"]) for x in o["rows"] if isinstance(x.get("gross_forward_return"),(int,float))]
 nets=[] if fr is None else [v-fr for v in vals]
 state="INSUFFICIENT_TARGETED_CASES" if len(nets)<5 else "TARGETED_NET_POSITIVE_CANDIDATE" if sum(nets)/len(nets)>0 and sum(v>0 for v in nets)/len(nets)>.5 else "TARGETED_NET_NOT_POSITIVE"
 return {"revision":"SSR_029","targeted_case_count":len(vals),"physical_friction_row_count":len(rr),
  "modeled_round_trip_friction":fr,"mean_gross_return":None if not vals else sum(vals)/len(vals),
  "mean_net_return":None if not nets else sum(nets)/len(nets),
  "net_positive_frequency":None if not nets else sum(v>0 for v in nets)/len(nets),
  "cases_needed_to_5":max(0,5-len(vals)),"state":state,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/targeted_rule_net_tracker.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
