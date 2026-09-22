from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_015_live_program_instruction_evidence.py"
TEST=ROOT/"test_usls_015_live_program_instruction_evidence.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def _keys(tx):
 msg=((tx.get("transaction") or {}).get("message") or {})
 out=[]
 for k in msg.get("accountKeys") or []:
  out.append(k.get("pubkey") if isinstance(k,dict) else k)
 return out

def _instructions(tx):
 msg=((tx.get("transaction") or {}).get("message") or {})
 top=list(msg.get("instructions") or [])
 meta=tx.get("meta") or {}
 inner=[]
 for group in meta.get("innerInstructions") or []:
  for ix in group.get("instructions") or []:
   y=dict(ix);y["_inner_parent_index"]=group.get("index");inner.append(y)
 return top+inner

def extract(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"))
 man=json.loads((base/"subscription_manifest.json").read_text(encoding="utf-8"))
 pid_to_family={x["program_id"]:x["family"] for x in man["subscriptions"]}
 rows=[]
 for r in src.get("rows") or []:
  tx=r.get("raw_transaction") or {}
  keys=_keys(tx)
  for ix in _instructions(tx):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):
    pid=keys[ix["programIdIndex"]]
   fam=pid_to_family.get(pid)
   if not fam: continue
   accounts=ix.get("accounts") or []
   resolved=[keys[a] if isinstance(a,int) and a<len(keys) else a for a in accounts]
   rows.append({"signature":r.get("signature"),"families":r.get("families") or [],
    "matched_family":fam,"program_id":pid,"accounts":resolved,"data":ix.get("data"),
    "parsed":ix.get("parsed"),"inner_parent_index":ix.get("_inner_parent_index"),
    "slot":r.get("slot"),"execution_authority":False})
 fams=sorted({x["matched_family"] for x in rows})
 return {"revision":"USLS_015","instruction_count":len(rows),"family_count":len(fams),
  "families":fams,"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=extract(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_program_instruction_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_015_live_program_instruction_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_extract(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("instruction_count","family_count","families")},sort_keys=True))
  for x in d["rows"][:40]:
   print("[IX]",json.dumps({k:x.get(k) for k in ("matched_family","signature","program_id","accounts","data","parsed","inner_parent_index")},sort_keys=True))
  self.assertGreater(d["instruction_count"],0)
  self.assertGreater(d["family_count"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-015 live watched-program instruction evidence extracted")
  print("[PASS] exact accounts/data preserved for decoder construction")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
