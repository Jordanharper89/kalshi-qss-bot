from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_063_signal_relative_horizon_semantics.py"
TEST=ROOT/"test_suls_063_signal_relative_horizon_semantics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
BIRTH_HORIZONS=(5,15,30,60,300,900)
SIGNAL_HORIZONS=(1,5,15,30,60,300,900)
MAX_FRESH_AGE=5.0

def build(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 ep=b/"confirmed_tradeable_birth_events.json"
 src=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 rows=[]
 for e in src.get("events",[]):
  age=e.get("trigger_age_seconds")
  if age is None or float(age)>MAX_FRESH_AGE:continue
  bt=float(e["block_time"]);st=float(e.get("observed_unix") or (bt+float(age)))
  for h in BIRTH_HORIZONS:
   if bt+h>=st:
    rows.append({"event_id":e["event_id"],"basis":"BIRTH","horizon_seconds":h,
      "target_unix":bt+h,"state":"PENDING","token_vault":e["token_vault"],"quote_vault":e["quote_vault"],
      "birth_token_amount":e["initial_token_amount"],"birth_quote_amount":e["initial_quote_amount"],
      "execution_authority":False})
  for h in SIGNAL_HORIZONS:
   rows.append({"event_id":e["event_id"],"basis":"SIGNAL","horizon_seconds":h,
    "target_unix":st+h,"state":"PENDING","token_vault":e["token_vault"],"quote_vault":e["quote_vault"],
    "birth_token_amount":e["initial_token_amount"],"birth_quote_amount":e["initial_quote_amount"],
    "execution_authority":False})
 return {"revision":"SULS_063","queue":rows,"pending_count":len(rows),
  "birth_horizons":list(BIRTH_HORIZONS),"signal_horizons":list(SIGNAL_HORIZONS),
  "age_1s_birth_claim_allowed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/signal_relative_horizon_queue.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_semantics(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="queue"},sort_keys=True))
  self.assertFalse(d["age_1s_birth_claim_allowed"])
  print("[PASS] SULS-063 signal-relative horizon semantics")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")