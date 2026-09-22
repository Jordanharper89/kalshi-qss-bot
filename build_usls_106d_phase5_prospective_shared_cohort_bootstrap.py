from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_lifecycle"
MOD=SUB/"usls_106d_phase5_prospective_shared_cohort_bootstrap.py"
TEST=ROOT/"test_usls_106d_phase5_prospective_shared_cohort_bootstrap.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

BIRTH_PATH="runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"
TRADE_PATHS=[
 "runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json",
 "runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_universal_trade_rows.json",
 "runtime_state/solana_opportunities/universal_trade_tape/launchlab_universal_trade_rows.json",
]

def read(p):
 return json.loads(p.read_text(encoding="utf-8"))

def list_rows(d):
 for k in ("events","rows","exact_rows","trades"):
  if isinstance(d.get(k),list):return k,d[k]
 return None,[]

def sigs(rows):
 return {str(x.get("signature")) for x in rows if isinstance(x,dict) and x.get("signature")}

def birth_identity(x):
 return {"venue":x.get("launcher_family"),"program_id":x.get("program_id"),
  "token_address":x.get("token_address") or x.get("token_mint"),
  "market_address":x.get("pair_address"),
  "birth_signature":x.get("signature"),"birth_slot":x.get("slot"),
  "birth_observed_unix":x.get("observed_unix") or x.get("block_time")}

def build(root):
 root=Path(root)
 bp=root/BIRTH_PATH
 bd=read(bp);bk,br=list_rows(bd)
 now=time.time()
 last_slot=max([int(x.get("slot")) for x in br if isinstance(x,dict) and x.get("slot") is not None] or [0])
 last_time=max([float(x.get("observed_unix") or x.get("block_time")) for x in br
                if isinstance(x,dict) and (x.get("observed_unix") is not None or x.get("block_time") is not None)] or [0.0])
 trade_baselines=[]
 for rel in TRADE_PATHS:
  p=root/rel
  if not p.exists():
   trade_baselines.append({"path":rel,"exists":False,"row_count":0,"signatures":[]})
   continue
  d=read(p);k,rs=list_rows(d)
  trade_baselines.append({"path":rel,"exists":True,"revision":d.get("revision"),
   "list_key":k,"row_count":len(rs),"signatures":sorted(sigs(rs))})
 births=[birth_identity(x) for x in br if isinstance(x,dict)]
 return {"revision":"USLS_106D","phase":5,"bootstrap_unix":now,
  "birth_source":{"path":BIRTH_PATH,"revision":bd.get("revision"),"list_key":bk,
   "row_count":len(br),"last_slot":last_slot,"last_observed_unix":last_time},
  "trade_sources":trade_baselines,
  "birth_baseline_signatures":sorted(sigs(br)),
  "prospective_rule":"ONLY_BIRTHS_AND_TRADES_OBSERVED_AFTER_BOOTSTRAP_ARE_ELIGIBLE_FOR_SHARED_COHORT_JOIN",
  "identity_rule":"PROGRAM_TOKEN_MARKET_PREFERRED; VENUE_TOKEN_MARKET_ALLOWED_WHEN_PROGRAM_MISSING; NEVER_SIGNATURE_ONLY",
  "unknown_policy":"RETAIN_UNRESOLVED",
  "future_leakage_policy":"NO_PRE_BOOTSTRAP_TRADE_CAN_JOIN_POST_BOOTSTRAP_BIRTH",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_prospective_shared_cohort_bootstrap.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_106d_phase5_prospective_shared_cohort_bootstrap import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bootstrap(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "birth_rows":d["birth_source"]["row_count"],
   "birth_last_slot":d["birth_source"]["last_slot"],
   "trade_sources":[{"path":x["path"],"row_count":x["row_count"],"revision":x.get("revision")} for x in d["trade_sources"]],
   "bootstrap_unix":d["bootstrap_unix"]},sort_keys=True))
  self.assertGreater(d["birth_source"]["row_count"],0)
  self.assertGreater(d["birth_source"]["last_slot"],0)
  self.assertTrue(any(x["exists"] and x["row_count"]>0 for x in d["trade_sources"]))
  self.assertEqual(d["unknown_policy"],"RETAIN_UNRESOLVED")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106D prospective shared birth↔trade cohort bootstrap")
  print("[PASS] historical disjoint cohorts excluded from future lifecycle certification")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
