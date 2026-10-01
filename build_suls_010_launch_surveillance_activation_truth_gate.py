from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_010_launch_surveillance_activation_truth_gate.py";TEST=ROOT/"test_suls_010_launch_surveillance_activation_truth_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 lat=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/discovery_latency_truth_gate.json").read_text(encoding="utf-8"))
 native=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/native_event_source_resolver.json").read_text(encoding="utf-8"))
 nxt="SULS_011_PHYSICAL_NATIVE_POOL_BIRTH_ACTIVATION" if native.get("native_event_candidate_found") else "SULS_011_NATIVE_SOLANA_BIRTH_SENSOR_FOUNDATION"
 return {"revision":"SULS_010","dexscreener_role":lat.get("classified_role"),
 "native_event_candidate_found":native.get("native_event_candidate_found"),"best_candidate":native.get("best_candidate"),
 "high_frequency_activation_ready":False,"next_required_boundary":nxt,"execution_authority":False}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_010_launch_surveillance_activation_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[DEXSCREENER_ROLE]",d["dexscreener_role"]);print("[NATIVE_EVENT_CANDIDATE_FOUND]",d["native_event_candidate_found"])
  print("[BEST_CANDIDATE]",json.dumps(d["best_candidate"],sort_keys=True));print("[HIGH_FREQUENCY_ACTIVATION_READY]",d["high_frequency_activation_ready"])
  print("[NEXT_REQUIRED_BOUNDARY]",d["next_required_boundary"]);print("[PASS] SULS-010 launch surveillance activation truth gate")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)