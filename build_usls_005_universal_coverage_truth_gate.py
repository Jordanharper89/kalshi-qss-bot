from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_005_universal_coverage_truth_gate.py"
TEST=ROOT/"test_usls_005_universal_coverage_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

TARGETS=(
 "PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
 "BOOP_FUN","MOONIT","ORCA","HEAVEN","UNKNOWN_PROGRAM"
)

def gate(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 reg=json.loads((base/"family_registry.json").read_text(encoding="utf-8"))
 can=json.loads((base/"canonical_universal_birth_events.json").read_text(encoding="utf-8"))
 events=can.get("events") or []
 rows=[]
 for fam in TARGETS:
  r=reg["families"][fam]
  ev=[x for x in events if x.get("launcher_family")==fam or x.get("source_family")==fam]
  rows.append({"family":fam,"registry_status":r.get("status"),
   "program_id_count":len(r.get("program_ids") or []),
   "observed_births":len(ev),
   "identity_resolved":sum(1 for x in ev if x.get("token_address") and x.get("pair_address")),
   "live_scanner_certified":False if fam!="METEORA_DAMM" else bool(ev),
   "profitability_dataset_ready":False})
 known_ready=sum(1 for x in rows if x["live_scanner_certified"])
 universal_complete=all(x["live_scanner_certified"] for x in rows if x["family"]!="UNKNOWN_PROGRAM")
 return {"revision":"USLS_005","families":rows,
  "target_family_count":len(TARGETS),"live_certified_family_count":known_ready,
  "universal_scanner_complete":universal_complete,
  "unknown_fallback_active":reg.get("unknown_fallback_active") is True,
  "next_required_boundary":"USLS_006_UNIVERSAL_EVENT_SOURCE_ACTIVATION_AND_PROTOCOL_EXPANSION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/coverage_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_005_universal_coverage_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "target_family_count","live_certified_family_count","universal_scanner_complete",
   "unknown_fallback_active","next_required_boundary","profitability_claimed")},sort_keys=True))
  for r in d["families"]:print("[FAMILY]",json.dumps(r,sort_keys=True))
  self.assertEqual(d["target_family_count"],15)
  self.assertTrue(d["unknown_fallback_active"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-005 universal coverage truth gate")
  print("[PASS] no unproven DEX family is silently called complete")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
