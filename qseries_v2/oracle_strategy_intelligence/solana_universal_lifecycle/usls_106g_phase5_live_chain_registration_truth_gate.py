from __future__ import annotations
import json,re
from pathlib import Path

CHAIN=("suls_083_persistent_event_driven_runtime","suls_081_event_driven_worker_checkpoint_foundation",
 "suls_080_event_driven_lifecycle_bridge","suls_070b_live_priority_runtime_cycle",
 "suls_062_confirmed_fast_lane_runtime_worker")
TRADE=("usls_101d_pumpswap_048b_direct_rematerialization_repair",
 "usls_098_remaining_venue_universal_trade_normalizer","usls_063b_launchlab_universal_trade_normalizer")

def pyfiles(root):
 out=[]
 for p in [Path(root)/"run_oracle_live.py",*(Path(root)/"qseries_v2").rglob("*.py")]:
  if p.exists() and p.is_file():out.append(p)
 return out

def refs(root,name):
 out=[]
 for p in pyfiles(root):
  try:s=p.read_text(encoding="utf-8",errors="ignore")
  except Exception:continue
  if name in s and p.stem!=name:
   out.append(str(p.relative_to(root)))
 return sorted(set(out))

def module_info(root,name):
 hits=list((Path(root)/"qseries_v2").rglob(name+".py"))
 if not hits:return {"module":name,"exists":False,"referenced_by":[]}
 p=hits[0];s=p.read_text(encoding="utf-8",errors="ignore")
 funcs=re.findall(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(",s,re.M)
 return {"module":name,"exists":True,"path":str(p.relative_to(root)),"functions":funcs,
  "referenced_by":refs(root,name)}

def build(root):
 chain=[module_info(root,x) for x in CHAIN]
 trade=[module_info(root,x) for x in TRADE]
 birth_registered=any("run_oracle_live.py" in x["referenced_by"] for x in chain)
 trade_registered=any("run_oracle_live.py" in x["referenced_by"] for x in trade)
 return {"revision":"USLS_106G","birth_chain":chain,"trade_modules":trade,
  "birth_chain_top_level_registered":birth_registered,
  "trade_modules_top_level_registered":trade_registered,
  "finding":"TRADE_SIDE_NOT_LIVE_REGISTERED" if not trade_registered else "TRADE_SIDE_REGISTRATION_PRESENT",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_live_chain_registration_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
