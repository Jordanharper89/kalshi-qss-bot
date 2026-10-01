from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_023_out_of_sample_rule_validation import build as validated
FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json";OUT="runtime_state/solana_opportunities/profitability_runtime/friction_aware_strategy_hypotheses.json"
def _load(p):
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}
def _med(v):
 v=sorted(v);return None if not v else v[len(v)//2]
def build(root):
 root=Path(root);d=validated(root);f=_load(root/FRI);by={}
 for x in f.get("ready_rows",[]):
  if x.get("family") and x.get("executable_ready"):by.setdefault(x["family"],[]).append(x)
 out=[]
 for h in d["rules"]:
  rows=by.get(h["family"],[]);fees=[float(x["fee_fraction"]) for x in rows if isinstance(x.get("fee_fraction"),(int,float))];devs=[abs(float(x["realized_execution_deviation_fraction"])) for x in rows if isinstance(x.get("realized_execution_deviation_fraction"),(int,float))]
  fee=_med(fees);dev=_med(devs);fr=None if fee is None or dev is None else 2*fee+2*dev;vg=h["validation"]["mean_gross_return"];net=None if fr is None or vg is None else vg-fr
  state="REJECTED_INITIAL_VALIDATION" if not h["validation_pass"] else "VALIDATED_GROSS_FRICTION_GAP" if fr is None else "NET_POSITIVE_HYPOTHESIS_NOT_CERTIFIED" if net>0 else "NET_NEGATIVE_AFTER_FRICTION"
  out.append({**h,"physical_friction_row_count":len(rows),"modeled_round_trip_friction":fr,"validation_estimated_net_return":net,"strategy_state":state})
 out.sort(key=lambda x:(x["strategy_state"]=="NET_POSITIVE_HYPOTHESIS_NOT_CERTIFIED",x["validation_estimated_net_return"] if isinstance(x["validation_estimated_net_return"],(int,float)) else -999,x["validation"]["n"]),reverse=True)
 return {"revision":"SSR_024","hypothesis_count":len(out),"net_positive_hypothesis_count":sum(x["strategy_state"]=="NET_POSITIVE_HYPOTHESIS_NOT_CERTIFIED" for x in out),"gross_validated_friction_gap_count":sum(x["strategy_state"]=="VALIDATED_GROSS_FRICTION_GAP" for x in out),"hypotheses":out,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
