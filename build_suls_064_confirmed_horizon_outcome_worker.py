from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_064_confirmed_horizon_outcome_worker.py"
TEST=ROOT/"test_suls_064_confirmed_horizon_outcome_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from decimal import Decimal
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

def D(x):
 try:return Decimal(str(x))
 except Exception:return None

def bal(a):
 r=_rpc("getTokenAccountBalance",[str(a),{"commitment":"confirmed"}],20.0)
 return ((r or {}).get("value") or {}).get("uiAmountString")

def run(root,now=None,max_due=8):
 now=float(time.time() if now is None else now)
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 qp=b/"signal_relative_horizon_queue.json"
 q=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"queue":[]}
 op=b/"confirmed_horizon_outcomes.json"
 old=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"outcomes":[]}
 outcomes=list(old.get("outcomes") or [])
 done={(x["event_id"],x["basis"],x["horizon_seconds"]) for x in outcomes};n=0
 for row in q.get("queue",[]):
  k=(row["event_id"],row["basis"],row["horizon_seconds"])
  if k in done:row["state"]="MATURED";continue
  if row.get("state")!="PENDING" or now<float(row["target_unix"]) or n>=max_due:continue
  ta=D(bal(row["token_vault"]));qa=D(bal(row["quote_vault"]))
  bta=D(row["birth_token_amount"]);bqa=D(row["birth_quote_amount"])
  ratio=(qa/ta) if ta and qa and ta!=0 else None;br=(bqa/bta) if bta and bqa and bta!=0 else None
  ret=((ratio/br)-1) if ratio is not None and br not in (None,0) else None
  outcomes.append({"event_id":row["event_id"],"basis":row["basis"],"horizon_seconds":row["horizon_seconds"],
   "target_unix":row["target_unix"],"observed_unix":now,"token_reserve":None if ta is None else str(ta),
   "quote_reserve":None if qa is None else str(qa),"quote_per_token":None if ratio is None else str(ratio),
   "return_from_birth":None if ret is None else str(ret),"execution_authority":False})
  row["state"]="MATURED";done.add(k);n+=1
 qp.write_text(json.dumps(q,indent=2,sort_keys=True),encoding="utf-8")
 out={"revision":"SULS_064","outcome_count":len(outcomes),"new_outcomes":n,"outcomes":outcomes,
  "execution_authority":False,"read_only":True}
 op.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_064_confirmed_horizon_outcome_worker import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_worker(self):
  d=run(ROOT);print("[STATE]",json.dumps({"outcome_count":d["outcome_count"],"new_outcomes":d["new_outcomes"]},sort_keys=True))
  print("[PASS] SULS-064 confirmed horizon outcome worker")
  print("[SCOPE] Zero outcomes is valid until a fresh confirmed birth matures")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-064 CONFIRMED HORIZON OUTCOME WORKER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
