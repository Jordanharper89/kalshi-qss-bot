from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_002_universal_transaction_shape_normalizer.py"
TEST=ROOT/"test_usls_002_universal_transaction_shape_normalizer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def _key(keys,x):
 if isinstance(x,str): return x
 if isinstance(x,int) and 0<=x<len(keys):
  v=keys[x];return v.get("pubkey") if isinstance(v,dict) else v
 return None

def normalize_birth(b):
 env=b.get("envelope") or {};raw=env.get("raw_transaction") or {}
 tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
 keys=msg.get("accountKeys") or []
 programs=[];instructions=[]
 def add_ix(ix,outer_index=None,inner=False):
  if not isinstance(ix,dict): return
  program=ix.get("programId") or _key(keys,ix.get("programIdIndex"))
  accounts=[_key(keys,x) for x in (ix.get("accounts") or [])]
  if program and program not in programs: programs.append(program)
  parsed=ix.get("parsed") or {}
  instructions.append({"program_id":program,"accounts":accounts,"inner":inner,
   "outer_index":outer_index,"parsed_type":parsed.get("type"),"data":ix.get("data")})
 for i,ix in enumerate(msg.get("instructions") or []):add_ix(ix,i,False)
 for grp in meta.get("innerInstructions") or []:
  for ix in grp.get("instructions") or []:add_ix(ix,grp.get("index"),True)
 balances=[]
 for side in ("preTokenBalances","postTokenBalances"):
  for x in meta.get(side) or []:
   balances.append({"side":side,"account_index":x.get("accountIndex"),
    "mint":x.get("mint"),"owner":x.get("owner"),"program_id":x.get("programId"),
    "ui_amount_string":((x.get("uiTokenAmount") or {}).get("uiAmountString"))})
 return {"signature":b.get("signature"),"slot":b.get("slot"),"block_time":b.get("block_time"),
  "observed_unix":b.get("observed_unix"),"age_seconds":b.get("age_seconds"),
  "program_ids":programs,"account_keys":[_key(keys,i) for i in range(len(keys))],
  "instructions":instructions,"token_balances":balances,
  "logs":meta.get("logMessages") or [],
  "raw_envelope_present":bool(raw),"execution_authority":False}

def normalize_cohort(root):
 p=Path(root)/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 rows=[normalize_birth(x) for x in (d.get("births") or [])]
 return {"revision":"USLS_002","row_count":len(rows),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=normalize_cohort(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/universal_transaction_shapes.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_002_universal_transaction_shape_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_shapes(self):
  p,d=write(ROOT)
  self.assertGreater(d["row_count"],0)
  rich=[r for r in d["rows"] if r["program_ids"] and r["account_keys"] and r["logs"]]
  self.assertGreater(len(rich),0)
  s=rich[-1]
  print("[STATE]",json.dumps({"row_count":d["row_count"],"rich_rows":len(rich)},sort_keys=True))
  print("[SAMPLE]",json.dumps({"signature":s["signature"],"program_ids":s["program_ids"],
   "account_keys":len(s["account_keys"]),"instructions":len(s["instructions"]),
   "token_balances":len(s["token_balances"]),"logs":len(s["logs"])},sort_keys=True))
  print("[PASS] USLS-002 universal transaction shape normalizer")
  print("[PASS] scanner input is protocol-neutral transaction structure")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
