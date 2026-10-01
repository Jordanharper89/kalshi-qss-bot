from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_004_birth_to_oracle_latency_measurement.py"
TEST=ROOT/"test_suls_004_birth_to_oracle_latency_measurement.py"

MOD_TEXT=r"""from __future__ import annotations
import json,statistics
from datetime import datetime
from pathlib import Path

def _dt(s):return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def measure(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/physical_multi_launcher_discovery.json"
 d=json.loads(src.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  ms=e.get("pair_created_at_ms")
  if ms is None:continue
  observed=_dt(e["oracle_observed_at"]).timestamp()
  created=float(ms)/1000.0
  latency=observed-created
  rows.append({"token_address":e["token_address"],"pair_address":e["pair_address"],
   "launcher_family":e["launcher_family"],"latency_seconds":latency,"nonnegative":latency>=0})
 vals=[x["latency_seconds"] for x in rows if x["nonnegative"]]
 return {"revision":"SULS_004","measured":len(rows),"valid_nonnegative":len(vals),
  "min_seconds":None if not vals else min(vals),"median_seconds":None if not vals else statistics.median(vals),
  "max_seconds":None if not vals else max(vals),"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=measure(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_to_oracle_latency.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_004_birth_to_oracle_latency_measurement import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[MEASURED]",d["measured"]);print("[VALID_NONNEGATIVE]",d["valid_nonnegative"])
  print("[MIN_SECONDS]",d["min_seconds"]);print("[MEDIAN_SECONDS]",d["median_seconds"]);print("[MAX_SECONDS]",d["max_seconds"])
  for x in d["rows"][:20]:print("[LATENCY]",json.dumps(x,sort_keys=True))
  if d["valid_nonnegative"]==0:self.fail("NO_VALID_BIRTH_TO_ORACLE_LATENCY")
  print("[PASS] SULS-004 physical birth-to-Oracle latency measurement")
  print("[SCOPE] Measures current discovery latency; does not claim sub-second native birth detection")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-004 BIRTH-TO-ORACLE LATENCY MEASUREMENT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
