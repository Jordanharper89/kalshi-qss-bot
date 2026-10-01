from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_012_native_block_shape_probe.py"
TEST=ROOT/"test_suls_012_native_block_shape_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,inspect
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as src

def probe():
 fn=src.acquire_finalized_block_batch
 sig=inspect.signature(fn)
 kwargs={}
 for name,p in sig.parameters.items():
  if p.default is not inspect._empty:continue
  if "count" in name or "limit" in name or "batch" in name:kwargs[name]=1
  elif "timeout" in name:kwargs[name]=20.0
 try:
  raw=fn(**kwargs)
  err=None
 except Exception as e:
  return {"revision":"SULS_012","signature":str(sig),"kwargs":kwargs,"ok":False,
   "error":f"{type(e).__name__}: {e}","execution_authority":False}
 typ=type(raw).__name__
 shape={"type":typ}
 if isinstance(raw,dict):shape["keys"]=sorted(raw.keys())
 elif isinstance(raw,(list,tuple)):
  shape["length"]=len(raw)
  if raw:
   x=raw[0];shape["first_type"]=type(x).__name__
   if isinstance(x,dict):shape["first_keys"]=sorted(x.keys())
   elif hasattr(x,"__dict__"):shape["first_attrs"]=sorted(k for k in vars(x) if not k.startswith("_"))
 elif hasattr(raw,"__dict__"):shape["attrs"]=sorted(k for k in vars(raw) if not k.startswith("_"))
 return {"revision":"SULS_012","signature":str(sig),"kwargs":kwargs,"ok":True,"shape":shape,
  "execution_authority":False}

def write(root):
 d=probe();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_block_shape_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_012_native_block_shape_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"]);print("[KWARGS]",json.dumps(d["kwargs"],sort_keys=True))
  print("[OK]",d["ok"])
  if d.get("shape"):print("[SHAPE]",json.dumps(d["shape"],sort_keys=True))
  if d.get("error"):print("[ERROR]",d["error"])
  if not d["ok"]:self.fail("NATIVE_FINALIZED_BLOCK_PROBE_FAILED")
  print("[PASS] SULS-012 native finalized-block physical shape probe")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-012 NATIVE FINALIZED-BLOCK SHAPE PROBE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
