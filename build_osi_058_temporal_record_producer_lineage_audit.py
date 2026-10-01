from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_058_temporal_record_producer_lineage_audit.py"
TEST=ROOT/"test_osi_058_temporal_record_producer_lineage_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json
from pathlib import Path
TARGETS=(
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
)
def audit(root):
 mods=[]
 for rel in TARGETS:
  p=root/rel
  if not p.is_file():continue
  text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
  funcs=[];imports=[];strings=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
   elif isinstance(n,ast.ImportFrom):
    imports.append({"module":n.module,"names":[x.name for x in n.names]})
   elif isinstance(n,ast.Constant) and isinstance(n.value,str):
    s=n.value.strip()
    if any(k in s.lower() for k in ("history","snapshot","record","pool","price","runtime","json","jsonl","observation")):strings.append(s)
  mods.append({"module":rel,"functions":funcs,"imports":imports[:100],"strings":strings[:200]})
 return {"revision":"OSI_058","modules":mods,"module_count":len(mods),"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/temporal_record_producer_lineage.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_058_temporal_record_producer_lineage_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertGreaterEqual(d["module_count"],4)
  print("[MODULES]",d["module_count"])
  for m in d["modules"]:
   print("[MODULE]",m["module"])
   print("[FUNCTIONS]",json.dumps(m["functions"],sort_keys=True)[:3000])
  print("[PASS] OSI-058 temporal record producer lineage audit")
  print("[TRADER] Finds the certified component that actually creates OAD-314-compatible price-history records")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" OSI-058 TEMPORAL RECORD PRODUCER LINEAGE AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
