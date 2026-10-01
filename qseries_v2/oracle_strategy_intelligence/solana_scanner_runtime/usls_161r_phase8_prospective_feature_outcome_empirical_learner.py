from __future__ import annotations
import json,math
from pathlib import Path
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"

def _bin(v,cuts):
 if not isinstance(v,(int,float)) or not math.isfinite(v):return "MISSING"
 for i,c in enumerate(cuts):
  if v<c:return f"B{i}"
 return f"B{len(cuts)}"

def run(root):
 root=Path(root);led=json.loads((root/LEDGER).read_text(encoding="utf-8"))
 frz=json.loads((root/FREEZE).read_text(encoding="utf-8"));fb={x["freeze_hash"]:x for x in frz.get("frozen_setups",[])}
 groups={}
 for c in led.get("cases",[]):
  f=fb.get(c.get("freeze_hash"))
  if not f:continue
  g=float(c["gross_forward_return"]);key=(c["family"],_bin(f.get("return_to_freeze"),[-.10,0,.10]),_bin(f.get("trade_count"),[2,5,10]))
  z=groups.setdefault(key,{"n":0,"returns":[]});z["n"]+=1;z["returns"].append(g)
 out=[]
 for (fam,mom,trades),z in sorted(groups.items()):
  vals=z["returns"];out.append({"family":fam,"momentum_bucket":mom,"trade_count_bucket":trades,
   "sample_size":len(vals),"raw_positive_frequency":sum(v>0 for v in vals)/len(vals),
   "mean_gross_forward_return":sum(vals)/len(vals),
   "median_gross_forward_return":sorted(vals)[len(vals)//2],
   "probability_calibrated":False,"net_profitability_claimed":False})
 return {"revision":"USLS_161R","prospective_case_count":len(led.get("cases",[])),
  "learned_group_count":len(out),"groups":out,
  "learning_semantics":"RAW_PROSPECTIVE_EMPIRICAL_FREQUENCY_NOT_CALIBRATED_PROBABILITY",
  "next_boundary":"PHASE8_UNIVERSAL_COVERAGE_AND_SAMPLE_GATE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_prospective_empirical_learning.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
