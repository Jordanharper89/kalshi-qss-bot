from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_065_live_token_candidate_viability_audit.py"
TEST=ROOT/"test_osi_065d_live_token_candidate_viability_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    discover_live_solana_tokens,
    select_live_solana_token,
    expand_live_solana_token_pools,
)

def _brief(v):
 if isinstance(v,dict):
  return {"type":"dict","keys":sorted(str(k) for k in v.keys())}
 if isinstance(v,(list,tuple)):
  return {"type":type(v).__name__,"length":len(v),"item_types":[type(x).__name__ for x in list(v)[:20]]}
 attrs={}
 for name in dir(v):
  if name.startswith("_"):continue
  try:x=getattr(v,name)
  except Exception:continue
  if callable(x):continue
  if isinstance(x,(str,int,float,bool,type(None))):attrs[name]=x
  elif isinstance(x,(list,tuple,dict)):attrs[name]=_brief(x)
  if len(attrs)>=30:break
 return {"type":type(v).__name__,"attributes":attrs}

def _addresses(v):
 out=[]
 if isinstance(v,str):
  return [v]
 if isinstance(v,dict):
  for k in ("token_address","address","mint","subject"):
   x=v.get(k)
   if isinstance(x,str) and x:out.append(x)
  for k in ("tokens","items","results","observations"):
   x=v.get(k)
   if isinstance(x,(list,tuple)):
    for i in x:out.extend(_addresses(i))
 elif isinstance(v,(list,tuple)):
  for i in v:out.extend(_addresses(i))
 else:
  for k in ("token_address","address","mint","subject"):
   try:x=getattr(v,k)
   except Exception:x=None
   if isinstance(x,str) and x:out.append(x)
 seen=[]
 for x in out:
  if x not in seen:seen.append(x)
 return seen

def _usable(raw):
 payload=getattr(raw,"payload",{}) or {}
 pools=payload.get("pools") or ()
 valid=[]
 for p in pools:
  if isinstance(p,dict) and p.get("pair_address") and p.get("price_usd") not in (None,""):
   valid.append({
    "pair_address":str(p["pair_address"]),
    "price_usd":str(p["price_usd"]),
    "liquidity_usd":p.get("liquidity_usd"),
    "pair_created_at":p.get("pair_created_at"),
   })
 return valid

def audit(root):
 discovered=discover_live_solana_tokens(timeout_seconds=20.0)
 selected=str(select_live_solana_token(timeout_seconds=20.0))
 candidates=_addresses(discovered)
 if selected and selected not in candidates:candidates.insert(0,selected)
 candidates=candidates[:20]
 results=[]
 for token in candidates:
  try:
   raw=expand_live_solana_token_pools(token_address=token,timeout_seconds=20.0)
   pools=_usable(raw)
   results.append({"token_address":token,"ok":True,"usable_pools":pools,"usable_pool_count":len(pools),"return_type":type(raw).__name__})
  except Exception as e:
   results.append({"token_address":token,"ok":False,"usable_pools":[],"usable_pool_count":0,"error":f"{type(e).__name__}: {e}"})
 return {
  "revision":"OSI_065D",
  "discovery_shape":_brief(discovered),
  "selected_token":selected,
  "candidate_count":len(candidates),
  "candidates":candidates,
  "results":results,
  "viable_count":sum(1 for x in results if x["usable_pool_count"]>0),
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/live_token_candidate_viability.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_065_live_token_candidate_viability_audit import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[DISCOVERY_SHAPE]",json.dumps(d["discovery_shape"],sort_keys=True))
  print("[SELECTED_TOKEN]",d["selected_token"])
  print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["results"]:
   print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  print("[VIABLE_COUNT]",d["viable_count"])
  if d["candidate_count"]==0:self.fail("NO_DISCOVERED_SOLANA_TOKEN_CANDIDATES")
  print("[PASS] OSI-065D live token candidate viability audit")
  print("[TRADER] Separates token discovery from actually expandable live pools before atomic anchoring")
  print("[SCOPE] Read-only audit; no persistence and no prospective anchor mutation")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-065D LIVE TOKEN CANDIDATE VIABILITY AUDIT")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Diagnostic replacement after selected token had no usable pool at expansion time")

if __name__=="__main__":
 main()
