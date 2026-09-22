from pathlib import Path
import ast, importlib.util, inspect, json, re

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_001e_solana_profitability_input_lineage_audit.py"
TEST=ROOT/"test_ssi_001e_solana_profitability_input_lineage_audit.py"

MODULE=r"""
from pathlib import Path
import ast,re,json
ROOT=Path.cwd()
FILES=[
"qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
"qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
"qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
"qseries_v2/oracle_adapters/independent/oad_360_solana_exact_observation_readback.py",
]
TOKENS=("price","usd","quote","reserve","liquidity","pool","mint","asset","token","observed_at",
        "timestamp","horizon","forward","outcome","observation_id","source_id","readback")
def audit():
 out={"schema_version":"SSI-001E","files":[],"missing":[],"price_lineage_hits":[],
      "read_only":True,"execution_authority":False}
 for rel in FILES:
  p=ROOT/rel
  if not p.exists():
   out["missing"].append(rel); continue
  text=p.read_text(encoding="utf-8",errors="replace"); tree=ast.parse(text)
  funcs=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
  hits=[]
  for i,line in enumerate(text.splitlines(),1):
   low=line.lower()
   found=tuple(t for t in TOKENS if t in low)
   if found:
    cleaned=line.strip()
    if len(cleaned)>240: cleaned=cleaned[:240]
    hits.append({"line":i,"tokens":found,"text":cleaned})
    if any(t in found for t in ("price","usd","quote","reserve","liquidity")):
     out["price_lineage_hits"].append({"file":rel,"line":i,"tokens":found,"text":cleaned})
  out["files"].append({"path":rel,"functions":funcs,"hits":hits})
 out["price_path_contract_found"]=bool(out["price_lineage_hits"])
 return out
def render():
 r=audit()
 print("[SSI-001E] SOLANA PROFITABILITY INPUT LINEAGE")
 print("[FILES_FOUND]",len(r["files"]),"[MISSING]",len(r["missing"]))
 for x in r["files"]:
  print("\\n[FILE]",x["path"])
  print("[FUNCTIONS]",x["functions"])
  for h in x["hits"]: print("[LINEAGE]",h)
 if r["missing"]:
  print("\\n[MISSING_FILES]",r["missing"])
 print("\\n[PRICE_LINEAGE_HITS]",len(r["price_lineage_hits"]))
 for h in r["price_lineage_hits"]: print("[PRICE]",h)
 print("[GATE] price_path_contract_found=",r["price_path_contract_found"])
 print("[CONTRACT] read_only=True execution_authority=False")
 return r
if __name__=="__main__": render()
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_001e_solana_profitability_input_lineage_audit import render
class T(unittest.TestCase):
 def test_physical_repo_lineage(self):
  r=render()
  self.assertGreaterEqual(len(r["files"]),2)
  self.assertTrue(any("oad_314" in x["path"] for x in r["files"]))
  self.assertFalse(r["execution_authority"])
  self.assertTrue(r["read_only"])
if __name__=="__main__": unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-001E SOLANA PROFITABILITY INPUT LINEAGE AUDIT INSTALLER");print("="*120)
 required=[
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"]
 for rel in required:
  p=ROOT/rel
  if not p.exists(): raise SystemExit("[FAIL] missing certified dependency: "+rel)
  ast.parse(p.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True)
 TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] repository/source audit only -- no PostgreSQL connection")
 print("[PASS] no acquisition, writer, runtime, or execution mutation")
 print("[DONE] SSI-001E INSTALLATION COMPLETE")
if __name__=="__main__": main()
