from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161f_phase8_family_semantic_decoder_provenance_gate.py"
TEST=ROOT/"test_usls_161f_phase8_family_semantic_decoder_provenance_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import importlib,json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase8_live_decoder_callable_certification.json"

TERMS={
 "PUMP_FUN":("pump_fun","pumpfun"),
 "PUMP_SWAP":("pump_swap","pumpswap"),
 "RAYDIUM_LAUNCHLAB":("raydium_launchlab","launchlab"),
 "RAYDIUM_V4":("raydium_v4","raydium"),
 "RAYDIUM_CLMM":("raydium_clmm","clmm"),
 "RAYDIUM_CPMM":("raydium_cpmm","cpmm"),
 "METEORA_DBC":("meteora_dbc","dbc"),
 "METEORA_DAMM_V1":("meteora_damm_v1","damm_v1"),
 "METEORA_DAMM_V2":("meteora_damm_v2","damm_v2"),
 "METEORA_DLMM":("meteora_dlmm","dlmm"),
 "ORCA":("orca",),
 "MOONIT":("moonit",),
 "BOOP_FUN":("boop_fun","boop"),
 "HEAVEN":("heaven",),
}

def _semantic_ok(fam,c):
 mod=(c.get("module") or "").lower()
 fn=(c.get("function") or "").lower()
 path=(c.get("path") or "").lower()
 hay=" ".join((mod,fn,path))
 if fam!="PUMP_SWAP" and "pumpswap" in fn:
  return False,"WRONG_FAMILY_FUNCTION_NAME"
 terms=TERMS[fam]
 if any(t in hay for t in terms):
  return True,"FAMILY_TERM_IN_MODULE_FUNCTION_OR_PATH"
 try:
  m=importlib.import_module(c["module"])
  src=Path(m.__file__).read_text(encoding="utf-8",errors="ignore").lower()
 except Exception:
  src=""
 if any(t in src for t in terms):
  return True,"FAMILY_TERM_IN_MODULE_SOURCE"
 return False,"NO_FAMILY_SPECIFIC_SEMANTIC_PROVENANCE"

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 result={};ready=[]
 for fam,cands in d.get("family_callable_candidates",{}).items():
  checked=[]
  for c in cands:
   if not c.get("callable"):continue
   ok,reason=_semantic_ok(fam,c)
   checked.append({**c,"semantic_ok":ok,"semantic_reason":reason})
  valid=[x for x in checked if x["semantic_ok"]]
  result[fam]={"valid_candidates":valid,"rejected_candidates":
               [x for x in checked if not x["semantic_ok"]],
               "selected":valid[0] if valid else None}
  if valid:ready.append(fam)
 return {"revision":"USLS_161F","family_count":len(result),
  "semantic_ready_family_count":len(ready),"semantic_ready_families":ready,
  "family_results":result,
  "invalid_cross_family_pumpswap_selection_count":
   sum(1 for fam,r in result.items() if fam!="PUMP_SWAP"
       for x in r["rejected_candidates"]
       if x.get("semantic_reason")=="WRONG_FAMILY_FUNCTION_NAME"),
  "gate_semantics":
   "CALLABLE_IS_INSUFFICIENT_FAMILY_SPECIFIC_DECODER_PROVENANCE_REQUIRED",
  "next_boundary":(
   "BUILD_DISPATCHER_ONLY_FOR_SEMANTICALLY_CERTIFIED_FAMILIES"
   if ready else
   "EXPOSE_FAMILY_SPECIFIC_DECODER_INTERFACES"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_family_semantic_decoder_provenance_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161f_phase8_family_semantic_decoder_provenance_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  sel={f:(None if r["selected"] is None else
      {"module":r["selected"]["module"],"function":r["selected"]["function"],
       "reason":r["selected"]["semantic_reason"]})
      for f,r in d["family_results"].items()}
  print("[STATE]",json.dumps({"semantic_ready_family_count":d["semantic_ready_family_count"],
   "semantic_ready_families":d["semantic_ready_families"],
   "invalid_cross_family_pumpswap_selection_count":
    d["invalid_cross_family_pumpswap_selection_count"],
   "selected":sel,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertGreater(d["invalid_cross_family_pumpswap_selection_count"],0,
   "EXPECTED_TO_DETECT_161E_CROSS_FAMILY_PUMPSWAP_FALSE_SELECTION")
  self.assertGreater(d["semantic_ready_family_count"],0,
   "NO_FAMILY_SPECIFIC_DECODER_PROVENANCE_FOUND")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161F family-semantic decoder provenance gate")
  print("[PASS] callable-only false positives rejected before live dispatcher")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
