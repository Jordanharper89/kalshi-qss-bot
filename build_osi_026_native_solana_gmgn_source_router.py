from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_026_native_solana_gmgn_source_router.py"
TEST=ROOT/"test_osi_026_native_solana_gmgn_source_router.py"
MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path
NATIVE_MODULES=(
 "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py")
TOKENS=("runtime_state","runtime/","runtime\\\\",".json",".jsonl","postgres","table","pool","mint","swap","slot","signature")
def _scan(path:Path)->list[dict]:
 if not path.is_file():return []
 out=[]
 for n,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
  low=line.lower()
  if any(t in low for t in TOKENS):out.append({"line":n,"text":line[:600]})
 return out[:300]
def build_registry(root:Path)->dict:
 native=[]
 for rel in NATIVE_MODULES:
  p=root/rel
  if p.is_file():native.append({"module":rel,"lineage":_scan(p)})
 gmgn=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  if "gmgn" in p.name.lower() or "gmgn" in p.read_text(encoding="utf-8",errors="replace").lower():
   gmgn.append({"module":str(p.relative_to(root)),"lineage":_scan(p)})
 cb=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  if "coinbase" in p.name.lower():cb.append(str(p.relative_to(root)))
 return {"revision":"OSI_026","primary":{"native_solana":native,"gmgn":gmgn},
  "context_only":{"coinbase":cb},"policy":{"coinbase_can_create_opportunity":False,
  "native_solana_priority":1,"gmgn_priority":2,"coinbase_priority":3},
  "execution_authority":False,"read_only":True}
def write_registry(root:Path)->Path:
 d=build_registry(root);p=root/"runtime_state/solana_opportunities/source_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_026_native_solana_gmgn_source_router import build_registry,write_registry
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_router(self):
  d=build_registry(ROOT);p=write_registry(ROOT)
  self.assertGreater(len(d["primary"]["native_solana"]),0);self.assertFalse(d["policy"]["coinbase_can_create_opportunity"]);self.assertFalse(d["execution_authority"])
  print("[REGISTRY]",p);print("[NATIVE_MODULES]",len(d["primary"]["native_solana"]));print("[GMGN_MODULES]",len(d["primary"]["gmgn"]))
  print("[COINBASE_CONTEXT_MODULES]",len(d["context_only"]["coinbase"]))
  print("[PASS] OSI-026 native Solana + GMGN source router")
  print("[TRADER] Native Solana creates opportunities; GMGN enriches; Coinbase only describes broader SOL regime")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-026 NATIVE SOLANA + GMGN SOURCE ROUTER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
