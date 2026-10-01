from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_046_canonical_solana_json_shape_profiler.py"
TEST=ROOT/"test_osi_046_canonical_solana_json_shape_profiler.py"
MOD_TEXT=r"""from __future__ import annotations
import collections,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import read
def _walk(v,prefix="",out=None):
 out=[] if out is None else out
 if isinstance(v,dict):
  for k,x in v.items():
   p=f"{prefix}.{k}" if prefix else str(k);out.append((p,type(x).__name__))
   if isinstance(x,(dict,list)):_walk(x,p,out)
 elif isinstance(v,list):
  for x in v[:3]:
   if isinstance(x,(dict,list)):_walk(x,prefix+"[]",out)
 return out
def profile(root,limit=750):
 rows=read(root,limit)["rows"];groups={}
 for r in rows:
  typ=r["observation_type"];g=groups.setdefault(typ,collections.Counter())
  for p,t in _walk(r.get("canonical_observation_json") or {}):g[(p,t)]+=1
 out={}
 for typ,c in groups.items():
  out[typ]=[{"path":p,"type":t,"count":n} for (p,t),n in c.most_common(120)]
 return {"revision":"OSI_046","rows_profiled":len(rows),"profiles":out,"execution_authority":False,"read_only":True}
def write(root):
 d=profile(root);p=root/"runtime_state/solana_opportunities/canonical_solana_json_shape_profile.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_046_canonical_solana_json_shape_profiler import profile,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=profile(ROOT);p=write(ROOT);self.assertGreater(d["rows_profiled"],0);self.assertTrue(d["profiles"])
  print("[ROWS_PROFILED]",d["rows_profiled"]);print("[OBSERVATION_TYPES]",sorted(d["profiles"]))
  for k in sorted(d["profiles"])[:6]:print("[PROFILE]",k,json.dumps(d["profiles"][k][:12],sort_keys=True))
  print("[PASS] OSI-046 canonical Solana JSON shape profiler")
  print("[TRADER] Shows the exact fields Oracle has actually scraped before formulas are defined")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-046 CANONICAL SOLANA JSON SHAPE PROFILER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
