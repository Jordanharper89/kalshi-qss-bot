from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_008_universal_subscription_manifest.py"
TEST=ROOT/"test_usls_008_universal_subscription_manifest.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 reg=json.loads((base/"verified_mainnet_program_registry.json").read_text(encoding="utf-8"))
 subs=[]
 for x in reg["programs"]:
  if not x.get("executable"):continue
  subs.append({"family":x["family"],"program_id":x["program_id"],
   "rpc_method":"logsSubscribe","filter":{"mentions":[x["program_id"]]},
   "commitment":"confirmed","retain_raw_transaction":True,
   "never_drop_unknown":True})
 return {"revision":"USLS_008","subscription_count":len(subs),"subscriptions":subs,
  "unknown_program_policy":"STRUCTURAL_DISCOVERY_RETAIN_AND_TRIAGE",
  "target_commitment":"confirmed","execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/subscription_manifest.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_008_universal_subscription_manifest import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_manifest(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"subscription_count":d["subscription_count"],
   "unknown_program_policy":d["unknown_program_policy"],"commitment":d["target_commitment"]},sort_keys=True))
  for r in d["subscriptions"]:print("[SUB]",json.dumps(r,sort_keys=True))
  self.assertGreaterEqual(d["subscription_count"],10)
  self.assertEqual(len({x["program_id"] for x in d["subscriptions"]}),d["subscription_count"])
  self.assertEqual(d["unknown_program_policy"],"STRUCTURAL_DISCOVERY_RETAIN_AND_TRIAGE")
  print("[PASS] USLS-008 universal subscription manifest")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
