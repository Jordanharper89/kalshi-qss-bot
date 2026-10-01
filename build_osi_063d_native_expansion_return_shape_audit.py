from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_063_native_expansion_return_shape_audit.py"
TEST=ROOT/"test_osi_063d_native_expansion_return_shape_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    expand_live_solana_token_pools,
)

def _shape(v,depth=0):
 if depth>3:
  return {"type":type(v).__name__}
 if isinstance(v,dict):
  return {
   "type":"dict",
   "keys":sorted(str(k) for k in v.keys()),
   "children":{str(k):_shape(x,depth+1) for k,x in list(v.items())[:20]},
  }
 if isinstance(v,(list,tuple)):
  return {
   "type":type(v).__name__,
   "length":len(v),
   "items":[_shape(x,depth+1) for x in list(v)[:5]],
  }
 attrs={}
 for name in dir(v):
  if name.startswith("_"):
   continue
  try:
   x=getattr(v,name)
  except Exception:
   continue
  if callable(x):
   continue
  attrs[name]=_shape(x,depth+1)
  if len(attrs)>=30:
   break
 return {"type":type(v).__name__,"attributes":attrs}

def audit(root):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:
  raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")
 raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
 return {
  "revision":"OSI_063D",
  "asset_key":asset,
  "return_type":type(raw).__name__,
  "shape":_shape(raw),
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/native_expansion_return_shape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_063_native_expansion_return_shape_audit import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[RETURN_TYPE]",d["return_type"])
  print("[RETURN_SHAPE]",json.dumps(d["shape"],sort_keys=True)[:12000])
  print("[PASS] OSI-063D native expansion return-shape audit")
  print("[TRADER] Exposes the exact live native pool object contract before the anchor parser is rebuilt")
  print("[SCOPE] Read-only shape audit; no PostgreSQL write and no guessed pool schema")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-063D NATIVE EXPANSION RETURN-SHAPE AUDIT")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement diagnostic after OSI-063C guessed wrong native expansion shape")

if __name__=="__main__":
 main()
