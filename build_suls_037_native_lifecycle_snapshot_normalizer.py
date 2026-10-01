from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_037_native_lifecycle_snapshot_normalizer.py"
TEST=ROOT/"test_suls_037_native_lifecycle_snapshot_normalizer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from decimal import Decimal
def D(x):
 try:return Decimal(str(x))
 except Exception:return None
def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 raw=json.loads((b/"native_vault_balance_readback.json").read_text(encoding="utf-8"))
 birth=json.loads((b/"canonical_tradeable_native_birth_events.json").read_text(encoding="utf-8"))
 bm={x["event_id"]:x for x in birth.get("events",[])};rows=[]
 for x in raw.get("snapshots",[]):
  e=bm.get(x["event_id"]) or {};ta=D(x["token"].get("ui_amount_string"));qa=D(x["quote"].get("ui_amount_string"))
  ratio=(qa/ta) if ta and qa and ta!=0 else None
  bta=D(e.get("initial_token_amount"));bqa=D(e.get("initial_quote_amount"))
  br=(bqa/bta) if bta and bqa and bta!=0 else None
  ret=((ratio/br)-1) if ratio is not None and br not in (None,0) else None
  rows.append({"event_id":x["event_id"],"signature":x["signature"],"age_seconds":x["age_seconds"],
   "token_reserve":None if ta is None else str(ta),"quote_reserve":None if qa is None else str(qa),
   "quote_per_token":None if ratio is None else str(ratio),
   "return_from_birth":None if ret is None else str(ret),"execution_authority":False})
 return {"revision":"SULS_037","snapshot_count":len(rows),"snapshots":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_lifecycle_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_037_native_lifecycle_snapshot_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[LIFECYCLE_SNAPSHOT]",json.dumps(x,sort_keys=True))
  if not d["snapshots"]:self.fail("NO_LIFECYCLE_SNAPSHOT")
  if not any(x.get("quote_per_token") for x in d["snapshots"]):self.fail("NO_NATIVE_RATIO")
  print("[PASS] SULS-037 native lifecycle snapshot normalizer")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")